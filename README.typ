// Some definitions presupposed by pandoc's typst output.
#let blockquote(body) = [
  #set text( size: 0.92em )
  #block(inset: (left: 1.5em, top: 0.2em, bottom: 0.2em))[#body]
]

#let horizontalrule = line(start: (25%,0%), end: (75%,0%))

#let endnote(num, contents) = [
  #stack(dir: ltr, spacing: 3pt, super[#num], contents)
]

#show terms: it => {
  it.children
    .map(child => [
      #strong[#child.term]
      #block(inset: (left: 1.5em, top: -0.4em))[#child.description]
      ])
    .join()
}

// Some quarto-specific definitions.

#show raw.where(block: true): set block(
    fill: luma(230),
    width: 100%,
    inset: 8pt,
    radius: 2pt
  )

#let block_with_new_content(old_block, new_content) = {
  let d = (:)
  let fields = old_block.fields()
  fields.remove("body")
  if fields.at("below", default: none) != none {
    // TODO: this is a hack because below is a "synthesized element"
    // according to the experts in the typst discord...
    fields.below = fields.below.abs
  }
  return block.with(..fields)(new_content)
}

#let empty(v) = {
  if type(v) == str {
    // two dollar signs here because we're technically inside
    // a Pandoc template :grimace:
    v.matches(regex("^\\s*$")).at(0, default: none) != none
  } else if type(v) == content {
    if v.at("text", default: none) != none {
      return empty(v.text)
    }
    for child in v.at("children", default: ()) {
      if not empty(child) {
        return false
      }
    }
    return true
  }

}

// Subfloats
// This is a technique that we adapted from https://github.com/tingerrr/subpar/
#let quartosubfloatcounter = counter("quartosubfloatcounter")

#let quarto_super(
  kind: str,
  caption: none,
  label: none,
  supplement: str,
  position: none,
  subrefnumbering: "1a",
  subcapnumbering: "(a)",
  body,
) = {
  context {
    let figcounter = counter(figure.where(kind: kind))
    let n-super = figcounter.get().first() + 1
    set figure.caption(position: position)
    [#figure(
      kind: kind,
      supplement: supplement,
      caption: caption,
      {
        show figure.where(kind: kind): set figure(numbering: _ => numbering(subrefnumbering, n-super, quartosubfloatcounter.get().first() + 1))
        show figure.where(kind: kind): set figure.caption(position: position)

        show figure: it => {
          let num = numbering(subcapnumbering, n-super, quartosubfloatcounter.get().first() + 1)
          show figure.caption: it => {
            num.slice(2) // I don't understand why the numbering contains output that it really shouldn't, but this fixes it shrug?
            [ ]
            it.body
          }

          quartosubfloatcounter.step()
          it
          counter(figure.where(kind: it.kind)).update(n => n - 1)
        }

        quartosubfloatcounter.update(0)
        body
      }
    )#label]
  }
}

