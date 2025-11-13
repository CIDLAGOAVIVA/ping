# 📊 Dashboard de Análise - PING UFF ANALYTICS

## 🎯 Visão Geral

O **Dashboard de Análise** é uma nova aba do PING que permite visualizar métricas agregadas dos dados raspados (posts e notícias) com filtros temporais e por fonte.

---

## ✨ Funcionalidades

### 📈 Métricas Principais

**Cards de Resumo:**
- 📝 **Total de Registros**: Posts + notícias no período
- ❤️ **Engajamento Total**: Soma de curtidas + comentários
- 👍 **Média de Curtidas**: Por post
- 💬 **Média de Comentários**: Por post

**Gráficos e Análises:**
- 📊 **Engajamento por Fonte**: Barras comparativas entre perfis
- 🎯 **Distribuição por Perfil**: Posts e engajamento
- 🏆 **Top 5 Posts**: Maior engajamento no período
- 📰 **Notícias**: Total e distribuição por publisher

---

## 🎛️ Filtros Disponíveis

### 📅 Filtro de Período

**Campo Manual:**
- Data Inicial (YYYY-MM-DD)
- Data Final (YYYY-MM-DD)

**Períodos Rápidos:**
- ⚡ Últimos 7 dias
- ⚡ Últimos 30 dias
- ⚡ Últimos 90 dias
- ⚡ Tudo (sem limite)

### 📊 Filtro de Fontes

Selecione uma ou mais fontes:
- ☑️ @dceuff
- ☑️ @reitor
- ☑️ @vicereitor
- ☑️ @noticias (notícias)

---

## 🔄 Como Usar

1. **Acesse a aba "Dashboard"** no menu principal
2. **Selecione o período** usando campos manuais ou botões rápidos
3. **Selecione as fontes** desejadas (padrão: todas)
4. **Clique em "Atualizar Dashboard"** para aplicar os filtros
5. **Visualize as métricas** nos cards e gráficos

---

## 📊 Exemplos de Análise

### Análise Mensal
```
Período: Últimos 30 dias
Fontes: Todas

Resultado:
- Total: 245 registros
- Engajamento: 15.340
- Média curtidas: 52.3
- Top post: @dceuff com 823 interações
```

### Comparação entre Fontes
```
Período: Últimos 90 dias
Fontes: @dceuff, @reitor

Resultado:
- @dceuff: 450 posts, 28.500 engajamento
- @reitor: 120 posts, 8.200 engajamento
- DCE tem 3.75x mais posts
```

### Análise Anual
```
Período: 2024-01-01 a 2024-12-31
Fontes: Todas

Resultado:
- Total: 2.413 registros
- Engajamento total: 145.000
- Post mais engajado: 1.234 interações
- 100 notícias de 5 publishers
```

---

## 🔧 Arquivos Relacionados

- **[`analytics_dashboard.py`](../analytics_dashboard.py)** - Lógica de análise
- **[`dashboard_visualizer.py`](../dashboard_visualizer.py)** - Geração de HTML
- **[`app.py`](../app.py)** - Integração na interface

---

## 🎨 Estilo Visual

O dashboard usa as mesmas **variáveis CSS** do resto da aplicação:
- ✅ Compatível com light/dark mode
- ✅ Gradientes nos cards
- ✅ Gráficos de barras CSS puro
- ✅ Responsivo

---

## 🚀 Futuras Melhorias

### Em Desenvolvimento
- [ ] Análise de sentimento em lote
- [ ] Word cloud de tópicos
- [ ] Gráficos de linha temporal
- [ ] Exportação de relatórios (PDF/CSV)

### Planejadas
- [ ] Comparação entre períodos
- [ ] Detecção de trending topics
- [ ] Heatmap de postagens
- [ ] Previsão de engajamento

---

## 📝 Changelog

### v3.0 (Dezembro 2025)
- ✅ Dashboard de análise inicial
- ✅ Filtros de período e fontes
- ✅ Métricas agregadas
- ✅ Top posts
- ✅ Distribuição por perfil
- ✅ Seção de notícias

---

**Data**: 27 de Janeiro de 2025  
**Versão**: 3.0  
**Desenvolvido com ❤️ para a comunidade UFF**