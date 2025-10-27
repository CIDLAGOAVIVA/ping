#!/usr/bin/env python3
"""
Script para testar queries específicas
"""
import sys
sys.path.insert(0, '/home/marcus/projects/ping')

from embedding_manager import EmbeddingManager
import json

print("=" * 60)
print("TESTE DE QUERIES - EMBEDDING MANAGER")
print("=" * 60)

em = EmbeddingManager()

test_queries = [
    "Posts sobre HUAP",
    "Comparar perfis",
    "HUAP hospital universitário atendimento saúde",
    "teste",
    "reitor",
]

for query in test_queries:
    print(f"\n\n📍 Query: '{query}'")
    print("-" * 60)
    
    try:
        results = em.search(query=query, n_results=5)
        
        print(f"IDs: {results.get('ids', [[]])}")
        print(f"Número de resultados: {len(results.get('ids', [[]])[0]) if results.get('ids') else 0}")
        
        if results.get('ids') and len(results['ids'][0]) > 0:
            for i, doc_id in enumerate(results['ids'][0]):
                metadata = results['metadatas'][0][i]
                document = results['documents'][0][i][:100]
                distance = results.get('distances', [[]])[0][i] if results.get('distances') else None
                
                print(f"\n  Resultado {i+1}:")
                print(f"    ID: {doc_id}")
                print(f"    Profile: {metadata.get('profile', 'N/A')}")
                print(f"    Type: {metadata.get('content_type', 'N/A')}")
                print(f"    Distance: {distance}")
                print(f"    Document (primeiros 100 chars): {document}...")
        else:
            print("  ❌ Nenhum resultado encontrado!")
            
    except Exception as e:
        print(f"  ❌ ERRO: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "=" * 60)
