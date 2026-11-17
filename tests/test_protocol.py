import socket
import threading
import tempfile
import os

from app.protocol import (
    send_json,
    recv_json,
    send_file,
    receive_file,
    calculate_sha256
)


def server_function(server_socket, received_file):
    message = recv_json(server_socket)
    print("Server received:", message)

    send_json(server_socket, {
        "status": "success",
        "message": "Hello client!"
    })

    receive_file(server_socket, received_file)


def test_protocol():
    with tempfile.TemporaryDirectory() as temp_dir:
        source_file = os.path.join(temp_dir, "original.txt")
        received_file = os.path.join(temp_dir, "received.txt")

        # Create a sample file
        with open(source_file, "w") as file:
            file.write("Testing file transfer using TCP sockets.")

        # Create connected sockets
        client_socket, server_socket = socket.socketpair()

        # Start server thread
        thread = threading.Thread(
            target=server_function,
            args=(server_socket, received_file)
        )
        thread.start()

        try:
            # Test JSON communication
            send_json(client_socket, {
                "type": "TEST",
                "filename": "original.txt",
                "file_size": os.path.getsize(source_file)
            })

            response = recv_json(client_socket)
            print("Client received:", response)

            assert response["status"] == "success"

            # Test file transfer
            send_file(client_socket, source_file)

            thread.join()

            # Verify received file
            assert os.path.exists(received_file)

            original_hash = calculate_sha256(source_file)
            received_hash = calculate_sha256(received_file)

            assert original_hash == received_hash

            print("PASS: JSON communication")
            print("PASS: File transfer")
            print("PASS: SHA-256 verification")

        finally:
            client_socket.close()
            server_socket.close()
            thread.join()


if __name__ == "__main__":
    test_protocol()
