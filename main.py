"""
Terminal AI Agent - Interface Principal Interativa (Fluida e Inteligente)
"""

import os
import sys
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt
from rich.markdown import Markdown

from config import load_config, save_config, set_api_key, MODEL_CATALOG
import tools
from agent import TerminalAgent

console = Console()

def print_banner():
    console.clear()
    banner_text = """
 [bold cyan]╔═════════════════════════════════════════════════════════════════════════════╗[/bold cyan]
 [bold cyan]║[/bold cyan]  [bold yellow]⚡ AI TERMINAL AGENT[/bold yellow] - Programação com IA & Acesso ao PC (Windows)         [bold cyan]║[/bold cyan]
 [bold cyan]╚═════════════════════════════════════════════════════════════════════════════╝[/bold cyan]
 [dim]• Modelos: Gemini 3.8 Flash, 3.7 Flash, 3.5 Flash, 3.5 Lite, 3.1 Pro, Claude, GPT[/dim]
 [dim]• Comandos rápidos: Digite [bold green]model[/bold green], [bold green]help[/bold green], [bold green]clear[/bold green], [bold green]yolo[/bold green] ou [bold red]exit[/bold red] (com ou sem barra)[/dim]
"""
    console.print(banner_text)

def confirmation_callback(action_type: str, details: str, is_read_only: bool = False):
    """Callback invocado pelas ferramentas antes de executar ações no PC."""
    cfg = load_config()
    
    # Se o comando for puramente leitura e a opção estiver ativa
    if is_read_only and cfg.get("auto_approve_read_only", True):
        console.print(f"[dim green]✔ Auto-aprovado (leitura): {details}[/dim green]")
        return True, "Aprovado automaticamente"
        
    # Se modo autônomo (YOLO) estiver ligado
    if cfg.get("yolo_mode", False):
        console.print(f"[yellow]⚡ Auto-executando (Modo YOLO): {details}[/yellow]")
        return True, "Modo autônomo ativo"

    # Caixa de confirmação visual para o usuário
    console.print()
    panel_title = f"[bold red]⚠ AUTORIZAÇÃO NECESSÁRIA: {action_type.upper()}[/bold red]"
    console.print(Panel(details, title=panel_title, border_style="yellow"))
    
    escolha = Prompt.ask(
        "[bold cyan]Permitir execução no seu PC?[/bold cyan]",
        choices=["s", "n", "todos"],
        default="s"
    ).lower().strip()
    
    if escolha == "s":
        return True, "Autorizado pelo usuário"
    elif escolha == "todos":
        cfg["yolo_mode"] = True
        save_config(cfg)
        console.print("[bold yellow]⚡ Modo de autorização total ativado para esta sessão![/bold yellow]")
        return True, "Autorização para todos os comandos ativada"
    else:
        return False, "Usuário recusou a execução."

def tool_status_callback(stage: str, func_name: str, data: any):
    """Exibe feedback visual quando a IA usa uma ferramenta."""
    if stage == "start":
        if func_name == "execute_terminal_command":
            console.print(f"[bold cyan]⚡ Executando comando:[/bold cyan] [yellow]{data.get('command')}[/yellow]")
        elif func_name == "web_search":
            console.print(f"[bold blue]🔍 Pesquisando na Web:[/bold blue] [cyan]{data.get('query')}[/cyan]")
        elif func_name == "read_file":
            console.print(f"[bold dim]📖 Lendo arquivo:[/bold dim] {data.get('path')}")
        elif func_name == "write_file":
            console.print(f"[bold dim]✍ Gravando arquivo:[/bold dim] {data.get('path')}")
        elif func_name == "list_directory":
            console.print(f"[bold dim]📁 Listando pasta:[/bold dim] {data.get('path', '.')}")
    elif stage == "finish":
        pass

def show_help():
    table = Table(title="Comandos do Terminal AI", border_style="cyan")
    table.add_column("Comando", style="green", no_wrap=True)
    table.add_column("Exemplos de Uso", style="yellow")
    table.add_column("Descrição", style="white")
    
    table.add_row("model [nome/nº]", "model 3.5 lite, model 1, /model", "Muda o modelo ou exibe a lista para escolher")
    table.add_row("key", "key, /key", "Adicionar ou alterar chave de API")
    table.add_row("yolo", "yolo, /yolo", "Liga/desliga confirmação a cada comando")
    table.add_row("clear", "clear, cls, /clear", "Limpa a tela do terminal")
    table.add_row("help", "help, ajuda, /help", "Exibe esta tela de ajuda")
    table.add_row("exit", "exit, sair, quit", "Fecha o AI Terminal")
    console.print(table)

