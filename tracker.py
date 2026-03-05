import tkinter as tk
import time
import logging
import urllib.request
import urllib.parse
from datetime import datetime

# ==========================================
# ⚙️ CONFIGURAÇÃO DO TELEGRAM
# ==========================================
TELEGRAM_TOKEN = "7724330024:AAFtoSLgXVDlvNmeyPCVMnkWIqbk4wvLSVg"
TELEGRAM_CHAT_ID = "1501131002"

# ==========================================
# 1. DIÁRIO DO AGENTE (Sistema de Logs)
# ==========================================
# Cria o ficheiro "historico_agente.txt" na mesma pasta.
# Podes abri-lo a qualquer momento para ver o que o agente fez.
logging.basicConfig(
    filename="historico_agente.txt",
    level=logging.INFO,
    encoding="utf-8",
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logging.info("Agente Antigravity v2.0 Iniciado.")

# ==========================================
# 2. A MEMÓRIA DO AGENTE: Os teus blocos de rotina
# ==========================================
rotina = {
    "07:00": "🌅 BLOCO 1: Alarme de Elite! Bebe 500ml de água e inicia o Treino.",
    "08:30": "💻 BLOCO 2: Deep Work & Prospecção. Postura Mewing e 2L de água.",
    "12:30": "🍱 BLOCO 3: Nutrição e Reset. Almoço e 20 min de descanso sem ecrãs.",
    "14:30": "🧪 BLOCO 4: Imersão Técnica. Curso #27 de Segurança de Dados.",
    "18:00": "🌙 BLOCO 5: Descompressão. Leitura e Jantar.",
    "21:30": "🚨 BLACKOUT TOTAL. Telemóvel fora e preparar o sono.",
    "11:35": "🧪 TESTE v2.0: Visibilidade Absoluta Confirmada!"
}

# ==========================================
# 3. NOTIFICAÇÃO TELEGRAM (ANDROID)
# ==========================================
def enviar_telegram(mensagem):
    """Envia notificação para o Android via Telegram Bot."""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        dados = urllib.parse.urlencode({
            "chat_id": TELEGRAM_CHAT_ID,
            "text": f"🚨 AGENTE ANTIGRAVITY\n\n{mensagem}",
        }).encode("utf-8")
        urllib.request.urlopen(urllib.request.Request(url, data=dados), timeout=5)
        logging.info("Notificação Telegram enviada com sucesso.")
    except Exception as e:
        logging.error(f"Falha no Telegram: {e}")

# ==========================================
# 4. O ATUADOR: Janela Teimosa v2.0 (Ecrã Inteiro)
# ==========================================
def disparar_alarme(mensagem_tarefa):
    """Janela que ocupa o ecrã inteiro e não pode ser fechada pelo X."""
    try:
        janela = tk.Tk()
        janela.title("ALERTA DO ARQUITETO")

        # Fundo preto, ecrã inteiro, sempre no topo
        janela.configure(bg="black")
        janela.attributes("-fullscreen", True)
        janela.attributes("-topmost", True)
        janela.focus_force()

        # Bloqueia o botão X
        def ignorar_fecho():
            logging.warning("Tentativa de fechar bloqueada.")
        janela.protocol("WM_DELETE_WINDOW", ignorar_fecho)

        # Texto da tarefa, grande e chamativo
        tk.Label(
            janela,
            text=mensagem_tarefa,
            font=("Arial", 30, "bold"),
            wraplength=1000,
            fg="red",
            bg="black",
            justify="center"
        ).pack(expand=True)

        # Botão de confirmação
        def confirmar():
            logging.info(f"Tarefa confirmada pelo utilizador.")
            janela.destroy()

        tk.Button(
            janela,
            text="✅  TAREFA CONCLUÍDA  ✅",
            command=confirmar,
            bg="green",
            fg="white",
            font=("Arial", 20, "bold"),
            padx=40,
            pady=20
        ).pack(pady=50)

        logging.info("Janela fullscreen exibida.")
        janela.mainloop()

    except Exception as e:
        logging.error(f"Erro ao abrir janela: {e}")

# ==========================================
# 5. O CORAÇÃO DO AGENTE: Loop Blindado v2.0
# ==========================================
def iniciar_agente():
    print("Agente Antigravity v2.0 a correr em background...")
    logging.info("Loop principal iniciado.")
    tarefas_concluidas = set()

    while True:
        try:
            agora = datetime.now()
            hora_atual = agora.strftime("%H:%M")

            # Reset diário à meia-noite
            if hora_atual == "00:00" and "00:00_reset" not in tarefas_concluidas:
                tarefas_concluidas.clear()
                logging.info("Reset diário efetuado.")
                tarefas_concluidas.add("00:00_reset")

            if hora_atual in rotina and hora_atual not in tarefas_concluidas:
                tarefa = rotina[hora_atual]
                logging.info(f"Gatilho ativado: {hora_atual}")

                # Notifica o Android ANTES de mostrar a janela
                enviar_telegram(tarefa)

                # Mostra a janela bloqueante
                disparar_alarme(tarefa)

                tarefas_concluidas.add(hora_atual)

        except Exception as erro_fatal:
            # ESCUDO: o agente nunca fecha por erro
            logging.critical(f"Erro crítico no loop: {erro_fatal}")

        # Espera 30 segundos entre verificações (baixo consumo de CPU)
        time.sleep(30)

if __name__ == "__main__":
    iniciar_agente()
