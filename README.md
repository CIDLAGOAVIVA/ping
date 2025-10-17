# 📱 Instagram RAG - Sistema de Análise de Posts Institucionais

Sistema RAG (Retrieval-Augmented Generation) para análise semântica de posts do Instagram dos perfis institucionais da UFF (Universidade Federal Fluminense).

## 🎯 Características

- **Busca Semântica**: Encontre posts relevantes usando linguagem natural
- **Análise Contextual**: Respostas baseadas em evidências reais dos posts
- **Interface Amigável**: Chat interativo com Gradio
- **100% Local**: Execução completa em sua máquina usando Ollama
- **Múltiplos Perfis**: Analise posts de diferentes perfis institucionais simultaneamente

## 🏗️ Arquitetura

```
┌─────────────┐
│   Usuário   │
└──────┬──────┘
       │ Pergunta
       ▼
┌─────────────────────┐
│   Interface Gradio  │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│    Sistema RAG      │
│  ┌───────────────┐  │
│  │  Embeddings   │  │
│  │  (ChromaDB)   │  │
│  └───────┬───────┘  │
│          │          │
│  ┌───────▼───────┐  │
│  │  Geração LLM  │  │
│  │   (Ollama)    │  │
│  └───────────────┘  │
└─────────────────────┘
       │
       ▼
┌─────────────────────┐
│   Posts JSON        │
│   data/             │
└─────────────────────┘
```

## 📋 Pré-requisitos

1. **Python 3.12+**
2. **uv** (gerenciador de pacotes Python)
3. **Ollama** instalado e rodando
4. Mínimo 8GB RAM (16GB recomendado)
5. ~20GB espaço em disco para modelos

## 🚀 Instalação

### 1. Instalar Ollama

```bash
# Linux
curl -fsSL https://ollama.com/install.sh | sh

# macOS
brew install ollama

# Windows
# Baixe de https://ollama.com/download
```

### 2. Clonar e configurar o projeto

```bash
# Clone o repositório (ou navegue até o diretório)
cd ping

# Sincronizar dependências com uv
uv sync
```

### 3. Instalar modelos do Ollama

Execute o script de setup para instalar os modelos necessários:

```bash
# Modelo de embedding (obrigatório)
ollama pull mxbai-embed-large

# Modelo de geração - escolha um:

# Opção 1: Leve e rápido (~2GB)
ollama pull qwen2.5:3b

# Opção 2: Melhor qualidade (~7GB)
ollama pull qwen2.5:7b

# Opção 3: Máxima qualidade (~18GB)
ollama pull qwen2.5:14b

# Alternativas:
# ollama pull gpt-oss:20b  # 13GB
# ollama pull gpt-oss:120b # 65GB (requer muito recurso)
```

## 📊 Estrutura de Dados

Os arquivos JSON devem estar na pasta `data/` com a seguinte estrutura:

```json
[
  {
    "id": "3737403160894992541",
    "type": "Video",
    "caption": "Texto da legenda...",
    "hashtags": ["tag1", "tag2"],
    "mentions": ["perfil1"],
    "url": "https://www.instagram.com/p/ABC123/",
    "commentsCount": 7,
    "likesCount": 124,
    "timestamp": "2025-10-06T14:58:54.000Z",
    "latestComments": [
      {
        "text": "Comentário...",
        "ownerUsername": "usuario"
      }
    ]
  }
]
```

## 🎮 Uso

### Iniciar a aplicação

```bash
# Com uv
uv run python app.py

# Com argumentos personalizados
uv run python app.py --generation-model qwen2.5:7b --port 8080

# Criar link público (share)
uv run python app.py --share
```

### Opções de linha de comando

```bash
--embedding-model    # Modelo para embeddings (padrão: mxbai-embed-large)
--generation-model   # Modelo para geração (padrão: qwen2.5:3b)
--port              # Porta da aplicação (padrão: 7860)
--share             # Criar link público do Gradio
```

### Acessar a interface

Após iniciar, abra seu navegador em:
```
http://localhost:7860
```

## 💡 Exemplos de Perguntas

### Busca Simples
- "Quais foram os posts mais recentes do DCE UFF?"
- "Mostre posts sobre o HUAP"
- "O que foi publicado sobre pesquisa?"

