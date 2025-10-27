# 📋 COPILOT INSTRUCTIONS - PING UFF Analytics

## Contexto do Projeto

**PING - UFF ANALYTICS** é uma plataforma de análise inteligente de dados da Universidade Federal Fluminense usando IA (DeepSeek Chat como LLM principal + Ollama para embeddings).

### Informações Críticas

- **Nome**: PING - UFF ANALYTICS (NÃO "Instagram Analytics")
- **Ambiente**: Python 3.12+ com UV (gerenciador de pacotes)
- **Stack Principal**: Gradio 4.x, ChromaDB, DeepSeek Chat (modelo principal), Ollama (embeddings)
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
├── data_injestion.py           # Pipeline de ingestão com Docling
├── static/
│   └── styles.css             # CSS separado (IMPORTAR NO APP)
├── chat_history.json          # Histórico de consultas (auto-gerado)
├── chroma_db/                 # Banco vetorial
├── data/                       # Dados de entrada
│   └── injected/              # Documentos injetados via interface
│       └── injested_metadata.json  # Metadados dos docs injetados
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
- 💬 **Chat**: Interface principal com "Lista de Fontes" dinâmica
- 📊 **Estatísticas**: Dashboard com metrics
- 📚 **Histórico**: Busca e histórico
- 📥 **Ingestão de Dados**: Upload e vetorização de documentos
-  **Documentação**: Guia de uso

#### 📊 Lista de Fontes (anteriormente "Filtro de Perfis")
- **O que é**: CheckboxGroup dinâmico que mostra tanto perfis Instagram quanto tipos de documentos
- **Instagram Profiles**: Prefixados com `@` (ex: `@dceuff`, `@reitor`)
- **Document Types**: Prefixados com `📄` (ex: `📄 Artigo`, `📄 Relatório`)
- **Comportamento**: 
  - Todos os perfis/tipos selecionados por padrão
  - Um único perfil selecionado → filtra por esse perfil
  - Múltiplos perfis/tipos → busca em todos (sem filtro de perfil)
  - Tipos de documentos não filtram (buscam por similaridade semântica)
- **Código em app.py**: Linhas 1124-1136 (construção dinâmica da lista)
- **Processamento em chat_response()**: Linhas 675-737 (extrai perfis e tipos)

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

### Modelos AI
- **Provider Principal**: DeepSeek Chat (API externa)
- **Modelo de Planejamento**: `deepseek-chat` (para planejar quais ferramentas usar)
- **Modelo de Geração**: `deepseek-chat` (para sintetizar respostas)
- **Modelo de Embeddings**: `mxbai-embed-large` (Ollama local - apenas para vetorização)
- **Fallback**: Ollama `qwen3:30b` (se DeepSeek indisponível)

### Banco de Dados
- **Tipo**: ChromaDB (vetorial)
- **Localização**: `./chroma_db/`
- **Collection**: `instagram_posts`
- **Documentos**: ~2.437

### Histórico
- **Arquivo**: `chat_history.json`
- **Limite**: 500 registros
- **Formato**: JSON com timestamps ISO

### Configuração de Providers
- **Arquivo**: `config.py`
- **Variável**: `DEFAULT_PROVIDER` (valor: 'deepseek')
- **API Key**: `DEEPSEEK_API_KEY` (variável de ambiente ou hardcoded)
- **Wrapper LLM**: `llm_chat.py` (abstração para DeepSeek/Ollama)

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
- DeepSeek API Key armazenada em `config.py` (use variáveis de ambiente em produção)
- ChromaDB local (sem nuvem)
- Ollama roda localmente apenas para embeddings (sem envio de dados)

---

## 🆕 Novos Componentes (Oct 2025)

### 1. **config.py** - Configuração de Providers
```python
DEFAULT_PROVIDER = 'deepseek'  # ou 'ollama'
DEEPSEEK_API_KEY = 'sk-...'
DEEPSEEK_MODEL = 'deepseek-chat'
OLLAMA_GENERATION_MODEL = 'qwen3:30b'
```

### 2. **llm_chat.py** - Wrapper LLM Unificado
```python
class LLMClient:
    def chat(model, messages) -> Dict
    def _deepseek_chat() # Usa OpenAI SDK
    def _ollama_chat()   # Usa ollama package
```
- Detecta provider automaticamente
- Mantém compatibilidade de formato de resposta
- Permite switch fácil entre DeepSeek e Ollama

