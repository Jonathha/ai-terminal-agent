"""
Módulo de Configuração do Terminal de IA
Gerencia chaves de API, detecção automática do provedor e catálogo de modelos modernos.
(Modelos obsoletos como Gemini 2.5 e inferiores foram totalmente removidos).
"""

import json
import os
from pathlib import Path
from typing import Optional, Dict, Any

CONFIG_FILE = Path(__file__).parent / "ai_terminal_config.json"

MODEL_CATALOG = {
    "gemini": {
        "name": "Google Gemini",
        "default": "gemini-3.8-flash",
        "models": [
            {"id": "gemini-3.8-flash",      "label": "Gemini 3.8 Flash (Recomendado)",  "desc": "Modelo de ponta para agentes autônomos e código"},
            {"id": "gemini-3.7-flash",      "label": "Gemini 3.7 Flash",                "desc": "Especializado em engenharia de software e web"},
            {"id": "gemini-3.6-flash",      "label": "Gemini 3.6 Flash",                "desc": "Versão 3.6 estável e eficiente"},
            {"id": "gemini-3.5-flash",      "label": "Gemini 3.5 Flash",                "desc": "Equilíbrio de velocidade e raciocínio multi-passo"},
            {"id": "gemini-3.5-flash-lite", "label": "Gemini 3.5 Flash-Lite",           "desc": "Ultrarrápido, ideal para respostas instantâneas"},
            {"id": "gemini-3.1-pro-preview","label": "Gemini 3.1 Pro (Preview)",        "desc": "Raciocínio analítico avançado para arquitetura"},
            {"id": "gemini-3.1-flash-lite", "label": "Gemini 3.1 Flash-Lite",           "desc": "Flash-Lite de nova geração"},
            {"id": "gemini-3-flash-preview","label": "Gemini 3.0 Flash (Preview)",      "desc": "Versão Flash 3.0 de alta eficiência"},
        ]
    },
    "claude": {
        "name": "Anthropic Claude",
        "default": "claude-3-7-sonnet-latest",
        "models": [
            {"id": "claude-3-7-sonnet-latest", "label": "Claude 3.7 Sonnet (Híbrido de Raciocínio)", "desc": "Topo de linha da Anthropic para código"},
            {"id": "claude-3-5-sonnet-latest", "label": "Claude 3.5 Sonnet", "desc": "Excelente para programação e refatoração"},
            {"id": "claude-3-5-haiku-latest", "label": "Claude 3.5 Haiku", "desc": "Super rápido e econômico"}
        ]
    },
    "openai": {
        "name": "OpenAI",
        "default": "gpt-4o",
        "models": [
            {"id": "gpt-4o", "label": "GPT-4o (Omni)", "desc": "Modelo principal da OpenAI"},
            {"id": "gpt-4o-mini", "label": "GPT-4o Mini", "desc": "Rápido e muito leve"},
            {"id": "o3-mini", "label": "o3-mini (Raciocínio Especializado)", "desc": "Otimizado para lógica de programação"}
        ]
    }
}

def detect_provider(api_key: str) -> Optional[str]:
    """Detecta automaticamente o provedor da API com base no padrão da chave."""
    key = api_key.strip()
    if key.startswith("AIza"):
        return "gemini"
    elif key.startswith("sk-ant-"):
        return "claude"
    elif key.startswith("sk-") or key.startswith("sess-"):
        return "openai"
    return None

def load_config() -> Dict[str, Any]:
    """Carrega as configurações salvas ou tenta variáveis de ambiente."""
    cfg = {
        "provider": None,
        "model": None,
        "api_keys": {},
        "auto_approve_read_only": True,
        "yolo_mode": False
    }
    
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                cfg.update(saved)
        except Exception:
            pass

    # Verifica variáveis de ambiente do sistema caso ainda não estejam salvas
    if "gemini" not in cfg.get("api_keys", {}) and os.environ.get("GEMINI_API_KEY"):
        cfg["api_keys"]["gemini"] = os.environ.get("GEMINI_API_KEY")
        if not cfg.get("provider"):
            cfg["provider"] = "gemini"
            cfg["model"] = "gemini-3.8-flash"
            
    if "openai" not in cfg.get("api_keys", {}) and os.environ.get("OPENAI_API_KEY"):
        cfg["api_keys"]["openai"] = os.environ.get("OPENAI_API_KEY")
        if not cfg.get("provider"):
            cfg["provider"] = "openai"
            cfg["model"] = "gpt-4o"

    if "claude" not in cfg.get("api_keys", {}) and os.environ.get("ANTHROPIC_API_KEY"):
        cfg["api_keys"]["claude"] = os.environ.get("ANTHROPIC_API_KEY")
        if not cfg.get("provider"):
            cfg["provider"] = "claude"
            cfg["model"] = "claude-3-7-sonnet-latest"

    # Sanitização: Se houver modelo antigo como 2.5 salvo, atualiza para 3.8
    if cfg.get("provider") == "gemini":
        current_m = str(cfg.get("model", ""))
        if "2.5" in current_m or "1.5" in current_m or not current_m:
            cfg["model"] = "gemini-3.8-flash"
            save_config(cfg)

    return cfg

def save_config(config: Dict[str, Any]) -> None:
    """Salva as configurações em arquivo JSON local."""
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

def set_api_key(api_key: str, provider: Optional[str] = None) -> tuple[str, str]:
    """Configura uma chave de API, autodetectando o provedor se não informado."""
    api_key = api_key.strip()
    detected = detect_provider(api_key)
    chosen_provider = provider or detected or "gemini"
    
    cfg = load_config()
    if "api_keys" not in cfg:
        cfg["api_keys"] = {}
    cfg["api_keys"][chosen_provider] = api_key
    cfg["provider"] = chosen_provider
    
    default_model = MODEL_CATALOG.get(chosen_provider, {}).get("default", "gemini-3.8-flash")
    cfg["model"] = default_model
    save_config(cfg)
    
    return chosen_provider, default_model
