# 📰 Integração de Notícias - Roberto Salles

## 🎯 Visão Geral

Este documento descreve a integração de **notícias jornalísticas** sobre o ex-reitor Roberto Salles ao sistema RAG. Agora o sistema trabalha com dois tipos de conteúdo:

1. **Posts do Instagram** (dceuff, reitor, vicereitor)
2. **Notícias** sobre a UFF e Roberto Salles (2009-2010)

## 📊 Dados de Notícias

### Fonte
- **Arquivo**: `data/_smoking_gun.json`
- **Total**: 23 notícias
- **Período**: 2009-2010
- **Publishers**: FAPERJ, BBC, O Globo, G1, e outros

### Estrutura dos Dados
```json
{
  "id": 53163,
  "title": "Título da notícia",
  "description": "Descrição breve",
  "content": "Conteúdo completo...",
  "link": "https://...",
  "published": "2009-12-03T08:00:00.000Z",
  "publisher_name": "FAPERJ",
  "publisher_link": "https://...",
  "country": "BR",
  "language": "pt-419"
}
```

## 🔧 Alterações nos Módulos

### 1. `data_loader.py`
**Novos métodos:**
- `extract_news_text()` - Extrai texto de notícias
- `load_news_articles()` - Carrega arquivo de notícias
- `load_all_content()` - Carrega posts + notícias juntos

**Mudanças:**
- `load_all_posts()` agora exclui arquivos de notícias
- `get_profile_stats()` inclui estatísticas de notícias
- Campo `news_files` lista arquivos de notícias

### 2. `embedding_manager.py`
**Mudanças:**
- `add_posts()` aceita posts E notícias
- Metadados específicos por tipo:
  - **Posts**: caption, hashtags, mentions, likesCount, commentsCount
  - **Notícias**: title, description, publisher_name, publisher_link, country, language
- `search()` aceita filtro `content_type_filter` ('news' ou 'instagram_post')

### 3. `query_tools.py`
**Novas ferramentas:**

#### `get_news_articles()`
Busca notícias por período e/ou publisher.
```python
results = tools.get_news_articles(
    limit=10,
    min_date="2009-01-01",
    max_date="2010-12-31",
    publisher="BBC"
)
```

#### `search_news_by_person()`
Busca notícias mencionando uma pessoa.
```python
results = tools.search_news_by_person(
    person_name="Roberto Salles",
    limit=10
)
```

#### `get_news_statistics()`
Estatísticas sobre notícias indexadas.
```python
stats = tools.get_news_statistics()
# Retorna: total, publishers, período coberto
```

### 4. `agent_system.py`
**Atualizações:**
- Descrição das 3 novas ferramentas no planejador
- Execução das ferramentas de notícias em `_execute_action()`
- Formatação de resultados de notícias em `_format_results_for_llm()`
- Diretrizes para o agente usar ferramentas de notícias

**Novo perfil disponível:**
- `noticias` - Notícias sobre UFF e Roberto Salles

### 5. `app.py`
**Interface Gradio:**
- Formatação visual diferenciada para notícias (card laranja 📰)
- Exibe: título, publisher, data, link
- Cards de posts do Instagram mantêm estilo original (roxo)

## 🚀 Como Usar

### 1. Reindexar o Banco Vetorial

Execute o script de reindexação para incluir notícias:

```bash
python reindex_with_news.py
```

Este script irá:
1. ✅ Limpar banco vetorial atual
2. ✅ Carregar todos os posts do Instagram
3. ✅ Carregar todas as notícias
4. ✅ Indexar tudo junto (embeddings)
5. ✅ Mostrar estatísticas finais

**Tempo estimado:** 3-5 minutos

### 2. Iniciar Aplicação

```bash
python app.py
```

ou

```bash
./start.sh
```

### 3. Fazer Perguntas

Experimente perguntas como:

**Sobre Roberto Salles:**
- "Me fale sobre Roberto Salles"
- "Notícias do ex-reitor"
- "O que a imprensa disse sobre Roberto Salles?"

**Notícias gerais:**
- "Notícias da UFF em 2009"
- "O que a BBC publicou sobre a UFF?"
- "Reportagens sobre o Morro do Bumba"

**Combinando posts e notícias:**
- "Compare o que é dito nos posts do reitor atual com as notícias do ex-reitor"
- "Qual a diferença entre a comunicação oficial e a imprensa?"

## 📋 Estrutura de Metadados

### Posts do Instagram
```python
{
    'content_type': 'instagram_post',
    'profile': 'dceuff',
    'url': 'https://instagram.com/...',
    'timestamp': '2024-01-01T10:00:00',
    'likesCount': 150,
    'commentsCount': 25,
    'caption': 'Texto do post...',
    'hashtags': ['#UFF', '#educacao'],
    'mentions': ['@outroperfil']
}
```

