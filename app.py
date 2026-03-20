import customtkinter as ctk
from PIL import Image
import zipfile
import io

class ReadEraClone(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Meu ReadEra PC - MVP")
        self.geometry("800x900")
        ctk.set_appearance_mode("dark")

        # Variáveis de controle
        self.pages = []
        self.current_page = 0

        # Interface - Área de exibição da imagem
        self.canvas_label = ctk.CTkLabel(self, text="Arraste um arquivo CBZ ou use o botão", text_color="gray")
        self.canvas_label.pack(expand=True, fill="both", padx=20, pady=20)

        # Indicador de progresso (Página X de Y)
        self.lbl_progress = ctk.CTkLabel(self, text="")
        self.lbl_progress.pack(pady=5)

        # Barra de progresso
        self.progress_bar = ctk.CTkProgressBar(self, width=400)
        self.progress_bar.set(0)
        self.progress_bar.pack(pady=5)

        # Botão para abrir arquivo
        self.btn_open = ctk.CTkButton(self, text="Abrir HQ (.cbz)", command=self.open_file)
        self.btn_open.pack(pady=10)

        # Atalhos de teclado
        self.bind("<Right>", lambda e: self.next_page())
        self.bind("<Left>", lambda e: self.prev_page())

    def open_file(self):
        file_path = ctk.filedialog.askopenfilename(filetypes=[("Comic Book Archive", "*.cbz")])
        if file_path:
            self.load_cbz(file_path)

    def extract_cover(self, path):
        """Extrai a primeira imagem de um arquivo CBZ para servir como capa."""
        try:
            with zipfile.ZipFile(path, 'r') as z:
                # Filtra e ordena as imagens
                file_list = sorted([f for f in z.namelist() if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))])

                if not file_list:
                    return None

                # Pega a primeira imagem e converte para Image do Pillow
                cover_data = z.read(file_list[0])
                cover_img = Image.open(io.BytesIO(cover_data))

                # Gera uma miniatura para a capa
                cover_img.thumbnail((200, 300), Image.Resampling.LANCZOS)
                return cover_img
        except Exception as e:
            print(f"Erro ao extrair capa: {e}")
            return None

    def load_cbz(self, path):
        self.pages = []

        # Opcional: Extrair e guardar a capa (preparação para a Estante)
        # self.current_cover = self.extract_cover(path)

        with zipfile.ZipFile(path, 'r') as z:
            # Filtra apenas arquivos de imagem e ordena alfabeticamente
            file_list = sorted([f for f in z.namelist() if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))])

            for file in file_list:
                img_data = z.read(file)
                self.pages.append(Image.open(io.BytesIO(img_data)))

        self.current_page = 0
        self.show_page()

    def show_page(self):
        if not self.pages:
            return

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
