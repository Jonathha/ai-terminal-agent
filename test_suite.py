"""
Script de Testes e Validação do AI Terminal
Verifica detecção de chaves, guardrails de segurança e ferramentas.
"""

import sys
from pathlib import Path

from config import detect_provider, set_api_key, load_config
from safety import is_command_blocked, is_read_only_command, is_safe_path
from tools import list_directory, read_file

def run_tests():
    print("--- Teste 1: Deteccao de Chaves de API ---")
    gemini_key = "AIzaSyD-fakeGeminiKeyForTesting12345"
    claude_key = "sk-ant-api03-fakeClaudeKeyForTesting123"
    openai_key = "sk-proj-fakeOpenAIKeyForTesting123456"
    
    assert detect_provider(gemini_key) == "gemini", "Falha na deteccao do Gemini"
    assert detect_provider(claude_key) == "claude", "Falha na deteccao do Claude"
    assert detect_provider(openai_key) == "openai", "Falha na deteccao da OpenAI"
    
    # Testar set_api_key com Gemini moderno
    prov, mod = set_api_key(gemini_key)
    assert "3." in mod or "3-" in mod, f"Modelo Gemini deveria ser geracao 3.x, obteve {mod}"
    print(f"[PASSOU] Auto-deteccao de provedores validada com modelo moderno: {mod}.")

    print("\n--- Teste 2: Guardrails de Seguranca ---")
    # Comandos perigosos que devem ser bloqueados:
    bad_commands = [
        "format C: /fs:NTFS",
        "diskpart",
        "rmdir /s /q C:\\",
        "del /f /s /q C:\\Windows\\System32",
        "shutdown -s -t 0",
        "reg delete HKLM\\Software\\Policies"
    ]
    for cmd in bad_commands:
        blocked, reason = is_command_blocked(cmd)
        assert blocked, f"FALHA: Comando perigoso '{cmd}' nao foi bloqueado!"
        print(f"[BLOQUEADO OK]: {cmd} -> {reason}")
    print("[PASSOU] Todos os comandos perigosos foram interceptados!")

    print("\n--- Teste 3: Deteccao de Comandos Seguros (Read-Only) ---")
    safe_commands = ["dir", "Get-ChildItem", "git status", "cat README.md", "python -V"]
    for cmd in safe_commands:
        assert is_read_only_command(cmd), f"FALHA: Comando '{cmd}' deveria ser somente-leitura"
    print("[PASSOU] Comandos seguros reconhecidos com sucesso.")

    print("\n--- Teste 4: Ferramentas Locais ---")
    listing = list_directory(".")
    assert "main.py" in listing, "Falha ao listar main.py no diretorio atual"
    print("[PASSOU] list_directory operando corretamente.")

    readme_content = read_file("config.py")
    assert "MODEL_CATALOG" in readme_content, "Falha ao ler config.py"
    print("[PASSOU] read_file operando corretamente.")

    print("\n==========================================")
    print("TODOS OS TESTES PASSARAM COM 100% DE SUCESSO!")
    print("==========================================")

if __name__ == "__main__":
    run_tests()
