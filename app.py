import customtkinter as ctk
from PIL import Image
import zipfile
import io
import os
import hashlib
import fitz  # PyMuPDF
from database import LibraryDB

# Garantir que a pasta de cache de capas exista
if not os.path.exists("covers"):
    os.makedirs("covers")

class ReadEraClone(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Meu ReadEra PC - MVP")
        self.geometry("800x900")
        ctk.set_appearance_mode("dark")

        # Configuração do Banco de Dados
        self.db = LibraryDB()
        self.current_file_path = ""

        # Variáveis de controle
        self.pages = []
        self.current_page = 0

        # Container principal para as telas
        self.main_container = ctk.CTkFrame(self)
        self.main_container.pack(expand=True, fill="both")

        # Inicializa os Frames das telas
        self.shelf_frame = ctk.CTkFrame(self.main_container)
        self.reader_frame = ctk.CTkFrame(self.main_container)

        # -- CONFIGURAÇÃO DA ESTANTE (SHELF) --
        # Botão para abrir novo arquivo (movido para a estante)
        self.btn_open = ctk.CTkButton(self.shelf_frame, text="Adicionar Nova HQ (.cbz)", command=self.open_file)
        self.btn_open.pack(pady=10)

        self.shelf_scroll = ctk.CTkScrollableFrame(self.shelf_frame)
        self.shelf_scroll.pack(expand=True, fill="both", padx=10, pady=10)

        # -- CONFIGURAÇÃO DO LEITOR (READER) --
        # Header do Leitor
        self.reader_header = ctk.CTkFrame(self.reader_frame, height=40)
        self.reader_header.pack(fill="x", padx=10, pady=5)

        self.btn_back = ctk.CTkButton(self.reader_header, text="< Voltar para Estante", width=120, command=self.show_shelf)
        self.btn_back.pack(side="left", padx=5, pady=5)

        # Interface - Área de exibição da imagem
        self.canvas_label = ctk.CTkLabel(self.reader_frame, text="Carregando imagem...", text_color="gray")
        self.canvas_label.pack(expand=True, fill="both", padx=20, pady=10)

        # Indicador de progresso (Página X de Y)
        self.lbl_progress = ctk.CTkLabel(self.reader_frame, text="")
        self.lbl_progress.pack(pady=5)

        # Barra de progresso
        self.progress_bar = ctk.CTkProgressBar(self.reader_frame, width=400)
        self.progress_bar.set(0)
        self.progress_bar.pack(pady=5)

        # Atalhos de teclado
        self.bind("<Right>", lambda e: self.next_page())
        self.bind("<Left>", lambda e: self.prev_page())

        # Evento de redimensionamento da janela
        self.bind("<Configure>", lambda e: self._on_resize(e))
        self._resize_timer = None

        # Mostra a Estante por padrão
        self.show_shelf()

    def _on_resize(self, event):
        # Evita chamar show_page repetidamente enquanto redimensiona (debounce)
        if event.widget == self:
            if self._resize_timer is not None:
                self.after_cancel(self._resize_timer)
            self._resize_timer = self.after(100, self.show_page)

    def show_shelf(self):
        """Alterna para a tela da Estante."""
        self.reader_frame.pack_forget()
        self.shelf_frame.pack(expand=True, fill="both")
        self.load_shelf_items()

    def load_shelf_items(self):
        """Carrega os livros do banco de dados e desenha na estante."""
        # Limpa itens antigos
        for widget in self.shelf_scroll.winfo_children():
            widget.destroy()

        books = self.db.get_all_books()

        if not books:
            lbl_empty = ctk.CTkLabel(self.shelf_scroll, text="Sua estante está vazia.\nAdicione uma HQ clicando no botão acima.", text_color="gray")
            lbl_empty.pack(pady=40)
            return

        # Configura o grid (3 colunas por padrão)
        columns = 3

        for i, book in enumerate(books):
            path, current_page, total_pages, cover_path = book
            filename = os.path.basename(path)

            row = i // columns
            col = i % columns

            # Frame para cada item da grade
            item_frame = ctk.CTkFrame(self.shelf_scroll)
            item_frame.grid(row=row, column=col, padx=15, pady=15, sticky="n")

            # Tenta carregar a capa
            ctk_cover = None
            if cover_path and os.path.exists(cover_path):
                try:
                    cover_img = Image.open(cover_path)
                    ctk_cover = ctk.CTkImage(light_image=cover_img, dark_image=cover_img, size=(120, 180))
                except Exception as e:
                    print(f"Erro ao carregar capa {cover_path}: {e}")

            # Se não tiver capa, usa um placeholder
            if ctk_cover:
                lbl_cover = ctk.CTkLabel(item_frame, image=ctk_cover, text="")
            else:
                lbl_cover = ctk.CTkLabel(item_frame, text="Sem Capa", width=120, height=180, fg_color="gray")

            lbl_cover.pack(pady=5, padx=5)

            # Clique na capa ou texto abre o arquivo
            lbl_cover.bind("<Button-1>", lambda e, p=path: self.open_book_from_shelf(p))

            # Nome do arquivo (truncado se for muito grande)
            display_name = filename[:15] + "..." if len(filename) > 18 else filename
            lbl_title = ctk.CTkLabel(item_frame, text=display_name, font=("Arial", 12))
            lbl_title.pack(pady=(0, 2))
            lbl_title.bind("<Button-1>", lambda e, p=path: self.open_book_from_shelf(p))

            # Progresso (ex: 5/20)
            if total_pages and total_pages > 0:
                progress_text = f"{current_page + 1}/{total_pages}"
            else:
                progress_text = "0/0"

            lbl_prog = ctk.CTkLabel(item_frame, text=progress_text, text_color="gray", font=("Arial", 10))
            lbl_prog.pack(pady=(0, 5))

    def open_book_from_shelf(self, path):
        """Abre um livro diretamente da estante e muda para o leitor."""
        if os.path.exists(path):
            self.load_file(path)
        else:
            # Livro não encontrado (foi movido ou apagado)
            # Em uma versão completa, poderíamos perguntar se o usuário quer remover da estante
            print(f"Arquivo não encontrado: {path}")

    def show_reader(self):
        """Alterna para a tela do Leitor e exibe a página atual."""
        self.shelf_frame.pack_forget()
        self.reader_frame.pack(expand=True, fill="both")
        self.show_page()

    def open_file(self):
        file_path = ctk.filedialog.askopenfilename(
            filetypes=[("Livros e HQs", "*.cbz *.pdf"), ("Todos os arquivos", "*.*")]
        )
        if file_path:
            self.load_file(file_path)

    def extract_cover(self, path):
        """Extrai a primeira imagem de um arquivo CBZ ou a primeira página de um PDF para servir como capa."""
        try:
            ext = path.lower()
            if ext.endswith((".cbz", ".zip")):
                with zipfile.ZipFile(path, 'r') as z:
                    # Filtra e ordena as imagens
                    file_list = sorted([f for f in z.namelist() if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))])

                    if not file_list:
                        return None

                    # Pega a primeira imagem e converte para Image do Pillow
                    cover_data = z.read(file_list[0])
                    cover_img = Image.open(io.BytesIO(cover_data))

            elif ext.endswith(".pdf"):
                doc = fitz.open(path)
                if len(doc) == 0:
                    return None
                page = doc.load_page(0)
                # Extrai a capa em baixa resolução para thumbnail (matrix 1.0)
                pix = page.get_pixmap(matrix=fitz.Matrix(1.0, 1.0))
                cover_img = Image.open(io.BytesIO(pix.tobytes("png")))
                doc.close()
            else:
                return None

            # Gera uma miniatura para a capa
            cover_img.thumbnail((200, 300), Image.Resampling.LANCZOS)
            return cover_img
        except Exception as e:
            print(f"Erro ao extrair capa de {path}: {e}")
            return None

    def _load_cbz_pages(self, path):
        with zipfile.ZipFile(path, 'r') as z:
            file_list = sorted([f for f in z.namelist() if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))])
            for file in file_list:
                img_data = z.read(file)
                self.pages.append(Image.open(io.BytesIO(img_data)))

    def _load_pdf_pages(self, path):
        try:
            doc = fitz.open(path)
            # Define o zoom da página renderizada. 2.0 = 2x mais resolução que o original.
            matrix = fitz.Matrix(2.0, 2.0)
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                pix = page.get_pixmap(matrix=matrix)
                img_data = pix.tobytes("png")
                self.pages.append(Image.open(io.BytesIO(img_data)))
            doc.close()
        except Exception as e:
            print(f"Erro ao extrair PDF de {path}: {e}")

    def load_file(self, path):
        self.current_file_path = path
        self.pages = []

        # 1. Verifica se já temos a capa salva, se não, extrai e guarda no cache local
        existing_books = self.db.get_all_books()
        book_data = next((b for b in existing_books if b[0] == path), None)

        # A capa está no índice 3 (path, current_page, total_pages, cover_path)
        cover_path = book_data[3] if book_data and len(book_data) > 3 else None

        if not cover_path or not os.path.exists(cover_path):
            file_hash = hashlib.md5(path.encode('utf-8')).hexdigest()
            cover_path = os.path.join("covers", f"{file_hash}.jpg")

            cover_img = self.extract_cover(path)
            if cover_img:
                if cover_img.mode in ("RGBA", "P"):
                    cover_img = cover_img.convert("RGB")
                cover_img.save(cover_path, "JPEG", quality=85)
            else:
                cover_path = None

        # 2. Carrega as páginas usando o motor adequado
        ext = path.lower()
        if ext.endswith((".cbz", ".zip")):
            self._load_cbz_pages(path)
        elif ext.endswith(".pdf"):
            self._load_pdf_pages(path)
        else:
            print(f"Formato não suportado: {ext}")
            return

        if not self.pages:
            print("Nenhuma página encontrada no arquivo.")
            return

        # 3. Recupera onde parou do banco de dados
        self.current_page = self.db.get_progress(path)
        if self.current_page >= len(self.pages):
             self.current_page = 0

        # Salva (ou atualiza) os metadados do livro no banco (incluindo o caminho da capa)
        self.db.save_progress(self.current_file_path, self.current_page, len(self.pages), cover_path=cover_path)

        # Mostra o leitor (que agora chama show_page() por conta própria)
        self.show_reader()

    def show_page(self):
        if not self.pages:
            return

        # Salva no banco sempre que mudar de página ou exibir a atual
        if self.current_file_path:
            self.db.save_progress(self.current_file_path, self.current_page, len(self.pages))

        # Redimensionar imagem para caber na tela mantendo proporção
        img = self.pages[self.current_page]

        # Lógica simples de redimensionamento
        canvas_width = self.winfo_width() - 40
        canvas_height = self.winfo_height() - 150

        # To handle cases where winfo_width/height are initially 1
        if canvas_width <= 0:
            canvas_width = 800 - 40
        if canvas_height <= 0:
            canvas_height = 900 - 150

        # Create a copy so we don't modify the original image in self.pages
        img_copy = img.copy()
        img_copy.thumbnail((canvas_width, canvas_height), Image.Resampling.LANCZOS)

        ctk_img = ctk.CTkImage(light_image=img_copy, dark_image=img_copy, size=(img_copy.width, img_copy.height))
        self.canvas_label.configure(image=ctk_img, text="")

        # Atualizar indicador de progresso
        total_pages = len(self.pages)
        current = self.current_page + 1
        self.lbl_progress.configure(text=f"Página {current} de {total_pages}")

        # Atualizar barra de progresso (0 a 1)
        if total_pages > 1:
            progress = current / total_pages
            self.progress_bar.set(progress)
        else:
            self.progress_bar.set(1.0)

    def next_page(self):
        if self.current_page < len(self.pages) - 1:
            self.current_page += 1
            self.show_page()

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.show_page()

if __name__ == "__main__":
    app = ReadEraClone()
    app.mainloop()
