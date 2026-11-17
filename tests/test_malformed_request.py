import socket
import struct

HOST = "127.0.0.1"
PORT = 5000


def test_malformed_request():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.settimeout(5)

    try:
        client.connect((HOST, PORT))

        # Invalid JSON with a valid 4-byte length prefix
        bad_message = b"this is not valid JSON"

        client.sendall(
            struct.pack("!I", len(bad_message)) + bad_message
        )

        response = client.recv(1024)

        assert response == b"", (
            f"Expected connection closure, received: {response!r}"
        )

        print("PASS: Server safely closed the malformed request")

    finally:
        client.close()


if __name__ == "__main__":
    test_malformed_request()
