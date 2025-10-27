#!/usr/bin/env python3
"""
Script para reindexar o banco vetorial incluindo notícias.
"""

from data_loader import InstagramDataLoader
from embedding_manager import EmbeddingManager
import sys


def main():
    """Reindexar posts e notícias."""
    print("=" * 60)
    print("  🔄 REINDEXAÇÃO COM NOTÍCIAS")
    print("=" * 60)
    print()
    
    # Confirma
    print("⚠️  ATENÇÃO: Este script vai APAGAR o banco vetorial atual e reindexar tudo.")
    print("    Isso inclui:")
    print("    - Todos os posts do Instagram (dceuff, reitor, vicereitor)")
    print("    - Todas as notícias sobre Roberto Salles (_smoking_gun.json)")
    print()
    
    resposta = input("Deseja continuar? (sim/não): ").strip().lower()
    
    if resposta not in ['sim', 's', 'yes', 'y']:
        print("❌ Operação cancelada.")
        sys.exit(0)
    
    print()
    print("🔧 Inicializando componentes...")
    
    # Inicializa
    loader = InstagramDataLoader()
    em = EmbeddingManager()
    
    print("✓ Componentes inicializados")
    print()
    
    # Limpa coleção atual
    print("🗑️  Limpando banco vetorial atual...")
    em.clear_collection()
    print("✓ Banco vetorial limpo")
    print()
    
    # Carrega todo o conteúdo (posts + notícias)
    print("📚 Carregando posts e notícias...")
    all_content = loader.load_all_content()
    print(f"✓ Carregados {len(all_content)} documentos no total")
    print()
    
    # Estatísticas por tipo
    posts_count = sum(1 for c in all_content if c.get('content_type') != 'news')
    news_count = sum(1 for c in all_content if c.get('content_type') == 'news')
    
    print("📊 Resumo do conteúdo:")
    print(f"   - Posts do Instagram: {posts_count}")
    print(f"   - Notícias: {news_count}")
    print()
    
    # Indexa
    print("🚀 Iniciando indexação no banco vetorial...")
    print("   (Isso pode levar alguns minutos...)")
    print()
    
    em.add_posts(all_content)
    
    print()
    print("=" * 60)
    print("  ✅ REINDEXAÇÃO CONCLUÍDA COM SUCESSO!")
    print("=" * 60)
    print()
    
    # Estatísticas finais
    stats = em.get_stats()
    print("📊 Estatísticas finais do banco:")
    print(f"   - Total de documentos: {stats['total_documents']}")
    print(f"   - Perfis/fontes: {', '.join(stats['profiles'])}")
    print()
    print("🎉 Agora você pode usar o sistema com posts E notícias!")
    print()
    print("💡 Experimente perguntas como:")
    print("   - 'Me fale sobre Roberto Salles'")
    print("   - 'Notícias do ex-reitor'")
    print("   - 'O que a imprensa disse sobre a UFF em 2009?'")
    print()


if __name__ == "__main__":
    main()
