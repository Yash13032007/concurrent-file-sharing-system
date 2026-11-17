import socket
import threading
import tempfile
import os
import uuid

from app.protocol import (
    send_json,
    recv_json,
    send_file,
    receive_file,
    calculate_sha256
)

HOST = "127.0.0.1"
PORT = 5000

USERNAME = "server_test_user"
PASSWORD = "ServerTest123"

results = {}
lock = threading.Lock()


def login(client):
    send_json(client, {
        "type": "LOGIN",
        "username": USERNAME,
        "password": PASSWORD
    })

    response = recv_json(client)
    assert response["status"] == "success", response


def upload_sample(source_file, filename):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        client.connect((HOST, PORT))
        login(client)

        file_size = os.path.getsize(source_file)
        file_hash = calculate_sha256(source_file)

        send_json(client, {
            "type": "UPLOAD",
            "filename": filename,
            "file_size": file_size,
            "sha256": file_hash
        })

        response = recv_json(client)
        assert response["status"] == "ready", response

        send_file(client, source_file)

        response = recv_json(client)
        assert response["status"] == "success", response

        return response["file_id"]

    finally:
        client.close()


def download_file(client_id, file_id, destination):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        client.connect((HOST, PORT))
        login(client)

        send_json(client, {
            "type": "DOWNLOAD",
            "file_id": file_id
        })

        response = recv_json(client)
        assert response["status"] == "ready", response

        receive_file(client, destination)

        assert os.path.exists(destination)

        with lock:
            results[client_id] = True

        print(client_id, ": Download completed")

    except Exception as error:
        with lock:
            results[client_id] = False

        print(client_id, "failed:", error)

    finally:
        client.close()


def test_simultaneous_downloads():
    with tempfile.TemporaryDirectory() as temp_dir:

        source1 = os.path.join(temp_dir, "source1.txt")
        source2 = os.path.join(temp_dir, "source2.txt")

        destination1 = os.path.join(temp_dir, "download1.txt")
        destination2 = os.path.join(temp_dir, "download2.txt")

        with open(source1, "w") as file:
            file.write("File for simultaneous download client 1.\n" * 1000)

        with open(source2, "w") as file:
            file.write("File for simultaneous download client 2.\n" * 1000)

        unique_id = uuid.uuid4().hex[:8]

        filename1 = f"sim_download_1_{unique_id}.txt"
        filename2 = f"sim_download_2_{unique_id}.txt"

        # Upload both files before testing downloads
        file_id1 = upload_sample(source1, filename1)
        file_id2 = upload_sample(source2, filename2)

        print("PASS: Two sample files uploaded")

        # Start two downloads simultaneously
        t1 = threading.Thread(
            target=download_file,
            args=("client1", file_id1, destination1)
        )

        t2 = threading.Thread(
            target=download_file,
            args=("client2", file_id2, destination2)
        )

        t1.start()
        t2.start()

        t1.join()
        t2.join()

        # Verify downloaded contents
        assert calculate_sha256(source1) == calculate_sha256(destination1)
        assert calculate_sha256(source2) == calculate_sha256(destination2)

        print("PASS: Client 1 SHA-256 verification")
        print("PASS: Client 2 SHA-256 verification")

        for client_id, success in results.items():
            print(client_id, ":", "PASS" if success else "FAIL")

        assert len(results) == 2
        assert all(results.values())

        print("SIMULTANEOUS DOWNLOAD TEST: PASSED")


if __name__ == "__main__":
    test_simultaneous_downloads()
