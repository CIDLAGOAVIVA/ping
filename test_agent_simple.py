#!/usr/bin/env python3
"""
Script simples para testar o raciocínio do agente sem usar InstagramRAGApp.
Testa diretamente o RAGAgent._plan_action() para ver como o DeepSeek decide.
"""

import sys
sys.path.insert(0, '/home/marcus/projects/ping')

from agent_system import RAGAgent
from config import DEFAULT_PROVIDER, DEEPSEEK_MODEL
import json

print("=" * 80)
print("🧪 TESTE DE RACIOCÍNIO DO AGENTE RAG COM DEEPSEEK")
print("=" * 80)
print(f"\n📋 Configuração:")
print(f"  Provider: {DEFAULT_PROVIDER}")
print(f"  Modelo: {DEEPSEEK_MODEL}")

# Inicializa o agente
print(f"\n⏳ Inicializando RAGAgent...")
agent = RAGAgent(
    embedding_model="mxbai-embed-large",
    generation_model="qwen3:30b",
    planning_model="qwen3:30b"
)

# Casos de teste
test_cases = [
    ("Quais são os posts mais curtidos do reitor?", "🏆 MÉTRICA"),
    ("O que foi dito sobre Roberto Salles?", "📰 NOTÍCIAS"),
    ("Posts sobre greve", "🔍 CONTEÚDO"),
    ("Compare o engajamento entre perfis", "📊 COMPARAÇÃO"),
    ("Qual é a situação da educação no Brasil?", "🌐 WEB_SEARCH"),
]

print("\n" + "=" * 80)
print("TESTANDO RACIOCÍNIO DO AGENTE")
print("=" * 80)

for i, (query, label) in enumerate(test_cases, 1):
    print(f"\n{'─' * 80}")
    print(f"Teste {i}: {label}")
    print(f"Query: \"{query}\"")
    print(f"{'─' * 80}")
    
    try:
        print(f"\n⏳ DeepSeek analisando...")
        
        # Chama o método de planejamento
        actions = agent._plan_action(query)
        
        print(f"\n✅ DECISÃO DO AGENTE:")
        
        # Processa a resposta
        if isinstance(actions, list):
            if len(actions) > 0:
                first_action = actions[0]
                
                # Se for um erro
                if 'error' in first_action:
                    print(f"  ⚠️ Erro: {first_action.get('params', {}).get('message', 'Desconhecido')}")
                else:
                    # Mostra as ferramentas
                    print(f"  🔧 Ferramentas a usar:")
                    for j, action in enumerate(actions, 1):
                        tool = action.get('tool', 'unknown')
                        params = action.get('params', {})
                        print(f"\n    {j}. {tool}")
                        if params:
                            param_str = json.dumps(params, ensure_ascii=False, indent=8)
                            print(f"       {param_str}")
            else:
                print(f"  ❌ Nenhuma ação planejada")
        else:
            print(f"  Resposta: {actions}")
            
    except json.JSONDecodeError as e:
        print(f"  ❌ Erro ao parsear JSON: {str(e)[:100]}")
    except Exception as e:
        print(f"  ❌ Erro: {type(e).__name__}: {str(e)[:150]}")
        import traceback
        traceback.print_exc()

print("\n" + "=" * 80)
print("✅ TESTES CONCLUÍDOS")
print("=" * 80)
print("\n💡 O que observar:")
print("  ✓ Se DeepSeek escolheu as ferramentas certas")
print("  ✓ Se os parâmetros estão adequados")
print("  ✓ Se web_search aparece quando relevante")
print("  ✓ Se combina múltiplas ferramentas quando necessário")