def find_matching_model(query: str, models: list) -> Optional[str]:
    """Busca inteligente de modelos por número, ID ou palavras-chave."""
    q = query.strip().lower()
    q_slug = q.replace(" ", "-")

    # 1. Checa se o usuário digitou o número correspondente (1, 2, 3...)
    try:
        idx = int(q) - 1
        if 0 <= idx < len(models):
            return models[idx]["id"]
    except ValueError:
        pass

    # 2. Checa correspondência exata
    for m in models:
        if m["id"].lower() == q_slug:
            return m["id"]

    # 3. Checa se o termo está contido no ID (ex: '3.5-lite', '3.8', 'pro')
    for m in models:
        if q_slug in m["id"].lower():
            return m["id"]

    # 4. Checa se todas as palavras digitadas aparecem no ID (ex: '3.5' e 'lite')
    words = q.split()
    for m in models:
        if all(w in m["id"].lower() for w in words):
            return m["id"]

    return None

def handle_model_switch(cfg: dict, arg: Optional[str] = None):
    provider = cfg.get("provider", "gemini")
    cat = MODEL_CATALOG.get(provider, {})
    models = cat.get("models", [])
    
    # Se o usuário já passou o modelo direto (ex: "model 3.5 lite" ou "model 2")
    if arg and arg.strip():
        matched = find_matching_model(arg, models)
        if matched:
            cfg["model"] = matched
            save_config(cfg)
            console.print(f"[bold green]✔ Modelo alterado diretamente para: [bold yellow]{matched}[/bold yellow][/bold green]\n")
            return matched
        else:
            console.print(f"[yellow]Não foi possível identificar o modelo '{arg}'. Veja as opções abaixo:[/yellow]")

    # Exibe a tabela interativa
    table = Table(title=f"Modelos Disponíveis ({cat.get('name')})", border_style="yellow")
    table.add_column("#", style="cyan", width=3)
    table.add_column("ID do Modelo", style="green")
    table.add_column("Descrição", style="white")
    
    for i, m in enumerate(models, 1):
        is_current = " [bold yellow]★ (Atual)[/bold yellow]" if m["id"] == cfg.get("model") else ""
        table.add_row(str(i), m["id"] + is_current, m["desc"])
    console.print(table)
    
    choice = Prompt.ask("Digite o número do modelo desejado (ex: 1, 2, 3...) ou 'c' para cancelar").strip()
    if choice.lower() == 'c' or not choice:
        return None
        
    matched = find_matching_model(choice, models)
    if matched:
        cfg["model"] = matched
        save_config(cfg)
        console.print(f"[bold green]✔ Modelo alterado para: [bold yellow]{matched}[/bold yellow][/bold green]\n")
        return matched
    else:
        cfg["model"] = choice
        save_config(cfg)
        console.print(f"[bold green]✔ Modelo definido como: [bold yellow]{choice}[/bold yellow][/bold green]\n")
        return choice

def handle_key_setup(cfg: dict):
    console.print("\n[bold cyan]=== Configuração de Chave de API ===[/bold cyan]")
    console.print("[dim]Pode colar usando Ctrl+V ou clicando com o Botão Direito do mouse.[/dim]")
    
    key = Prompt.ask("[bold green]Cole sua Chave de API aqui[/bold green]").strip()
    key = key.strip('"').strip("'")
    
    if not key:
        console.print("[red]Nenhuma chave inserida.[/red]")
        return
        
    provider, default_model = set_api_key(key)
    masked = key[:6] + "..." + key[-4:] if len(key) > 10 else "***"
    console.print(f"[bold green]✔ Chave recebida: {masked} ({len(key)} caracteres)[/bold green]")
    console.print(f"[bold green]✔ Provedor detectado: {provider.upper()}[/bold green]")
    console.print(f"[bold green]✔ Modelo ativo: {default_model}[/bold green]\n")

