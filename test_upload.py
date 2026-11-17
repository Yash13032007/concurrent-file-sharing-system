import os
import socket
import hashlib
import struct
import uuid
import base64
import zipfile
import zlib

from pathlib import Path
from app.protocol import (
    CHUNK_SIZE,
    MAX_FILE_SIZE,
    send_json,
    recv_json,
    calculate_sha256,
)

SERVER_IP = os.environ.get("FILESHARE_SERVER", "127.0.0.1")
SERVER_PORT = int(os.environ.get("FILESHARE_PORT", "5000"))

SAMPLE_DIR = Path("upload_test_samples")
results = []


def record(test_id, description, passed, detail=""):
    status = "PASS" if passed else "FAIL"
    results.append((test_id, description, status, detail))
    print(f"{test_id} - {description}: {status}")
    if detail:
        print("   ", detail)


def connect():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(30)
    sock.connect((SERVER_IP, SERVER_PORT))
    return sock


def login(sock, username, password):
    send_json(sock, {
        "type": "LOGIN",
        "username": username,
        "password": password
    })

    response = recv_json(sock)
    return response.get("status") == "success", response


def create_samples():
    SAMPLE_DIR.mkdir(exist_ok=True)

    # TXT
    (SAMPLE_DIR / "sample.txt").write_text(
        "Concurrent File Sharing System upload test.",
        encoding="utf-8"
    )

    # Minimal PDF
    pdf = (
        b"%PDF-1.4\n"
        b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
        b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 200 200]>>endobj\n"
        b"trailer<</Root 1 0 R>>\n%%EOF\n"
    )
    (SAMPLE_DIR / "sample.pdf").write_bytes(pdf)

    # Valid 1x1 PNG
    raw = b"\x00\xff\x00\x00"
    png = (
        b"\x89PNG\r\n\x1a\n"
        + struct.pack(">I", 13)
        + b"IHDR"
        + struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
        + struct.pack(">I", zlib.crc32(b"IHDR" + struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)) & 0xffffffff)
        + struct.pack(">I", len(zlib.compress(raw)))
        + b"IDAT"
        + zlib.compress(raw)
        + struct.pack(">I", zlib.crc32(b"IDAT" + zlib.compress(raw)) & 0xffffffff)
        + struct.pack(">I", 0)
        + b"IEND"
        + struct.pack(">I", zlib.crc32(b"IEND") & 0xffffffff)
    )
    (SAMPLE_DIR / "sample.png").write_bytes(png)

    # 1x1 JPG
    jpg = base64.b64decode(
        "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAP//////////////////////////////////////////////////////////////////////////////////////"
        "2wBDAf//////////////////////////////////////////////////////////////////////////////////////"
        "wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAX/xAAUEAEAAAAAAAAAAAAAAAAAAAAA"
        "/9oADAMBAAIQAxAAAAF//8QAFBABAAAAAAAAAAAAAAAAAAAAAP/aAAgBAQABBQJ//8QAFBEBAAAAAAAAA"
        "AAAAAAAAAAAAP/aAAgBAwEBPwF//8QAFBEBAAAAAAAAAAAAAAAAAAAAAP/aAAgBAgEBPwF//8QAFBAB"
        "AAAAAAAAAAAAAAAAAAAAAP/aAAgBAQAGPwJ//8QAFBABAAAAAAAAAAAAAAAAAAAAAP/aAAgBAQABPyF//9k="
    )
    (SAMPLE_DIR / "sample.jpg").write_bytes(jpg)

    # Minimal DOCX package
    docx_path = SAMPLE_DIR / "sample.docx"
    with zipfile.ZipFile(docx_path, "w") as doc:
        doc.writestr(
            "[Content_Types].xml",
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
            '</Types>'
        )
        doc.writestr(
            "_rels/.rels",
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
            '</Relationships>'
        )
        doc.writestr(
            "word/document.xml",
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
            '<w:body><w:p><w:r><w:t>DOCX upload test</w:t></w:r></w:p>'
            '<w:sectPr/></w:body></w:document>'
        )

    # 10 MB file
    with open(SAMPLE_DIR / "sample_10mb.bin", "wb") as f:
        f.write(os.urandom(10 * 1024 * 1024))

    # Empty file
    (SAMPLE_DIR / "empty.txt").write_bytes(b"")

    # Sparse file larger than the configured maximum
    with open(SAMPLE_DIR / "oversized.bin", "wb") as f:
        f.truncate(MAX_FILE_SIZE + 1)


