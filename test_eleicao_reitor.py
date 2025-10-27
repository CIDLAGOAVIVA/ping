#!/usr/bin/env python3
"""
Script para testar a pergunta: "Quando será a próxima eleição para reitor da UFF?"
Este é um bom teste de web_search porque:
1. É sobre informação atualizada (2025)
2. Não está nos dados locais do Instagram
3. O agente precisa de contexto externo
"""

import sys
sys.path.insert(0, '/home/marcus/projects/ping')

from agent_system import RAGAgent
from config import DEFAULT_PROVIDER, DEEPSEEK_MODEL
import json

print("=" * 90)
print("🧪 TESTE: PERGUNTA SOBRE ELEIÇÃO PARA REITOR DA UFF")
print("=" * 90)
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

# Pergunta de teste
query = "Quando será a próxima eleição para reitor da UFF?"

print("\n" + "=" * 90)
print("ANALISANDO PERGUNTA")
print("=" * 90)
print(f"\nPergunta: \"{query}\"")
print(f"\n{'─' * 90}")

try:
    print(f"\n⏳ DeepSeek analisando a pergunta...")
    
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
                        for line in param_str.split('\n'):
                            print(f"       {line}")
        else:
            print(f"  ❌ Nenhuma ação planejada")
    else:
        print(f"  Resposta: {actions}")

    # Agora executa as ações
    print(f"\n{'─' * 90}")
    print(f"\n⏳ Executando as ferramentas...")
    
    if isinstance(actions, list) and len(actions) > 0:
        all_results = []
        for action in actions:
            tool = action.get('tool')
            params = action.get('params', {})
            
            if tool and tool != 'error':
                print(f"\n  ⚙️ Executando {tool}...")
                try:
                    results = agent._execute_action(action)
                    print(f"     ✓ Obteve {len(results) if isinstance(results, list) else 1} resultado(s)")
                    
                    # Mostra resumo dos resultados
                    if isinstance(results, list) and len(results) > 0:
                        for i, result in enumerate(results[:2], 1):  # Mostra apenas 2 primeiros
                            if isinstance(result, dict):
                                if 'document' in result:
                                    doc_preview = result['document'][:150] + "..." if len(str(result['document'])) > 150 else result['document']
                                    print(f"       {i}. {doc_preview}")
                                elif 'metadata' in result:
                                    print(f"       {i}. {str(result['metadata'])[:150]}...")
                    
                    all_results.extend(results if isinstance(results, list) else [results])
                except Exception as e:
                    print(f"     ❌ Erro: {str(e)[:100]}")
        
        # Agora sintetiza a resposta
        print(f"\n{'─' * 90}")
        print(f"\n⏳ Sintetizando resposta final com DeepSeek...")
        
        try:
            # Prepara os resultados no formato esperado: List[Tuple[str, List]]
            formatted_results = []
            for action in actions:
                tool = action.get('tool')
                if tool and tool != 'error':
                    # Encontra os resultados desta ferramenta
                    for result in all_results:
                        if isinstance(result, dict):
                            formatted_results.append((tool, [result]))
                        else:
                            formatted_results.append((tool, [{'document': str(result)}]))
            
            final_response = agent._synthesize_response(
                user_question=query,
                all_results=formatted_results
            )
            
            print(f"\n✅ RESPOSTA FINAL DO AGENTE:")
            print(f"\n{final_response}")
            
        except Exception as e:
            print(f"  ❌ Erro ao sintetizar: {str(e)[:200]}")
            import traceback
            traceback.print_exc()
            
except Exception as e:
    print(f"  ❌ Erro: {type(e).__name__}: {str(e)[:150]}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 90)
print("✅ TESTE CONCLUÍDO")
print("=" * 90)
print("\n💡 Observações:")
print("  • Se web_search foi usado, você verá resultados sobre eleições")
print("  • A resposta deve mencionar informações atualizadas (2025)")
print("  • O raciocínio deve explicar por que usou web_search")
