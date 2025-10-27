#!/usr/bin/env python3
"""
Script de testes rápidos - versão simplificada.
Use para testar perguntas específicas rapidamente.
"""

from agent_system import RAGAgent
import sys


def test_question(question: str, profile: str = None):
    """Testa uma pergunta específica."""
    print(f"\n{'='*80}")
    print(f"❓ Pergunta: {question}")
    if profile:
        print(f"🔍 Filtro: @{profile}")
    print(f"{'='*80}\n")
    
    agent = RAGAgent(
        embedding_model="mxbai-embed-large",
        generation_model="qwen3:30b"
    )
    
    try:
        answer, posts = agent.query(question, profile_filter=profile, stream=False)
        
        print(f"\n{'='*80}")
        print("📝 RESPOSTA:")
        print(f"{'='*80}")
        print(answer)
        print(f"\n{'='*80}")
        print(f"📊 Posts recuperados: {len(posts)}")
        print(f"{'='*80}\n")
        
    except Exception as e:
        print(f"\n❌ ERRO: {e}\n")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Testes rápidos de cenários problemáticos
    test_cases = [
        # Edge cases
        ("", None),  # Pergunta vazia
        ("O que ele postou ontem?", None),  # Ambígua - pronome
        ("Quais posts da Maria Silva?", None),  # Pessoa inexistente
        ("Me mostre posts do @naoexisto", None),  # Perfil inexistente
        ("Roberto Salles postou algo essa semana?", None),  # Ex-reitor
        ("Quanto é 2 + 2?", None),  # Fora de escopo
        ("Quem é o reitor da USP?", None),  # Outra universidade
        ("😀🎓", None),  # Só emoji
        ("Quais posts NÃO falam sobre saúde?", None),  # Negação
    ]
    
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                     TESTES RÁPIDOS - CENÁRIOS CRÍTICOS                       ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)
    
    for i, (question, profile) in enumerate(test_cases, 1):
        print(f"\n\n{'#'*80}")
        print(f"# TESTE {i}/{len(test_cases)}")
        print(f"{'#'*80}")
        
        test_question(question, profile)
        
        if i < len(test_cases):
            input("\n⏸️  Pressione ENTER para continuar...")
