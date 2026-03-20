import sqlite3
import hashlib
import os
import datetime
import pymupdf
import io
from PIL import Image

class LibraryDB:
    def __init__(self, db_name="library.db"):
        self.db_name = db_name
        self.cache_dir = ".cache/covers/"
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS books (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT UNIQUE,
                    title TEXT,
                    author TEXT,
                    cover_path TEXT,
                    last_page INTEGER DEFAULT 0,
                    total_pages INTEGER,
                    date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()

    def _get_file_hash(self, file_path):
        return hashlib.md5(file_path.encode()).hexdigest()

    def extract_cover_and_metadata(self, file_path):
        ext = file_path.lower()
        title = os.path.basename(file_path)
        author = "Desconhecido"
        total_pages = 0
        cover_path = ""

        try:
            if ext.endswith(".pdf"):
                doc = pymupdf.open(file_path)
                total_pages = len(doc)
                metadata = doc.metadata
                if metadata.get("title"):
                    title = metadata["title"]
                if metadata.get("author"):
                    author = metadata["author"]

                # Extract first page as cover
                if total_pages > 0:
                    page = doc.load_page(0)
                    pix = page.get_pixmap(matrix=pymupdf.Matrix(0.5, 0.5))
                    img_data = pix.tobytes("png")

                    file_hash = self._get_file_hash(file_path)
                    cover_path = os.path.join(self.cache_dir, f"{file_hash}.png")

                    with open(cover_path, "wb") as f:
                        f.write(img_data)
                doc.close()

            elif ext.endswith((".cbz", ".zip")):
                import zipfile
                with zipfile.ZipFile(file_path, 'r') as z:
                    imgs = sorted([f for f in z.namelist() if f.lower().endswith(('.png','.jpg','.jpeg','.webp'))])
                    total_pages = len(imgs)
                    if imgs:
                        # Extract first image as cover
                        with z.open(imgs[0]) as first_img:
                            img_data = first_img.read()
                            img = Image.open(io.BytesIO(img_data))
                            img.thumbnail((300, 400)) # Resize for cover

                            file_hash = self._get_file_hash(file_path)
                            cover_path = os.path.join(self.cache_dir, f"{file_hash}.png")
                            img.save(cover_path, "PNG")

        except Exception as e:
            print(f"Erro ao extrair metadados/capa de {file_path}: {e}")

        return title, author, total_pages, cover_path

    def add_book(self, file_path):
        title, author, total_pages, cover_path = self.extract_cover_and_metadata(file_path)

        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO books (file_path, title, author, cover_path, total_pages)
                    VALUES (?, ?, ?, ?, ?)
                ''', (file_path, title, author, cover_path, total_pages))
                conn.commit()
                return cursor.lastrowid
        except sqlite3.IntegrityError:
            # Book already exists
            return None

    def get_books(self):
        with sqlite3.connect(self.db_name) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM books ORDER BY date_added DESC')
            return [dict(row) for row in cursor.fetchall()]

    def update_last_page(self, book_id, page):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE books SET last_page = ? WHERE id = ?', (page, book_id))
            conn.commit()

    def delete_book(self, book_id):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM books WHERE id = ?', (book_id,))
            conn.commit()

if __name__ == "__main__":
    db = LibraryDB()
    print("Banco de dados inicializado.")