### 3. **Web Search Tool** - Busca na Internet
```python
tools.web_search(query, limit)  # Em query_tools.py
```
- Provider: DuckDuckGo (sem API key necessária)
- Uso: Contexto externo, notícias recentes
- Integração: `_plan_action()` sabe quando usar
- Exemplo: "Qual é a situação da educação em 2025?"

### 4. **data_injestion.py** - Pipeline de Ingestão de Dados
```python
class DataInjestionPipeline:
    def ingest_document(file_path, content_type, tags, author, description)
    def ingest_raw_text(text, source_name, content_type)
    def get_injected_documents() -> List[Dict]
    def delete_document(doc_id)
```
- **Docling Integration**: Converte PDF, DOCX, PPTX, MD, HTML, XLSX para JSON
- **Vetorização Automática**: Documentos são divididos em chunks e indexados no ChromaDB
- **Metadados Ricos**: Tags, autor, descrição, tipo de conteúdo
- **Formatos Suportados**: PDF, DOCX, PPTX, MD, HTML, XLSX, AsciiDoc, imagens (PNG, JPG, TIFF)
- **Interface Gradio**: Aba dedicada para upload e gerenciamento de documentos
- **Persistência**: Metadados salvos em `data/injected/injested_metadata.json`

#### Tipos de Conteúdo:
- `DOCUMENT` - Documentos gerais
- `ARTICLE` - Artigos e notícias
- `REPORT` - Relatórios
- `RESEARCH` - Trabalhos acadêmicos
- `MANUAL` - Manuais e guias
- `POLICY` - Políticas e regulamentos
- `OTHER` - Outros tipos

### 5. **Agent System Improvements**
- LLM agora decide automaticamente qual ferramenta usar
- Suporta planejamento complexo com múltiplas ferramentas
- Valida dados e evita alucinações sobre datas
- Limpa vazamentos de prompt da resposta final

---

## 🌐 Ferramentas Disponíveis no Agente

### Estruturadas (Métricas)
- `get_top_posts_by_likes` - Posts mais curtidos
- `get_top_posts_by_comments` - Posts mais comentados
- `get_posts_by_engagement` - Maior engajamento total
- `get_bottom_posts_by_likes` - Posts menos curtidos
- `get_recent_posts` - Posts recentes (últimos N dias)
- `compare_profiles` - Comparar perfis
- `get_profile_statistics` - Estatísticas de um perfil
- `count_term_occurrences` - Quantificar menções de termo

### Semânticas (Conteúdo)
- `semantic_search` - Busca por tema/conteúdo
- `analyze_sentiment` - Análise de sentimento

### Notícias
- `get_news_articles` - Notícias por data/publisher
- `search_news_by_person` - Notícias sobre pessoa específica
- `get_news_statistics` - Estatísticas de notícias

### Web (Externo)
- `web_search` - Busca na internet via DuckDuckGo

### Ingestão
- `ingest_document` - Upload e vetorização de documentos via Docling
- `ingest_raw_text` - Ingestão de texto bruto sem arquivo

---

## 📥 Pipeline de Ingestão de Dados

### Como Usar a Interface de Ingestão

1. **Upload de Arquivo**:
   - Acesse a aba "📥 Ingestão de Dados"
   - Selecione um arquivo (PDF, DOCX, PPTX, MD, HTML, XLSX, imagens)
   - Escolha o tipo de conteúdo
   - Preencha metadados opcionais (autor, descrição, tags, URL)
   - Clique em "🚀 Ingerir Documento"

2. **Texto Direto**:
   - Cole o texto na área de texto
   - Forneça um nome para a fonte
   - Escolha o tipo de conteúdo
   - Clique em "📝 Ingerir Texto"

3. **Documentos Injetados**:
   - Visualize todos os documentos injetados na seção inferior
   - Veja estatísticas (total, páginas, tamanho)
   - Documentos ficam disponíveis para busca no chat

### Fluxo de Processamento

```
Arquivo → Docling (conversão) → JSON estruturado → Chunks → Vetorização → ChromaDB
```

1. **Docling converte** o documento em JSON com estrutura preservada
2. **Documentos grandes** são divididos em chunks por página
3. **Cada chunk** recebe um ID único e metadados
4. **Vetorização** com modelo de embeddings local (Ollama)
5. **Indexação** no ChromaDB junto com posts e notícias
6. **Busca semântica** disponível imediatamente no chat

### Metadados Armazenados