### Notícias
```python
{
    'content_type': 'news',
    'profile': 'noticias',
    'url': 'https://www.bbc.com/...',
    'timestamp': '2009-12-03T08:00:00',
    'title': 'Título da notícia',
    'description': 'Descrição breve',
    'publisher_name': 'BBC',
    'publisher_link': 'https://www.bbc.com',
    'country': 'BR',
    'language': 'pt-419',
    'likesCount': 0,  # Notícias não têm likes
    'commentsCount': 0
}
```

## 🤖 Como o Agente Decide

O agente agora reconhece palavras-chave relacionadas a notícias:

**Triggers para ferramentas de notícias:**
- "notícias", "reportagens", "imprensa", "mídia"
- "Roberto Salles", "ex-reitor"
- Nomes de publishers: "FAPERJ", "BBC", "O Globo", "G1"
- Período histórico: "2009", "2010"

**Exemplos de raciocínio do agente:**

```
Usuário: "O que a BBC disse sobre a UFF?"
Agente: 
  1. Detecta: pergunta sobre notícias + publisher específico
  2. Usa: get_news_articles(publisher="BBC")
  3. Sintetiza: resposta com as notícias encontradas
```

```
Usuário: "Notícias sobre Roberto Salles"
Agente:
  1. Detecta: pergunta sobre pessoa específica em notícias
  2. Usa: search_news_by_person(person_name="Roberto Salles")
  3. Sintetiza: resumo das notícias que mencionam ele
```

## 📈 Estatísticas

Após a reindexação, você pode verificar:

```python
from embedding_manager import EmbeddingManager
from query_tools import QueryTools

em = EmbeddingManager()
tools = QueryTools(em)

# Estatísticas gerais
print(em.get_stats())

# Estatísticas de notícias
print(tools.get_news_statistics())
```

## 🔍 Busca Semântica

As notícias também estão disponíveis na busca semântica:

```python
# Buscar apenas notícias
results = em.search(
    query="internet gratuita Baixada Fluminense",
    content_type_filter="news",
    n_results=5
)

# Buscar apenas posts
results = em.search(
    query="HUAP hospital",
    content_type_filter="instagram_post",
    n_results=5
)

# Buscar em ambos (padrão)
results = em.search(
    query="Roberto Salles",
    n_results=10
)
```

## ⚠️ Observações Importantes

1. **Reindexação obrigatória**: Você DEVE rodar `reindex_with_news.py` para incluir notícias
2. **Memória**: A indexação usa mais memória (~500MB a mais)
3. **Tempo de resposta**: Pode ser ligeiramente maior devido ao volume maior de dados
4. **Qualidade**: Notícias antigas (2009-2010) podem conter links quebrados
5. **Idioma**: Todas as notícias estão em português do Brasil

## 🎨 Interface Visual

A interface Gradio foi atualizada para diferenciar visualmente:

- **Posts do Instagram**: Cards roxos com curtidas/comentários
- **Notícias**: Cards laranjas com título/publisher
- **Análise de sentimento**: Mantém formatação original
- **Estatísticas**: Incluem contagem de notícias

## 🐛 Solução de Problemas

### "Nenhuma notícia encontrada"
- Execute `reindex_with_news.py`
- Verifique se `data/_smoking_gun.json` existe
- Confirme que o arquivo tem 23 notícias

### "Erro ao carregar notícias"
- Verifique formato JSON do arquivo
- Confirme encoding UTF-8
- Veja logs do `data_loader.py`

### "Agente não está usando ferramentas de notícias"
- Use palavras-chave específicas ("notícias", "imprensa", "Roberto Salles")
- Verifique se a reindexação foi feita
- Teste com: "Estatísticas de notícias"

## 📝 Changelog

**v2.0 - Integração de Notícias**
- ✅ Suporte para notícias jornalísticas
- ✅ 3 novas ferramentas especializadas
- ✅ Formatação visual diferenciada
- ✅ Script de reindexação
- ✅ Documentação completa
- ✅ Perfil `noticias` no sistema
- ✅ Metadados ricos para notícias

## 🎓 Casos de Uso

### Pesquisa Acadêmica
- Análise de cobertura da imprensa sobre a UFF
- Comparação entre comunicação oficial e mídia
- Evolução de narrativas (2009-2010 vs 2024)

### Análise Institucional
- Percepção pública do ex-reitor
- Eventos importantes cobertos pela mídia
- Projetos e iniciativas destacados

### Contexto Histórico
- Gestão de Roberto Salles
- Projetos da época (Rio Estado Digital, etc)
- Eventos relevantes (Morro do Bumba, etc)

---

**Desenvolvido para o projeto UFF Instagram Analytics**  
*Adicionando contexto histórico através de notícias jornalísticas*
