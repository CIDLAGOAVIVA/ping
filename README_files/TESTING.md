# 🧪 Testes de Homologação do Sistema RAG

Este diretório contém scripts para testar o sistema RAG com diversos cenários, incluindo casos de borda e situações não planejadas.

## 📋 Scripts Disponíveis

### 1. `test_homologacao.py` - Teste Completo
**Teste completo e abrangente com 30+ cenários**

```bash
uv run python test_homologacao.py
```

**Categorias testadas:**
- ✅ **Básico**: Perguntas simples que devem funcionar
  - Identidade (quem é o reitor?)
  - Busca simples (posts sobre HUAP)
  - Rankings (posts mais curtidos)

- ⚠️ **Ambíguas**: Perguntas vagas
  - Temporal ("o que aconteceu recentemente?")
  - Vagas ("me conte sobre a universidade")
  - Com pronomes ("o que ele postou?")

- ❌ **Incorretas**: Informações erradas
  - Nomes que não existem
  - Perfis inexistentes
  - Datas impossíveis
  - Ex-reitor confundido com atual

- 🎯 **Complexas**: Múltiplos filtros
  - Combinação de perfil + tema + métrica
  - Comparações entre perfis
  - Temporal + semântica
  - Agregações e médias

- 🚨 **Edge Cases**: Casos extremos
  - Pergunta vazia
  - Só emojis
  - Textos muito longos
  - Caracteres especiais

- 🚫 **Fora de Escopo**: Perguntas inadequadas
  - Matemática
  - Outras universidades
  - Política geral

- 🔄 **Negação**: Perguntas com "não"
  - "Posts que NÃO falam sobre..."
  - "Posts com menos de X curtidas"

- 🤔 **Meta**: Sobre o próprio sistema
  - "Quantos posts você tem?"
  - "O que você pode fazer?"

- 🔒 **Sensíveis**: Requerem neutralidade
  - Opiniões
  - Polêmicas

**Saída:**
- Relatório detalhado no terminal
- Arquivo JSON com todos os resultados (`homologacao_relatorio_YYYYMMDD_HHMMSS.json`)

### 2. `test_quick.py` - Testes Rápidos
**Testes rápidos de cenários críticos (9 testes)**

```bash
uv run python test_quick.py
```

Testa apenas os casos mais problemáticos:
- Pergunta vazia
- Pronomes ambíguos
- Pessoas/perfis inexistentes
- Ex-reitor vs reitor atual
- Perguntas fora de escopo
- Emojis
- Negação

## 📊 Interpretando os Resultados

### Status dos Testes
- ✅ **PASSOU**: Sistema respondeu adequadamente
- ⚠️ **ATENÇÃO**: Funcionou mas com ressalvas
- ❌ **FALHOU**: Não respondeu como esperado

### Métricas Importantes
- **Taxa de Sucesso**: % de testes que passaram
- **Tempo de Execução**: Performance das queries
- **Posts Recuperados**: Quantidade e relevância

### Análise por Categoria
```
✅ Básico: 100% (4/4)          → Sistema funciona bem no uso normal
⚠️ Ambíguas: 66% (2/3)         → Pode melhorar clarificação
❌ Incorretas: 50% (2/4)       → Precisa validar inputs melhor
✅ Complexas: 100% (4/4)       → Lida bem com múltiplos filtros
❌ Edge Cases: 25% (1/4)       → Vulnerável a entradas malformadas
⚠️ Fora de Escopo: 66% (2/3)  → Geralmente reconhece limitações
```

## 🔍 Exemplos de Cenários

### ✅ Cenário que DEVE funcionar
```python
{
    "pergunta": "Quais foram os 5 posts mais curtidos?",
    "esperado": "Lista com 5 posts ordenados",
    "sucesso_esperado": True
}
```

### ❌ Cenário que DEVE falhar/avisar
```python
{
    "pergunta": "Roberto Salles postou algo essa semana?",
    "esperado": "Deve esclarecer que é ex-reitor (2009-2018)",
    "sucesso_esperado": False  # É uma limitação esperada
}
```

## 🛠️ Adicionando Novos Testes

Edite `test_homologacao.py` e adicione em `cenarios_teste()`:

```python
{
    "categoria": "Nova Categoria - Tipo",
    "pergunta": "Sua pergunta aqui",
    "esperado": "O que espera como resultado",
    "perfil_filtro": None,  # ou "reitor", "dceuff", etc.
    "sucesso_esperado": True  # ou False
}
```

## 📈 Melhorias Sugeridas Baseadas nos Testes

Com base nos resultados da homologação, você pode:

1. **Adicionar validação de entrada**
   - Rejeitar perguntas vazias
   - Sanitizar caracteres especiais

2. **Melhorar prompts para casos ambíguos**
   - Pedir esclarecimento quando necessário
   - Assumir contexto de forma explícita

3. **Adicionar mensagens de erro amigáveis**
   - "Não encontrei o perfil @xyz. Perfis disponíveis: ..."
   - "Roberto Salles foi reitor de 2009-2018. O atual reitor é..."

4. **Implementar guard rails**
   - Detectar perguntas fora de escopo
   - Limitar tamanho de entrada
   - Validar datas

## 🎯 Uso Recomendado

### Durante Desenvolvimento
```bash
# Teste rápido após mudanças
uv run python test_quick.py
```

### Antes de Deploy
```bash
# Homologação completa
uv run python test_homologacao.py
```

### CI/CD
Adicione ao pipeline:
```bash
uv run python test_homologacao.py --ci-mode
# (implementar modo CI com exit codes)
```

## 📝 Formato do Relatório JSON

```json
{
  "timestamp": "20250426_143022",
  "resumo": {
    "total": 30,
    "executados": 28,
    "erros": 2,
    "passou": 24,
    "taxa_sucesso": 80.0
  },
  "por_categoria": {
    "Básico": {"total": 4, "passou": 4},
    "Ambígua": {"total": 3, "passou": 2}
  },
  "resultados_detalhados": [
    {
      "categoria": "Básico - Identidade",
      "pergunta": "Quem é o reitor?",
      "resposta": "...",
      "num_posts": 5,
      "tempo_execucao": 3.2,
      "avaliacao": {
        "passou": true,
        "observacoes": ["✅ Retornou resultados..."]
      }
    }
  ]
}
```

## 🐛 Reportando Problemas

Se um teste falhar inesperadamente:

1. Verifique o arquivo JSON de relatório
2. Analise a resposta gerada vs. esperada
3. Considere se é bug ou limitação esperada
4. Ajuste prompts ou adicione validação

## 📚 Recursos Adicionais

- `agent_system.py` - Implementação do agente
- `query_tools.py` - Ferramentas de consulta
- `ARCHITECTURE.md` - Arquitetura do sistema
