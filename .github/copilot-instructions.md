# 📋 COPILOT INSTRUCTIONS - PING UFF Analytics

## Contexto do Projeto

**PING - UFF ANALYTICS** é uma plataforma de análise inteligente de dados da Universidade Federal Fluminense usando IA local (Ollama).

### Informações Críticas

- **Nome**: PING - UFF ANALYTICS (NÃO "Instagram Analytics")
- **Ambiente**: Python 3.12+ com UV (gerenciador de pacotes)
- **Stack Principal**: Gradio 4.x, ChromaDB, Ollama (qwen3:30b)
- **Localização**: `/home/marcus/projects/ping/`
- **Banco de Dados**: ChromaDB (vetorial)
- **Registros**: ~2.437 posts/documentos indexados
- **Fontes**: @dceuff, @noticias, @reitor, @vicereitor

---

## 🎨 Sistema de Temas

### Prioridades de Design

1. **Tema Claro é PADRÃO** - não mudar isso
2. **Dark Mode automático** via `@media (prefers-color-scheme: dark)`
3. **CSS em arquivo separado**: `/static/styles.css`
4. **Variáveis CSS** para consistência:
   - `--bg-primary`, `--text-primary`, `--border-primary`, etc.
5. **Transições suaves** (0.3s) entre temas

### Cores Principais

**Tema Claro:**
- Fundo: `#ffffff` (branco)
- Texto: `#1a1a1a` (preto)
- Bordas: `#e0e0e0` (cinza claro)
- Gradiente Primário: `#667eea` → `#764ba2` (roxo/lilás)

**Tema Escuro:**
- Fundo: `#1a1a1a` (preto)
- Texto: `#f0f0f0` (branco)
- Bordas: `#444444` (cinza escuro)
- Gradiente: mesmo (mantém cores)

### Ao Fazer Mudanças de UI

```css
/* ERRADO - cores hardcoded */
background: #ffffff;
color: #333;

/* CERTO - usar variáveis */
background: var(--bg-primary);
color: var(--text-primary);
```

---

## 📁 Estrutura de Arquivos

```
/home/marcus/projects/ping/
├── app.py                      # App principal (SEM CSS inline)
├── static/
│   └── styles.css             # CSS separado (IMPORTAR NO APP)
├── chat_history.json          # Histórico de consultas (auto-gerado)
├── chroma_db/                 # Banco vetorial
├── data/                       # Dados de entrada
├── MELHORIAS_FINAIS_UI.md     # Documentação de melhorias
├── GUIA_RAPIDO_UI.md          # Guia do usuário
├── start.sh                   # Script de inicialização
├── stop.sh                    # Script de parada
└── requirements.txt           # Dependências
```

---

## 🚀 Como Executar

### Iniciar
```bash
cd /home/marcus/projects/ping
bash start.sh
# Acessa em http://localhost:7860
```

### Parar
```bash
bash stop.sh
```

### Com UV (desenvolvimento)
```bash
cd /home/marcus/projects/ping
uv run python app.py --port 7860
```

---

## 🎯 Componentes Principais

### 1. **HistoryManager** (em `app.py`)
```python
class HistoryManager:
    def add(question, response, profile_filter, posts_count)
    def search(query: str) -> List[Dict]
    def get_stats() -> Dict
```
- Salva em `chat_history.json`
- Limite: 500 últimos registros
- Formato: ISO datetime timestamps

### 2. **InstagramRAGApp** (em `app.py`)
```python
class InstagramRAGApp:
    def __init__(embedding_model, generation_model, use_agent)
    def create_interface() -> gr.Blocks
    def chat_response() -> Tuple[str, str]
    def get_dashboard_html() -> str
    def get_history_html() -> str
```

### 3. **Abas Gradio**
- 💬 **Chat**: Interface principal
- 📊 **Estatísticas**: Dashboard com metrics
- 📚 **Histórico**: Busca e histórico
- 📖 **Documentação**: Guia de uso

---

## 💾 Importar CSS no App

**NO APP.PY**, importe o CSS assim:

```python
with open('static/styles.css', 'r', encoding='utf-8') as f:
    custom_css = f.read()

with gr.Blocks(
    title="PING - UFF ANALYTICS",
    theme=gr.themes.Soft(primary_hue="purple", secondary_hue="blue"),
    css=custom_css  # CSS do arquivo separado
) as app:
    # ... interface aqui
```

---

## 📝 Nomes e Terminologia

### ✅ USAR
- "PING - UFF ANALYTICS" (nome do app)
- "Registros" (em vez de posts)
- "Fontes de Dados" (em vez de perfis)
- "Consultas" (em vez de perguntas)
- "Engajamento" (em vez de curtidas)

### ❌ NÃO USAR
- "UFF Instagram Analytics"
- "Posts"
- "Perfis"
- "Perguntas"
- "Likes"

---

## 🔧 Configurações do Sistema

### Modelos AI (Ollama)
- **Embedding**: `mxbai-embed-large`
- **Geração**: `qwen3:30b`
- **Planejamento**: `qwen3:30b` (mesmo modelo)

### Banco de Dados
- **Tipo**: ChromaDB (vetorial)
- **Localização**: `./chroma_db/`
- **Collection**: `instagram_posts`
- **Documentos**: ~2.437

### Histórico
- **Arquivo**: `chat_history.json`
- **Limite**: 500 registros
- **Formato**: JSON com timestamps ISO

---

## 🎨 Melhorias Futuras

### Sugeridas (em ordem de prioridade)
1. Gráficos interativos (Plotly)
2. Exportação CSV/PDF
3. Word clouds de tópicos
4. Cache de respostas
5. Temas customizados UFF
6. API REST
7. Analytics de consultas
8. Sugestões inteligentes

---

## 🐛 Troubleshooting

### App não inicia
```bash
pkill -9 -f "python.*app.py"
sleep 2
bash start.sh
```

### CSS não carrega
- Verificar se `static/styles.css` existe
- Verificar path no app.py: `'static/styles.css'`
- Verificar permissões de arquivo

### Tema não muda
- Verificar media queries no CSS
- Usar dev tools (F12) → Inspect
- Limpar cache do navegador

### Histórico não salva
- Verificar permissões de `chat_history.json`
- Verificar espaço em disco
- Verificar logs: `tail -f /var/log/cid-ping.log`

---

## 📞 Contato e Suporte

**Projeto**: PING - UFF ANALYTICS  
**Owner**: Marcus (nextmarte)  
**Data Atualização**: 26 de Outubro de 2025  
**Versão**: 2.1  

---

## 🔐 Notas de Segurança

- Histórico salvado localmente em JSON (privado)
- Sem envio de dados para APIs externas
- Ollama roda localmente (privacidade total)
- ChromaDB local (sem nuvem)

---

## ✨ Checklist para Novas Features

- [ ] Nome do app menciona "PING - UFF ANALYTICS"
- [ ] Usar terminologia correta (registros, fontes, consultas)
- [ ] CSS com variáveis (não hardcoded)
- [ ] Suporte a dark/light mode
- [ ] Testado em ambos os temas
- [ ] Histórico persistente se necessário
- [ ] Documentação atualizada
- [ ] Sem console errors/warnings

---

**Criado com ❤️ por GitHub Copilot**
