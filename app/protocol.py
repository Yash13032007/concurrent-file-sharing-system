import hashlib
import json
import os
import socket
import struct

CHUNK_SIZE = 64 * 1024
MAX_HEADER_SIZE = 65536
MAX_FILE_SIZE = 100 * 1024 * 1024

def recv_exact(sock, size):
    data = bytearray()

    while len(data) < size:
        chunk = sock.recv(min(CHUNK_SIZE, size - len(data)))

        if not chunk:
            raise ConnectionError("Connection closed unexpectedly")

        data.extend(chunk)

    return bytes(data)

def send_json(sock, message):
    payload = json.dumps(message).encode("utf-8")

    if len(payload) > MAX_HEADER_SIZE:
        raise ValueError("Message too large")

    sock.sendall(struct.pack("!I", len(payload)) + payload)

def recv_json(sock):
    header = recv_exact(sock, 4)
    length = struct.unpack("!I", header)[0]

    if length > MAX_HEADER_SIZE:
        raise ValueError("Message too large")

    message = json.loads(recv_exact(sock, length).decode("utf-8"))

    if not isinstance(message, dict):
        raise ValueError("Invalid JSON request")

    return message

def send_file(sock, filepath):
    size = os.path.getsize(filepath)

    if size > MAX_FILE_SIZE:
        raise ValueError("File too large")

    sock.sendall(size.to_bytes(8, "big"))

    with open(filepath, "rb") as file:
        while True:
            chunk = file.read(CHUNK_SIZE)

            if not chunk:
                break

            sock.sendall(chunk)

def receive_file(sock, filepath):
    size = int.from_bytes(recv_exact(sock, 8), "big")

    if size > MAX_FILE_SIZE:
        raise ValueError("File too large")

    received = 0

    try:
        with open(filepath, "wb") as file:
            while received < size:
                chunk = recv_exact(
                    sock,
                    min(CHUNK_SIZE, size - received)
                )

                file.write(chunk)
                received += len(chunk)

    except Exception:
        if os.path.exists(filepath):
            os.remove(filepath)
        raise

    return size

def calculate_sha256(filepath):
    digest = hashlib.sha256()

    with open(filepath, "rb") as file:
        for chunk in iter(lambda: file.read(CHUNK_SIZE), b""):
            digest.update(chunk)

    return digest.hexdigest()
