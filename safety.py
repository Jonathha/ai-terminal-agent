"""
Módulo de Segurança e Guardrails
Impede que a IA execute comandos perigosos, destrua o sistema operacional
ou acesse/modifique arquivos críticos do Windows.
"""

import re
import os
from pathlib import Path
from typing import Tuple

# Palavras e padrões terminantemente proibidos
BLOCKED_PATTERNS = [
    # Formatação e particionamento
    r"\bformat\b",
    r"\bdiskpart\b",
    r"\bfdisk\b",
    
    # Destruição de diretórios raiz ou do sistema
    r"rmdir\s+.*[a-zA-Z]:\\",
    r"rd\s+.*[a-zA-Z]:\\",
    r"del\s+.*[a-zA-Z]:\\(windows|system32)",
    r"del\s+.*\/[sSqQfF].*[a-zA-Z]:\\",
    r"remove-item\s+.*-recurse.*[a-zA-Z]:\\",
    
    # Alterações críticas no Registro do Windows e Boot
    r"reg\s+delete\s+hklm",
    r"bcdedit",
    
    # Desligamento não autorizado do computador
    r"\bshutdown\b",
    r"\bstop-computer\b",
    r"\brestart-computer\b",
    
    # Comandos destrutivos genéricos
    r":\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:", # Fork bomb
]

# Comandos considerados puramente de leitura (seguros para auto-aprovação se configurado)
READ_ONLY_PREFIXES = [
    "dir", "ls", "pwd", "cd", "Get-ChildItem", "Get-Location",
    "cat", "type", "Get-Content", "head", "tail",
    "git status", "git log", "git diff", "git branch",
    "python --version", "python -V", "node -v", "npm -v",
    "echo", "where", "which"
]

PROTECTED_PATHS = [
    os.environ.get("WINDIR", r"C:\Windows").lower(),
    os.environ.get("PROGRAMFILES", r"C:\Program Files").lower(),
    os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)").lower(),
]

def is_command_blocked(command: str) -> Tuple[bool, str]:
    """Verifica se o comando contém instruções destrutivas bloqueadas."""
    cmd_lower = command.strip().lower()
    
    for pattern in BLOCKED_PATTERNS:
        if re.search(pattern, cmd_lower):
            return True, f"COMANDO BLOQUEADO POR SEGURANÇA: Padrão de risco detectado ({pattern})."
            
    # Proteger caminhos críticos do Windows
    for p_path in PROTECTED_PATHS:
        if p_path in cmd_lower and any(act in cmd_lower for act in ["del", "rmdir", "remove-item", "attrib", "takeown"]):
            return True, f"SEGURANÇA: Modificação em diretório do sistema operacional negada ({p_path})."
            
    return False, ""

def is_read_only_command(command: str) -> bool:
    """Verifica se um comando é seguro/somente-leitura."""
    cmd_strip = command.strip().lower()
    return any(cmd_strip.startswith(prefix.lower()) for prefix in READ_ONLY_PREFIXES)

def is_safe_path(target_path: str, base_dir: Path) -> Tuple[bool, str]:
    """Garante que a escrita de arquivos não ocorra em pastas de sistema."""
    try:
        resolved = Path(target_path).resolve()
        resolved_str = str(resolved).lower()
        
        for p_path in PROTECTED_PATHS:
            if resolved_str.startswith(p_path):
                return False, f"Acesso negado: O caminho '{target_path}' pertence ao sistema operacional."
        return True, ""
    except Exception as e:
        return False, f"Caminho inválido: {str(e)}"
