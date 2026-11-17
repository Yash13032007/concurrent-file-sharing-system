import hashlib
import os
import socket

from app.protocol import (
    CHUNK_SIZE,
    MAX_FILE_SIZE,
    calculate_sha256,
    recv_exact,
    recv_json,
    send_json
)

SERVER_IP = os.environ.get("FILESHARE_SERVER", "127.0.0.1")
SERVER_PORT = int(os.environ.get("FILESHARE_PORT", "5000"))

DOWNLOAD_DIR = "downloads"

def connect_server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((SERVER_IP, SERVER_PORT))

    print("Connected to server:", SERVER_IP)

    return sock

def register(sock):
    username = input("Choose username: ").strip()
    password = input("Choose password (minimum 8 characters): ")

    send_json(sock, {
        "type": "REGISTER",
        "username": username,
        "password": password
    })

    response = recv_json(sock)

    print(response.get("message", response.get("status")))

def login(sock):
    username = input("Username: ").strip()
    password = input("Password: ")

    send_json(sock, {
        "type": "LOGIN",
        "username": username,
        "password": password
    })

    response = recv_json(sock)

    print(response.get("message", response.get("status")))

    if response.get("status") == "success":
        return username

    return None

def list_files(sock):
    send_json(sock, {"type": "LIST"})

    response = recv_json(sock)

    if response.get("status") != "success":
        print(response.get("message"))
        return

    files = response.get("files", [])

    if not files:
        print("No files available.")
        return

    print("\nAvailable files:")

    for item in files:
        print(
            f"ID: {item['file_id']} | "
            f"Name: {item['filename']} | "
            f"Owner: {item['owner']} | "
            f"Size: {item['file_size']} bytes"
        )

def upload_file(sock):
    filepath = input("Enter file path: ").strip().strip('"')

    if not os.path.isfile(filepath):
        print("File not found!")
        return

    filename = os.path.basename(filepath)
    file_size = os.path.getsize(filepath)

    if file_size > MAX_FILE_SIZE:
        print("File exceeds maximum allowed size.")
        return

    file_hash = calculate_sha256(filepath)

    send_json(sock, {
        "type": "UPLOAD",
        "filename": filename,
        "file_size": file_size,
        "sha256": file_hash
    })

    response = recv_json(sock)

    if response.get("status") != "ready":
        print(response.get("message"))
        return

    # Send 8-byte file-size prefix first
    sock.sendall(file_size.to_bytes(8, "big"))

    # Send file data
    with open(filepath, "rb") as file:
        while True:
            chunk = file.read(CHUNK_SIZE)

            if not chunk:
                break

            sock.sendall(chunk)

    response = recv_json(sock)

    print(response.get("message", response.get("status")))

    if response.get("status") == "success":
        print("Upload completed.")
        print("SHA-256:", response.get("sha256"))

def download_file(sock):
    try:
        file_id = int(input("Enter file ID: "))
    except ValueError:
        print("Invalid file ID.")
        return

    send_json(sock, {
        "type": "DOWNLOAD",
        "file_id": file_id
    })

    response = recv_json(sock)

    if response.get("status") != "ready":
        print(response.get("message"))
        return

    filename = os.path.basename(response["filename"])
    expected_size = int(response["file_size"])
    expected_hash = response["sha256"]

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    filepath = os.path.join(DOWNLOAD_DIR, filename)
    temp_path = filepath + ".part"

    digest = hashlib.sha256()

    try:
        # Receive 8-byte file-size prefix
        received_size = int.from_bytes(
            recv_exact(sock, 8),
            "big"
        )

        if received_size != expected_size or received_size > MAX_FILE_SIZE:
            raise ValueError("File size mismatch")

        # Receive file data
        with open(temp_path, "wb") as file:
            remaining = received_size

            while remaining > 0:
                chunk = recv_exact(
                    sock,
                    min(CHUNK_SIZE, remaining)
                )

                file.write(chunk)
                digest.update(chunk)

                remaining -= len(chunk)

        actual_hash = digest.hexdigest()

        if actual_hash.lower() != expected_hash.lower():
            raise ValueError("SHA-256 verification failed")

        os.replace(temp_path, filepath)

        print("Download successful:", filepath)
        print("SHA-256 verification passed.")

    except Exception:
        if os.path.exists(temp_path):
            os.remove(temp_path)

        raise

def main():
    sock = connect_server()

    try:
        print("\n===== FILE SHARING SYSTEM =====")
        print("1. Register")
        print("2. Login")

        choice = input("Choose option: ").strip()

        if choice == "1":
            register(sock)
            return

        elif choice == "2":
            username = login(sock)

            if username is None:
                return

        else:
            print("Invalid option.")
            return

        while True:
            print("\n===== FILE SHARING MENU =====")
            print("1. List files")
            print("2. Upload file")
            print("3. Download file")
            print("4. Logout")

            choice = input("Enter choice: ").strip()

            if choice == "1":
                list_files(sock)

            elif choice == "2":
                upload_file(sock)

            elif choice == "3":
                download_file(sock)

            elif choice == "4":
                send_json(sock, {"type": "LOGOUT"})

                response = recv_json(sock)

                print(response.get("message", "Logged out"))
                break

            else:
                print("Invalid choice.")

    except (ConnectionError, OSError, ValueError, KeyError) as error:
        print("Error:", error)

    finally:
        sock.close()

if __name__ == "__main__":
    main()