Para cada documento injetado:
- `id`: Hash único MD5 (12 chars)
- `filename`: Nome do arquivo original
- `content_type`: Tipo do conteúdo (DOCUMENT, ARTICLE, etc.)
- `source`: Origem (UPLOAD, INTERNAL, etc.)
- `upload_date`: ISO timestamp
- `file_size_bytes`: Tamanho em bytes
- `page_count`: Número de páginas
- `language`: Idioma (default: "pt")
- `custom_tags`: Lista de tags
- `author`: Autor/criador
- `description`: Descrição fornecida

### Formatos de Arquivo Suportados

**Documentos de Texto:**
- `.pdf` - Adobe PDF
- `.docx` - Microsoft Word
- `.pptx` - Microsoft PowerPoint
- `.md` - Markdown
- `.html` - HTML
- `.xlsx` - Microsoft Excel
- `.asciidoc` - AsciiDoc

**Imagens (com OCR):**
- `.png` - PNG
- `.jpg`, `.jpeg` - JPEG
- `.tiff` - TIFF

**⚠️ NÃO suportado:**
- `.txt` - Arquivos de texto puro (converter para `.md`)

### Exemplo de Uso Programático

```python
from data_injestion import DataInjestionPipeline, ContentType
from embedding_manager import EmbeddingManager

# Inicializa
em = EmbeddingManager()
pipeline = DataInjestionPipeline(embedding_manager=em)

# Ingere documento
success, message, result = pipeline.ingest_document(
    file_path="/path/to/document.pdf",
    content_type=ContentType.REPORT,
    custom_tags=["HUAP", "Saúde"],
    author="Dr. João Silva",
    description="Relatório anual do HUAP"
)

if success:
    print(f"✅ Documento injetado: {result['doc_id']}")
    print(f"📄 {result['pages']} páginas, {result['chunks_created']} chunks")

# Ingere texto bruto
success, message, result = pipeline.ingest_raw_text(
    text="Conteúdo do documento...",
    source_name="Artigo X",
    content_type=ContentType.ARTICLE
)
```

### Estrutura de Dados no ChromaDB

Cada chunk injetado tem os seguintes metadados no ChromaDB:

```python
{
    "doc_id": "abc123def456",
    "filename": "documento.pdf",
    "content_type": "report",
    "source": "upload",
    "upload_date": "2025-10-27T14:30:00",
    "author": "Dr. João",
    "language": "pt",
    "tags": "HUAP,Saúde",
    "description": "Relatório anual",
    "page_count": 10,
    "page": 1  # (apenas para chunks de páginas individuais)
}
```

### Diferenciação de Fontes na Interface

O sistema agora suporta múltiplos tipos de fontes, cada um renderizado de forma diferente:

1. **Posts do Instagram** (roxo/lilás):
   - Badge: `@perfil`
   - Métricas: ❤️ curtidas, 💬 comentários, 📊 engajamento
   - Botão: "Ver no Instagram"

2. **Notícias** (laranja):
   - Badge: `📰 Notícia`
   - Mostra: Título, Publisher, Descrição
   - Botão: "Ler notícia completa"

3. **Web Search** (verde):
   - Badge: `🌐 Web`
   - Mostra: Título, Corpo do texto
   - Botão: "Visitar página"

4. **Documentos Injetados** (azul - futuro):
   - Badge: `📄 Documento`
   - Mostra: Título, Autor, Tags
   - Botão: "Ver documento"

---

## ✨ Checklist para Novas Features

- [ ] Nome do app menciona "PING - UFF ANALYTICS"
- [ ] Usar terminologia correta (registros, fontes, consultas)
- [ ] CSS com variáveis (não hardcoded)
- [ ] Suporte a dark/light mode
- [ ] Testado em ambos os temas
- [ ] Histórico persistente se necessário
- [ ] **Documentação atualizada neste arquivo (`copilot-instructions.md`)** ⚠️ **OBRIGATÓRIO**
- [ ] Sem console errors/warnings
- [ ] Se usa LLM: verificar se usa `llm_chat.chat()` e não `ollama.chat()` diretamente
- [ ] Se nova ferramenta: adicionar em `TOOL_DEFINITIONS` do query_tools.py
- [ ] Se nova ferramenta: adicionar exemplo no `planning_prompt`

---

## 📝 DIRETRIZ IMPORTANTE PARA O COPILOT

**🚨 SEMPRE QUE FINALIZAR QUALQUER IMPLEMENTAÇÃO, ATUALIZAR ESTE ARQUIVO (`copilot-instructions.md`)**

