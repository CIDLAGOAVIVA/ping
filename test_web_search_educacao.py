#!/usr/bin/env python3
"""
Script para testar web_search com uma pergunta que terá resultados relevantes
"""

import sys
sys.path.insert(0, '/home/marcus/projects/ping')

from agent_system import RAGAgent
from config import DEFAULT_PROVIDER, DEEPSEEK_MODEL
import json

print("=" * 100)
print("🧪 TESTE COMPLETO: WEB SEARCH COM PERGUNTA SOBRE EDUCAÇÃO BRASILEIRA")
print("=" * 100)
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

# Pergunta que terá bons resultados na web
query = "Qual é a situação da educação superior no Brasil em 2025?"

print("\n" + "=" * 100)
print("TESTE COMPLETO COM WEB SEARCH - PERGUNTA SOBRE EDUCAÇÃO")
print("=" * 100)
print(f"\n❓ Pergunta: \"{query}\"")
print(f"\n{'─' * 100}")

try:
    print(f"\n⏳ ETAPA 1: DeepSeek analisando...")
    print(f"{'─' * 100}\n")
    
    # Chama o método de planejamento
    actions = agent._plan_action(query)
    
    # Processa a resposta
    if isinstance(actions, list):
        if len(actions) > 0:
            first_action = actions[0]
            
            if 'error' not in first_action:
                print(f"✅ RACIOCÍNIO DO AGENTE:")
                print(f"\n🔧 Ferramentas a usar:")
                for j, action in enumerate(actions, 1):
                    tool = action.get('tool', 'unknown')
                    params = action.get('params', {})
                    print(f"\n    {j}. {tool}")
                    if params:
                        print(f"       Query: \"{params.get('query', '')}\"" if tool == 'web_search' else f"       Parâmetros: {json.dumps(params, ensure_ascii=False, indent=10)}")

    # Executa as ações
    print(f"\n{'─' * 100}")
    print(f"\n⏳ ETAPA 2: Executando as ferramentas...")
    print(f"{'─' * 100}\n")
    
    all_results = []
    for i, action in enumerate(actions, 1):
        tool = action.get('tool')
        params = action.get('params', {})
        
        if tool and tool != 'error':
            print(f"\n  ⚙️ [{i}] Executando {tool}...")
            if tool == 'web_search':
                print(f"      Query: \"{params.get('query', '')}\"")
            
            try:
                results = agent._execute_action(action)
                print(f"      ✓ Obteve {len(results) if isinstance(results, list) else 1} resultado(s)\n")
                
                # Mostra os resultados
                if isinstance(results, list) and len(results) > 0:
                    for idx, result in enumerate(results, 1):
                        if isinstance(result, dict):
                            if 'document' in result:
                                print(f"      📄 Resultado {idx}:")
                                doc = result['document']
                                # Trunca se muito grande
                                if len(str(doc)) > 250:
                                    print(f"          {str(doc)[:250]}...")
                                else:
                                    print(f"          {doc}")
                                
                                # Mostra metadata se tiver
                                if 'metadata' in result and result['metadata']:
                                    meta = result['metadata']
                                    if 'source' in meta:
                                        print(f"          🔗 Fonte: {meta['source']}")
                                    if 'date' in meta and meta['date']:
                                        print(f"          📅 Data: {meta['date']}")
                                print()
                            elif 'metadata' in result:
                                print(f"      📊 Resultado {idx}: {str(result['metadata'])[:200]}...")
                                print()
                
                all_results.extend(results if isinstance(results, list) else [results])
            except Exception as e:
                print(f"      ❌ Erro: {str(e)[:100]}\n")
    
    # Sintetiza a resposta
    print(f"{'─' * 100}")
    print(f"\n⏳ ETAPA 3: DeepSeek sintetizando a resposta...")
    print(f"{'─' * 100}\n")
    
    try:
        # Prepara os resultados no formato esperado
        formatted_results = []
        for i, action in enumerate(actions):
            tool = action.get('tool')
            if tool and tool != 'error':
                # Coleta resultados desta ferramenta
                for result in all_results:
                    if isinstance(result, dict):
                        formatted_results.append((tool, [result]))
                    else:
                        formatted_results.append((tool, [{'document': str(result)}]))
        
        final_response = agent._synthesize_response(
            user_question=query,
            all_results=formatted_results
        )
        
        print(f"✅ RESPOSTA FINAL DO AGENTE:\n")
        print(f"{final_response}")
        
    except Exception as e:
        print(f"❌ Erro ao sintetizar: {str(e)[:200]}")
            
except Exception as e:
    print(f"❌ Erro geral: {type(e).__name__}: {str(e)[:150]}")

print(f"\n{'=' * 100}")
print("✅ TESTE CONCLUÍDO")
print("=" * 100)
