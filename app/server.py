import logging
import os
import re
import socket
import threading

from app import auth, storage

from app.protocol import (
    MAX_FILE_SIZE,
    recv_json,
    send_json,
    receive_file,
    send_file,
    calculate_sha256
)

HOST = "0.0.0.0"
PORT = 5000

SHARED_DIR = "shared_files"
LOG_DIR = "logs"

os.makedirs(SHARED_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    filename=os.path.join(LOG_DIR, "server.log"),
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

def valid_filename(filename):
    return (
        isinstance(filename, str)
        and bool(filename)
        and filename not in (".", "..")
        and filename == os.path.basename(filename)
        and "/" not in filename
        and "\\" not in filename
        and "\x00" not in filename
    )

def handle_client(client_socket, client_address):
    username = None

    print("[CONNECTED]", client_address)

    try:
        while True:

            request = recv_json(client_socket)
            command = str(request.get("type", "")).upper()

            # REGISTER
            if command == "REGISTER":

                new_username = request.get("username", "")
                password = request.get("password", "")

                if not isinstance(new_username, str) or not isinstance(password, str):
                    send_json(client_socket, {
                        "status": "error",
                        "message": "Invalid username or password"
                    })

                elif auth.register_user(new_username, password):
                    send_json(client_socket, {
                        "status": "success",
                        "message": "Registration successful"
                    })

                else:
                    send_json(client_socket, {
                        "status": "error",
                        "message": "Registration failed. Username may exist or password must be at least 8 characters."
                    })

            # LOGIN
            elif command == "LOGIN":

                login_name = request.get("username", "")
                password = request.get("password", "")

                if not isinstance(login_name, str) or not isinstance(password, str):
                    send_json(client_socket, {
                        "status": "error",
                        "message": "Invalid credentials"
                    })

                elif auth.authenticate_user(login_name, password):
                    username = login_name

                    send_json(client_socket, {
                        "status": "success",
                        "message": "Login successful"
                    })

                    logging.info("LOGIN SUCCESS: %s", username)

                else:
                    send_json(client_socket, {
                        "status": "error",
                        "message": "Invalid username or password"
                    })

            # LOGOUT
            elif command == "LOGOUT":

                username = None

                send_json(client_socket, {
                    "status": "success",
                    "message": "Logged out"
                })

            # FILE OPERATIONS
            elif command in ("LIST", "LIST_FILES", "UPLOAD", "DOWNLOAD"):

                if username is None:
                    send_json(client_socket, {
                        "status": "error",
                        "message": "Please login first"
                    })
                    continue

                # LIST FILES
                if command in ("LIST", "LIST_FILES"):

                    available = []

                    for item in storage.list_files():
                        path = os.path.join(SHARED_DIR, item["filename"])

                        if os.path.isfile(path):
                            available.append(item)

                    send_json(client_socket, {
                        "status": "success",
                        "files": available
                    })

                # UPLOAD FILE
                elif command == "UPLOAD":

                    filename = request.get("filename", "")
                    expected_size = request.get("file_size")
                    expected_hash = request.get("sha256", "")

                    if not valid_filename(filename):
                        send_json(client_socket, {
                            "status": "error",
                            "message": "Invalid filename"
                        })
                        continue

                    if (
                        not isinstance(expected_size, int)
                        or isinstance(expected_size, bool)
                        or expected_size < 0
                        or expected_size > MAX_FILE_SIZE
                    ):
                        send_json(client_socket, {
                            "status": "error",
                            "message": "Invalid file size"
                        })
                        continue

                    if (
                        not isinstance(expected_hash, str)
                        or not re.fullmatch(r"[0-9a-fA-F]{64}", expected_hash)
                    ):
                        send_json(client_socket, {
                            "status": "error",
                            "message": "Invalid SHA-256 value"
                        })
                        continue

                    final_path = os.path.join(SHARED_DIR, filename)
                    temp_path = final_path + ".part"

                    if os.path.exists(final_path):
                        send_json(client_socket, {
                            "status": "error",
                            "message": "File already exists"
                        })
                        continue

                    send_json(client_socket, {
                        "status": "ready",
                        "message": "Send file data"
                    })

                    try:
                        actual_size = receive_file(client_socket, temp_path)

                        if actual_size != expected_size:
                            raise ValueError("File size mismatch")

                        actual_hash = calculate_sha256(temp_path)

                        if actual_hash.lower() != expected_hash.lower():
                            raise ValueError("SHA-256 verification failed")

                        # Avoid replacing an existing file
                        os.link(temp_path, final_path)
                        os.remove(temp_path)

                        try:
                            file_id = storage.add_file(
                                filename,
                                username,
                                actual_size,
                                actual_hash
                            )

                        except Exception:
                            if os.path.exists(final_path):
                                os.remove(final_path)
                            raise

                        send_json(client_socket, {
                            "status": "success",
                            "message": "File uploaded and verified",
                            "file_id": file_id,
                            "sha256": actual_hash
                        })

                        logging.info(
                            "UPLOAD SUCCESS: user=%s file=%s",
                            username,
                            filename
                        )

                        print("[UPLOAD]", username, filename)

                    except Exception as error:

                        if os.path.exists(temp_path):
                            os.remove(temp_path)

                        send_json(client_socket, {
                            "status": "error",
                            "message": str(error)
                        })

                        if isinstance(
                            error,
                            (ConnectionError, BrokenPipeError, ConnectionResetError)
                        ):
                            raise

                # DOWNLOAD FILE
                elif command == "DOWNLOAD":

                    try:
                        file_id = int(request.get("file_id"))
                    except (TypeError, ValueError):
                        send_json(client_socket, {
                            "status": "error",
                            "message": "Invalid file ID"
                        })
                        continue

                    item = storage.get_file_by_id(file_id)

                    if item is None:
                        send_json(client_socket, {
                            "status": "error",
                            "message": "File not found"
                        })
                        continue

                    filepath = os.path.join(SHARED_DIR, item["filename"])

                    if not os.path.isfile(filepath):
                        send_json(client_socket, {
                            "status": "error",
                            "message": "File missing from server"
                        })
                        continue

                    send_json(client_socket, {
                        "status": "ready",
                        "filename": item["filename"],
                        "file_size": item["file_size"],
                        "sha256": item["sha256"]
                    })

                    send_file(client_socket, filepath)

                    logging.info(
                        "DOWNLOAD SUCCESS: user=%s file=%s",
                        username,
                        item["filename"]
                    )

                    print("[DOWNLOAD]", username, item["filename"])

            else:
                send_json(client_socket, {
                    "status": "error",
                    "message": "Unknown command"
                })

    except (ConnectionError, BrokenPipeError, ConnectionResetError) as error:
        logging.info("Client disconnected: %s | %s", client_address, error)

    except Exception:
        logging.exception("Client handler failed: %s", client_address)

    finally:
        client_socket.close()
        print("[DISCONNECTED]", client_address)

def start_server():

    storage.init_db()

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    server.bind((HOST, PORT))
    server.listen()

    print(f"[SERVER] Listening on {HOST}:{PORT}")

    try:
        while True:

            client_socket, client_address = server.accept()

            thread = threading.Thread(
                target=handle_client,
                args=(client_socket, client_address),
                daemon=True
            )

            thread.start()

    except KeyboardInterrupt:
        print("\n[SERVER] Shutting down")

    finally:
        server.close()

if __name__ == "__main__":
    start_server()
