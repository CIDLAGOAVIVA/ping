# 📋 Estrutura do Projeto - Instagram RAG

## 🎯 Visão Geral

Sistema completo de RAG para análise semântica de posts do Instagram usando Ollama local, ChromaDB e Gradio.

---

## 📂 Arquivos Criados

### **Aplicação Principal**

| Arquivo | Descrição | Tamanho |
|---------|-----------|---------|
| `app.py` | Interface Gradio com chat RAG | 13KB |
| `rag_system.py` | Sistema RAG completo (busca + geração) | 9.1KB |
| `embedding_manager.py` | Gerenciamento de embeddings e ChromaDB | 8.8KB |
| `data_loader.py` | Carregamento e processamento de JSONs | 7.6KB |

### **Scripts de Utilitários**

| Arquivo | Descrição | Uso |
|---------|-----------|-----|
| `setup.sh` | Setup completo e interativo | `./setup.sh` |
| `start.sh` | Inicialização rápida | `./start.sh` |
| `check_system.py` | Diagnóstico do sistema | `uv run python check_system.py` |

### **Documentação**

| Arquivo | Conteúdo |
|---------|----------|
| `README.md` | Documentação completa (7.9KB) |
| `QUICKSTART.md` | Guia rápido de início |
| `config.example` | Exemplo de configuração |

### **Configuração**

| Arquivo | Propósito |
|---------|-----------|
| `pyproject.toml` | Dependências e metadados do projeto |
| `requirements.txt` | Alternativa para pip (sem uv) |
| `.gitignore` | Arquivos a ignorar no Git |

---

## 🏗️ Arquitetura do Sistema

```
┌─────────────────────────────────────────────────────────┐
│                    CAMADA DE INTERFACE                  │
│                                                         │
│  app.py (Gradio)                                       │
│  - Chat interativo                                     │
│  - Histórico de conversas                              │
│  - Exibição de posts recuperados                       │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                    CAMADA RAG                           │
│                                                         │
│  rag_system.py                                         │
│  - Coordenação do pipeline RAG                         │
│  - Formatação de contexto                              │
│  - Geração de prompts                                  │
└───────────┬─────────────────────┬───────────────────────┘
            │                     │
            ▼                     ▼
┌──────────────────────┐ ┌────────────────────────────────┐
│  BUSCA VETORIAL      │ │  GERAÇÃO LLM                   │
│                      │ │                                │
│  embedding_manager   │ │  ollama.chat()                 │
│  - ChromaDB          │ │  - qwen2.5 / gpt-oss          │
│  - mxbai-embed       │ │  - Streaming support           │
└──────────────────────┘ └────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────┐
│                  CAMADA DE DADOS                        │
│                                                         │
│  data_loader.py                                        │
│  - Parsing de JSON                                     │
│  - Limpeza de texto                                    │
│  - Extração de metadados                               │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                  FONTES DE DADOS                        │
│                                                         │
│  data/*.json                                           │
│  - dceuff.json (1505 posts)                            │
│  - reitor.json (595 posts)                             │
│  - vicereitor.json (346 posts)                         │
└─────────────────────────────────────────────────────────┘
```

---

## 🔄 Fluxo de Dados

### **1. Inicialização**

```
Início → load_data() → create_embeddings() → ChromaDB
```

1. `data_loader.py` lê JSONs
2. Limpa e normaliza textos
3. `embedding_manager.py` gera embeddings
4. Armazena no ChromaDB

### **2. Query do Usuário**

```
Pergunta → Embedding → Busca Vetorial → Top-K Posts → LLM → Resposta
```

1. Usuário faz pergunta no chat
2. Gera embedding da pergunta
3. ChromaDB retorna top-K similares
4. Formata contexto com posts
5. LLM gera resposta baseada no contexto
6. Exibe resposta + fontes

---

## 📊 Estatísticas do Sistema

### **Dados Indexados**

- **Total de posts**: 2.446
- **Perfis**: 3 (dceuff, reitor, vicereitor)
- **Período**: Variável por perfil

### **Recursos Necessários**

| Componente | Uso de Memória | Espaço em Disco |
|------------|----------------|-----------------|
| mxbai-embed-large | ~500MB RAM | ~700MB |
| qwen2.5:3b | ~2GB RAM | ~2GB |
| qwen2.5:7b | ~4GB RAM | ~4GB |
| ChromaDB (2446 posts) | ~100MB RAM | ~50MB |
| Gradio App | ~500MB RAM | - |
| **Total (modelo 3b)** | **~3GB RAM** | **~3GB disk** |

