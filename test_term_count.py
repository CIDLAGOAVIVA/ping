#!/usr/bin/env python3
"""
Script de teste para a nova ferramenta count_term_occurrences.
"""

from embedding_manager import EmbeddingManager
from query_tools import QueryTools

def test_term_count():
    """Testa a contagem de termos."""
    print("=== Testando count_term_occurrences ===\n")
    
    # Inicializa
    em = EmbeddingManager()
    tools = QueryTools(em)
    
    # Teste 1: Termo genérico em todos os perfis
    print("📊 Teste 1: Quantos posts mencionam 'greve'?")
    result = tools.count_term_occurrences(term="greve")
    print(f"✓ Encontrados: {result['count']} posts de {result['total_posts']} ({result['percentage']}%)")
    print(f"  Perfil: {result['profile']}\n")
    
    # Teste 2: Termo específico em um perfil
    print("📊 Teste 2: Quantos posts do DCE mencionam 'assembleia'?")
    result = tools.count_term_occurrences(term="assembleia", profile="dceuff")
    print(f"✓ Encontrados: {result['count']} posts de {result['total_posts']} ({result['percentage']}%)")
    print(f"  Perfil: {result['profile']}\n")
    
    # Teste 3: Termo que deve aparecer pouco
    print("📊 Teste 3: Quantos posts mencionam 'HUAP'?")
    result = tools.count_term_occurrences(term="HUAP")
    print(f"✓ Encontrados: {result['count']} posts de {result['total_posts']} ({result['percentage']}%)")
    if result['matching_posts']:
        print(f"  Exemplo de post: @{result['matching_posts'][0]['metadata']['profile']}")
        print(f"  URL: {result['matching_posts'][0]['metadata']['url']}\n")
    
    # Teste 4: Case sensitive
    print("📊 Teste 4: 'UFF' vs 'uff' (case sensitive)")
    result_sensitive = tools.count_term_occurrences(term="UFF", case_sensitive=True)
    result_insensitive = tools.count_term_occurrences(term="UFF", case_sensitive=False)
    print(f"✓ Case sensitive: {result_sensitive['count']} posts")
    print(f"✓ Case insensitive: {result_insensitive['count']} posts\n")
    
    # Teste 5: Termo do reitor
    print("📊 Teste 5: Quantos posts do reitor mencionam 'universidade'?")
    result = tools.count_term_occurrences(term="universidade", profile="reitor")
    print(f"✓ Encontrados: {result['count']} posts de {result['total_posts']} ({result['percentage']}%)")
    
    print("\n✅ Testes concluídos!")

if __name__ == "__main__":
    test_term_count()