def check_file_key(cfg: dict) -> bool:
    key_file = Path(__file__).parent / "api_key.txt"
    if key_file.exists():
        k = key_file.read_text("utf-8").strip().strip('"').strip("'")
        if k and not k.startswith("#"):
            provider, default_model = set_api_key(k)
            console.print(f"[bold green]✔ Chave carregada de api_key.txt ({provider.upper()})![/bold green]")
            return True
    return False

def main():
    print_banner()
    tools.set_confirm_callback(confirmation_callback)
    
    cfg = load_config()
    
    if not cfg.get("provider") or not cfg.get("api_keys", {}).get(cfg.get("provider")):
        check_file_key(cfg)
        cfg = load_config()
        
    provider = cfg.get("provider")
    
    while not provider or not cfg.get("api_keys", {}).get(provider):
        console.print("\n[yellow]Nenhuma chave de API configurada encontrada.[/yellow]")
        console.print("[dim]Você pode colar sua chave agora ou colar no arquivo 'api_key.txt'.[/dim]")
        
        handle_key_setup(cfg)
        cfg = load_config()
        provider = cfg.get("provider")
        
        if not provider or not cfg.get("api_keys", {}).get(provider):
            tentar = Prompt.ask("[yellow]Deseja tentar novamente?[/yellow]", choices=["s", "n"], default="s")
            if tentar.lower() != "s":
                console.print("[red]Encerrando.[/red]")
                return

    current_model = cfg.get("model") or MODEL_CATALOG[provider]["default"]
    api_key = cfg["api_keys"][provider]

    console.print(f"[bold green]● Status:[/bold green] Conectado a [bold cyan]{provider.upper()}[/bold cyan] ([bold yellow]{current_model}[/bold yellow])")
    console.print(f"[dim]Diretório de trabalho:[/dim] {Path.cwd()}\n")

    agent = TerminalAgent(provider, current_model, api_key)

    while True:
        try:
            # Mostra o modelo atual no prompt para o usuário sempre saber onde está!
            prompt_label = f"[dim][{cfg['model']}][/dim] [bold green]Você[/bold green]"
            user_input = Prompt.ask(prompt_label).strip()
            if not user_input:
                continue

            # Parser inteligente de comandos (com ou sem barra '/')
            parts = user_input.split(maxsplit=1)
            raw_cmd = parts[0].lower().lstrip("/")
            arg = parts[1].strip() if len(parts) > 1 else ""

            if raw_cmd in ["exit", "quit", "sair", "fechar"]:
                console.print("[bold yellow]Até logo![/bold yellow]")
                break
            elif raw_cmd in ["help", "ajuda", "comandos"]:
                show_help()
                continue
            elif raw_cmd in ["clear", "limpar", "cls"]:
                print_banner()
                continue
            elif raw_cmd in ["model", "modelo"]:
                new_m = handle_model_switch(cfg, arg)
                if new_m:
                    cfg = load_config()
                    agent = TerminalAgent(cfg["provider"], cfg["model"], cfg["api_keys"][cfg["provider"]])
                continue
            elif raw_cmd in ["key", "chave", "api"]:
                handle_key_setup(cfg)
                cfg = load_config()
                agent = TerminalAgent(cfg["provider"], cfg["model"], cfg["api_keys"][cfg["provider"]])
                continue
            elif raw_cmd in ["yolo", "auto"]:
                cfg["yolo_mode"] = not cfg.get("yolo_mode", False)
                save_config(cfg)
                status_str = "[red]LIGADO (Execução sem confirmação)[/red]" if cfg["yolo_mode"] else "[green]DESLIGADO (Seguro com confirmação)[/green]"
                console.print(f"Modo YOLO: {status_str}")
                continue

            # Se for conversa normal, envia para a IA
            with console.status("[bold green]IA processando...[/bold green]", spinner="dots"):
                response = agent.chat_step(user_input, tool_callback=tool_status_callback)

            console.print(f"\n[bold yellow]IA ({cfg['model']}):[/bold yellow]")
            console.print(Markdown(response))
            console.print()

        except KeyboardInterrupt:
            console.print("\n[yellow]Operação cancelada pelo usuário (Ctrl+C).[/yellow]")
        except Exception as e:
            console.print(f"\n[bold red]Erro:[/bold red] {str(e)}\n")

if __name__ == "__main__":
    main()
