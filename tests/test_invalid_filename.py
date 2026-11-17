import socket
from app.protocol import send_json, recv_json

HOST = "127.0.0.1"
PORT = 5000

USERNAME = "server_test_user"
PASSWORD = "ServerTest123"


def test_invalid_filename():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.settimeout(5)

    try:
        client.connect((HOST, PORT))

        # Login first
        send_json(client, {
            "type": "LOGIN",
            "username": USERNAME,
            "password": PASSWORD
        })

        response = recv_json(client)
        assert response["status"] == "success"

        # Attempt path traversal
        send_json(client, {
            "type": "UPLOAD",
            "filename": "../../outside.txt",
            "file_size": 10,
            "sha256": "a" * 64
        })

        response = recv_json(client)

        assert response["status"] == "error"
        print("PASS: Path traversal filename rejected")

    finally:
        client.close()


if __name__ == "__main__":
    test_invalid_filename()