// callout rendering
// this is a figure show rule because callouts are crossreferenceable
#show figure: it => {
  if type(it.kind) != str {
    return it
  }
  let kind_match = it.kind.matches(regex("^quarto-callout-(.*)")).at(0, default: none)
  if kind_match == none {
    return it
  }
  let kind = kind_match.captures.at(0, default: "other")
  kind = upper(kind.first()) + kind.slice(1)
  // now we pull apart the callout and reassemble it with the crossref name and counter

  // when we cleanup pandoc's emitted code to avoid spaces this will have to change
  let old_callout = it.body.children.at(1).body.children.at(1)
  let old_title_block = old_callout.body.children.at(0)
  let old_title = old_title_block.body.body.children.at(2)

  // TODO use custom separator if available
  let new_title = if empty(old_title) {
    [#kind #it.counter.display()]
  } else {
    [#kind #it.counter.display(): #old_title]
  }

  let new_title_block = block_with_new_content(
    old_title_block, 
    block_with_new_content(
      old_title_block.body, 
      old_title_block.body.body.children.at(0) +
      old_title_block.body.body.children.at(1) +
      new_title))

  block_with_new_content(old_callout,
    block(below: 0pt, new_title_block) +
    old_callout.body.children.at(1))
}

// 2023-10-09: #fa-icon("fa-info") is not working, so we'll eval "#fa-info()" instead
#let callout(body: [], title: "Callout", background_color: rgb("#dddddd"), icon: none, icon_color: black, body_background_color: white) = {
  block(
    breakable: false, 
    fill: background_color, 
    stroke: (paint: icon_color, thickness: 0.5pt, cap: "round"), 
    width: 100%, 
    radius: 2pt,
    block(
      inset: 1pt,
      width: 100%, 
      below: 0pt, 
      block(
        fill: background_color, 
        width: 100%, 
        inset: 8pt)[#text(icon_color, weight: 900)[#icon] #title]) +
      if(body != []){
        block(
          inset: 1pt, 
          width: 100%, 
          block(fill: body_background_color, width: 100%, inset: 8pt, body))
      }
    )
}



#let article(
  title: none,
  subtitle: none,
  authors: none,
  date: none,
  abstract: none,
  abstract-title: none,
  cols: 1,
  lang: "en",
  region: "US",
  font: "libertinus serif",
  fontsize: 11pt,
  title-size: 1.5em,
  subtitle-size: 1.25em,
  heading-family: "libertinus serif",
  heading-weight: "bold",
  heading-style: "normal",
  heading-color: black,
  heading-line-height: 0.65em,
  sectionnumbering: none,
  toc: false,
  toc_title: none,
  toc_depth: none,
  toc_indent: 1.5em,
  doc,
) = {
  set par(justify: true)
  set text(lang: lang,
           region: region,
           font: font,
           size: fontsize)
  set heading(numbering: sectionnumbering)
  if title != none {
    align(center)[#block(inset: 2em)[
      #set par(leading: heading-line-height)
      #if (heading-family != none or heading-weight != "bold" or heading-style != "normal"
           or heading-color != black) {
        set text(font: heading-family, weight: heading-weight, style: heading-style, fill: heading-color)
        text(size: title-size)[#title]
        if subtitle != none {
          parbreak()
          text(size: subtitle-size)[#subtitle]
        }
      } else {
        text(weight: "bold", size: title-size)[#title]
        if subtitle != none {
          parbreak()
          text(weight: "bold", size: subtitle-size)[#subtitle]
        }
      }
    ]]
  }

  if authors != none {
    let count = authors.len()
    let ncols = calc.min(count, 3)
    grid(
      columns: (1fr,) * ncols,
      row-gutter: 1.5em,
      ..authors.map(author =>
          align(center)[
            #author.name \
            #author.affiliation \
            #author.email
          ]
      )
    )
  }

  if date != none {
    align(center)[#block(inset: 1em)[
      #date
    ]]
  }

  if abstract != none {
    block(inset: 2em)[
    #text(weight: "semibold")[#abstract-title] #h(1em) #abstract
    ]
  }

  if toc {
    let title = if toc_title == none {
      auto
    } else {
      toc_title
    }
    block(above: 0em, below: 2em)[
    #outline(
      title: toc_title,
      depth: toc_depth,
      indent: toc_indent
    );
    ]
  }

  if cols == 1 {
    doc
  } else {
    columns(cols, doc)
  }
}

#set table(
  inset: 6pt,
  stroke: none
)

#set page(
  paper: "us-letter",
  margin: (x: 1.25in, y: 1.25in),
  numbering: "1",
)

#show: doc => article(
  toc_title: [Table of contents],
  toc_depth: 3,
  cols: 1,
  doc,
)

= 📱 UFF Instagram Analytics - Sistema RAG Inteligente
<uff-instagram-analytics---sistema-rag-inteligente>
#quote(block: true)[
Sistema de análise semântica e análise de sentimento para posts do Instagram dos perfis institucionais da UFF (Universidade Federal Fluminense) usando IA local.
]

#block[
#box(image("README_files/mediabag/Python-3.12--blue.svg")) #box(image("README_files/mediabag/Ollama-Local-AI-gree.svg")) #box(image("README_files/mediabag/ChromaDB-Vector-DB-o.svg")) #box(image("README_files/mediabag/Gradio-4.0--red.svg"))

#strong[#link(<-início-rápido>)[Início Rápido];] • #strong[#link(<-funcionalidades>)[Funcionalidades];] • #strong[#link(<-arquitetura>)[Arquitetura];] • #strong[#link(<-documentação-completa>)[Documentação];]

]

#horizontalrule

== 📋 Índice
<índice>
- #link(<-visão-geral>)[Visão Geral]
- #link(<-funcionalidades>)[Funcionalidades]
- #link(<-arquitetura-do-sistema>)[Arquitetura do Sistema]
- #link(<-início-rápido>)[Início Rápido]
- #link(<-configuração>)[Configuração]
- #link(<-uso-da-interface>)[Uso da Interface]
- #link(<-ferramentas-disponíveis>)[Ferramentas Disponíveis]
- #link(<-api-rest>)[API REST]
- #link(<-documentação-completa>)[Documentação Completa]
- #link(<-solução-de-problemas>)[Solução de Problemas]

#horizontalrule

== 🎯 Visão Geral
<visão-geral>
O #strong[UFF Instagram Analytics] é um sistema completo de análise de posts do Instagram que combina:

- 🤖 #strong[Agente Inteligente] - LLM decide automaticamente quais ferramentas usar
- 🔍 #strong[Busca Semântica] - Encontre posts por significado, não apenas palavras-chave
- 📊 #strong[Análise Quantitativa] - Estatísticas de engajamento, ranking, comparações
- 🎭 #strong[Análise de Sentimento] - Compreenda percepções e opiniões automaticamente
- 💬 #strong[Interface de Chat] - Pergunte em linguagem natural
- 🌐 #strong[100% Local] - Privacidade total, sem enviar dados para APIs externas