Quando completar qualquer feature, bugfix ou mudança significativa:

1. ✅ Atualizar seções relevantes deste arquivo
2. ✅ Adicionar novos componentes na seção "🆕 Novos Componentes"
3. ✅ Atualizar estrutura de arquivos se necessário
4. ✅ Adicionar troubleshooting para novos erros conhecidos
5. ✅ Incrementar número de versão
6. ✅ Atualizar data de atualização
7. ✅ Documentar exemplos de uso para novas funcionalidades
8. ✅ Adicionar ao checklist se criar novo padrão obrigatório

**Exemplo de quando atualizar:**
- ✅ Nova aba na interface Gradio
- ✅ Novo módulo Python criado
- ✅ Nova ferramenta de query adicionada
- ✅ Integração com nova API/biblioteca
- ✅ Mudança de fluxo ou arquitetura
- ✅ Novos formatos de dados suportados
- ✅ Correção de bugs críticos com contexto importante

**Não precisa atualizar para:**
- ❌ Pequenos ajustes de CSS
- ❌ Typos e correções de texto
- ❌ Refatorações sem mudança de comportamento
- ❌ Logs de debug temporários

---

## 🚨 Troubleshooting DeepSeek

### DeepSeek API indisponível
```bash
# Verifica se API_KEY está correto em config.py
# Volta para Ollama automaticamente se ERROR
# Veja os logs: tail -f /var/log/cid-ping.log
```

### Erro: "No module named 'openai'"
```bash
cd /home/marcus/projects/ping
uv pip install openai
bash stop.sh
bash start.sh
```

### Erro: "No module named 'duckduckgo_search'"
```bash
cd /home/marcus/projects/ping
uv pip install duckduckgo-search
bash stop.sh
bash start.sh
```

### Erro: "No module named 'docling'"
```bash
cd /home/marcus/projects/ping
uv add docling
uv sync
bash stop.sh
bash start.sh
```

### Erro na conversão Docling
- Verificar formato do arquivo (suportados: PDF, DOCX, PPTX, MD, HTML, XLSX, AsciiDoc, imagens)
- Arquivos TXT puros não são suportados - converter para MD
- Verificar se arquivo existe e tem permissões de leitura
- Logs detalhados em `data/injected/injested_metadata.json`

---

## 📞 Contato e Suporte

**Projeto**: PING - UFF ANALYTICS  
**Owner**: Marcus (nextmarte)  
**Data Atualização**: 27 de Outubro de 2025  
**Versão**: 3.3 (com DeepSeek Chat + Web Search + Data Ingestion + Multi-Source UI + RAG Melhorado)

---

---

## 📥 Pipeline de Ingestão de Dados - Resumo Rápido

### Novos Arquivos Criados
- `data_injestion.py` - Pipeline completo com Docling
- `data/injected/` - Diretório para docs injetados
- `data/injected/injested_metadata.json` - Metadados persistidos

### Aba Nova no Gradio
- **📥 Ingestão de Dados** - Upload e vetorização de documentos

### Formatos Suportados
- PDF, DOCX, PPTX, MD, HTML, XLSX, AsciiDoc, Imagens (PNG, JPG, TIFF)

### Tipos de Conteúdo
- Documento, Artigo, Relatório, Pesquisa, Manual, Política, Outro

### Fluxo de Vetorização com Chunking
1. Upload → Docling converte para JSON
2. **Divide em chunks** (2000 chars cada, com overlap de 200 chars)
3. Vetoriza cada chunk com Ollama (mxbai-embed-large)
4. Indexa no ChromaDB junto com posts/notícias
5. Disponível imediatamente para busca no chat

### Metadados Estrutura Unificada
Todos os documentos (Instagram, notícias, injetados) no ChromaDB agora têm estrutura consistente:

**Posts Instagram (source=None):**
- profile, likesCount, commentsCount, timestamp, url, caption, type

**Documentos Injetados (source='upload'):**
- doc_id, filename, content_type, author, tags, description, upload_date
- chunk_index, total_chunks (para documentos divididos)

**Função Helper:**
```python
QueryTools._filter_instagram_posts(results, profile=None)
# Filtra apenas posts do Instagram (que têm likesCount)
```

### Método Adicionado
```python
EmbeddingManager.add_documents(documents, ids, metadatas)
```

---

## 🎨 Refatoração UI para Múltiplas Fontes (Versão 3.2)

### O que mudou

