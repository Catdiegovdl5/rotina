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
            last_access DATETIME
        )
        """
        self.conn.execute(query)
        self.conn.commit()

    def save_progress(self, path, current_page, total_pages):
        query = """
        INSERT INTO books (path, current_page, total_pages, last_access)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(path) DO UPDATE SET
            current_page = excluded.current_page,
            last_access = excluded.last_access
        """
        self.conn.execute(query, (path, current_page, total_pages, datetime.now()))
        self.conn.commit()

    def get_progress(self, path):
        query = "SELECT current_page FROM books WHERE path = ?"
        cursor = self.conn.execute(query, (path,))
        result = cursor.fetchone()
        return result[0] if result else 0
