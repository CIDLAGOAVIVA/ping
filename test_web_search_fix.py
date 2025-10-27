#!/usr/bin/env python3
"""
Teste para verificar se web_search agora funciona na interface
após a correção do KeyError: 'likesCount'
"""

from agent_system import RAGAgent

# Inicializa agente
print("🤖 Iniciando agente...")
agent = RAGAgent(
    embedding_model="mxbai-embed-large",
    generation_model="qwen3:30b",
    planning_model="qwen3:30b"
)

# Testa pergunta que dava erro
print("\n" + "="*60)
print("🧪 Testando: 'qual é a situação da educação no brasil'")
print("="*60)

response, posts = agent.query(
    question="qual é a situação da educação no brasil",
    profile_filter=None
)

print("\n📝 RESPOSTA DO AGENTE:")
print("-" * 60)
print(response)

print("\n\n📌 POSTS/RESULTADOS RETORNADOS:")
print("-" * 60)
if posts:
    print(f"Total de resultados: {len(posts)}")
    for i, post in enumerate(posts, 1):
        metadata = post.get('metadata', {})
        content = post.get('document', '')[:100]
        profile = metadata.get('profile', 'desconhecido')
        print(f"\n{i}. Profile: {profile}")
        print(f"   Metadata keys: {list(metadata.keys())}")
        print(f"   Content preview: {content}...")
        
        # Verifica se é web_search
        if profile == 'web_search':
            print(f"   ✅ É web_search!")
            print(f"   Title: {metadata.get('title', 'N/A')}")
            print(f"   Source: {metadata.get('source', 'N/A')}")
            print(f"   Date: {metadata.get('date', 'N/A')}")
        else:
            print(f"   ❌ É post normal do Instagram")
else:
    print("Nenhum resultado retornado!")

print("\n\n✅ Teste concluído! Se chegou aqui sem erros, a correção funcionou!")