#### 1. **Renomeação: "Filtro de Perfis" → "Lista de Fontes"**
- **Local**: Aba Chat, painel lateral (linha 1132 em app.py)
- **Antes**: "📊 Filtro de Perfis (selecione um ou mais)"
- **Depois**: "📊 Lista de Fontes (selecione uma ou mais)"
- **Motivo**: Agora suporta perfis Instagram + tipos de documentos injetados

#### 2. **Construção Dinâmica de Fontes**
```python
# Em app.py (linhas 1124-1136)
instagram_profiles = ["@" + p for p in self.stats.get('profiles', [])]
document_types = ["📄 " + t for t in self.stats.get('content_types', [])]
all_sources = instagram_profiles + document_types

profile_filter = gr.CheckboxGroup(
    choices=all_sources if all_sources else ["(nenhuma fonte disponível)"],
    value=all_sources,  # Todos selecionados por padrão
    label="📊 Lista de Fontes (selecione uma ou mais)",
    interactive=True,
    elem_classes="profile-checkbox-group"
)
```

#### 3. **Processamento em chat_response()**
```python
# Extrai perfis Instagram (remover @) e tipos de documentos (remover 📄)
profiles_selected = [f.replace("@", "").strip() for f in profile_filter if f.startswith("@")]
content_types_selected = [f.replace("📄", "").strip() for f in profile_filter if f.startswith("📄")]

# Para compatibilidade com query tools, passa um perfil único ou None
profile = None
if profiles_selected and len(profiles_selected) == 1:
    profile = profiles_selected[0]
```

#### 4. **Atualização do Rodapé**
- **Antes**: "{N} posts • {N} perfis"
- **Depois**: "{N} documentos • {N} perfis • {N} tipos de conteúdo"
- **Motivo**: Refletir realidade de múltiplas fontes

#### 5. **Salvamento no Histórico**
```python
# Format: "@dceuff, 📄 Artigo, @reitor"
filter_label = ", ".join(profile_filter) if profile_filter else "Todas as fontes"
self.history_manager.add(..., profile_filter=filter_label, ...)
```

### Comportamento da Interface

1. **Seleção Padrão**: Todas as fontes marcadas
2. **Um perfil Instagram**: Filtra apenas por esse perfil (passa `profile=None` se tiver documentos também)
3. **Múltiplos perfis/tipos**: Busca em todos sem filtro de perfil (RetroieveRAG busca por similaridade)
4. **Histórico**: Mostra badge com fontes selecionadas (ex: "@dceuff, 📄 Relatório")

### Arquivos Modificados

- **app.py**:
  - Linha 158-162: Adicionado `content_types` ao `self.stats` durante inicialização
  - Linha 1124-1136: Construção dinâmica de lista de fontes
  - Linha 675-737: Função `chat_response()` atualizada para processar lista de fontes
  - Linha 1615-1625: Rodapé atualizado com múltiplas fontes

- **copilot-instructions.md**: Documentação atualizada

### Compatibilidade Backward

✅ Todas as funções de query tools continuam funcionando:
- Aceitam `profile_filter: Optional[str]`
- Filtram apenas Instagram posts quando necessário
- Usam `.get()` para acessar metadados de forma segura

✅ Histórico continua funcionando:
- Agora salva string formatada com múltiplas fontes
- Interface de histórico renderiza automaticamente

### Próximas Melhorias Sugeridas

1. ✨ Suporte a persistência de preferências de fontes (salvar no localStorage)
2. ✨ Filtro visual por source type (apenas documentos ou apenas Instagram)
3. ✨ Busca rápida na lista de fontes quando houver muitas
4. ✨ Indicador visual de "nova fonte adicionada"

---

## 🔧 RAG System - Suporte para Múltiplas Fontes de Dados (Versão 3.3)

### Mudanças Implementadas

#### 1. **format_post_for_context() - Agora Suporta Documentos**
- **Antes**: Esperava campos específicos de Instagram (`profile`, `caption`, `likesCount`, etc.)
- **Depois**: Detecta automaticamente o tipo de fonte (Instagram vs. Documento)
- **Instagram Posts**: Formata com perfil, data, legenda, engajamento, link
- **Documentos**: Formata com arquivo, autor, tipo de conteúdo, chunk index
- **Resultado**: Sem mais erros ao encontrar documentos nos resultados

