# 🔍 Ferramenta de Contagem de Termos

## Visão Geral

A ferramenta `count_term_occurrences` foi adicionada ao sistema RAG para **quantificar** menções de termos específicos em toda a base de posts, diferente da busca semântica que retorna apenas os posts mais relevantes.

## Problema Resolvido

Antes desta ferramenta:
- ❌ "Quantos posts falam sobre greve?" → Retornava apenas os 10 posts mais relevantes
- ❌ Não era possível saber o total de posts que mencionavam um termo
- ❌ Análise quantitativa limitada

Agora com `count_term_occurrences`:
- ✅ Consulta **TODA** a base de posts (10.000+ documentos)
- ✅ Retorna contagem exata e porcentagem
- ✅ Lista exemplos de posts que contêm o termo

## Implementação

### 1. Método em `query_tools.py`

```python
def count_term_occurrences(
    self,
    term: str,
    profile: Optional[str] = None,
    case_sensitive: bool = False
) -> Dict[str, Any]:
    """
    Quantifica quantos posts mencionam um termo específico.
    
    Args:
        term: Termo a buscar (pode ser palavra ou frase)
        profile: Perfil específico ou None para todos
        case_sensitive: Se True, considera maiúsculas/minúsculas
        
    Returns:
        Dict com:
        - count: Número de posts que mencionam o termo
        - percentage: Porcentagem do total de posts
        - total_posts: Total de posts analisados
        - matching_posts: Lista de posts que mencionam o termo
    """
```

**Como funciona:**
1. Busca TODOS os posts da coleção (limite: 10.000)
2. Filtra por perfil (se especificado)
3. Busca o termo no texto completo de cada post
4. Retorna estatísticas + posts que contêm o termo

### 2. Integração no Agente (`agent_system.py`)

A ferramenta foi adicionada como **ferramenta #7** no sistema de agente:

```python
7. **count_term_occurrences**
   - Uso: QUANTIFICAR quantos posts mencionam um termo específico
   - Quando usar: "quantos posts falam sobre X", "frequência de Y"
   - Parâmetros: term (str), profile (str, opcional), case_sensitive (bool)
   - Exemplo: {"tool": "count_term_occurrences", "term": "greve", "profile": "dceuff"}
```

**Diretrizes para o LLM:**
```
### Use FERRAMENTAS ESTRUTURADAS quando:
✅ QUANTIFICAÇÃO DE TERMOS: "quantos posts falam sobre X", "frequência de Y" 
   (use count_term_occurrences)
```

### 3. Formatação na Interface (`app.py`)

A interface Gradio agora formata resultados de contagem de termos:

- **Card especial** com estatísticas de contagem
- **Porcentagem** do total de posts
- **Exemplos** dos 5 primeiros posts que mencionam o termo
- **Visual diferenciado** com cor roxa (#667eea)

## Exemplos de Uso

### Via Código Direto

```python
from embedding_manager import EmbeddingManager
from query_tools import QueryTools

em = EmbeddingManager()
tools = QueryTools(em)

# Exemplo 1: Termo em todos os perfis
result = tools.count_term_occurrences(term="greve")
print(f"Encontrados: {result['count']} posts ({result['percentage']}%)")

# Exemplo 2: Termo em perfil específico
result = tools.count_term_occurrences(term="assembleia", profile="dceuff")

# Exemplo 3: Case sensitive
result = tools.count_term_occurrences(term="UFF", case_sensitive=True)
```

### Via Agente (Interface)

O agente automaticamente usa esta ferramenta quando detecta perguntas quantitativas:

**Perguntas que acionam `count_term_occurrences`:**
- ✅ "Quantos posts falam sobre greve?"
- ✅ "Qual a frequência de menções ao HUAP?"
- ✅ "Quantas vezes o DCE mencionou assembleia?"
- ✅ "Posts que contêm a palavra 'universidade'"

**Perguntas que NÃO acionam (usam `semantic_search`):**
- ❌ "Quais posts falam sobre greve?" → Busca semântica (conteúdo)
- ❌ "O que foi dito sobre HUAP?" → Busca semântica (tema)
- ❌ "Mostre posts sobre assembleia" → Busca semântica (exemplos)

## Diferenças: count_term_occurrences vs semantic_search

| Aspecto | count_term_occurrences | semantic_search |
|---------|------------------------|-----------------|
| **Objetivo** | Quantificar ocorrências | Encontrar conteúdo relevante |
| **Método** | Busca literal de string | Busca vetorial semântica |
| **Cobertura** | TODA a base (10k posts) | Top N mais relevantes (5-10) |
| **Retorno** | Contagem + exemplos | Posts mais relevantes |
| **Uso** | Análise quantitativa | Análise qualitativa |
| **Exemplo** | "Quantos posts?" | "Quais posts?" |

## Formato de Retorno

```python
{
    'count': 42,                    # Número de posts encontrados
    'percentage': 1.74,             # Porcentagem do total
    'total_posts': 2413,            # Total analisado
    'term': 'greve',                # Termo buscado
    'profile': 'todos os perfis',   # Filtro aplicado
    'matching_posts': [             # Lista de posts
        {
            'document': '...',       # Texto completo
            'metadata': {
                'profile': 'dceuff',
                'url': '...',
                'likesCount': 120,
                'commentsCount': 8,
                # ... outros metadados
            }
        },
        # ... mais posts
    ]
}
```

## Casos de Uso

### 1. Análise Política
```
"Quantos posts do DCE mencionam 'assembleia'?"
→ count_term_occurrences(term="assembleia", profile="dceuff")
```

### 2. Monitoramento de Temas
```
"Qual a frequência de posts sobre 'HUAP'?"
→ count_term_occurrences(term="HUAP")
```

### 3. Análise de Eventos
```
"Quantos posts falam sobre 'calourada'?"
→ count_term_occurrences(term="calourada")
```

### 4. Comparação de Termos
```python
# Via código: comparar frequência de termos
greve_count = tools.count_term_occurrences(term="greve")
paralisacao_count = tools.count_term_occurrences(term="paralisação")

print(f"'greve': {greve_count['count']} posts")
print(f"'paralisação': {paralisacao_count['count']} posts")
```

## Performance

- **Tempo de execução:** ~1-2 segundos para 2.413 posts
- **Memória:** Carrega todos os documentos em memória
- **Limite:** 10.000 posts (ajustável via `limit` no código)
- **Escalabilidade:** Para bases muito grandes (100k+ posts), considerar:
  - Indexação full-text (ElasticSearch, Whoosh)
  - Processamento em chunks
  - Cache de resultados frequentes

## Arquivos Modificados

1. **`query_tools.py`**
   - Adicionado método `count_term_occurrences()`
   - Adicionada definição no `TOOL_DEFINITIONS`

2. **`agent_system.py`**
   - Registrada ferramenta #7 em `_create_tools_description()`
   - Adicionado caso em `_execute_action()`
   - Adicionada formatação em `_format_results_for_llm()`
   - Atualizada diretriz: "QUANTIFICAÇÃO DE TERMOS"

3. **`app.py`**
   - Adicionado caso `is_term_count` em `format_sources()`
   - Card especial com estatísticas de contagem
   - Exibição de exemplos de posts

## Testes

Execute o script de teste:

```bash
uv run python test_term_count.py
```

**Testes incluídos:**
- ✅ Termo genérico em todos os perfis
- ✅ Termo específico em um perfil
- ✅ Termo raro (baixa frequência)
- ✅ Case sensitive vs insensitive
- ✅ Múltiplos perfis

## Próximos Passos (Sugestões)

1. **Análise de Co-ocorrência**
   - Contar posts que mencionam múltiplos termos juntos
   - Ex: "greve" AND "assembleia"

2. **Tendências Temporais**
   - Agrupar contagens por mês/ano
   - Visualizar evolução de menções

3. **Nuvem de Palavras**
   - Gerar word cloud dos termos mais frequentes
   - Integrar com biblioteca `wordcloud`

4. **Exportação de Resultados**
   - Exportar resultados para CSV/JSON
   - Facilitar análise externa

5. **Regex Support**
   - Permitir busca por padrões regex
   - Ex: `count_term_occurrences(term=r"greve|paralisação", is_regex=True)`

## Conclusão

A ferramenta `count_term_occurrences` preenche uma lacuna importante no sistema RAG:

- **Antes:** Apenas busca semântica qualitativa (top N posts relevantes)
- **Agora:** Análise quantitativa completa (todos os posts que mencionam um termo)

Isso torna o sistema mais poderoso para:
- 📊 Análise estatística de menções
- 🔍 Monitoramento de temas específicos
- 📈 Estudos de frequência e tendências
- 🎯 Validação de hipóteses quantitativas

---

**Status:** ✅ Implementado e funcional  
**Versão:** 1.0  
**Data:** 17/10/2025