### Análise de Engajamento
- "Quais posts tiveram mais curtidas?"
- "Posts com mais comentários nos últimos 30 dias"
- "Compare o engajamento entre os perfis"

### Busca por Tema
- "Posts que mencionam estudantes"
- "Publicações sobre eventos"
- "Novidades sobre infraestrutura"

### Filtros Temporais
- "Posts de setembro de 2024"
- "Últimas publicações do reitor"
- "Conteúdo recente do vice-reitor"

## 🔧 Testes Individuais

### Testar carregamento de dados
```bash
uv run python data_loader.py
```

### Testar embeddings
```bash
uv run python embedding_manager.py
```

### Testar sistema RAG completo
```bash
uv run python rag_system.py
```

## 📁 Estrutura do Projeto

```
ping/
├── data/                    # Arquivos JSON dos posts
│   ├── dceuff.json
│   ├── reitor.json
│   └── vicereitor.json
├── chroma_db/              # Banco vetorial (gerado automaticamente)
├── app.py                  # Aplicação Gradio principal
├── rag_system.py           # Sistema RAG completo
├── embedding_manager.py    # Gerenciamento de embeddings
├── data_loader.py          # Carregamento e processamento de dados
├── pyproject.toml          # Configuração do projeto
└── README.md              # Esta documentação
```

## ⚙️ Configuração Avançada

### Modelos Recomendados por Recurso

| Recurso Disponível | Embedding Model | Generation Model | Qualidade |
|-------------------|----------------|------------------|-----------|
| 8GB RAM | mxbai-embed-large | qwen2.5:3b | Básica |
| 16GB RAM | mxbai-embed-large | qwen2.5:7b | Boa |
| 32GB+ RAM | mxbai-embed-large | qwen2.5:14b | Excelente |

### Alternativas de Modelos de Embedding

```bash
# Opção 1: Rápido e eficiente (padrão)
ollama pull mxbai-embed-large

# Opção 2: Alta qualidade
ollama pull nomic-embed-text

# Opção 3: Multilíngue
ollama pull snowflake-arctic-embed
```

### Reindexar Posts

Se você adicionar novos arquivos JSON ou quiser reindexar:

```python
from rag_system import RAGSystem

rag = RAGSystem()
rag.index_all_posts(force_reindex=True)
```

## 🐛 Solução de Problemas

### Erro: "Model not found"
```bash
# Certifique-se de que o Ollama está rodando
ollama list

# Instale o modelo necessário
ollama pull <nome-do-modelo>
```

### Erro: "Connection refused" (Ollama)
```bash
# Inicie o serviço Ollama
# Linux/macOS
ollama serve

# Ou verifique se está rodando
ps aux | grep ollama
```

### ChromaDB não persiste dados
```bash
# Verifique permissões do diretório
chmod -R 755 chroma_db/

# Ou remova e recrie
rm -rf chroma_db/
uv run python rag_system.py
```

### Memória insuficiente
- Use modelo menor: `qwen2.5:3b` em vez de `qwen2.5:14b`
- Reduza `batch_size` em `embedding_manager.py`
- Feche outros aplicativos

## 📈 Performance

### Tempos Esperados (aprox.)

| Operação | Quantidade | Tempo |
|----------|-----------|-------|
| Indexação inicial | 1000 posts | ~5-10 min |
| Busca semântica | 5 resultados | ~1-2 seg |
| Geração resposta | 1 resposta | ~3-10 seg |

*Tempos variam conforme hardware e modelo escolhido*

## 🤝 Contribuindo

Melhorias são bem-vindas! Áreas de interesse:

- Suporte a mais formatos de dados
- Filtros temporais avançados
- Visualizações de dados
- Análise de sentimento
- Exportação de relatórios

## 📄 Licença

Este projeto é de código aberto. Use livremente para fins educacionais e institucionais.

## 🙏 Agradecimentos

Construído com:
- [Ollama](https://ollama.com/) - Modelos de linguagem locais
- [ChromaDB](https://www.trychroma.com/) - Banco de dados vetorial
- [Gradio](https://gradio.app/) - Interface web interativa
- [uv](https://docs.astral.sh/uv/) - Gerenciador de pacotes Python

---

**Desenvolvido para análise de posts institucionais da UFF**

Para dúvidas ou sugestões, abra uma issue no repositório.