#### 2. **generate_response() - Context Adaptativo**
- **Contexto Dinâmico**: Título muda baseado no tipo de fonte encontrado
  - "Posts Relevantes do Instagram" (só Instagram)
  - "Contexto Relevante (Documentos Injetados)" (só documentos)
  - "Contexto Relevante (Posts + Documentos)" (ambos)
- **System Prompt Atualizado**: Agora menciona explicitamente suporte a documentos
- **Instrução de Priorização**: "Priorize documentos oficiais sobre posts quando ambos estiverem disponíveis"
- **Resultado**: Respostas agora citam corretamente a origem das informações

#### 3. **n_results Aumentado para 10**
- **Antes**: `n_results=5` (podia perder documentos se muitos posts do Instagram)
- **Depois**: `n_results=10` (melhor chance de recuperar documentos relevantes)
- **Motivo**: Com ~2544 documentos totais (2539 posts + 5 chunks injetados), precisávamos de mais espaço
- **Trade-off**: Mais contexto = input maior pro LLM (ainda dentro dos limites)

### Fluxo de Funcionamento

```
Pergunta: "Art. 96, § 2º"
    ↓
Busca Semântica (10 resultados) → Mix de posts + chunks do Estatuto
    ↓
format_post_for_context() → Formata corretamente cada tipo
    ↓
generate_response() → LLM recebe contexto mesclado
    ↓
Resposta → Cita tanto posts quanto documento com as informações corretas
```

### Exemplo de Saída

**Antes (com o bug):**
```
"Não foi possível localizar o Art. 96, § 2º nos posts analisados"
(mesmo tendo o Estatuto nos resultados recuperados)
```

**Depois (com o fix):**
```
"Com base no Estatuto e Regimento Geral da UFF:

Art. 96, § 2º: [conteúdo exato do Estatuto]

Fonte: 📄 Estatuto e Regimento Geral (Chunk 43/105)
Arquivo: estatuto-regimento-uff.pdf
Autor: UFF"
```

### Benefícios

1. ✅ **Respostas Mais Completas**: Combina dados de múltiplas fontes
2. ✅ **Melhor Recuperação**: Com 10 resultados, documentos têm maior chance
3. ✅ **Citações Corretas**: Cada fonte é formatada adequadamente
4. ✅ **Sem Erros KeyError**: Detecta tipo de fonte antes de acessar campos
5. ✅ **Backward Compatible**: Continua funcionando com apenas Instagram posts

### Arquivos Modificados

- **rag_system.py**:
  - `format_post_for_context()` (linhas 72-131): Suporte para documentos
  - `generate_response()` (linhas 133-235): Context adaptativo + prompt melhorado
  - `query()` (linha 263): `n_results` aumentado de 5 para 10

### Compatibilidade

✅ Todos os queries RAG agora suportam múltiplas fontes  
✅ Agent system continua funcionando normalmente  
✅ Query tools não precisam de mudanças  

#### 4. **System Prompt Aprimorado para Extração de Documentos**
- **Antes**: Prompt genérico que não diferenciava fontes
- **Depois**: Instruções explícitas para priorizar documentos em perguntas sobre "estatuto", "regulamento", "Art.", "eleição"
- **Mudança no user_prompt**: Agora instruções críticas guiam o LLM a PROCURAR EM DOCUMENTOS
- **Resultado**: Respostas sobre artigos estatutários agora extraem do Estatuto em vez de desistir

### Fluxo de Funcionamento

```
Pergunta: "Art. 96, § 2º"
    ↓
Busca Semântica (10 resultados) → Mix de posts + chunks do Estatuto
    ↓
format_post_for_context() → Formata corretamente cada tipo
    ↓
generate_response() COM NOVO SYSTEM_PROMPT:
  - Detecta keywords: "Art.", "§", "estatuto", "regulamento", "eleição"
  - Instruções explícitas: PROCURE NOS DOCUMENTOS
  - LLM extrai resposta dos chunks
    ↓
Resposta → Cita Artigo completo + Fonte do Documento
```

### Exemplo de Saída Melhorada

**Pergunta**: "O que fala o Art. 96, § 2º do Estatuto?"

**Antes (com prompt genérico):**
```
"Não foi possível localizar o Art. 96, § 2º nos posts analisados"
```

**Depois (com prompt agressivo para documentos):**
```
"Art. 96, § 2º: [conteúdo exato extraído do Estatuto]

Fonte: 📄 Estatuto e Regimento Geral da UFF | Chunk 43/105"
```

---

**Criado com ❤️ por GitHub Copilot**
