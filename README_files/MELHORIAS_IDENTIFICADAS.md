# 🔍 Melhorias Identificadas - Testes de Homologação

**Data:** 26/10/2025  
**Status:** Análise após testes iniciais

## ✅ Pontos Positivos

1. **Pergunta Vazia** ✅
   - Sistema rejeita adequadamente
   - Resposta: "Não consegui determinar como responder sua pergunta"

2. **Pergunta Fora de Escopo (matemática)** ✅
   - Sistema reconhece que não deve responder
   - Não tenta forçar busca semântica

3. **Pergunta sobre Reitor Atual** ✅
   - Após correções, funciona perfeitamente
   - Identifica Antonio Claudio Nobrega

## ⚠️ Pontos de Atenção

### 1. Ex-reitor vs Reitor Atual ⚠️

**Problema:**
```
Pergunta: "Roberto Salles postou algo essa semana?"
Resposta: Buscou em notícias antigas (2014) mas não esclareceu que ele é EX-reitor
```

**O que aconteceu:**
- Sistema buscou corretamente em notícias históricas ✅
- Mas não esclareceu explicitamente que Roberto Salles foi reitor de 2009-2018 ❌
- Usuário pode ficar confuso sobre por que não há posts recentes

**Solução sugerida:**
Adicionar no prompt de síntese uma regra específica:
```
Se a pergunta mencionar "Roberto Salles" ou "Roberto Sales":
- SEMPRE esclarecer que foi reitor de 2009-2018
- Explicar que posts recentes são do reitor atual (Antonio Claudio Nobrega)
- Indicar que informações sobre ele estão em notícias históricas
```

### 2. Perfil Inexistente ⚠️

**Problema:**
```
Pergunta: "Posts do @naoexisto"
Resposta: Tentou busca semântica com termo "naoexisto"
```

**O que aconteceu:**
- Sistema não validou se perfil existe antes de buscar
- Fez busca semântica genérica
- Resposta correta ("não encontrado") mas processo ineficiente

**Solução sugerida:**
```python
def validar_perfil(profile: str) -> bool:
    """Valida se perfil existe antes de buscar."""
    perfis_validos = ['reitor', 'vicereitor', 'dceuff']
    
    # Remove @ se houver
    profile_clean = profile.replace('@', '').lower()
    
    if profile_clean not in perfis_validos:
        return False
    return True

# No planejamento, adicionar:
"Se a pergunta mencionar @perfil, validar se perfil existe nos dados.
Perfis disponíveis: @reitor, @vicereitor, @dceuff
Se perfil não existe, retornar erro específico ao invés de buscar."
```

### 3. Tempo de Resposta Alto ⚠️

**Observação:**
- Pergunta simples (vazia): 6s ✅
- Pergunta complexa (ex-reitor): 24s ⚠️
- Pergunta média (perfil inexistente): 19s ⚠️

**Causas possíveis:**
- Modelo grande (qwen3:30b)
- Múltiplas chamadas ao LLM (planejamento + síntese)
- Busca semântica pesada

**Soluções:**
1. **Curto prazo:** Cache de respostas comuns
2. **Médio prazo:** Modelo mais rápido para planejamento
3. **Longo prazo:** Paralelização de buscas

## 🔧 Implementações Recomendadas

### Alta Prioridade

1. **Validação de Perfil**
   ```python
   # Adicionar em agent_system.py
   PERFIS_VALIDOS = ['reitor', 'vicereitor', 'dceuff']
   
   def validar_perfil(profile: str) -> tuple[bool, str]:
       if not profile:
           return True, ""
       
       profile_clean = profile.replace('@', '').lower()
       if profile_clean not in PERFIS_VALIDOS:
           return False, f"Perfil @{profile_clean} não encontrado. Perfis disponíveis: {', '.join(['@' + p for p in PERFIS_VALIDOS])}"
       
       return True, profile_clean
   ```

2. **Esclarecimento sobre Ex-reitor**
   ```python
   # No prompt de síntese, adicionar:
   CONTEXTO_REITORES = """
   IMPORTANTE: Se a pergunta mencionar Roberto Salles/Sales:
   - Foi reitor da UFF de 2009 a 2018
   - NÃO tem posts no Instagram (apenas notícias históricas)
   - Reitor atual (2023-presente): Antonio Claudio Nobrega
   - SEMPRE esclarecer isso na resposta
   """
   ```

### Média Prioridade

3. **Cache de Perguntas Comuns**
   ```python
   RESPOSTAS_CACHE = {
       "quem é o reitor": "Antonio Claudio Nobrega é o atual reitor...",
       "quantos posts": "O sistema tem X posts indexados...",
   }
   ```

4. **Detecção de Perguntas Fora de Escopo**
   ```python
   PADROES_FORA_ESCOPO = [
       r'\d+\s*[\+\-\*/]\s*\d+',  # Matemática
       r'quem é o reitor da (USP|UFRJ|UERJ)',  # Outras universidades
       r'(quem vai ganhar|resultado das eleições)',  # Política
   ]
   ```

### Baixa Prioridade

5. **Otimização de Performance**
   - Usar modelo menor para planejamento (qwen2.5:3b)
   - Paralelizar buscas independentes
   - Implementar timeout

6. **Logs e Métricas**
   ```python
   # Logging estruturado
   log_query = {
       'timestamp': datetime.now(),
       'question': question,
       'planning_time': t1 - t0,
       'execution_time': t2 - t1,
       'synthesis_time': t3 - t2,
       'total_time': t3 - t0,
       'num_posts': len(posts),
       'tools_used': [a['tool'] for a in actions]
   }
   ```

## 📊 Próximos Passos

1. [ ] Implementar validação de perfil
2. [ ] Melhorar esclarecimento sobre ex-reitor
3. [ ] Adicionar testes unitários para validações
4. [ ] Executar homologação completa (30+ testes)
5. [ ] Analisar relatório JSON gerado
6. [ ] Priorizar melhorias baseadas em impacto x esforço
7. [ ] Implementar top 3 melhorias
8. [ ] Re-executar testes de homologação
9. [ ] Documentar melhorias no CHANGELOG

## 🎯 Métricas de Sucesso

**Antes:**
- Taxa de sucesso: ~50% (estimado baseado em demo)
- Tempo médio: 15-20s
- Respostas ambíguas: Frequentes

**Meta após melhorias:**
- Taxa de sucesso: >80%
- Tempo médio: <10s
- Respostas ambíguas: <10%

## 📝 Notas Adicionais

- Sistema já funciona bem para perguntas bem formadas
- Principais problemas estão em edge cases e validações
- Arquitetura é sólida, apenas precisa de refinamentos
- Testes automatizados são essenciais para manter qualidade

---

**Última atualização:** 26/10/2025  
**Responsável:** Sistema de Homologação Automatizado