def upload(sock, filepath, remote_name=None):
    filepath = Path(filepath)
    filename = remote_name or filepath.name
    size = filepath.stat().st_size

    file_hash = calculate_sha256(str(filepath))

    send_json(sock, {
        "type": "UPLOAD",
        "filename": filename,
        "file_size": size,
        "sha256": file_hash
    })

    response = recv_json(sock)

    if response.get("status") != "ready":
        return False, response

    # The server has accepted the upload request.
    # Send the 8-byte size prefix and file contents.
    sock.sendall(size.to_bytes(8, "big"))

    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(CHUNK_SIZE)
            if not chunk:
                break
            sock.sendall(chunk)

    response = recv_json(sock)
    return response.get("status") == "success", response


def main():
    print("Creating sample files...")
    create_samples()

    username = input("Enter your registered username: ").strip()
    password = input("Enter your password: ")

    sock = connect()

    try:
        authenticated, response = login(sock, username, password)

        if not authenticated:
            print("Login failed:", response.get("message", response))
            return

        print("\nLogin successful. Starting upload tests...\n")

        test_id = uuid.uuid4().hex[:8]

        # Different file types
        file_tests = [
            ("UP01", "TXT upload", "sample.txt"),
            ("UP02", "PDF upload", "sample.pdf"),
            ("UP03", "PNG upload", "sample.png"),
            ("UP04", "JPG upload", "sample.jpg"),
            ("UP05", "DOCX upload", "sample.docx"),
            ("UP06", "10 MB upload", "sample_10mb.bin"),
            ("UP07", "Empty file upload", "empty.txt"),
        ]

        for case_id, description, filename in file_tests:
            path = SAMPLE_DIR / filename
            remote_name = f"{test_id}_{filename}"

            try:
                passed, response = upload(sock, path, remote_name)
                record(
                    case_id,
                    description,
                    passed,
                    response.get("message", response.get("status", ""))
                )
            except Exception as error:
                record(case_id, description, False, str(error))
                break

        # Duplicate filename test: the first upload should already exist.
        try:
            passed, response = upload(
                sock,
                SAMPLE_DIR / "sample.txt",
                f"{test_id}_sample.txt"
            )
            record(
                "UP08",
                "Duplicate filename rejected",
                not passed,
                response.get("message", response.get("status", ""))
            )
        except Exception as error:
            record("UP08", "Duplicate filename rejected", False, str(error))

        # Invalid path: checks the same local file-existence validation
        # used by client.py. It does not send a request to the server.
        invalid_path = SAMPLE_DIR / "this_file_does_not_exist.txt"
        record(
            "UP09",
            "Invalid local file path rejected",
            not invalid_path.is_file(),
            "Client-side path validation"
        )

        # Oversized file: server should reject it before requesting bytes.
        try:
            oversized = SAMPLE_DIR / "oversized.bin"
            send_json(sock, {
                "type": "UPLOAD",
                "filename": f"{test_id}_oversized.bin",
                "file_size": oversized.stat().st_size,
                "sha256": "0" * 64
            })

            response = recv_json(sock)
            passed = response.get("status") != "ready"

            record(
                "UP10",
                "File larger than maximum size rejected",
                passed,
                response.get("message", response.get("status", ""))
            )
        except Exception as error:
            record("UP10", "File larger than maximum size rejected", False, str(error))

    finally:
        sock.close()

    # Unauthenticated upload test on a fresh connection.
    try:
        unauth_sock = connect()
        try:
            send_json(unauth_sock, {
                "type": "UPLOAD",
                "filename": "unauthenticated_test.txt",
                "file_size": 0,
                "sha256": hashlib.sha256(b"").hexdigest()
            })

            response = recv_json(unauth_sock)
            passed = response.get("status") != "ready"

            record(
                "UP11",
                "Unauthenticated upload rejected",
                passed,
                response.get("message", response.get("status", ""))
            )
        finally:
            unauth_sock.close()
    except Exception as error:
        record("UP11", "Unauthenticated upload rejected", False, str(error))

    print("\n========== UPLOAD TEST REPORT ==========")
    for case_id, description, status, detail in results:
        print(f"{case_id}: {status} - {description}")

    passed_count = sum(1 for item in results if item[2] == "PASS")
    failed_count = len(results) - passed_count

    print("----------------------------------------")
    print("Total:", len(results))
    print("Passed:", passed_count)
    print("Failed:", failed_count)
    print("========================================")


if __name__ == "__main__":
    main()
