#!/usr/bin/env python3
"""
Script para testar o fluxo completo do app
"""
import sys
sys.path.insert(0, '/home/marcus/projects/ping')

from agent_system import RAGAgent

print("=" * 60)
print("TESTE DO FLUXO DE CHAT")
print("=" * 60)

agent = RAGAgent()

test_cases = [
    ("Posts sobre HUAP", None),
    ("Comparar perfis", None),
    ("Qual foi a última aparição do reitor?", "reitor"),
    ("Posts do DCE", "dceuff"),
]

for question, profile in test_cases:
    print(f"\n\n{'='*60}")
    print(f"❓ Pergunta: {question}")
    print(f"👤 Perfil: {profile or 'Nenhum (todos)'}")
    print(f"{'='*60}")
    
    try:
        response, posts = agent.query(question, profile_filter=profile)
        
        print(f"\n✅ RESPOSTA (primeiras 300 chars):")
        print(response[:300] + "..." if len(response) > 300 else response)
        
        print(f"\n📊 Posts recuperados: {len(posts)}")
        if posts:
            print(f"   Primeiro post profile: {posts[0].get('metadata', {}).get('profile', 'N/A')}")
        
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "=" * 60)
print("✓ TESTES CONCLUÍDOS!")
print("=" * 60)
