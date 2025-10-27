#!/usr/bin/env python3
"""
Teste com variações de pergunta para triggar web_search corretamente
"""

import sys
sys.path.insert(0, '/home/marcus/projects/ping')

from agent_system import RAGAgent
from config import DEFAULT_PROVIDER
import json

print("=" * 90)
print("🧪 TESTE: VARIAÇÕES DE PERGUNTA SOBRE ELEIÇÃO")
print("=" * 90)

agent = RAGAgent(
    embedding_model="mxbai-embed-large",
    generation_model="qwen3:30b",
    planning_model="qwen3:30b"
)

# Variações da pergunta que devem triggar web_search
questions = [
    "Quando será a próxima eleição para reitor da UFF?",
    "Qual é o calendário eleitoral para reitor da UFF em 2025?",
    "Há notícias recentes sobre eleição de reitor na UFF?",
    "Como está o processo eleitoral para a próxima gestão da UFF?",
]

for query in questions:
    print(f"\n{'─' * 90}")
    print(f"❓ Pergunta: \"{query}\"")
    print(f"{'─' * 90}")
    
    try:
        actions = agent._plan_action(query)
        
        if isinstance(actions, list) and len(actions) > 0:
            tools_used = [a.get('tool') for a in actions]
            print(f"🔧 Ferramentas: {', '.join(tools_used)}")
            
            # Marca se usou web_search
            if 'web_search' in tools_used:
                print(f"✅ WEB_SEARCH ATIVADO!")
                for a in actions:
                    if a.get('tool') == 'web_search':
                        print(f"   Query: {a.get('params', {}).get('query', '')}")
            else:
                print(f"⚠️ Não usou web_search")
                
    except Exception as e:
        print(f"❌ Erro: {str(e)[:100]}")

print(f"\n{'=' * 90}")