=== Base de Dados Atual
<base-de-dados-atual>
- #strong[2.413 posts] indexados
- #strong[3 perfis] oficiais da UFF:
  - `@dceuff` (Diretório Central dos Estudantes) - 1.503 posts
  - `@reitor` (Reitoria da UFF) - 575 posts
  - `@vicereitor` (Vice-Reitoria da UFF) - 335 posts

#horizontalrule

== ✨ Funcionalidades
<funcionalidades>
=== 🎯 Sistema de Agente Inteligente
<sistema-de-agente-inteligente>
O sistema usa um #strong[agente autônomo] que: 1. 📋 #strong[Analisa] sua pergunta em linguagem natural 2. 🧠 #strong[Decide] automaticamente quais ferramentas usar 3. ⚙️ #strong[Executa] as ferramentas necessárias (uma ou múltiplas) 4. 🎨 #strong[Sintetiza] uma resposta clara e completa

#strong[Exemplo:]

```
Você: "Como o reitor é visto pelos estudantes?"

Agente:
  1. Detecta: pergunta de sentimento
  2. Usa: analyze_sentiment(topic="reitor", profile="dceuff")
  3. Retorna: Análise completa com positivo/negativo, críticas, elogios
```

=== 🛠️ 9 Ferramentas Especializadas
<ferramentas-especializadas>
#table(
  columns: (10.71%, 39.29%, 17.86%, 32.14%),
  align: (auto,auto,auto,auto,),
  table.header([\#], [Ferramenta], [Uso], [Exemplo],),
  table.hline(),
  [1], [`get_top_posts_by_likes`], [Posts mais curtidos], ["Post mais curtido do reitor"],
  [2], [`get_top_posts_by_comments`], [Posts mais comentados], ["Top 5 com mais comentários"],
  [3], [`get_posts_by_engagement`], [Maior engajamento total], ["Posts com maior interação"],
  [4], [`get_recent_posts`], [Publicações recentes], ["Posts dos últimos 7 dias"],
  [5], [`get_profile_statistics`], [Estatísticas agregadas], ["Estatísticas do DCE"],
  [6], [`compare_profiles`], [Comparação entre perfis], ["Compare os 3 perfis"],
  [7], [`count_term_occurrences`], [Contagem de menções], ["Quantos posts falam de greve?"],
  [8], [`analyze_sentiment`], [Análise de sentimento (IA)], ["Como o HUAP é visto?"],
  [9], [`semantic_search`], [Busca por conteúdo], ["Posts sobre saúde"],
)
=== 🎭 Análise de Sentimento com IA
<análise-de-sentimento-com-ia>
Ferramenta única que usa LLM para analisar percepção e opiniões:

```
Entrada: "Como o reitor é visto pelos estudantes?"

Saída:
  ✅ 5 posts positivos (25%)
  ❌ 12 posts negativos (60%)
  ⚪ 3 posts neutros (15%)
  
  Aspectos Positivos:
  - Gestão transparente
  - Diálogo com comunidade
  
  Aspectos Negativos:
  - Demora em decisões
  - Falta de comunicação clara
  
  + Resumo narrativo completo
  + Exemplos de posts de cada categoria
```

#horizontalrule

== 🏗️ Arquitetura do Sistema
<arquitetura-do-sistema>
=== Visão Geral
<visão-geral-1>
```
┌─────────────────────────────────────────────────────────────┐
│                    INTERFACE GRADIO                          │
│              (Chat + Filtros + Visualizações)                │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    AGENTE RAG (LLM)                          │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │ Planejamento│→ │  Execução    │→ │  Síntese     │        │
│  │  (qwen3:30b)│  │ (Ferramentas)│  │  (qwen3:30b) │        │
│  └─────────────┘  └──────────────┘  └──────────────┘        │
└────────────────────────┬────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
         ▼               ▼               ▼
┌────────────────┐ ┌──────────┐ ┌──────────────┐
│ ChromaDB       │ │ Análise  │ │ Estatísticas │
│ (Embeddings)   │ │Sentimento│ │  Agregadas   │
│ 2.413 posts    │ │  (LLM)   │ │   (Python)   │
└────────────────┘ └──────────┘ └──────────────┘
         │
         ▼
┌─────────────────────────────────────────────┐
│         DADOS BRUTOS (JSON)                 │
│  dceuff.json | reitor.json | vicereitor.json│
└─────────────────────────────────────────────┘
```

=== Componentes Principais
<componentes-principais>
==== 1. #strong[Interface (app.py)]
<interface-app.py>
- Interface web com Gradio 4.0+
- Chat interativo com histórico
- Filtros por perfil
- Exibição de resultados (cards, gráficos, estatísticas)
- Avatar customizado do agente

==== 2. #strong[Agente RAG (agent\_system.py)]
<agente-rag-agent_system.py>
- #strong[Planejamento];: LLM analisa a pergunta e decide quais ferramentas usar
- #strong[Execução];: Roda as ferramentas escolhidas (pode ser múltiplas)
- #strong[Síntese];: LLM combina resultados em resposta coerente

==== 3. #strong[Ferramentas (query\_tools.py)]
<ferramentas-query_tools.py>
- 9 ferramentas especializadas
- Queries estruturadas no ChromaDB
- Análise de sentimento com LLM
- Estatísticas calculadas em Python

==== 4. #strong[Embeddings (embedding\_manager.py)]
<embeddings-embedding_manager.py>
- Gerencia ChromaDB
- Modelo: `mxbai-embed-large` (669MB)
- Busca vetorial semântica
- Persistência em disco

==== 5. #strong[Dados (data\_loader.py)]
<dados-data_loader.py>
- Carrega posts de arquivos JSON
- Processa e limpa dados
- Extrai metadados (curtidas, comentários, data, etc.)

=== Fluxo de Uma Consulta
<fluxo-de-uma-consulta>
```mermaid
graph TD
    A[Usuário faz pergunta] --> B[Agente: Planejamento]
    B --> C{Qual ferramenta?}
    C -->|Sentimento| D[analyze_sentiment]
    C -->|Contagem| E[count_term_occurrences]
    C -->|Ranking| F[get_top_posts]
    C -->|Busca| G[semantic_search]
    D --> H[Agente: Síntese]
    E --> H
    F --> H
    G --> H
    H --> I[Resposta formatada]
    I --> J[Interface: Exibição]
```

#horizontalrule

== 🚀 Início Rápido
<início-rápido>
=== Pré-requisitos
<pré-requisitos>
- #strong[Python 3.12+]
- #strong[uv] (gerenciador de pacotes)
- #strong[Ollama] (para rodar LLMs localmente)
- #strong[8GB RAM] mínimo (16GB recomendado)
- #strong[20GB] de espaço em disco para modelos

=== Instalação em 3 Passos
<instalação-em-3-passos>
==== 1. Instalar Ollama
<instalar-ollama>
```bash
# Linux
curl -fsSL https://ollama.com/install.sh | sh

# macOS
brew install ollama

# Windows
# Baixe de https://ollama.com/download
```

==== 2. Configurar Projeto
<configurar-projeto>
```bash
# Navegue até o diretório
cd /home/marcus/projects/ping

# Sincronize dependências
uv sync
```

==== 3. Instalar Modelos
<instalar-modelos>
```bash
# Modelo de embeddings (OBRIGATÓRIO) - 669MB
ollama pull mxbai-embed-large

# Modelo de geração (escolha um):

# Opção 1: Leve - 2GB RAM
ollama pull qwen2.5:3b

# Opção 2: Balanceado - 7GB RAM (recomendado)
ollama pull qwen2.5:7b

# Opção 3: Melhor qualidade - 18GB RAM
ollama pull qwen3:30b  # ← Modelo atual do sistema
```

=== Iniciar a Aplicação
<iniciar-a-aplicação>
```bash
# Modo padrão (porta 7860)
uv run python app.py

# Com modelo específico
uv run python app.py --generation-model qwen2.5:7b

# Criar link público
uv run python app.py --share

# Porta customizada
uv run python app.py --port 8080
```

Acesse: #strong[http:\/\/localhost:7860]

#horizontalrule

== ⚙️ Configuração
<configuração>
=== Argumentos de Linha de Comando
<argumentos-de-linha-de-comando>
```bash
--embedding-model TEXT    # Modelo para embeddings
                         # Padrão: mxbai-embed-large

--generation-model TEXT   # Modelo para geração de respostas
                         # Padrão: qwen3:30b

--port INTEGER           # Porta da aplicação web
                         # Padrão: 7860

--share                  # Criar link público Gradio
                         # Padrão: False
```

=== Modelos Recomendados por Recurso
<modelos-recomendados-por-recurso>
#table(
  columns: 5,
  align: (auto,auto,auto,auto,auto,),
  table.header([RAM Disponível], [Embedding], [Generation], [Qualidade], [Velocidade],),
  table.hline(),
  [8GB], [mxbai-embed-large], [qwen2.5:3b], [⭐⭐], [⚡⚡⚡],
  [16GB], [mxbai-embed-large], [qwen2.5:7b], [⭐⭐⭐], [⚡⚡],
  [32GB+], [mxbai-embed-large], [qwen3:30b], [⭐⭐⭐⭐⭐], [⚡],
)
=== Estrutura de Dados (JSON)
<estrutura-de-dados-json>
Os posts devem estar em `data/` no formato:

