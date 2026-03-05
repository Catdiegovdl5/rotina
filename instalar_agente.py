import os
import sys

def instalar_atalho_simples():
    startup_dir = os.path.join(
        os.environ.get("APPDATA", ""),
        "Microsoft", "Windows", "Start Menu", "Programs", "Startup"
    )
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    tracker_path = os.path.join(script_dir, "tracker.py")
    
    # [NOVIDADE] sys.executable descobre a pasta exata do teu Python
    # e nós substituímos "python.exe" por "pythonw.exe" para ser invisível.
    caminho_python_base = sys.executable
    pythonw_path = caminho_python_base.replace("python.exe", "pythonw.exe")
    
    bat_content = f'@echo off\nstart "" "{pythonw_path}" "{tracker_path}"\n'
    bat_path = os.path.join(startup_dir, "agente_antigravity.bat")
    
    with open(bat_path, "w") as f:
        f.write(bat_content)
    
    print(f"✅ Atalho instalado em:\n   {bat_path}")
    print(f"✅ Python detetado em:\n   {pythonw_path}")
    print("\nO agente vai iniciar AUTOMATICAMENTE na próxima vez que ligares o PC!")

if __name__ == "__main__":
    print("═══════════════════════════════════════")
    print("  INSTALADOR DO AGENTE ANTIGRAVITY v2.1")
    print("═══════════════════════════════════════\n")
    instalar_atalho_simples()
    input("\nPressiona ENTER para fechar...")
