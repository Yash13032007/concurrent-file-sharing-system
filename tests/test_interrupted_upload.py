import socket
import os
import time
import hashlib

from app.protocol import send_json, recv_json

HOST = "127.0.0.1"
PORT = 5000

USERNAME = "server_test_user"
PASSWORD = "ServerTest123"

FILENAME = "interrupted_test.txt"
TEMP_FILE = os.path.join("shared_files", FILENAME + ".part")
FINAL_FILE = os.path.join("shared_files", FILENAME)


def test_interrupted_upload():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        client.connect((HOST, PORT))
        print("Connected to server")

        # Login
        send_json(client, {
            "type": "LOGIN",
            "username": USERNAME,
            "password": PASSWORD
        })

        response = recv_json(client)
        assert response["status"] == "success"
        print("PASS: Login")

        # Prepare upload metadata
        file_size = 1000
        expected_hash = hashlib.sha256(b"A" * file_size).hexdigest()

        send_json(client, {
            "type": "UPLOAD",
            "filename": FILENAME,
            "file_size": file_size,
            "sha256": expected_hash
        })

        response = recv_json(client)
        assert response["status"] == "ready"
        print("PASS: Server accepted upload")

        # Send size prefix and only part of the file
        client.sendall(file_size.to_bytes(8, "big"))
        client.sendall(b"A" * 100)

        print("Interrupting upload...")
        client.close()

        # Allow server thread to process disconnect
        time.sleep(1)

        assert not os.path.exists(TEMP_FILE), (
            "Temporary file was not cleaned up"
        )

        assert not os.path.exists(FINAL_FILE), (
            "Incomplete file was incorrectly saved"
        )

        print("PASS: Interrupted upload detected")
        print("PASS: Incomplete temporary file cleaned up")

    finally:
        client.close()


if __name__ == "__main__":
    test_interrupted_upload()
