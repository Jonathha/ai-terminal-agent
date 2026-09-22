"""
Script para criar o inicializador e atalho do AI Terminal na Área de Trabalho do Usuário.
"""

import os
import subprocess
from pathlib import Path

def get_real_desktop():
    import winreg
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders")
        desktop_val, _ = winreg.QueryValueEx(key, "Desktop")
        return Path(os.path.expandvars(desktop_val))
    except Exception:
        return Path(os.environ.get("USERPROFILE", "")) / "Desktop"

def create_desktop_launchers():
    project_dir = Path(__file__).parent.resolve()
    desktop = get_real_desktop()
    print(f"Detectada Area de Trabalho em: {desktop}")
    main_script = project_dir / "main.py"
    
    # 1. Cria o script batch na pasta do projeto
    local_bat = project_dir / "launch.bat"
    bat_content = f"""@echo off
title AI Terminal Agent
cd /d "{project_dir}"
python main.py
if errorlevel 1 (
    echo.
    echo Ocorreu um erro ao rodar o AI Terminal. Pressione qualquer tecla para fechar.
    pause >nul
)
"""
    with open(local_bat, "w", encoding="utf-8") as f:
        f.write(bat_content)
        
    # 2. Cria o arquivo executável .bat direto no Desktop (100% garantido no Windows)
    desktop_bat = desktop / "AI Terminal.bat"
    with open(desktop_bat, "w", encoding="utf-8") as f:
        f.write(bat_content)
    print(f"[OK] Inicializador criado na Area de Trabalho: {desktop_bat}")
    
    # 3. Tenta criar também o atalho .lnk elegante com PowerShell WScript.Shell
    try:
        ps_cmd = f"""
        $WshShell = New-Object -comObject WScript.Shell
        $Shortcut = $WshShell.CreateShortcut('{desktop}\\AI Terminal.lnk')
        $Shortcut.TargetPath = '{local_bat}'
        $Shortcut.WorkingDirectory = '{project_dir}'
        $Shortcut.Description = 'AI Terminal Agent - Terminal Inteligente com IA'
        $Shortcut.Save()
        """
        subprocess.run(["powershell", "-Command", ps_cmd], capture_output=True, text=True)
        print(f"[OK] Atalho .lnk criado na Area de Trabalho: {desktop / 'AI Terminal.lnk'}")
    except Exception as e:
        print(f"Nota: atalho .lnk nao criado ({e}), mas o arquivo 'AI Terminal.bat' esta pronto.")

if __name__ == "__main__":
    create_desktop_launchers()
