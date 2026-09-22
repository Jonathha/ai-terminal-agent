# AI Terminal Agent ⚡

Terminal inteligente com acesso ao PC, ferramentas de desenvolvimento, pesquisa na web e guardrails de segurança.

## Recursos
- **Configuração Automática por Chave**: Cole a chave de API (Gemini, Claude ou OpenAI) e o sistema detecta o provedor automaticamente.
- **Modelos Suportados**:
  - **Google Gemini**: Gemini 3.0 Flash, Gemini 3.0 Pro, Gemini 3.5 Flash, Gemini 3.5 Lite, Gemini 2.5 Flash, Gemini 2.5 Pro.
  - **Anthropic Claude**: Claude 3.7 Sonnet, Claude 3.5 Sonnet, Claude 3.5 Haiku.
  - **OpenAI**: GPT-4o, GPT-4o Mini, o3-mini.
- **Ferramentas Integradas**:
  - Execução de comandos no PowerShell do Windows com confirmação `[s/n]`.
  - Pesquisa na Web em tempo real (DuckDuckGo).
  - Leitura, escrita e listagem de arquivos e diretórios.
- **Segurança Rigorosa**:
  - System Prompt com diretrizes estritas.
  - Bloqueio determinístico de comandos destrutivos (formatação, deleção de pastas do sistema, registro do Windows, etc.).
- **Atalho na Área de Trabalho**:
  - Ícone na Área de Trabalho (`AI Terminal.bat` / `AI Terminal.lnk`) para abrir diretamente com 2 cliques.

## Comandos do Terminal
- `/model`: Alterar o modelo de IA em uso.
- `/key`: Trocar ou inserir nova chave de API.
- `/yolo`: Ligar/desligar confirmação a cada passo.
- `/clear`: Limpar a tela.
- `/help`: Exibir ajuda.
- `/exit`: Sair.
