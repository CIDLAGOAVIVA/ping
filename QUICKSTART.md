# 🚀 Guia Rápido de Início

## Instalação em 3 Passos

### 1️⃣ Instalar Ollama

```bash
# Linux/macOS
curl -fsSL https://ollama.com/install.sh | sh
```

### 2️⃣ Executar Setup

```bash
cd ping
./setup.sh
```

O script irá:
- ✅ Verificar dependências
- ✅ Instalar modelos necessários
- ✅ Sincronizar pacotes Python
- ✅ Iniciar a aplicação

### 3️⃣ Acessar Interface

Abra seu navegador em: **http://localhost:7860**

---

## Uso Rápido

### Iniciar aplicação (após primeira configuração)

```bash
./start.sh
```

### Iniciar com opções

```bash
# Porta customizada
./start.sh --port 8080

# Criar link público
./start.sh --share

# Modelo diferente
./start.sh --generation-model qwen2.5:7b
```

---

## Perguntas Exemplo

Digite no chat:

- "Quais posts do DCE UFF falam sobre eventos?"
- "Mostre os 5 posts mais curtidos"
- "O que o reitor publicou sobre o HUAP?"
- "Posts recentes com a palavra pesquisa"

---

## Solução Rápida de Problemas

### Ollama não está rodando
```bash
ollama serve
```

### Modelo não encontrado
```bash
ollama pull mxbai-embed-large
ollama pull qwen2.5:3b
```

### Reindexar posts
```bash
rm -rf chroma_db/
./start.sh
```

---

## Arquitetura Simplificada

```
Pergunta → Busca Vetorial → Recupera Posts → LLM gera Resposta
         (ChromaDB)         (Top 5)        (Ollama)
```

---

## Recursos do Sistema

| Componente | Tecnologia | Função |
|------------|-----------|--------|
| Interface | Gradio | Chat web interativo |
| Embeddings | mxbai-embed-large | Vetorização semântica |
| Busca | ChromaDB | Banco de dados vetorial |
| Geração | Qwen/GPT-OSS | Resposta contextual |

---

## Próximos Passos

1. ✅ Testar perguntas básicas
2. ✅ Explorar filtros de perfil
3. ✅ Ajustar número de resultados
4. 🔄 Adicionar novos JSONs em `data/`
5. 🔄 Experimentar modelos maiores

---

Para mais detalhes, consulte o **[README.md](README.md)** completo.
