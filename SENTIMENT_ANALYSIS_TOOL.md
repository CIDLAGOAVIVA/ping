# 🎭 Ferramenta de Análise de Sentimento

## Visão Geral

A ferramenta `analyze_sentiment` foi adicionada ao sistema RAG para **analisar o sentimento e percepção** sobre tópicos/entidades nos posts usando inteligência artificial (LLM).

## Problema Resolvido

Antes desta ferramenta:
- ❌ "Como o reitor é visto?" → Apenas busca semântica, sem análise qualitativa
- ❌ Não era possível saber o tom geral (positivo/negativo/neutro)
- ❌ Faltava identificação de aspectos positivos e negativos
- ❌ Análise subjetiva dependia de interpretação manual

Agora com `analyze_sentiment`:
- ✅ Análise automatizada de sentimento usando LLM
- ✅ Classificação em positivo/negativo/neutro
- ✅ Identificação de aspectos positivos e negativos
- ✅ Resumo qualitativo inteligente
- ✅ Exemplos de posts por categoria de sentimento

## Implementação

### 1. Método em `query_tools.py`

```python
def analyze_sentiment(
    self,
    topic: str,
    profile: Optional[str] = None,
    n_posts: int = 20
) -> Dict[str, Any]:
    """
    Analisa o sentimento de posts sobre um tópico específico usando LLM.
    
    Args:
        topic: Tópico ou entidade a analisar (ex: "reitor", "greve", "HUAP")
        profile: Perfil específico ou None para todos
        n_posts: Número de posts a analisar (padrão: 20)
        
    Returns:
        Dict com análise completa de sentimento
    """
```

**Como funciona:**
1. Busca todos os posts que mencionam o tópico
2. Seleciona até N posts para análise (padrão: 20)
3. Envia os posts para o LLM com prompt estruturado
4. LLM analisa e classifica cada post
5. Retorna estatísticas + aspectos + exemplos

### 2. Integração no Agente (`agent_system.py`)

A ferramenta foi adicionada como **ferramenta #8** no sistema de agente:

```python
8. **analyze_sentiment**
   - Uso: ANALISAR SENTIMENTO e percepção sobre um tópico/entidade
   - Quando usar: "como é visto X?", "percepção sobre Y", "análise de sentimento"
   - Parâmetros: topic (str), profile (str, opcional), n_posts (int, default=20)
   - Retorna: Contagem positivo/negativo/neutro, aspectos, resumo qualitativo
```

**Diretrizes para o LLM:**
```
### Use FERRAMENTAS ESTRUTURADAS quando:
✅ ANÁLISE DE SENTIMENTO: "como é visto X?", "percepção sobre Y", "opinião sobre Z"
   (use analyze_sentiment)
```

### 3. Interface Visual (`app.py`)

A interface agora exibe análises de sentimento com:

- **Card com resumo geral** (texto sintetizado pelo LLM)
- **Gráficos de barras** mostrando distribuição (positivo/negativo/neutro)
- **Listas de aspectos** positivos e negativos identificados
- **Pontos-chave** extraídos da análise
- **Design colorido** (verde para positivo, vermelho para negativo, cinza para neutro)

## Formato de Retorno

```python
{
    'topic': 'reitor',                      # Tópico analisado
    'profile': 'dceuff',                    # Perfil(s) analisado(s)
    'total_posts': 20,                      # Posts analisados
    'total_relevant': 45,                   # Total de posts que mencionam o tópico
    'sentiment_summary': '...',             # Resumo geral (2-3 frases)
    'positive_count': 5,                    # Número de posts positivos
    'negative_count': 12,                   # Número de posts negativos
    'neutral_count': 3,                     # Número de posts neutros
    'key_points': [                         # 3-5 pontos-chave
        'Críticas frequentes sobre...',
        'Elogios em relação a...',
    ],
    'positive_aspects': [                   # Aspectos positivos
        'Gestão transparente',
        'Proximidade com estudantes'
    ],
    'negative_aspects': [                   # Críticas identificadas
        'Falta de diálogo',
        'Demora em decisões'
    ],
    'examples': {                           # Exemplos de posts
        'positive': [...],                  # Até 2 posts positivos
        'negative': [...],                  # Até 2 posts negativos
        'neutral': [...]                    # Até 2 posts neutros
    }
}
```

