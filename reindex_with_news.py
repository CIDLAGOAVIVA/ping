#!/usr/bin/env python3
"""
Script para reindexar o banco vetorial incluindo notícias.
"""

from data_loader import InstagramDataLoader
from embedding_manager import EmbeddingManager
from sentiment_cache import SentimentCache
import sys


def main():
    """Reindexar posts e notícias."""
    print("=" * 60)
    print("  🔄 REINDEXAÇÃO DO BANCO VETORIAL")
    print("=" * 60)
    print()
    
    # Inicializa componentes
    print("🛠️  Inicializando componentes...")
    loader = InstagramDataLoader()
    em = EmbeddingManager()
    print("✓ Componentes inicializados")
    print()
    
    # 🆕 Limpa cache de sentimento
    print("🗑️  Limpando cache de análise de sentimento...")
    cache = SentimentCache()
    cache.clear_all()
    print("✓ Cache limpo")
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