```json
[
  {
    "id": "3737403160894992541",
    "type": "Video",
    "caption": "Texto da legenda do post...",
    "hashtags": ["uff", "universidade"],
    "mentions": ["@perfil"],
    "url": "https://www.instagram.com/p/ABC123/",
    "commentsCount": 7,
    "likesCount": 124,
    "timestamp": "2025-10-06T14:58:54.000Z",
    "latestComments": [
      {
        "text": "Ótima iniciativa!",
        "ownerUsername": "usuario123"
      }
    ]
  }
]
```

#horizontalrule

== 💬 Uso da Interface
<uso-da-interface>
=== Painel Principal
<painel-principal>
```
┌─────────────────────────────────────────────────────────┐
│  📱 UFF Instagram Analytics                             │
│  Faça perguntas sobre os 2.413 posts                    │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  💬 CHAT                     │  ⚙️ CONFIGURAÇÕES        │
│  ┌──────────────────┐        │  Filtrar por Perfil:     │
│  │ Bot: Olá!        │        │  [🌐 Todos os Perfis ▼] │
│  │ User: Quantos... │        │                          │
│  └──────────────────┘        │  📊 Estatísticas         │
│                              │  💡 Exemplos             │
│  [Digite sua pergunta...]    │  🏆 Post mais curtido    │
│  [Enviar 🚀]                 │  📊 Compare perfis       │
│                              │  🔍 Posts sobre HUAP     │
└──────────────────────────────┴──────────────────────────┘
```

