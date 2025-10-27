#!/usr/bin/env python3
"""
Script para testar status do ChromaDB e RAG System
"""

import sys
sys.path.insert(0, '/home/marcus/projects/ping')

print("=" * 60)
print("TESTE DO SISTEMA PING - UFF ANALYTICS")
print("=" * 60)

# Test 1: Ollama
print("\n[1] Testando Ollama...")
try:
    import ollama
    response = ollama.list()
    print("✓ Ollama está rodando")
    print(f"  Modelos disponíveis: {len(response.models)} modelo(s)")
except Exception as e:
    print(f"✗ Erro com Ollama: {e}")
    sys.exit(1)

# Test 2: ChromaDB
print("\n[2] Testando ChromaDB...")
try:
    import chromadb
    client = chromadb.PersistentClient(path='./chroma_db')
    collection = client.get_collection('instagram_posts')
    count = collection.count()
    print(f"✓ ChromaDB está OK")
    print(f"  Documentos indexados: {count}")
    
    if count == 0:
        print("  ⚠️  AVISO: Nenhum documento indexado! Precisa reindexar.")
    else:
        # Testa busca simples
        print("\n  Testando busca...")
        try:
            test_embedding = ollama.embeddings(
                model="mxbai-embed-large",
                prompt="teste"
            )['embedding']
            
            results = collection.query(
                query_embeddings=[test_embedding],
                n_results=2
            )
            
            if results['ids'] and len(results['ids'][0]) > 0:
                print(f"  ✓ Busca funcionando - encontrados {len(results['ids'][0])} resultados")
            else:
                print(f"  ⚠️  Busca não retornou resultados")
        except Exception as search_error:
            print(f"  ✗ Erro na busca: {search_error}")
            
except Exception as e:
    print(f"✗ Erro com ChromaDB: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: RAG System
print("\n[3] Testando RAG System...")
try:
    from rag_system import RAGSystem
    rag = RAGSystem()
    print("✓ RAG System inicializado com sucesso")
except Exception as e:
    print(f"✗ Erro ao inicializar RAG System: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Agent System
print("\n[4] Testando Agent System...")
try:
    from agent_system import RAGAgent
    agent = RAGAgent()
    print("✓ Agent System inicializado com sucesso")
except Exception as e:
    print(f"✗ Erro ao inicializar Agent System: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("✓ TODOS OS TESTES PASSARAM!")
print("=" * 60)
