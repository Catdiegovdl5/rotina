import os
import sys

# ==========================================
# Script de instalação do Atalho Invisível
# ==========================================
# Este script cria um atalho (.lnk) na pasta Startup do Windows
# para que o agente seja iniciado automaticamente no arranque do PC.
# Corre este ficheiro UMA ÚNICA VEZ para instalar o agente.

try:
    import winshell
    from win32com.client import Dispatch
    HAS_WINSHELL = True
except ImportError:
    HAS_WINSHELL = False

def instalar_atalho_simples():
    """Método simples: cria um ficheiro .bat na pasta Startup."""
    startup_dir = os.path.join(
        os.environ.get("APPDATA", ""),
        "Microsoft", "Windows", "Start Menu", "Programs", "Startup"
    )
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    tracker_path = os.path.join(script_dir, "tracker.py")
    pythonw_path = r"C:\Python314\pythonw.exe"
    
    # Conteúdo do ficheiro .bat que arranca o agente de forma invisível
    bat_content = f'@echo off\nstart "" "{pythonw_path}" "{tracker_path}"\n'
    bat_path = os.path.join(startup_dir, "agente_antigravity.bat")
    
    with open(bat_path, "w") as f:
        f.write(bat_content)
    
    print(f"✅ Atalho instalado em:\n   {bat_path}")
    print("\nO agente vai iniciar AUTOMATICAMENTE na próxima vez que ligares o PC!")
    print("Para desinstalar, apaga esse ficheiro .bat.")

if __name__ == "__main__":
    print("═══════════════════════════════════════")
    print("  INSTALADOR DO AGENTE ANTIGRAVITY v2.0")
    print("═══════════════════════════════════════\n")
    instalar_atalho_simples()
    input("\nPressiona ENTER para fechar...")
