# 🎭 Análise de Sentimento - PING UFF ANALYTICS

## 📊 Visão Geral

A análise de sentimento do PING agora utiliza **Inteligência Artificial** para analisar o tom e percepção dos posts e **seus comentários**.

## 🆕 Novidades (v3.3)

### 1. **Filtro de Conteúdo** ⭐ NOVO
- ✅ **Legendas + Comentários** - Análise completa (padrão)
- ✅ **Apenas Legendas** - Sentimento do autor do post
- ✅ **Apenas Comentários** - Sentimento da comunidade
- ✅ **Cache separado** por tipo de conteúdo

### 2. **Sistema de Cache Inteligente**
- ✅ Cache automático de análises de sentimento
- ✅ Invalidação inteligente - recalcula apenas quando necessário
- ✅ Detecta automaticamente quando novos posts são adicionados
- ✅ Economiza **5-10 minutos** em análises repetidas
- ✅ Persistente em disco (JSON)

### 3. **Análise de Comentários**
- ✅ Analisa tanto **legendas** quanto **comentários dos usuários**
- ✅ Considera o tom geral da conversa
- ✅ Detecta divergências entre legenda e comentários

### 4. **Sem Limite de Amostra**
- ✅ Analisa **TODOS** os posts disponíveis
- ✅ Não há mais limite de 100 posts
- ✅ Respeita filtros de período e perfil

### 5. **Dois Modos de Análise**

#### 🤖 Modo IA Avançada (Recomendado)
- Usa DeepSeek Chat ou Ollama Qwen3:30b
- Análise contextual e precisa
- Entende ironia, sarcasmo, nuances
- Processa em lotes de 50 posts
- **Tempo**: ~5-10min para 1000 posts (primeira vez)
- **Cache**: ~1s para análises repetidas ⚡

#### ⚡ Modo Palavras-chave (Rápido)
- Análise básica por lista de palavras
- Não entende contexto
- Ideal para visualização rápida
- **Tempo**: ~1-2s para 1000 posts
- Não usa cache (muito rápido)

## 🎯 Como Usar

### 1. Na Interface Web

**Aba 📊 Estatísticas:**
```
1. Selecione o perfil (ou "Todos")
2. Escolha o modo:
   - 🤖 IA Avançada
   - ⚡ Palavras-chave
3. Escolha o conteúdo: 🆕
   - 📝 Legendas + Comentários (padrão)
   - 🏷️ Apenas Legendas
   - 💬 Apenas Comentários
4. Clique em "🔄 Atualizar Sentimento" (usa cache)
   
   OU
   
   Clique em "🔥 Forçar Recálculo" (ignora cache)
```

**Gerenciar Cache:**
- **Limpar Cache:** Botão "🗑️ Limpar Cache" remove todas as análises salvas
- **Ver Estatísticas:** Painel "💾 Estatísticas do Cache" mostra uso
- **Indicador:** 💾 = cache, 🆕 = análise nova

### 2. Via Código

```python
from analytics_dashboard import DashboardAnalytics
from embedding_manager import EmbeddingManager

em = EmbeddingManager()
analytics = DashboardAnalytics(em)

# Análise completa (legendas + comentários)
sentiment = analytics.get_sentiment_by_profile(
    profile="dceuff",
    use_llm=True,
    use_cache=True,
    content_filter="both",  # 🆕 Padrão
    limit=None
)

# Analisar apenas legendas (percepção do autor)
sentiment = analytics.get_sentiment_by_profile(
    profile="dceuff",
    use_llm=True,
    content_filter="caption"  # 🆕 Apenas legendas
)

# Analisar apenas comentários (percepção da comunidade)
sentiment = analytics.get_sentiment_by_profile(
    profile="dceuff",
    use_llm=True,
    content_filter="comments"  # 🆕 Apenas comentários
)

# Ver estatísticas do cache
cache_stats = analytics.get_cache_stats()
print(cache_stats)

# Invalidar cache de um perfil e tipo de conteúdo
analytics.invalidate_cache(
    profile="dceuff",
    content_filter="caption"  # 🆕 Especificar tipo
)

# Limpar todo o cache
analytics.cache.clear_all()
```

## 💡 Casos de Uso

### 1. **Análise Completa (Padrão)**
```python
content_filter="both"
```
- Analisa legenda + comentários
- Visão geral do sentimento
- Detecta divergências

### 2. **Sentimento do Autor**
```python
content_filter="caption"
```
- Apenas o que o perfil postou
- Tom oficial da comunicação
- Posicionamento institucional

### 3. **Sentimento da Comunidade**
```python
content_filter="comments"
```
- Reação dos seguidores
- Feedback do público
- Percepção externa

## 📊 Exemplo de Resultado

