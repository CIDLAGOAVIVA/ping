# 🎭 Análise de Sentimento - PING UFF ANALYTICS

## 📊 Visão Geral

A análise de sentimento do PING agora utiliza **Inteligência Artificial** para analisar o tom e percepção dos posts e **seus comentários**.

## 🆕 Novidades (v3.1)

### 1. **Análise de Comentários**
- ✅ Analisa tanto **legendas** quanto **comentários dos usuários**
- ✅ Considera o tom geral da conversa
- ✅ Detecta divergências entre legenda e comentários

### 2. **Sem Limite de Amostra**
- ✅ Analisa **TODOS** os posts disponíveis
- ✅ Não há mais limite de 100 posts
- ✅ Respeita filtros de período e perfil

### 3. **Dois Modos de Análise**

#### 🤖 Modo IA Avançada (Recomendado)
- Usa DeepSeek Chat ou Ollama Qwen3:30b
- Análise contextual e precisa
- Entende ironia, sarcasmo, nuances
- Processa em lotes de 50 posts
- **Tempo**: ~5-10min para 1000 posts

#### ⚡ Modo Palavras-chave (Rápido)
- Análise básica por lista de palavras
- Não entende contexto
- Ideal para visualização rápida
- **Tempo**: ~1-2s para 1000 posts

## 🎯 Como Usar

### 1. Na Interface Web

**Aba 📊 Estatísticas:**
```
1. Selecione o perfil (ou "Todos")
2. Escolha o modo:
   - 🤖 IA Avançada
   - ⚡ Palavras-chave
3. Clique em "🔄 Atualizar Sentimento"
```

### 2. Via Código

```python
from analytics_dashboard import DashboardAnalytics
from embedding_manager import EmbeddingManager

em = EmbeddingManager()
analytics = DashboardAnalytics(em)

# Análise com IA (todos os posts)
sentiment = analytics.get_sentiment_by_profile(
    profile="dceuff",
    use_llm=True,
    limit=None  # Sem limite
)

# Análise rápida (primeiros 100)
sentiment = analytics.get_sentiment_by_profile(
    profile="reitor",
    use_llm=False,
    limit=100
)
```

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
  "note": "Análise usando IA (modelo: DEEPSEEK) - 2437 registros completos"
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
  "text": "Perfil: dceuff\nLegenda: Parabéns!\n\nComentários:\n- Que ótimo!\n- Finalmente!",
  "profile": "dceuff",
  "comments_text": "Que ótimo!\nFinalmente!",
  "likesCount": 250,
  "commentsCount": 45
}
```

## 📈 Performance

| Modo | Posts | Tempo | Precisão |
|------|-------|-------|----------|
| 🤖 IA | 1000 | ~8min | ⭐⭐⭐⭐⭐ |
| 🤖 IA | 2500 | ~20min | ⭐⭐⭐⭐⭐ |
| ⚡ Keywords | 1000 | ~1s | ⭐⭐⭐ |
| ⚡ Keywords | 2500 | ~2s | ⭐⭐⭐ |

## 🚨 Troubleshooting

### Análise muito lenta
```python
# Use modo keywords para visualização rápida
sentiment = analytics.get_sentiment_by_profile(
    profile="dceuff",
    use_llm=False
)
```

### Erro de timeout
```python
# Em config.py, aumente o timeout
SENTIMENT_TIMEOUT = 600  # 10 minutos
```

### Sem comentários nos posts
```bash
# Verifique se seus JSONs têm o campo 'comments'
python check_data_structure.py
```

## 🔮 Próximas Melhorias

- [ ] Cache de análises (evitar recalcular)
- [ ] Análise de hashtags e menções
- [ ] Detecção de tópicos emergentes
- [ ] Comparação de sentimento entre períodos
- [ ] Exportação de relatórios

---

**Versão**: 3.1  
**Data**: 27 de Outubro de 2025  
**Status**: ✅ Produção