=== Exemplos de Perguntas
<exemplos-de-perguntas>
==== 📊 Análise Quantitativa
<análise-quantitativa>
```
✅ "Quantos posts falam sobre greve?"
→ Usa: count_term_occurrences
→ Retorna: 42 posts (1.74%)

✅ "Qual foi o post mais curtido do reitor?"
→ Usa: get_top_posts_by_likes(profile="reitor", limit=1)
→ Retorna: Post com 1.234 curtidas + link

✅ "Compare o engajamento dos 3 perfis"
→ Usa: compare_profiles()
→ Retorna: Tabela comparativa completa
```

==== 🔍 Busca Semântica
<busca-semântica>
```
✅ "Posts sobre saúde e hospital"
→ Usa: semantic_search(query="saúde hospital HUAP atendimento")
→ Retorna: 10 posts mais relevantes

✅ "O que foi dito sobre a greve em 2024?"
→ Usa: semantic_search + filtro temporal
→ Retorna: Posts relevantes ordenados

✅ "Última aparição pública do reitor"
→ Usa: semantic_search(profile="reitor") + get_recent_posts
→ Retorna: Post mais recente relevante
```

==== 🎭 Análise de Sentimento
<análise-de-sentimento>
```
✅ "Como o reitor é visto pelos estudantes?"
→ Usa: analyze_sentiment(topic="reitor", profile="dceuff")
→ Retorna:
  • 60% negativos, 25% positivos, 15% neutros
  • Aspectos positivos: transparência, diálogo
  • Críticas: demora, falta de comunicação
  • Resumo narrativo + exemplos

✅ "Qual a percepção sobre o HUAP?"
→ Usa: analyze_sentiment(topic="HUAP")
→ Retorna: Análise completa de sentimento

✅ "O que pensam sobre a gestão?"
→ Usa: analyze_sentiment(topic="gestão")
→ Retorna: Opiniões e tendências identificadas
```

==== 📈 Estatísticas
<estatísticas>
```
✅ "Estatísticas do DCE"
→ Usa: get_profile_statistics(profile="dceuff")
→ Retorna:
  • 1.503 posts
  • 45.678 curtidas totais
  • Média: 30.4 curtidas/post
  • Post mais engajado

✅ "Posts da última semana"
→ Usa: get_recent_posts(days=7)
→ Retorna: Todos os posts recentes

✅ "Top 5 posts com mais comentários"
→ Usa: get_top_posts_by_comments(limit=5)
→ Retorna: Ranking com links
```

#horizontalrule

== 🛠️ Ferramentas Disponíveis
<ferramentas-disponíveis>
=== 1. get\_top\_posts\_by\_likes
<get_top_posts_by_likes>
#strong[Uso:] Encontrar posts mais curtidos \
#strong[Parâmetros:] - `limit` (int): Quantidade de posts - `profile` (str, opcional): Filtrar por perfil

#strong[Exemplo:]

```python
tools.get_top_posts_by_likes(limit=10, profile="reitor")
```

=== 2. get\_top\_posts\_by\_comments
<get_top_posts_by_comments>
#strong[Uso:] Posts com mais comentários \
#strong[Parâmetros:] - `limit` (int): Quantidade - `profile` (str, opcional): Perfil

=== 3. get\_posts\_by\_engagement
<get_posts_by_engagement>
#strong[Uso:] Maior engajamento (curtidas + comentários) \
#strong[Parâmetros:] - `limit` (int): Quantidade - `profile` (str, opcional): Perfil

=== 4. get\_recent\_posts
<get_recent_posts>
#strong[Uso:] Publicações recentes \
#strong[Parâmetros:] - `days` (int): Últimos N dias - `limit` (int): Quantidade - `profile` (str, opcional): Perfil

=== 5. get\_profile\_statistics
<get_profile_statistics>
#strong[Uso:] Estatísticas agregadas de um perfil \
#strong[Parâmetros:] - `profile` (str, opcional): Se vazio, retorna todos

