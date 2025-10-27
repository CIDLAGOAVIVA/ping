#!/usr/bin/env python3
"""
Script para testar o raciocínio do agente e suas decisões de ferramentas.
Mostra exatamente o que o LLM (DeepSeek) decidiu fazer.
"""

import sys
sys.path.insert(0, '/home/marcus/projects/ping')

from agent_system import InstagramRAGApp
from config import DEFAULT_PROVIDER, DEEPSEEK_MODEL
import json

print("=" * 80)
print("🧪 TESTE DE RACIOCÍNIO DO AGENTE RAG")
print("=" * 80)
print(f"\n📋 Configuração:")
print(f"  Provider: {DEFAULT_PROVIDER}")
print(f"  Modelo: {DEEPSEEK_MODEL}")

# Inicializa o agente
app = InstagramRAGApp(
    embedding_model="mxbai-embed-large",
    generation_model="qwen3:30b",
    use_agent=True
)

# Casos de teste
test_cases = [
    {
        "query": "Quais são os posts mais curtidos do reitor?",
        "description": "🏆 MÉTRICA: Top posts por curtidas",
        "expected_tool": "get_top_posts_by_likes"
    },
    {
        "query": "O que foi dito sobre Roberto Salles?",
        "description": "📰 NOTÍCIAS: Ex-reitor histórico",
        "expected_tool": "search_news_by_person"
    },
    {
        "query": "Posts sobre greve na última semana",
        "description": "🔍 CONTEÚDO: Busca semântica temporal",
        "expected_tool": "semantic_search"
    },
    {
        "query": "Compare o engajamento entre reitor e DCE",
        "description": "📊 COMPARAÇÃO: Estatísticas entre perfis",
        "expected_tool": "compare_profiles"
    },
    {
        "query": "Quantos posts mencionam educação?",
        "description": "🔢 QUANTIFICAÇÃO: Contagem de termos",
        "expected_tool": "count_term_occurrences"
    },
    {
        "query": "Qual é a situação da educação no Brasil em 2025?",
        "description": "🌐 WEB_SEARCH: Contexto externo atualizado",
        "expected_tool": "web_search"
    },
    {
        "query": "Como está a economia nacional? E o DCE falou sobre isso?",
        "description": "🔗 COMBINADO: Web search + semantic search",
        "expected_tool": "web_search"  # Deve combinar ambas
    },
    {
        "query": "Posts do reitor que tiveram mais engajamento",
        "description": "🎯 COMBINADO: Conteúdo + métrica",
        "expected_tool": "semantic_search"  # Combina com get_posts_by_engagement
    }
]

print("\n" + "=" * 80)
print("TESTANDO RACIOCÍNIO DO AGENTE")
print("=" * 80)

for i, test in enumerate(test_cases, 1):
    print(f"\n{'─' * 80}")
    print(f"Teste {i}: {test['description']}")
    print(f"Query: \"{test['query']}\"")
    print(f"Esperado: {test['expected_tool']}")
    print(f"{'─' * 80}")
    
    try:
        # Obtém o planejamento do agente (sem executar as ferramentas ainda)
        actions = app._plan_action(test['query'])
        
        print(f"\n✅ RACIOCÍNIO DO AGENTE:")
        if isinstance(actions, list) and len(actions) > 0:
            first_action = actions[0]
            
            if 'error' in first_action:
                print(f"  ⚠️ Erro: {first_action.get('params', {}).get('message', 'Desconhecido')}")
            else:
                # Tenta extrair o raciocínio (se disponível no JSON)
                if isinstance(first_action, dict) and 'reasoning' in first_action:
                    print(f"  💭 Raciocínio: {first_action['reasoning']}")
                
                print(f"\n  🔧 Ferramentas a usar:")
                
                # Se actions for uma lista de dicts com 'tool' e 'params'
                if isinstance(actions, list):
                    for j, action in enumerate(actions, 1):
                        if 'tool' in action and 'params' in action:
                            tool = action['tool']
                            params = action['params']
                            print(f"    {j}. {tool}")
                            print(f"       Parâmetros: {json.dumps(params, ensure_ascii=False, indent=10)}")
                        elif 'actions' in action:
                            # Actions retorna um dict com 'reasoning' e 'actions'
                            for sub_action in action['actions']:
                                tool = sub_action.get('tool', 'unknown')
                                params = sub_action.get('params', {})
                                print(f"    {j}. {tool}")
                                print(f"       Parâmetros: {json.dumps(params, ensure_ascii=False, indent=10)}")
                                j += 1
                else:
                    print(f"  Resposta: {actions}")
                
                # Verifica se acertou a ferramenta esperada
                tools_used = []
                if isinstance(actions, list):
                    for action in actions:
                        if 'tool' in action:
                            tools_used.append(action['tool'])
                        elif isinstance(action, dict) and 'actions' in action:
                            for sub_action in action['actions']:
                                tools_used.append(sub_action.get('tool'))
                
                if test['expected_tool'] in tools_used:
                    print(f"\n  ✅ CORRETO! Usou {test['expected_tool']}")
                elif len(tools_used) > 0:
                    print(f"\n  ⚠️ Esperado: {test['expected_tool']}")
                    print(f"     Usado: {', '.join(tools_used)}")
                else:
                    print(f"\n  ❌ Nenhuma ferramenta foi planejada")
        else:
            print(f"  ❌ Nenhuma ação retornada")
            
    except json.JSONDecodeError as e:
        print(f"  ❌ Erro ao parsear JSON: {e}")
        print(f"     Resposta bruta: {str(e)[:200]}")
    except Exception as e:
        print(f"  ❌ Erro: {type(e).__name__}: {str(e)[:200]}")

print("\n" + "=" * 80)
print("✅ TESTES CONCLUÍDOS")
print("=" * 80)
print("\n💡 Dicas:")
print("  • Se web_search foi usado corretamente, você verá a ferramenta listada")
print("  • DeepSeek (modelo melhor) deve fazer escolhas mais inteligentes")
print("  • Procure por padrões nas decisões do agente")