## Exemplos de Uso

### Via Interface (o agente decide automaticamente)

**Perguntas que acionam `analyze_sentiment`:**
- ✅ "Como o reitor é visto pelos estudantes?"
- ✅ "Qual a percepção sobre o HUAP?"
- ✅ "O que pensam sobre a greve?"
- ✅ "Análise de sentimento sobre a universidade"
- ✅ "Como os estudantes avaliam o vice-reitor?"

**Perguntas que NÃO acionam (usam outras ferramentas):**
- ❌ "Quantos posts falam do reitor?" → `count_term_occurrences`
- ❌ "Quais posts mencionam o reitor?" → `semantic_search`
- ❌ "Posts mais curtidos do reitor" → `get_top_posts_by_likes`

### Via Código Direto

```python
from embedding_manager import EmbeddingManager
from query_tools import QueryTools

em = EmbeddingManager()
tools = QueryTools(em, llm_model="qwen3:30b")

# Exemplo 1: Análise geral
result = tools.analyze_sentiment(topic="reitor")
print(f"Resumo: {result['sentiment_summary']}")
print(f"Positivos: {result['positive_count']}")
print(f"Negativos: {result['negative_count']}")

# Exemplo 2: Análise por perfil específico
result = tools.analyze_sentiment(
    topic="greve",
    profile="dceuff",
    n_posts=30
)

# Exemplo 3: Ver aspectos identificados
print("Aspectos positivos:", result['positive_aspects'])
print("Aspectos negativos:", result['negative_aspects'])
```

## Casos de Uso

### 1. Análise de Reputação
```
"Como o reitor é visto pelos estudantes?"
→ analyze_sentiment(topic="reitor", profile="dceuff")
```
**Retorna:** Sentimento geral, críticas comuns, elogios, exemplos

### 2. Monitoramento de Temas Sensíveis
```
"Qual a percepção sobre a greve?"
→ analyze_sentiment(topic="greve")
```
**Retorna:** Divisão de opiniões, argumentos de cada lado

### 3. Avaliação de Serviços
```
"O que pensam sobre o HUAP?"
→ analyze_sentiment(topic="HUAP")
```
**Retorna:** Satisfação geral, problemas recorrentes, pontos positivos

### 4. Comparação de Percepções
```python
# Via código: comparar sentimento em diferentes perfis
dce_sentiment = tools.analyze_sentiment(topic="reitor", profile="dceuff")
reitor_sentiment = tools.analyze_sentiment(topic="reitor", profile="reitor")

print(f"DCE - Negativos: {dce_sentiment['negative_count']}")
print(f"Reitor - Negativos: {reitor_sentiment['negative_count']}")
```

## Interface Visual

### Gráficos de Barras
```
✅ Positivo:  [████████░░░░░░░░░░░░] 5 (25.0%)
❌ Negativo:  [████████████████░░░░] 12 (60.0%)
⚪ Neutro:    [███░░░░░░░░░░░░░░░░░] 3 (15.0%)
```

