import customtkinter as ctk
import os
import threading
import queue
import io
import zipfile
from PIL import Image, ImageOps
import pymupdf
from database import LibraryDB

class ReadEraClone(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("ReadEra PC - Scroll Contínuo")
        self.geometry("1100x900")
        ctk.set_appearance_mode("dark")
        self.db = LibraryDB()

        # State
        self.pages_data = [] # Stores (type, data) where type is "cbz" (bytes) or "pdf" (page index)
        self.rendered_pages = {} # Cache of currently visible PIL images/CTkImages
        self.color_mode = ctk.StringVar(value="Padrão")
        self.current_book_id = None
        self.current_file_path = ""
        self.pdf_doc = None

        # Threading/Queue for rendering
        self.render_queue = queue.Queue()
        self.worker_threads = []
        self.stop_workers = threading.Event()
        self._start_render_workers(num_workers=2)

        # Layout
        self.main_container = ctk.CTkFrame(self)
        self.main_container.pack(expand=True, fill="both")

        self.shelf_frame = ctk.CTkFrame(self.main_container)
        self.reader_frame = ctk.CTkFrame(self.main_container)

        self._init_shelf_ui()
        self._init_reader_ui()

        self.show_shelf()

    def _start_render_workers(self, num_workers=2):
        for _ in range(num_workers):
            t = threading.Thread(target=self._render_worker, daemon=True)
            t.start()
            self.worker_threads.append(t)

    def _render_worker(self):
        while not self.stop_workers.is_set():
            try:
                # Each thread needs its own PDF doc instance for safety
                local_pdf_doc = None

                while not self.stop_workers.is_set():
                    try:
                        index, file_path, color_mode, w_target = self.render_queue.get(timeout=1)
                    except queue.Empty:
                        if local_pdf_doc:
                            local_pdf_doc.close()
                            local_pdf_doc = None
                        continue

                    if file_path != self.current_file_path:
                        self.render_queue.task_done()
                        continue

                    try:
                        entry = self.pages_data[index]
                        page_type = entry[0]
                        page_data = entry[1]
                        img = None

                        if page_type == "cbz":
                            with zipfile.ZipFile(file_path, 'r') as z:
                                img_data = z.read(page_data)
                                img = Image.open(io.BytesIO(img_data))
                        else:
                            if local_pdf_doc is None:
                                local_pdf_doc = pymupdf.open(file_path)

                            page = local_pdf_doc.load_page(page_data)
                            pix = page.get_pixmap(matrix=pymupdf.Matrix(1.5, 1.5))
                            img = Image.open(io.BytesIO(pix.tobytes("png")))

                        if img:
                            img = img.convert("RGB")
                            if color_mode == "Noite":
                                img = ImageOps.invert(img)
                            elif color_mode == "Sépia":
                                img = ImageOps.colorize(ImageOps.grayscale(img), "#433422", "#f4ecd8")

                            h_target = int(img.height * (w_target / img.width))
                            ctk_img = ctk.CTkImage(img, size=(w_target, h_target))

                            # Schedule UI update in main thread
                            self.after(0, lambda i=index, ci=ctk_img, ht=h_target: self._update_page_ui(i, ci, ht))

                    except Exception as e:
                        print(f"Worker Error: {e}")
                    finally:
                        self.render_queue.task_done()
            except Exception as outer_e:
                print(f"Outer Worker Error: {outer_e}")

    def _update_page_ui(self, index, ctk_img, h_target):
        if index < len(self.page_labels):
            # Update pages_data with actual height if it was just an estimate
            entry = list(self.pages_data[index])
            if entry[2] != h_target:
                entry[2] = h_target
                self.pages_data[index] = tuple(entry)
                # Height change may shift other labels; CTK handles layout
                # but we need to update the label's placeholder height
                self.page_labels[index].configure(height=h_target)

            self.page_labels[index].configure(image=ctk_img, text="")
            self.rendered_pages[index] = True

    def _init_shelf_ui(self):
        header = ctk.CTkFrame(self.shelf_frame, height=60)
        header.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(header, text="Minha Biblioteca", font=("Arial", 24, "bold")).pack(side="left", padx=10)
        ctk.CTkButton(header, text="+ Adicionar HQ/PDF", command=self.open_file).pack(side="right", padx=10)

        self.shelf_scroll = ctk.CTkScrollableFrame(self.shelf_frame, fg_color="transparent")
        self.shelf_scroll.pack(expand=True, fill="both", padx=10, pady=10)

        # Grid layout for shelf
        self.shelf_grid = ctk.CTkFrame(self.shelf_scroll, fg_color="transparent")
        self.shelf_grid.pack(fill="both", expand=True)

    def _init_reader_ui(self):
        header = ctk.CTkFrame(self.reader_frame, height=50)
        header.pack(fill="x", padx=10, pady=5)

        ctk.CTkButton(header, text="< Voltar", command=self.show_shelf, width=80).pack(side="left", padx=5)

        self.title_label = ctk.CTkLabel(header, text="Leitor", font=("Arial", 16, "bold"))
        self.title_label.pack(side="left", padx=20)

        ctk.CTkSegmentedButton(header, values=["Padrão", "Sépia", "Noite"],
                               variable=self.color_mode, command=self.refresh_reader).pack(side="right", padx=10)

        self.reader_scroll = ctk.CTkScrollableFrame(self.reader_frame, fg_color="#121212")
        self.reader_scroll.pack(expand=True, fill="both")

        # Scroll Events
        self.reader_scroll._canvas.bind("<Configure>", lambda e: self.check_visibility())
        self.reader_scroll._canvas.bind("<MouseWheel>", self._on_scroll)
        self.reader_scroll._canvas.bind("<Button-4>", self._on_scroll)
        self.reader_scroll._canvas.bind("<Button-5>", self._on_scroll)

    def _on_scroll(self, event):
        # Small delay to avoid excessive calls
        self.after(10, self.check_visibility)
        # Update progress based on scroll with debouncing
        if hasattr(self, "_save_id"):
            self.after_cancel(self._save_id)
        self._save_id = self.after(1000, self._save_progress)

    def _save_progress(self):
        if self.current_book_id and self.page_labels:
            canvas = self.reader_scroll._canvas
            v_start = canvas.canvasy(0)

            # Estimate page based on scroll position
            # This is tricky because pages have different heights
            # Find the first label that is roughly at the top
            for i, lbl in enumerate(self.page_labels):
                if lbl.winfo_y() >= v_start:
                    self.db.update_last_page(self.current_book_id, i)
                    break

    def show_shelf(self):
        self.reader_frame.pack_forget()
        self.shelf_frame.pack(expand=True, fill="both")
        self.load_shelf_data()

    def load_shelf_data(self):
        for widget in self.shelf_grid.winfo_children():
            widget.destroy()

        books = self.db.get_books()
        cols = 5 # Initial fixed columns, could be dynamic

        for i, book in enumerate(books):
            row = i // cols
            col = i % cols

            book_item = ctk.CTkFrame(self.shelf_grid, fg_color="transparent", cursor="hand2")
            book_item.grid(row=row, column=col, padx=15, pady=15)
            book_item.bind("<Button-1>", lambda e, b=book: self.load_book(b))

            # Cover
            if book['cover_path'] and os.path.exists(book['cover_path']):
                try:
                    img = Image.open(book['cover_path'])
                    ctk_cover = ctk.CTkImage(img, size=(160, 220))
                    lbl_cover = ctk.CTkLabel(book_item, image=ctk_cover, text="")
                    lbl_cover.pack()
                    lbl_cover.bind("<Button-1>", lambda e, b=book: self.load_book(b))
                except:
                    ctk.CTkLabel(book_item, text="Sem Capa", width=160, height=220, fg_color="gray").pack()
            else:
                ctk.CTkLabel(book_item, text="Sem Capa", width=160, height=220, fg_color="gray").pack()

            # Title
            title = book['title']
            if len(title) > 20: title = title[:17] + "..."
            lbl_title = ctk.CTkLabel(book_item, text=title, font=("Arial", 12), wraplength=150)
            lbl_title.pack(pady=5)
            lbl_title.bind("<Button-1>", lambda e, b=book: self.load_book(b))

    def open_file(self):
        p = ctk.filedialog.askopenfilename(filetypes=[("Livros", "*.cbz *.pdf *.zip")])
        if p:
            self.db.add_book(p)
            self.load_shelf_data()

    def load_book(self, book):
        self.current_book_id = book['id']
        self.current_file_path = book['file_path']
        self.title_label.configure(text=book['title'])
        self.load_file_to_reader(book['file_path'], last_page=book['last_page'])

    def load_file_to_reader(self, path, last_page=0):
        self.pages_data = []
        self.rendered_pages = {}
        # Clear previous queue
        with self.render_queue.mutex:
            self.render_queue.queue.clear()

        ext = path.lower()
        for widget in self.reader_scroll.winfo_children():
            widget.destroy()

        # Initial width for height calculation
        w_target = self.reader_scroll.winfo_width() - 80
        if w_target < 200: w_target = 800

        try:
            if ext.endswith((".cbz", ".zip")):
                with zipfile.ZipFile(path, 'r') as z:
                    imgs = sorted([f for f in z.namelist() if f.lower().endswith(('.png','.jpg','.jpeg','.webp'))])

                    # Optimization: Instead of opening every image to get dimensions,
                    # we use a default height for the first pass and update it when rendered.
                    # This prevents UI freeze on opening large CBZs.
                    for f in imgs:
                        self.pages_data.append(("cbz", f, 1200)) # Default estimated height
            elif ext.endswith(".pdf"):
                doc = pymupdf.open(path)
                for p in range(len(doc)):
                    page = doc.load_page(p)
                    rect = page.rect
                    width, height = rect.width, rect.height
                    h_target = int(height * (w_target / width))
                    self.pages_data.append(("pdf", p, h_target))
                doc.close()
        except Exception as e:
            print(f"Erro ao abrir arquivo: {e}")
            return

        self.page_labels = []
        for i in range(len(self.pages_data)):
            type, data, h_target = self.pages_data[i]
            lbl = ctk.CTkLabel(self.reader_scroll, text=f"Carregando página {i+1}...", height=h_target)
            lbl.pack(pady=15, padx=20)
            self.page_labels.append(lbl)

        self.show_reader(last_page)

    def show_reader(self, last_page=0):
        self.shelf_frame.pack_forget()
        self.reader_frame.pack(expand=True, fill="both")
        self.update_idletasks() # Ensure sizes are calculated

        if last_page > 0 and last_page < len(self.page_labels):
            # Jump to last_page
            # Need to wait for rendering/layout
            self.after(200, lambda: self._jump_to_page(last_page))
        else:
            self.after(200, self.check_visibility)

    def _jump_to_page(self, index):
        if index < len(self.page_labels):
            lbl = self.page_labels[index]
            y = lbl.winfo_y()
            total_h = self.reader_scroll._canvas.bbox("all")[3]
            if total_h > 0:
                fraction = y / total_h
                self.reader_scroll._canvas.yview_moveto(fraction)
            self.check_visibility()

    def check_visibility(self):
        if not self.pages_data: return

        canvas = self.reader_scroll._canvas
        # Get relative position within the scrollable content
        v_start = canvas.canvasy(0)
        v_end = v_start + canvas.winfo_height()

        w_target = self.reader_scroll.winfo_width() - 80
        if w_target < 200: w_target = 800

        for i, lbl in enumerate(self.page_labels):
            y_pos = lbl.winfo_y()
            type, data, h_target = self.pages_data[i]
            # 1000px margin for pre-loading
            if v_start - 1000 < y_pos < v_end + 1000:
                if i not in self.rendered_pages:
                    # Mark as "pending" to avoid double queuing
                    self.rendered_pages[i] = "pending"
                    self.render_queue.put((i, self.current_file_path, self.color_mode.get(), w_target))
            else:
                # Unload pages far away
                if i in self.rendered_pages and self.rendered_pages[i] != "pending":
                    del self.rendered_pages[i]
                    lbl.configure(image=None, text=f"Página {i+1}", height=h_target)

    def refresh_reader(self):
        mode = self.color_mode.get()
        if mode == "Noite":
            self.reader_scroll.configure(fg_color="black")
        elif mode == "Sépia":
            self.reader_scroll.configure(fg_color="#e3d5c1")
        else:
            self.reader_scroll.configure(fg_color="#121212")

        # Re-render visible pages with new filter
        self.rendered_pages = {}
        with self.render_queue.mutex:
            self.render_queue.queue.clear()
        self.check_visibility()

if __name__ == "__main__":
    app = ReadEraClone()
    app.mainloop()
