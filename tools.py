"""
Módulo de Ferramentas (Tools / Function Calling)
Fornece execução de comandos PowerShell, busca na web, e manipulação de arquivos.
"""

import os
import subprocess
from pathlib import Path
from typing import Dict, Any, List
from safety import is_command_blocked, is_read_only_command, is_safe_path

# Callback de confirmação visual (injetado pela UI do terminal)
_confirm_callback = None

def set_confirm_callback(callback):
    global _confirm_callback
    _confirm_callback = callback

def execute_terminal_command(command: str) -> str:
    """
    Executa um comando no PowerShell do Windows do usuário e retorna a saída.
    Ações de modificação ou perigosas solicitam confirmação do usuário.
    """
    # 1. Checagem de segurança rígida
    blocked, reason = is_command_blocked(command)
    if blocked:
        return f"[ERRO DE SEGURANÇA]: {reason}"

    # 2. Confirmação do usuário
    is_ro = is_read_only_command(command)
    if _confirm_callback:
        allowed, msg = _confirm_callback("comando", command, is_read_only=is_ro)
        if not allowed:
            return f"Operação cancelada pelo usuário: {msg}"

    # 3. Execução no PowerShell com suporte UTF-8
    try:
        proc = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", command],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120
        )
        out = proc.stdout.strip()
        err = proc.stderr.strip()
        
        result_parts = []
        if out:
            result_parts.append(out)
        if err:
            result_parts.append(f"[stderr]: {err}")
        if proc.returncode != 0:
            result_parts.append(f"[Código de saída: {proc.returncode}]")
            
        return "\n".join(result_parts) if result_parts else "[Comando executado com sucesso sem saída de texto]"
    except subprocess.TimeoutExpired:
        return "[ERRO]: O comando excedeu o tempo limite de 120 segundos e foi interrompido."
    except Exception as e:
        return f"[ERRO DE EXECUÇÃO]: {str(e)}"

def web_search(query: str, max_results: int = 5) -> str:
    """
    Pesquisa na web em tempo real usando DuckDuckGo para encontrar documentação,
    soluções de erros de programação e informações recentes.
    """
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
            if not results:
                return f"Nenhum resultado encontrado para: '{query}'"
            
            formatted = []
            for i, r in enumerate(results, 1):
                title = r.get("title", "Sem título")
                snippet = r.get("body", "")
                link = r.get("href", "")
                formatted.append(f"{i}. **{title}**\n   {snippet}\n   *Link: {link}*")
            return "\n\n".join(formatted)
    except Exception as e:
        return f"[Falha na busca web]: {str(e)}"

def read_file(path: str) -> str:
    """Lê o conteúdo completo de um arquivo local de texto."""
    try:
        p = Path(path).resolve()
        if not p.exists():
            return f"[ERRO]: Arquivo '{path}' não encontrado."
        if not p.is_file():
            return f"[ERRO]: '{path}' é um diretório, use list_directory."
        with open(p, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        return content if content else "[Arquivo vazio]"
    except Exception as e:
        return f"[ERRO AO LER ARQUIVO]: {str(e)}"

def write_file(path: str, content: str) -> str:
    """
    Cria ou sobrescreve um arquivo de texto no computador.
    Solicita confirmação prévia ao usuário.
    """
    safe, reason = is_safe_path(path, Path.cwd())
    if not safe:
        return f"[ERRO DE SEGURANÇA]: {reason}"

    if _confirm_callback:
        allowed, msg = _confirm_callback("escrever_arquivo", f"Arquivo: {path}\n{len(content)} caracteres", is_read_only=False)
        if not allowed:
            return f"Operação cancelada pelo usuário: {msg}"

    try:
        p = Path(path).resolve()
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(content)
        return f"[SUCESSO]: Arquivo salvo com sucesso em '{p}'"
    except Exception as e:
        return f"[ERRO AO ESCREVER ARQUIVO]: {str(e)}"

def list_directory(path: str = ".") -> str:
    """Lista os arquivos e pastas do diretório especificado."""
    try:
        p = Path(path).resolve()
        if not p.exists():
            return f"[ERRO]: O caminho '{path}' não existe."
        
        items = []
        for item in sorted(p.iterdir()):
            kind = "[PASTA]" if item.is_dir() else "[ARQUIVO]"
            size = f"({item.stat().st_size} bytes)" if item.is_file() else ""
            items.append(f"{kind} {item.name} {size}")
            
        if not items:
            return f"O diretório '{p}' está vazio."
        return f"Conteúdo de '{p}':\n" + "\n".join(items)
    except Exception as e:
        return f"[ERRO AO LISTAR DIRETÓRIO]: {str(e)}"

# Definições JSON de ferramentas (padrão OpenAPI / Tool Calling)
AVAILABLE_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "execute_terminal_command",
            "description": "Executa comandos no PowerShell do Windows do usuário (ex: compilar, rodar scripts, instalar pacotes, testar).",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "O comando exato a ser executado no PowerShell."
                    }
                },
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Pesquisa na web por documentação de código, bibliotecas, resolução de erros do terminal e novidades.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "A frase ou termos de busca."
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Lê o código ou conteúdo textual de um arquivo local.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Caminho do arquivo a ser lido."
                    }
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Escreve ou cria código/conteúdo em um arquivo local.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Caminho do arquivo a ser criado ou sobrescrito."
                    },
                    "content": {
                        "type": "string",
                        "description": "Conteúdo de texto completo do arquivo."
                    }
                },
                "required": ["path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_directory",
            "description": "Lista os arquivos e subpastas de um diretório no computador.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Caminho do diretório (padrão: '.')."
                    }
                },
                "required": []
            }
        }
    }
]

TOOL_FUNCTIONS = {
    "execute_terminal_command": execute_terminal_command,
    "web_search": web_search,
    "read_file": read_file,
    "write_file": write_file,
    "list_directory": list_directory
}
