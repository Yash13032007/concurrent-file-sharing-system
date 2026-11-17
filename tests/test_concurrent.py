import socket
import threading
import tempfile
import os

from app.protocol import (
    send_json,
    recv_json,
    send_file,
    calculate_sha256
)

HOST = "127.0.0.1"
PORT = 5000

USERNAME = "server_test_user"
PASSWORD = "ServerTest123"

results = []
lock = threading.Lock()


def upload_file(client_number, source_file):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        client.connect((HOST, PORT))

        # Login
        send_json(client, {
            "type": "LOGIN",
            "username": USERNAME,
            "password": PASSWORD
        })

        response = recv_json(client)
        assert response["status"] == "success"

        filename = f"concurrent_test_{client_number}.txt"

        file_size = os.path.getsize(source_file)
        file_hash = calculate_sha256(source_file)

        # Upload request
        send_json(client, {
            "type": "UPLOAD",
            "filename": filename,
            "file_size": file_size,
            "sha256": file_hash
        })

        response = recv_json(client)
        assert response["status"] == "ready"

        # Send file
        send_file(client, source_file)

        response = recv_json(client)
        assert response["status"] == "success"

        with lock:
            results.append(f"Client {client_number}: PASS")

    except Exception as error:
        with lock:
            results.append(f"Client {client_number}: FAIL - {error}")

    finally:
        client.close()


def test_concurrent_uploads():
    with tempfile.TemporaryDirectory() as temp_dir:

        threads = []

        # Create three sample files
        for number in range(1, 4):
            source_file = os.path.join(
                temp_dir, f"source_{number}.txt"
            )

            with open(source_file, "w") as file:
                file.write(
                    f"Concurrent upload from client {number}.\n" * 1000
                )

            thread = threading.Thread(
                target=upload_file,
                args=(number, source_file)
            )

            threads.append(thread)

        # Start all clients simultaneously
        for thread in threads:
            thread.start()

        # Wait for all uploads
        for thread in threads:
            thread.join()

        for result in results:
            print(result)

        assert len(results) == 3
        assert all("PASS" in result for result in results)

        print("PASS: Three concurrent client uploads")


if __name__ == "__main__":
    test_concurrent_uploads()
