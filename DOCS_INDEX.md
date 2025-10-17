# 📚 Índice de Documentação

> Guia de navegação para toda a documentação do projeto UFF Instagram Analytics

## 🎯 Início Rápido

Se você é novo no projeto, comece por aqui:

1. **[README.md](README.md)** - **COMECE AQUI!** 📖
   - Documentação completa e consolidada
   - Todas as funcionalidades
   - Guia de instalação e uso
   - Exemplos práticos
   - Solução de problemas

2. **[QUICKSTART.md](QUICKSTART.md)** - Guia rápido ⚡
   - Instalação em 3 passos
   - Primeiros comandos
   - Testes básicos

## 📊 Documentação por Categoria

### 🏗️ Arquitetura e Design

| Documento | Conteúdo | Quando Ler |
|-----------|----------|------------|
| **[ARCHITECTURE.md](ARCHITECTURE.md)** | Arquitetura completa do sistema | Entender como tudo funciona |
| **[AGENT_VS_CLASSIC.md](AGENT_VS_CLASSIC.md)** | Comparação: Agente vs Sistema Clássico | Entender evolução do sistema |
| **[BALANCED_AGENT.md](BALANCED_AGENT.md)** | Como o agente equilibra ferramentas | Entender decisões do agente |
| **[SUMMARY_AGENT.md](SUMMARY_AGENT.md)** | Resumo do sistema de agente | Visão geral do agente |

### 🛠️ Ferramentas Específicas

| Documento | Ferramenta | Quando Ler |
|-----------|-----------|------------|
| **[TOOLS.md](TOOLS.md)** | Visão geral de todas as 9 ferramentas | Conhecer todas as ferramentas |
| **[SENTIMENT_ANALYSIS_TOOL.md](SENTIMENT_ANALYSIS_TOOL.md)** | Ferramenta #8: Análise de Sentimento (IA) | Usar análise de sentimento |
| **[TERM_COUNT_TOOL.md](TERM_COUNT_TOOL.md)** | Ferramenta #7: Contagem de Termos | Quantificar menções |

### 🌐 API e Integração

| Documento | Conteúdo | Quando Ler |
|-----------|----------|------------|
| **[API_QUICKSTART.md](API_QUICKSTART.md)** | Guia rápido da API REST | Integrar com a API |
| **[API_USAGE.md](API_USAGE.md)** | Exemplos detalhados de uso da API | Casos de uso avançados |
| **[API_SUMMARY.md](API_SUMMARY.md)** | Resumo das capacidades da API | Visão geral da API |

### 🎨 Interface e UX

| Documento | Conteúdo | Quando Ler |
|-----------|----------|------------|
| **[INTERFACE_IMPROVEMENTS.md](INTERFACE_IMPROVEMENTS.md)** | Melhorias na interface Gradio | Entender evolução da UI |
| **[AVATAR_SETUP.md](AVATAR_SETUP.md)** | Como configurar avatar do agente | Personalizar interface |

### 🔧 Manutenção e Fixes

| Documento | Conteúdo | Quando Ler |
|-----------|----------|------------|
| **[FIXES_SUMMARY.md](FIXES_SUMMARY.md)** | Resumo de correções recentes | Debugar problemas |
| **[SUMMARY.md](SUMMARY.md)** | Resumo geral do projeto | Visão geral rápida |

## 🗺️ Fluxo de Leitura Recomendado

### Para Iniciantes

```
1. README.md (visão completa)
   ↓
2. QUICKSTART.md (instalação)
   ↓
3. TOOLS.md (conhecer ferramentas)
   ↓
4. Usar a interface!
```

### Para Desenvolvedores

```
1. README.md (fundamentos)
   ↓
2. ARCHITECTURE.md (entender estrutura)
   ↓
3. TOOLS.md (API de ferramentas)
   ↓
4. API_QUICKSTART.md (integração)
   ↓
5. Código fonte
```

### Para Pesquisadores

```
1. README.md (capacidades)
   ↓
2. SENTIMENT_ANALYSIS_TOOL.md (análise qualitativa)
   ↓
3. TERM_COUNT_TOOL.md (análise quantitativa)
   ↓
4. BALANCED_AGENT.md (metodologia)
   ↓
5. Experimentar queries
```

### Para Usuários Finais

```
1. QUICKSTART.md (começar)
   ↓
2. Ver exemplos no README.md
   ↓
3. Usar interface Gradio
   ↓
4. Consultar README.md para dúvidas
```

## 📖 Documentação Consolidada vs Específica

### ✅ Use README.md para:
- Guia completo de instalação
- Todas as funcionalidades
- Exemplos de uso
- Solução de problemas comuns
- Referência rápida

### ✅ Use documentos específicos para:
- Detalhes técnicos profundos
- Casos de uso avançados
- Histórico de desenvolvimento
- Documentação de APIs
- Guias especializados

## 🔍 Busca Rápida

### Quero saber...

