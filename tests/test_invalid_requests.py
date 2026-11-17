import socket
from app.protocol import send_json, recv_json

HOST = "127.0.0.1"
PORT = 5000


def test_unauthenticated_request(command):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.settimeout(5)

    try:
        client.connect((HOST, PORT))

        send_json(client, {
            "type": command
        })

        response = recv_json(client)

        assert response["status"] == "error"
        assert response["message"] == "Please login first"

        print(f"PASS: Unauthenticated {command} rejected")

    finally:
        client.close()


if __name__ == "__main__":
    test_unauthenticated_request("UPLOAD")
    test_unauthenticated_request("DOWNLOAD")
