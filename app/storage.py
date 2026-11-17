import sqlite3

DB_NAME = "fileshare.db"

def get_connection():
    connection = sqlite3.connect(DB_NAME, timeout=30)
    connection.row_factory = sqlite3.Row
    return connection

def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS files (
                file_id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL UNIQUE,
                owner TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                sha256 TEXT NOT NULL
            )
        """)

def add_user(username, password_hash):
    try:
        with get_connection() as conn:
            conn.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                (username, password_hash)
            )
        return True

    except sqlite3.IntegrityError:
        return False

def get_user(username):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT password_hash FROM users WHERE username = ?",
            (username,)
        ).fetchone()

    return row["password_hash"] if row else None

def update_password_hash(username, new_hash):
    with get_connection() as conn:
        conn.execute(
            "UPDATE users SET password_hash = ? WHERE username = ?",
            (new_hash, username)
        )

def add_file(filename, owner, file_size, sha256):
    with get_connection() as conn:
        cursor = conn.execute(
            """INSERT INTO files
               (filename, owner, file_size, sha256)
               VALUES (?, ?, ?, ?)""",
            (filename, owner, file_size, sha256)
        )

        return cursor.lastrowid

def list_files():
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT file_id, filename, owner, file_size, sha256
               FROM files ORDER BY file_id"""
        ).fetchall()

    return [dict(row) for row in rows]

def get_file_by_id(file_id):
    with get_connection() as conn:
        row = conn.execute(
            """SELECT file_id, filename, owner, file_size, sha256
               FROM files WHERE file_id = ?""",
            (file_id,)
        ).fetchone()

    return dict(row) if row else None
