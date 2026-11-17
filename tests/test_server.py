import socket
import threading
import time
import tempfile
import os

from app import storage
from app.protocol import (
    send_json,
    recv_json,
    send_file,
    receive_file,
    calculate_sha256
)

HOST = "127.0.0.1"
PORT = 5000


def test_server():
    username = "server_test_user"
    password = "ServerTest123"

    with tempfile.TemporaryDirectory() as temp_dir:

        source_file = os.path.join(temp_dir, "test_upload.txt")
        downloaded_file = os.path.join(temp_dir, "downloaded.txt")

        with open(source_file, "w") as file:
            file.write("Testing complete server functionality.")

        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            client.connect((HOST, PORT))
            print("Connected to server!")

            # TEST 1: REGISTER
            send_json(client, {
                "type": "REGISTER",
                "username": username,
                "password": password
            })

            response = recv_json(client)
            print("Registration:", response)

            # TEST 2: LOGIN
            send_json(client, {
                "type": "LOGIN",
                "username": username,
                "password": password
            })

            response = recv_json(client)
            assert response["status"] == "success"
            print("PASS: Login")

            # TEST 3: LIST FILES
            send_json(client, {"type": "LIST"})
            response = recv_json(client)

            assert response["status"] == "success"
            print("PASS: File listing")

            # TEST 4: UPLOAD FILE
            filename = "server_test_upload.txt"
            file_size = os.path.getsize(source_file)
            file_hash = calculate_sha256(source_file)

            send_json(client, {
                "type": "UPLOAD",
                "filename": filename,
                "file_size": file_size,
                "sha256": file_hash
            })

            response = recv_json(client)
            assert response["status"] == "ready"

            send_file(client, source_file)

            response = recv_json(client)
            assert response["status"] == "success"

            file_id = response["file_id"]
            print("PASS: File upload")

            # TEST 5: DOWNLOAD FILE
            send_json(client, {
                "type": "DOWNLOAD",
                "file_id": file_id
            })

            response = recv_json(client)
            assert response["status"] == "ready"

            receive_file(client, downloaded_file)

            assert os.path.exists(downloaded_file)

            original_hash = calculate_sha256(source_file)
            downloaded_hash = calculate_sha256(downloaded_file)

            assert original_hash == downloaded_hash
            print("PASS: File download")
            print("PASS: Download SHA-256 verification")

            # TEST 6: LOGOUT
            send_json(client, {"type": "LOGOUT"})
            response = recv_json(client)

            assert response["status"] == "success"
            print("PASS: Logout")

        finally:
            client.close()


if __name__ == "__main__":
    test_server()
