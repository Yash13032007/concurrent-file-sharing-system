import socket
import threading
import tempfile
import os

from app.protocol import send_file, receive_file, calculate_sha256


def test_file_transfer():
    with tempfile.TemporaryDirectory() as temp_dir:
        source_file = os.path.join(temp_dir, "original.txt")
        received_file = os.path.join(temp_dir, "received.txt")

        # Create sample file
        with open(source_file, "w") as file:
            file.write("Testing file transfer using TCP sockets.")

        client_socket, server_socket = socket.socketpair()

        def server_function():
            receive_file(server_socket, received_file)

        thread = threading.Thread(target=server_function)
        thread.start()

        try:
            send_file(client_socket, source_file)
            thread.join()

            assert os.path.exists(received_file)

            original_hash = calculate_sha256(source_file)
            received_hash = calculate_sha256(received_file)

            assert original_hash == received_hash

            print("PASS: File transfer")
            print("PASS: SHA-256 verification")

        finally:
            client_socket.close()
            server_socket.close()
            thread.join()


if __name__ == "__main__":
    test_file_transfer()
