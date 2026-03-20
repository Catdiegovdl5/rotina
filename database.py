import sqlite3
from datetime import datetime

class LibraryDB:
    def __init__(self, db_name="library.db"):
        self.conn = sqlite3.connect(db_name)
        self.create_table()

    def create_table(self):
        query = """
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            path TEXT UNIQUE,
            current_page INTEGER,
            total_pages INTEGER,
            last_access DATETIME,
            cover_path TEXT
        )
        """
        self.conn.execute(query)
        self.conn.commit()

        # Handle migration if table existed before cover_path was added
        try:
            self.conn.execute("ALTER TABLE books ADD COLUMN cover_path TEXT")
            self.conn.commit()
        except sqlite3.OperationalError:
            # Column already exists
            pass

    def save_progress(self, path, current_page, total_pages, cover_path=None):
        query = """
        INSERT INTO books (path, current_page, total_pages, last_access, cover_path)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(path) DO UPDATE SET
            current_page = excluded.current_page,
            last_access = excluded.last_access,
            cover_path = COALESCE(excluded.cover_path, books.cover_path)
        """
        self.conn.execute(query, (path, current_page, total_pages, datetime.now(), cover_path))
        self.conn.commit()

    def get_progress(self, path):
        query = "SELECT current_page FROM books WHERE path = ?"
        cursor = self.conn.execute(query, (path,))
        result = cursor.fetchone()
        return result[0] if result else 0

    def get_all_books(self):
        query = "SELECT path, current_page, total_pages, cover_path FROM books ORDER BY last_access DESC"
        cursor = self.conn.execute(query)
        return cursor.fetchall()