#strong[Retorna:]

```json
{
  "total_posts": 1503,
  "total_likes": 45678,
  "total_comments": 2341,
  "avg_likes_per_post": 30.4,
  "avg_comments_per_post": 1.6,
  "total_engagement": 48019,
  "top_post": {...}
}
```

=== 6. compare\_profiles
<compare_profiles>
#strong[Uso:] Comparar todos os perfis \
#strong[Sem parâmetros]

#strong[Retorna:]

```json
{
  "dceuff": {
    "total_posts": 1503,
    "total_likes": 45678,
    "avg_likes": 30.4,
    ...
  },
  "reitor": {...},
  "vicereitor": {...}
}
```

=== 7. count\_term\_occurrences ⭐ NOVO
<count_term_occurrences-novo>
#strong[Uso:] Quantificar menções de um termo \
#strong[Parâmetros:] - `term` (str): Termo a buscar - `profile` (str, opcional): Perfil - `case_sensitive` (bool): Maiúsculas/minúsculas

#strong[Retorna:]

```json
{
  "count": 42,
  "percentage": 1.74,
  "total_posts": 2413,
  "term": "greve",
  "matching_posts": [...]
}
```

#strong[Diferença de semantic\_search:] - `count_term_occurrences`: #strong[QUANTIFICA] (todos os posts) - `semantic_search`: #strong[QUALIFICA] (posts mais relevantes)

=== 8. analyze\_sentiment ⭐ NOVO - IA
<analyze_sentiment-novo---ia>
#strong[Uso:] Análise de sentimento com LLM \
#strong[Parâmetros:] - `topic` (str): Tópico/entidade - `profile` (str, opcional): Perfil - `n_posts` (int): Posts a analisar (padrão: 20)

#strong[Retorna:]

```json
{
  "topic": "reitor",
  "sentiment_summary": "Análise narrativa...",
  "positive_count": 5,
  "negative_count": 12,
  "neutral_count": 3,
  "positive_aspects": ["transparência", "diálogo"],
  "negative_aspects": ["demora", "comunicação"],
  "key_points": [...],
  "examples": {
    "positive": [...],
    "negative": [...],
    "neutral": [...]
  }
}
```

#strong[Como funciona:] 1. Busca posts que mencionam o tópico 2. Seleciona até N posts para análise 3. LLM analisa e classifica cada post 4. Extrai aspectos positivos e negativos 5. Gera resumo qualitativo 6. Retorna estatísticas + exemplos

=== 9. semantic\_search
<semantic_search>
#strong[Uso:] Busca vetorial por conteúdo \
#strong[Parâmetros:] - `query` (str): Consulta semântica - `n_results` (int): Quantidade - `profile` (str, opcional): Perfil

#strong[Como funciona:] - Converte query em embedding - Busca posts similares no espaço vetorial - Retorna os N mais relevantes

#horizontalrule

== 🌐 API REST
<api-rest>
A aplicação Gradio expõe uma API REST automática.

=== Endpoint Principal
<endpoint-principal>
```
POST http://localhost:7860/api/predict
```

=== Fazer uma Pergunta
<fazer-uma-pergunta>
```bash
curl -X POST http://localhost:7860/api/predict \
  -H "Content-Type: application/json" \
  -d '{
    "data": [
      "Quantos posts falam de greve?",
      [],
      5,
      "🌐 Todos os Perfis"
    ]
  }'
```

#strong[Parâmetros (array `data`):] 1. Pergunta (string) 2. Histórico do chat (array, pode ser `[]`) 3. Número de resultados (int, ignorado no modo agente) 4. Filtro de perfil (string: "🌐 Todos os Perfis", "#cite(<dceuff>, form: "prose");", "#cite(<reitor>, form: "prose");", "#cite(<vicereitor>, form: "prose");")

=== Resposta
<resposta>
```json
{
  "data": [
    "",  // Input vazio (limpo após envio)
    [    // Histórico atualizado
      [
        "Quantos posts falam de greve?",
        "Encontrados 42 posts (1.74%) que mencionam 'greve'..."
      ]
    ],
    "<div>...</div>"  // HTML dos posts recuperados
  ],
  "duration": 2.34
}
```

=== Exemplo com Python
<exemplo-com-python>
```python
import requests

response = requests.post(
    "http://localhost:7860/api/predict",
    json={
        "data": [
            "Como o reitor é visto?",
            [],
            5,
            "@dceuff"
        ]
    }
)

result = response.json()
answer = result['data'][1][0][1]  # Resposta do bot
print(answer)
```

#horizontalrule

== 📚 Documentação Completa
<documentação-completa>
=== Arquivos de Documentação
<arquivos-de-documentação>
Toda a documentação está consolidada aqui, mas arquivos individuais ainda existem:

#table(
  columns: 2,
  align: (auto,auto,),
  table.header([Arquivo], [Conteúdo],),
  table.hline(),
  [`README.md`], [#strong[Este arquivo] - Documentação completa],
  [`QUICKSTART.md`], [Guia rápido de início],
  [`API_QUICKSTART.md`], [Exemplos de uso da API],
  [`TOOLS.md`], [Detalhes de todas as ferramentas],
  [`SENTIMENT_ANALYSIS_TOOL.md`], [Análise de sentimento (ferramenta \#8)],
  [`TERM_COUNT_TOOL.md`], [Contagem de termos (ferramenta \#7)],
  [`ARCHITECTURE.md`], [Arquitetura detalhada],
  [`AGENT_VS_CLASSIC.md`], [Comparação agente vs sistema clássico],
  [`BALANCED_AGENT.md`], [Como o agente equilibra ferramentas],
)
=== Estrutura de Arquivos
<estrutura-de-arquivos>
```
ping/
├── 📁 data/                      # Dados dos posts (JSON)
│   ├── dceuff.json              # 1.503 posts
│   ├── reitor.json              # 575 posts
│   └── vicereitor.json          # 335 posts
│
├── 📁 chroma_db/                # Banco vetorial (auto-gerado)
│   └── ...                      # Embeddings persistidos
│
├── 📁 assets/                   # Assets da interface
│   └── agent_avatar.png         # Avatar do agente
│
├── 🐍 CÓDIGO PRINCIPAL
│   ├── app.py                   # Interface Gradio
│   ├── agent_system.py          # Sistema de agente RAG
│   ├── query_tools.py           # 9 ferramentas especializadas
│   ├── embedding_manager.py     # Gerenciador ChromaDB
│   ├── data_loader.py           # Carregador de dados
│   └── rag_system.py            # Sistema RAG clássico (legado)
│
├── 📄 CONFIGURAÇÃO
│   ├── pyproject.toml           # Dependências (uv)
│   └── .python-version          # Python 3.12+
│
├── 🧪 TESTES
│   ├── test_term_count.py       # Teste de contagem
│   └── check_profiles.py        # Debug de perfis
│
└── 📚 DOCUMENTAÇÃO
    ├── README.md                # ← VOCÊ ESTÁ AQUI
    ├── QUICKSTART.md
    ├── API_QUICKSTART.md
    ├── TOOLS.md
    ├── SENTIMENT_ANALYSIS_TOOL.md
    ├── TERM_COUNT_TOOL.md
    ├── ARCHITECTURE.md
    ├── AGENT_VS_CLASSIC.md
    └── BALANCED_AGENT.md
```

=== Tecnologias Utilizadas
<tecnologias-utilizadas>
#table(
  columns: 3,
  align: (auto,auto,auto,),
  table.header([Tecnologia], [Versão], [Uso],),
  table.hline(),
  [#strong[Python];], [3.12+], [Linguagem principal],
  [#strong[uv];], [Latest], [Gerenciador de pacotes],
  [#strong[Ollama];], [Latest], [Runtime para LLMs locais],
  [#strong[ChromaDB];], [Latest], [Banco de dados vetorial],
  [#strong[Gradio];], [4.0+], [Interface web],
  [#strong[mxbai-embed-large];], [669MB], [Modelo de embeddings],
  [#strong[qwen3:30b];], [18GB], [Modelo de geração (padrão)],
)

#horizontalrule

== 🐛 Solução de Problemas
<solução-de-problemas>
=== Erro: "Model not found"
<erro-model-not-found>
```bash
# Verifique modelos instalados
ollama list

# Instale o modelo necessário
ollama pull mxbai-embed-large
ollama pull qwen3:30b
```

=== Erro: "Connection refused" (Ollama)
<erro-connection-refused-ollama>
```bash
# Verifique se Ollama está rodando
ollama list

# Se não estiver, inicie:
ollama serve

# Ou no sistema
ps aux | grep ollama
```

=== ChromaDB não persiste dados
<chromadb-não-persiste-dados>
```bash
# Verifique permissões
chmod -R 755 chroma_db/

# Ou recrie do zero
rm -rf chroma_db/
uv run python app.py  # Reindexará automaticamente
```

=== Interface não mostra todos os perfis
<interface-não-mostra-todos-os-perfis>
```bash
# Verifique se os 3 perfis estão carregados
uv run python check_profiles.py

# Deve mostrar:
# Perfis encontrados: ['dceuff', 'reitor', 'vicereitor']

# Limpe cache do navegador (Ctrl+Shift+R)
```

=== Memória insuficiente
<memória-insuficiente>
#strong[Opção 1: Use modelo menor]

```bash
uv run python app.py --generation-model qwen2.5:3b
```

#strong[Opção 2: Libere memória] - Feche outros aplicativos - Reinicie Ollama: `killall ollama && ollama serve`

#strong[Opção 3: Configure swap (Linux)]

```bash
sudo fallocate -l 8G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

=== Respostas lentas
<respostas-lentas>
+ #strong[Use modelo mais leve:]

  ```bash
  uv run python app.py --generation-model qwen2.5:7b
  ```

+ #strong[Reduza posts analisados:]

  - Análise de sentimento: max 20 posts
  - Busca semântica: max 10 posts

+ #strong[Verifique GPU:]

  ```bash
  # Se tiver NVIDIA GPU
  nvidia-smi
  # Ollama usa GPU automaticamente
  ```

=== Erro de parsing JSON (análise de sentimento)
<erro-de-parsing-json-análise-de-sentimento>
Às vezes o LLM retorna JSON malformado. O sistema tem fallback automático, mas você pode:

+ Usar modelo maior (qwen3:30b mais confiável que qwen2.5:3b)
+ Reduzir número de posts analisados
+ Tentar novamente (LLMs podem variar)

#horizontalrule

== 📊 Performance e Benchmarks
<performance-e-benchmarks>
=== Tempos Médios (Hardware: 16GB RAM, qwen3:30b)
<tempos-médios-hardware-16gb-ram-qwen330b>
#table(
  columns: 4,
  align: (auto,auto,auto,auto,),
  table.header([Operação], [Quantidade], [Tempo], [Cache],),
  table.hline(),
  [Indexação inicial], [2.413 posts], [\~8 min], [N/A],
  [Busca semântica], [10 resultados], [\~1-2s], [Warm],
  [Contagem de termo], [Toda base], [\~1-2s], [N/A],
  [Análise de sentimento], [20 posts], [\~8-15s], [N/A],
  [Estatísticas], [1 perfil], [\~0.5s], [N/A],
  [Síntese LLM], [1 resposta], [\~3-8s], [Warm],
)
=== Uso de Recursos
<uso-de-recursos>
#table(
  columns: 4,
  align: (auto,auto,auto,auto,),
  table.header([Componente], [RAM], [Disco], [GPU],),
  table.hline(),
  [ChromaDB], [\~200MB], [\~50MB], [Não],
  [mxbai-embed-large], [\~700MB], [669MB], [Opcional],
  [qwen3:30b], [\~18GB], [18GB], [Sim\*],
  [Gradio], [\~100MB], [-], [Não],
  [#strong[Total];], [#strong[\~19GB];], [#strong[\~19GB];], [#strong[Opcional];],
)
\*GPU acelera significativamente (3-5x mais rápido)

#horizontalrule

== 🤝 Contribuindo
<contribuindo>
Melhorias são bem-vindas! Áreas de interesse:

=== Funcionalidades
<funcionalidades-1>
- ☐ Análise temporal (trends ao longo do tempo)
- ☐ Exportação de relatórios (PDF, CSV)
- ☐ Visualizações (gráficos, word clouds)
- ☐ Suporte a mais redes sociais
- ☐ Sistema de cache inteligente
- ☐ Análise de imagens (multimodal)

=== Melhorias Técnicas
<melhorias-técnicas>
- ☐ Testes automatizados
- ☐ CI/CD pipeline
- ☐ Docker container
- ☐ Documentação em inglês
- ☐ Logs estruturados
- ☐ Monitoring e métricas

=== Como Contribuir
<como-contribuir>
+ Fork o repositório
+ Crie uma branch (`git checkout -b feature/MinhaFeature`)
+ Commit suas mudanças (`git commit -m 'Add: MinhaFeature'`)
+ Push para a branch (`git push origin feature/MinhaFeature`)
+ Abra um Pull Request

#horizontalrule

== 📄 Licença
<licença>
Este projeto é de código aberto para fins educacionais e institucionais.

#horizontalrule

== 🙏 Créditos
<créditos>
=== Tecnologias
<tecnologias>
- #strong[#link("https://ollama.com/")[Ollama];] - Runtime para LLMs locais
- #strong[#link("https://www.trychroma.com/")[ChromaDB];] - Banco de dados vetorial
- #strong[#link("https://gradio.app/")[Gradio];] - Framework de interface web
- #strong[#link("https://docs.astral.sh/uv/")[uv];] - Gerenciador de pacotes Python moderno

=== Modelos de IA
<modelos-de-ia>
- #strong[mxbai-embed-large] - Embeddings (mixedbread.ai)
- #strong[qwen3:30b / qwen2.5] - Modelos de linguagem (Alibaba Cloud)

=== Desenvolvimento
<desenvolvimento>
Desenvolvido para análise de comunicação institucional da #strong[Universidade Federal Fluminense (UFF)];.

#horizontalrule

== 📞 Suporte
<suporte>
- #strong[Issues:] Abra uma issue no repositório
- #strong[Documentação:] Consulte os arquivos `.md` na raiz
- #strong[Comunidade:] Compartilhe sua experiência e melhorias

#horizontalrule

#block[
#strong[#link(<-uff-instagram-analytics---sistema-rag-inteligente>)[⬆ Voltar ao topo];]

#horizontalrule

Feito com ❤️ para a comunidade UFF \
#emph[Versão 2.0 - Outubro 2025]

]