### Cards Coloridos
- **Verde** (#4caf50): Aspectos positivos
- **Vermelho** (#f44336): Aspectos negativos/críticas
- **Roxo** (#667eea): Pontos-chave

### Informações Exibidas
1. Resumo geral (texto narrativo do LLM)
2. Distribuição visual de sentimentos
3. Lista de aspectos positivos
4. Lista de aspectos negativos/críticas
5. Pontos-chave da análise

## Performance

- **Tempo de execução:** ~5-15 segundos (depende do LLM)
- **Posts analisados:** Padrão 20, máximo recomendado 50
- **Modelo LLM:** qwen3:30b (configurável)
- **Custo computacional:** Alto (cada análise requer chamada ao LLM)

## Limitações e Considerações

### 1. Dependência do LLM
- Qualidade da análise depende do modelo usado
- Modelos maiores (30B+) geram melhores análises
- Tempo de resposta aumenta com modelos maiores

### 2. Subjetividade
- Classificação de sentimento pode ser subjetiva
- LLM pode ter vieses próprios
- Contexto cultural influencia a interpretação

### 3. Quantidade de Posts
- Analisar muitos posts (>50) pode gerar timeout
- LLM pode perder nuances em lotes muito grandes
- Recomendado: 20-30 posts para análise equilibrada

### 4. Idioma e Contexto
- Posts em português com gírias podem ser mal interpretados
- Ironia e sarcasmo são desafios para análise automática

## Melhorias Futuras (Sugestões)

### 1. Análise Temporal
```python
# Analisar mudança de sentimento ao longo do tempo
analyze_sentiment_timeline(
    topic="reitor",
    start_date="2024-01-01",
    end_date="2024-12-31",
    interval="monthly"
)
```

### 2. Comparação de Tópicos
```python
# Comparar sentimento entre múltiplos tópicos
compare_sentiments(topics=["reitor", "vice-reitor", "gestão"])
```

### 3. Análise de Co-ocorrência
```python
# Sentimento quando dois tópicos aparecem juntos
analyze_sentiment(topic="reitor greve")  # Como o reitor é visto em relação à greve
```

### 4. Exportação de Relatórios
```python
# Gerar relatório PDF/HTML com análise completa
export_sentiment_report(
    result=analysis,
    format="pdf",
    output="analise_reitor.pdf"
)
```

### 5. Cache de Análises
- Cachear análises recentes para evitar reprocessamento
- Invalidar cache quando novos posts são adicionados

### 6. Análise Multimodal
- Analisar também imagens e vídeos dos posts
- Detectar sentimento em emojis e figurinhas

## Arquivos Modificados

1. **`query_tools.py`** (+ 180 linhas)
   - Adicionado método `analyze_sentiment()`
   - Import do `ollama` para chamadas ao LLM
   - Prompt estruturado para análise de sentimento
   - Parsing de resposta JSON do LLM

2. **`agent_system.py`** (+ 70 linhas)
   - Ferramenta registrada como #8
   - Caso adicionado em `_execute_action()`
   - Formatação completa em `_format_results_for_llm()`
   - Diretriz: "ANÁLISE DE SENTIMENTO"

3. **`app.py`** (+ 110 linhas)
   - Tratamento do caso `is_sentiment`
   - Gráficos de barras visuais
   - Cards coloridos para aspectos
   - Layout responsivo

## Testes

### Teste Rápido
```bash
uv run python -c "
from embedding_manager import EmbeddingManager
from query_tools import QueryTools

em = EmbeddingManager()
tools = QueryTools(em, llm_model='qwen3:30b')

result = tools.analyze_sentiment(topic='reitor', n_posts=10)
print(f'✅ Análise concluída!')
print(f'Resumo: {result[\"sentiment_summary\"]}')
print(f'Positivos: {result[\"positive_count\"]}')
print(f'Negativos: {result[\"negative_count\"]}')
"
```

### Via Interface
1. Inicie a aplicação: `uv run python app.py`
2. Pergunte: "Como o reitor é visto pelos estudantes?"
3. O agente automaticamente usa `analyze_sentiment`
4. Veja o resultado com gráficos e análise completa

## Conclusão

A ferramenta `analyze_sentiment` traz **análise qualitativa inteligente** para o sistema RAG:

- **Antes:** Apenas busca e contagem de posts
- **Agora:** Compreensão profunda do sentimento e percepção

Isso torna o sistema capaz de:
- 🎭 Analisar reputação e imagem
- 📊 Quantificar opiniões (positivo/negativo/neutro)
- 🔍 Identificar aspectos específicos (críticas e elogios)
- 📈 Monitorar sentimento sobre temas sensíveis
- 💡 Fornecer insights acionáveis

---

**Status:** ✅ Implementado e funcional  
**Ferramenta:** #8 no sistema de agente  
**Versão:** 1.0  
**Data:** 17/10/2025