---

## 🚀 Comandos Principais

### **Setup e Verificação**

```bash
# Setup completo (primeira vez)
./setup.sh

# Verificar sistema
uv run python check_system.py

# Sincronizar dependências
uv sync
```

### **Inicialização**

```bash
# Modo padrão
./start.sh

# Com opções
./start.sh --port 8080 --share

# Com modelo específico
./start.sh --generation-model qwen2.5:7b
```

### **Testes de Módulos**

```bash
# Testar carregamento
uv run python data_loader.py

# Testar embeddings
uv run python embedding_manager.py

# Testar RAG completo
uv run python rag_system.py

# Interface Gradio
uv run python app.py
```

### **Manutenção**

```bash
# Reindexar posts
rm -rf chroma_db/
./start.sh

# Atualizar modelos
ollama pull mxbai-embed-large
ollama pull qwen2.5:7b

# Listar modelos
ollama list
```

---

## 🔧 Configuração Customizada

### **Variáveis de Ambiente (opcional)**

Crie arquivo `.env`:

```bash
EMBEDDING_MODEL=mxbai-embed-large
GENERATION_MODEL=qwen2.5:7b
DATA_DIR=data
CHROMA_DB_DIR=./chroma_db
PORT=7860
```

### **Modelos Alternativos**

**Embeddings:**
- `nomic-embed-text` - Alta qualidade
- `snowflake-arctic-embed` - Multilíngue

**Geração:**
- `qwen2.5:3b` - Leve (2GB)
- `qwen2.5:7b` - Médio (4GB)
- `qwen2.5:14b` - Pesado (8GB)
- `gpt-oss:20b` - Alternativa (13GB)

---

## 📈 Métricas de Performance

### **Tempos Médios** (hardware médio)

| Operação | Quantidade | Tempo |
|----------|-----------|-------|
| Indexação inicial | 2446 posts | ~8 min |
| Busca vetorial | 1 query | ~0.5s |
| Geração (3b) | 1 resposta | ~3s |
| Geração (7b) | 1 resposta | ~6s |
| Query completa | fim-a-fim | ~4-7s |

### **Escalabilidade**

| Posts | Indexação | Busca | RAM |
|-------|-----------|-------|-----|
| 1.000 | ~3 min | <0.5s | 2GB |
| 2.446 | ~8 min | <0.5s | 3GB |
| 10.000 | ~30 min | <1s | 4GB |
| 50.000 | ~2h | ~1s | 6GB |

---

## 🎓 Casos de Uso

### **Análise Institucional**
- Monitorar comunicação oficial
- Analisar engajamento de posts
- Identificar temas recorrentes
- Comparar perfis

### **Pesquisa Acadêmica**
- Análise de discurso
- Estudo de redes sociais
- Comunicação organizacional
- Sentiment analysis (futuro)

### **Gestão de Conteúdo**
- Descobrir posts populares
- Identificar gaps de comunicação
- Benchmarking entre perfis
- Planejamento de conteúdo

---

## 🔮 Roadmap Futuro

### **Curto Prazo**
- [ ] Filtros temporais avançados
- [ ] Exportação de relatórios (PDF/CSV)
- [ ] Análise de sentimento
- [ ] Gráficos de engajamento

### **Médio Prazo**
- [ ] Suporte a imagens (análise visual)
- [ ] Detecção de trending topics
- [ ] Comparação automática entre perfis
- [ ] API REST

### **Longo Prazo**
- [ ] Multi-idioma
- [ ] Fine-tuning de modelos
- [ ] Previsão de engajamento
- [ ] Integração com Instagram API

---

## 📞 Suporte

### **Problemas Comuns**

Consulte a seção "Solução de Problemas" no `README.md`

### **Logs e Debug**

```bash
# Ver logs do Ollama
journalctl -u ollama -f

# Testar conexão Ollama
curl http://localhost:11434/api/version

# Debug ChromaDB
uv run python -c "import chromadb; print(chromadb.__version__)"
```

---

## 📝 Changelog

### **Versão 0.1.0** (2025-10-17)
- ✅ Sistema RAG completo
- ✅ Interface Gradio
- ✅ Suporte a múltiplos perfis
- ✅ Busca vetorial com ChromaDB
- ✅ Geração com Ollama
- ✅ Scripts de setup e início
- ✅ Documentação completa

---

**Desenvolvido para análise de posts institucionais da UFF**

Este documento serve como referência técnica completa do sistema.
