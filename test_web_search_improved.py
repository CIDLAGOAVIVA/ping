#!/usr/bin/env python3
"""
Teste melhorado de web_search
"""

from query_tools import QueryTools
from embedding_manager import EmbeddingManager

# Inicializa embedding_manager
print("📊 Inicializando EmbeddingManager...")
em = EmbeddingManager(embedding_model="mxbai-embed-large")

# Inicializa ferramentas
print("🔧 Inicializando QueryTools...")
tools = QueryTools(embedding_manager=em)

# Testa web_search com a pergunta problemática
print("\n" + "="*70)
print("🧪 TESTE: web_search - 'situação educação brasil'")
print("="*70 + "\n")

results = tools.web_search(
    query="situação educação brasil",
    limit=5
)

print(f"\n📊 Resultados retornados: {len(results)}")
print("-" * 70)

for i, result in enumerate(results, 1):
    print(f"\n{i}. {result['title']}")
    print(f"   🔗 {result['source']}")
    print(f"   📝 {result['body'][:200]}...")
    print(f"   📅 {result['date'] or 'Data não disponível'}")

print("\n" + "="*70)
print("✅ Teste concluído!")
print("="*70)
