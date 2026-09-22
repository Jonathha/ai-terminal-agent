"""
Módulo do Agente Unificado
Conecta com Google Gemini, Anthropic Claude ou OpenAI com suporte completo a Tool Calling.
"""

import json
from typing import List, Dict, Any, Generator, Tuple
from system_prompt import INTERNAL_SYSTEM_PROMPT
from tools import AVAILABLE_TOOLS, TOOL_FUNCTIONS

class TerminalAgent:
    def __init__(self, provider: str, model_name: str, api_key: str):
        self.provider = provider
        self.model_name = model_name
        self.api_key = api_key
        self.history: List[Dict[str, Any]] = []
        self._init_client()

    def _init_client(self):
        if self.provider == "gemini":
            # Gemini via endpoint OpenAI-compatível oficial do Google
            # Permite uso idêntico de function calling e streaming com total confiabilidade
            from openai import OpenAI
            self.client = OpenAI(
                api_key=self.api_key,
                base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
            )
        elif self.provider == "openai":
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key)
        elif self.provider == "claude":
            import anthropic
            self.client = anthropic.Anthropic(api_key=self.api_key)
        else:
            raise ValueError(f"Provedor não suportado: {self.provider}")

    def chat_step(self, user_message: str, tool_callback=None) -> str:
        """
        Envia mensagem do usuário e gerencia o loop de Tool Calling (ReAct)
        até a resposta final da IA.
        """
        # Adiciona mensagem do usuário ao histórico
        self.history.append({"role": "user", "content": user_message})
        
        # Inicia loop de raciocínio e execução de ferramentas
        max_turns = 10
        turn = 0
        final_answer = ""
        
        while turn < max_turns:
            turn += 1
            
            if self.provider in ["gemini", "openai"]:
                messages = [{"role": "system", "content": INTERNAL_SYSTEM_PROMPT}] + self.history
                
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    tools=AVAILABLE_TOOLS,
                    tool_choice="auto"
                )
                
                choice = response.choices[0]
                msg = choice.message
                
                # Se houver chamadas de ferramentas
                if msg.tool_calls:
                    # Registra a mensagem com tool_calls no histórico
                    self.history.append(msg)
                    
                    for tool_call in msg.tool_calls:
                        func_name = tool_call.function.name
                        call_id = tool_call.id
                        try:
                            func_args = json.loads(tool_call.function.arguments)
                        except Exception:
                            func_args = {}
                            
                        if tool_callback:
                            tool_callback("start", func_name, func_args)
                            
                        # Executa a ferramenta
                        if func_name in TOOL_FUNCTIONS:
                            try:
                                result = TOOL_FUNCTIONS[func_name](**func_args)
                            except Exception as e:
                                result = f"[ERRO AO EXECUTAR FERRAMENTA]: {str(e)}"
                        else:
                            result = f"[ERRO]: Ferramenta '{func_name}' não existe."
                            
                        if tool_callback:
                            tool_callback("finish", func_name, result)
                            
                        # Adiciona o resultado da ferramenta ao histórico
                        self.history.append({
                            "role": "tool",
                            "tool_call_id": call_id,
                            "content": str(result)
                        })
                    # Continua o loop para a IA analisar o resultado das ferramentas
                    continue
                else:
                    # Resposta final em texto
                    final_answer = msg.content or ""
                    self.history.append({"role": "assistant", "content": final_answer})
                    break
                    
            elif self.provider == "claude":
                # Formato Anthropic Claude
                anthropic_tools = []
                for t in AVAILABLE_TOOLS:
                    fn = t["function"]
                    anthropic_tools.append({
                        "name": fn["name"],
                        "description": fn["description"],
                        "input_schema": fn["parameters"]
                    })
                    
                # Filtra o histórico para o formato do Claude
                claude_messages = []
                for m in self.history:
                    if isinstance(m, dict):
                        role = m["role"]
                        if role in ["user", "assistant"]:
                            claude_messages.append({"role": role, "content": m["content"]})
                    elif hasattr(m, "role"):
                        # Se for objeto de tool call do OpenAI, adapta
                        pass
                
                resp = self.client.messages.create(
                    model=self.model_name,
                    system=INTERNAL_SYSTEM_PROMPT,
                    max_tokens=4096,
                    messages=claude_messages,
                    tools=anthropic_tools
                )
                
                has_tool_use = False
                for block in resp.content:
                    if block.type == "tool_use":
                        has_tool_use = True
                        func_name = block.name
                        func_args = block.input
                        
                        if tool_callback:
                            tool_callback("start", func_name, func_args)
                            
                        if func_name in TOOL_FUNCTIONS:
                            result = TOOL_FUNCTIONS[func_name](**func_args)
                        else:
                            result = f"Ferramenta '{func_name}' não encontrada."
                            
                        if tool_callback:
                            tool_callback("finish", func_name, result)
                            
                        claude_messages.append({"role": "assistant", "content": resp.content})
                        claude_messages.append({
                            "role": "user",
                            "content": [{
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": str(result)
                            }]
                        })
                        break
                    elif block.type == "text":
                        final_answer = block.text
                        
                if not has_tool_use:
                    self.history.append({"role": "assistant", "content": final_answer})
                    break
                    
        return final_answer
