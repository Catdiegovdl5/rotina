import tkinter as tk
import time
import logging
import urllib.request
import urllib.parse
from datetime import datetime
import winsound # [NOVIDADE] Biblioteca para emitir som no Windows

TELEGRAM_TOKEN = "7724330024:AAFtoSLgXVDlvNmeyPCVMnkWIqbk4wvLSVg"
TELEGRAM_CHAT_ID = "1501131002"

logging.basicConfig(
    filename="historico_agente.txt",
    level=logging.INFO,
    encoding="utf-8",
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logging.info("Agente Antigravity v2.1 Iniciado.")

rotina = {
    "07:00": "🌅 BLOCO 1: Alarme de Elite! Bebe 500ml de água e inicia o Treino.",
    "08:30": "💻 BLOCO 2: Deep Work & Prospecção. Postura Mewing e 2L de água.",
    "12:30": "🍱 BLOCO 3: Nutrição e Reset. Almoço e 20 min de descanso.",
    "14:30": "🧪 BLOCO 4: Imersão Técnica. Curso #27 de Segurança de Dados.",
    "18:00": "🌙 BLOCO 5: Descompressão. Leitura e Jantar.",
    "21:30": "🚨 BLACKOUT TOTAL. Telemóvel fora e preparar o sono."
}

def enviar_telegram(mensagem):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        dados = urllib.parse.urlencode({
            "chat_id": TELEGRAM_CHAT_ID,
            "text": f"🚨 AGENTE ANTIGRAVITY\n\n{mensagem}",
        }).encode("utf-8")
        urllib.request.urlopen(urllib.request.Request(url, data=dados), timeout=5)
    except Exception as e:
        logging.error(f"Falha no Telegram: {e}")

def disparar_alarme(mensagem_tarefa):
    try:
        # [NOVIDADE] Toca 3 apitos físicos antes de abrir a janela
        winsound.Beep(1000, 400) # Frequência 1000Hz por 400ms
        winsound.Beep(1000, 400)
        winsound.Beep(1500, 600) # Um apito mais agudo e longo no final

        janela = tk.Tk()
        janela.title("ALERTA DO ARQUITETO")
        janela.configure(bg="black")
        janela.attributes("-fullscreen", True)
        janela.attributes("-topmost", True)
        janela.focus_force()

        def ignorar_fecho():
            logging.warning("Tentativa de fechar bloqueada.")
        janela.protocol("WM_DELETE_WINDOW", ignorar_fecho)

        tk.Label(
            janela, text=mensagem_tarefa, font=("Arial", 30, "bold"),
            wraplength=1000, fg="red", bg="black", justify="center"
        ).pack(expand=True)

        def confirmar():
            logging.info("Tarefa confirmada pelo utilizador.")
            janela.destroy()

        tk.Button(
            janela, text="✅  TAREFA CONCLUÍDA  ✅", command=confirmar,
            bg="green", fg="white", font=("Arial", 20, "bold"), padx=40, pady=20
        ).pack(pady=50)

        janela.mainloop()

    except Exception as e:
        logging.error(f"Erro ao abrir janela: {e}")

def iniciar_agente():
    logging.info("Loop principal iniciado.")
    tarefas_concluidas = set()
    
    # [NOVIDADE] Guarda a data exata em que o programa iniciou
    dia_atual = datetime.now().date() 

    while True:
        try:
            agora = datetime.now()
            hora_atual = agora.strftime("%H:%M")
            dia_de_hoje = agora.date()

            # [NOVIDADE] Reset Inteligente: Se o dia mudou, limpa as tarefas!
            if dia_de_hoje != dia_atual:
                tarefas_concluidas.clear()
                dia_atual = dia_de_hoje # Atualiza para o novo dia
                logging.info("Reset diário efetuado com sucesso para o novo dia.")

            if hora_atual in rotina and hora_atual not in tarefas_concluidas:
                tarefa = rotina[hora_atual]
                
                enviar_telegram(tarefa)
                disparar_alarme(tarefa)
                
                tarefas_concluidas.add(hora_atual)

        except Exception as erro_fatal:
            logging.critical(f"Erro crítico no loop: {erro_fatal}")

        time.sleep(30)

if __name__ == "__main__":
    iniciar_agente()
