# 🚀 Guia Rápido de Comandos com UV

## 📋 Comandos Principais

### Iniciar/Parar Aplicação

```bash
# Iniciar em background com nohup
./start.sh

# Parar aplicação
./stop.sh

# Reiniciar (para + inicia)
./restart.sh

# Ver logs em tempo real
tail -f nohup.out
```

### Reindexação

```bash
# Reindexar com notícias (RECOMENDADO após adicionar notícias)
uv run reindex_with_news.py

# Testar integração de notícias
uv run test_news.py
```

### Scripts Python Avulsos

```bash
# Executar qualquer script Python
uv run python script.py

# Ou diretamente
uv run script.py

# Exemplos:
uv run check_system.py
uv run check_profiles.py
uv run data_loader.py
```

## 🧪 Testes e Diagnósticos

### Verificar Sistema

```bash
# Diagnóstico completo
uv run check_system.py

# Estatísticas do banco
uv run python -c "
from embedding_manager import EmbeddingManager
em = EmbeddingManager()
print(em.get_stats())
"
```

### Testar Notícias

```bash
# Teste completo de notícias
uv run test_news.py

# Buscar notícias sobre pessoa
uv run python -c "
from query_tools import QueryTools
from embedding_manager import EmbeddingManager
em = EmbeddingManager()
tools = QueryTools(em)
news = tools.search_news_by_person('Roberto Salles', limit=3)
for n in news:
    print(n['metadata']['title'])
"

# Estatísticas de notícias
uv run python -c "
from query_tools import QueryTools
from embedding_manager import EmbeddingManager
em = EmbeddingManager()
tools = QueryTools(em)
print(tools.get_news_statistics())
"
```

### Testar Busca Semântica

```bash
# Busca combinada (posts + notícias)
uv run python -c "
from embedding_manager import EmbeddingManager
em = EmbeddingManager()
results = em.search('Roberto Salles UFF', n_results=5)
print(f'Encontrados: {len(results[\"ids\"][0])} resultados')
"

# Buscar apenas notícias
uv run python -c "
from embedding_manager import EmbeddingManager
em = EmbeddingManager()
results = em.search('expansão universidade', n_results=5, content_type_filter='news')
print(f'Notícias: {len(results[\"ids\"][0])}')
"

# Buscar apenas posts
uv run python -c "
from embedding_manager import EmbeddingManager
em = EmbeddingManager()
results = em.search('HUAP saúde', n_results=5, content_type_filter='instagram_post')
print(f'Posts: {len(results[\"ids\"][0])}')
"
```

## 🎯 Desenvolvimento

### Iniciar com Diferentes Modelos

```bash
# Modelo leve (rápido, menos preciso)
PORT=7860 uv run app.py --generation-model qwen2.5:3b

# Modelo médio (balanceado)
PORT=7860 uv run app.py --generation-model qwen2.5:7b

# Modelo pesado (melhor, mais lento) - PADRÃO
PORT=7860 uv run app.py --generation-model qwen3:30b

# Com link público
PORT=7860 uv run app.py --share
```

### Gerenciar Dependências

```bash
# Instalar/atualizar dependências
uv sync

# Adicionar nova dependência
uv add nome-do-pacote

# Remover dependência
uv remove nome-do-pacote

# Ver dependências instaladas
uv pip list
```

## 🔧 Manutenção

### Limpar e Reiniciar

```bash
# Parar aplicação
./stop.sh

# Limpar logs
rm nohup.out

# Reindexar completamente
uv run reindex_with_news.py

# Iniciar novamente
./start.sh
```

### Backup do Banco Vetorial

```bash
# Backup
tar -czf chroma_db_backup_$(date +%Y%m%d).tar.gz chroma_db/

# Restaurar
tar -xzf chroma_db_backup_20241024.tar.gz
```

### Ver Processos

```bash
# Ver se está rodando
ps aux | grep app.py

# Ver PID
pgrep -f "python.*app.py"

# Matar processo específico
kill -9 <PID>
```

## 📊 Estatísticas Rápidas

```bash
# Uma linha - Estatísticas gerais
uv run python -c "from embedding_manager import EmbeddingManager; print(EmbeddingManager().get_stats())"

# Uma linha - Estatísticas de notícias
uv run python -c "from query_tools import QueryTools; from embedding_manager import EmbeddingManager; print(QueryTools(EmbeddingManager()).get_news_statistics())"

# Uma linha - Buscar notícias
uv run python -c "from query_tools import QueryTools; from embedding_manager import EmbeddingManager; [print(n['metadata']['title']) for n in QueryTools(EmbeddingManager()).search_news_by_person('Roberto Salles', 3)]"
```

## 🆘 Solução de Problemas

### Ollama não está rodando

```bash
# Verificar status
curl http://localhost:11434/api/version

# Iniciar Ollama
ollama serve

# Em outra janela, listar modelos
ollama list
```

### Erro de dependências

```bash
# Reinstalar tudo
rm -rf .venv
uv sync
```

### Banco vetorial corrompido

```bash
# Recriar do zero
rm -rf chroma_db
uv run reindex_with_news.py
```

### Porta já em uso

```bash
# Ver o que está usando a porta 7860
lsof -i :7860

# Ou usar outra porta
PORT=8000 ./start.sh
```

## 💡 Dicas

1. **Use sempre `uv run`** para executar scripts Python - ele garante ambiente correto
2. **Logs são importantes** - sempre verifique `nohup.out` se algo der errado
3. **Reindexe após mudanças** nos dados - garante consistência
4. **Backup regular** do `chroma_db/` - indexação demora!
5. **Monitore memória** - modelos grandes (qwen3:30b) usam ~18GB RAM

## 🎓 Exemplos de Uso Real

```bash
# Setup inicial completo
uv sync
uv run reindex_with_news.py  # Responder "sim"
./start.sh

# Verificar se funcionou
uv run test_news.py

# Ver logs
tail -f nohup.out

# Parar quando terminar
./stop.sh

# Próximo uso (já configurado)
./start.sh  # Só isso!
```

---

**Lembre-se:** O prefixo `uv run` garante que você está usando o ambiente virtual correto com todas as dependências instaladas! 🎯