| Pergunta | Documento |
|----------|-----------|
| Como instalar? | README.md → Início Rápido |
| Quais ferramentas existem? | README.md → Ferramentas ou TOOLS.md |
| Como fazer análise de sentimento? | SENTIMENT_ANALYSIS_TOOL.md |
| Como contar menções? | TERM_COUNT_TOOL.md |
| Como usar a API? | API_QUICKSTART.md |
| Como o agente funciona? | BALANCED_AGENT.md |
| Qual modelo usar? | README.md → Configuração |
| Como resolver erro X? | README.md → Solução de Problemas |
| Arquitetura do sistema? | ARCHITECTURE.md |

## 📝 Mapa de Arquivos

```
docs/
├── 🌟 README.md                          # PRINCIPAL - Tudo em um lugar
├── ⚡ QUICKSTART.md                      # Início rápido
├── 📚 DOCS_INDEX.md                      # Este arquivo
│
├── 🏗️ ARQUITETURA
│   ├── ARCHITECTURE.md
│   ├── AGENT_VS_CLASSIC.md
│   ├── BALANCED_AGENT.md
│   └── SUMMARY_AGENT.md
│
├── 🛠️ FERRAMENTAS
│   ├── TOOLS.md                          # Todas as ferramentas
│   ├── SENTIMENT_ANALYSIS_TOOL.md        # Ferramenta #8
│   └── TERM_COUNT_TOOL.md                # Ferramenta #7
│
├── 🌐 API
│   ├── API_QUICKSTART.md
│   ├── API_USAGE.md
│   └── API_SUMMARY.md
│
├── 🎨 INTERFACE
│   ├── INTERFACE_IMPROVEMENTS.md
│   └── AVATAR_SETUP.md
│
└── 🔧 MANUTENÇÃO
    ├── FIXES_SUMMARY.md
    └── SUMMARY.md
```

## 🎓 Tutoriais por Caso de Uso

### Caso 1: "Quero apenas usar o sistema"
```
1. Leia: QUICKSTART.md
2. Instale conforme instruções
3. Abra interface: http://localhost:7860
4. Consulte exemplos no README.md
```

### Caso 2: "Quero integrar com minha aplicação"
```
1. Leia: README.md → API REST
2. Leia: API_QUICKSTART.md
3. Teste exemplos em API_USAGE.md
4. Implemente integração
```

### Caso 3: "Quero entender como funciona"
```
1. Leia: README.md → Arquitetura
2. Leia: ARCHITECTURE.md
3. Leia: BALANCED_AGENT.md
4. Explore código fonte
```

### Caso 4: "Quero fazer pesquisa"
```
1. Leia: README.md → Funcionalidades
2. Leia: SENTIMENT_ANALYSIS_TOOL.md
3. Leia: TERM_COUNT_TOOL.md
4. Use ferramentas para coleta de dados
5. Analise resultados
```

## 🔄 Documentação por Versão

| Versão | Data | Principais Mudanças | Documentos Afetados |
|--------|------|---------------------|---------------------|
| **2.0** | Out/2025 | Sistema de Agente + Análise Sentimento | Todos consolidados no README |
| 1.5 | Out/2025 | Contagem de termos | TERM_COUNT_TOOL.md |
| 1.0 | Out/2025 | Sistema RAG básico | Documentos originais |

## 📊 Estatísticas da Documentação

- **Total de arquivos .md:** 16
- **Documento principal:** README.md (1.200+ linhas)
- **Documentos técnicos:** 8
- **Guias de uso:** 5
- **Cobertura:** 100% das funcionalidades

## 🤝 Contribuindo para a Documentação

Se você quer melhorar a documentação:

1. **Pequenas correções:** Edite README.md diretamente
2. **Novos tutoriais:** Crie arquivo específico e adicione aqui
3. **Traduções:** Crie pasta `docs/lang/` com traduções
4. **Exemplos:** Adicione em README.md → Exemplos

## ⚡ Atalhos Rápidos

| Ação | Comando |
|------|---------|
| Ver toda documentação | `ls *.md` |
| Buscar em docs | `grep -r "termo" *.md` |
| Contar linhas | `wc -l *.md` |
| Ver última modificação | `ls -lt *.md` |

## 🎯 Próximos Passos

Depois de ler este índice:

1. ✅ Leia o [README.md](README.md) completo
2. ✅ Instale seguindo o [QUICKSTART.md](QUICKSTART.md)
3. ✅ Experimente a interface
4. ✅ Consulte documentos específicos conforme necessário

---

## 📞 Ajuda

- **Não encontrou o que procura?** Verifique o README.md primeiro
- **Dúvida técnica?** Consulte ARCHITECTURE.md
- **Problema de instalação?** Veja README.md → Solução de Problemas
- **Quer contribuir?** Leia README.md → Contribuindo

---

<div align="center">

**[⬆ Voltar ao topo](#-índice-de-documentação)**

*Mantenha este índice atualizado ao adicionar novos documentos!*

</div>