```json
{
  "total_analyzed": 2437,
  "positive": 856,
  "negative": 1024,
  "neutral": 557,
  "positive_pct": 35.1,
  "negative_pct": 42.0,
  "neutral_pct": 22.9,
  "trend": "negative",
  "profiles": ["dceuff"],
  "note": "Análise usando IA (modelo: DEEPSEEK) - 2437 registros completos",
  "cached": true,
  "content_filter": "both"
}
```

## ⚙️ Configuração

**Arquivo: `config.py`**
```python
# Modo padrão
DEFAULT_SENTIMENT_MODE = 'llm'  # ou 'keywords'

# Tamanho do batch
SENTIMENT_BATCH_SIZE = 50

# Timeout
SENTIMENT_TIMEOUT = 300  # 5 min
```

## 🔍 Estrutura de Dados

### Posts com Comentários
```json
{
  "text": "Perfil: dceuff\nData: 2024-10-15\n\n=== LEGENDA ===\nParabéns!\n\n=== COMENTÁRIOS ===\nQue ótimo!\nFinalmente!",
  "profile": "dceuff",
  "caption": "Parabéns!",
  "comments_text": "Que ótimo!\nFinalmente!",
  "likesCount": 250,
  "commentsCount": 45
}
```

### Cache (arquivo: `./cache/sentiment_cache.json`)
```json
{
  "abc123def456": {
    "result": { /* análise de sentimento */ },
    "profile": "dceuff",
    "start_date": null,
    "end_date": null,
    "total_docs": 1503,
    "content_filter": "both",
    "cached_at": "2025-10-27T14:30:00"
  }
}
```

## 📈 Performance

| Modo | Posts | Conteúdo | Tempo (1ª vez) | Tempo (cache) | Precisão |
|------|-------|----------|----------------|---------------|----------|
| 🤖 IA | 1000 | Both | ~8min | ~0.5s ⚡ | ⭐⭐⭐⭐⭐ |
| 🤖 IA | 1000 | Caption | ~5min | ~0.3s ⚡ | ⭐⭐⭐⭐⭐ |
| 🤖 IA | 1000 | Comments | ~6min | ~0.4s ⚡ | ⭐⭐⭐⭐⭐ |
| ⚡ Keywords | 1000 | Both | ~1s | ~1s | ⭐⭐⭐ |

> **Cache acelera análises IA em ~500-1000x! 🚀**

## 💾 Sistema de Cache

### Como Funciona

1. **Chave única:** Gerada a partir de:
   - Perfil
   - Data inicial
   - Data final
   - Total de documentos
   - **Tipo de conteúdo** 🆕

2. **Invalidação automática:**
   - Novos posts adicionados → cache invalidado
   - Total de documentos mudou → recalcula
   - Tipo de conteúdo diferente → cache separado
   - Mesmos parâmetros + mesmo total → usa cache

3. **Persistência:**
   - Salvo em `./cache/sentiment_cache.json`
   - Metadados em `./cache/cache_metadata.json`
   - Sobrevive a reinicializações

### Quando o Cache é Usado

✅ **USA CACHE:**
- Modo IA Avançada
- Mesmos filtros (perfil, datas, **tipo de conteúdo** 🆕)
- Nenhum post novo adicionado

❌ **NÃO USA CACHE:**
- Modo Palavras-chave (muito rápido)
- Total de posts mudou
- Tipo de conteúdo diferente 🆕
- `use_cache=False` explícito
- Cache limpo manualmente

## 🚨 Troubleshooting

### Análise muito lenta
```python
# Use modo keywords para visualização rápida
sentiment = analytics.get_sentiment_by_profile(
    profile="dceuff",
    use_llm=False
)
```

### Cache desatualizado
```python
# Force recálculo
sentiment = analytics.get_sentiment_by_profile(
    profile="dceuff",
    use_cache=False
)

# Ou limpe o cache
analytics.cache.clear_all()
```

### Sem comentários nos posts
```python
# Analise apenas legendas
sentiment = analytics.get_sentiment_by_profile(
    profile="dceuff",
    content_filter="caption"  # 🆕 Ignora comentários
)
```

### Erro de timeout
```python
# Em config.py, aumente o timeout
SENTIMENT_TIMEOUT = 600  # 10 minutos
```

### Cache corrompido
```bash
# Limpe manualmente
rm -rf ./cache/
```

## 🔮 Próximas Melhorias

- [x] Cache de análises (evitar recalcular) ✅
- [x] Filtro de conteúdo (legenda/comentários) ✅
- [ ] Análise de hashtags e menções
- [ ] Detecção de tópicos emergentes
- [ ] Comparação de sentimento entre períodos
- [ ] Exportação de relatórios
- [ ] TTL (Time-To-Live) para cache
- [ ] Compressão do cache
- [ ] Análise de divergência legenda vs. comentários

---

**Versão**: 3.3  
**Data**: 27 de Outubro de 2025  
**Status**: ✅ Produção
