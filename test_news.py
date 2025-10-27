#!/usr/bin/env python3
"""
Script rápido para testar a integração de notícias.
"""

from embedding_manager import EmbeddingManager
from query_tools import QueryTools

def main():
    print("=" * 60)
    print("  🧪 TESTE DE INTEGRAÇÃO DE NOTÍCIAS")
    print("=" * 60)
    print()
    
    # Inicializa
    em = EmbeddingManager()
    tools = QueryTools(em)
    
    # 1. Estatísticas gerais
    print("📊 ESTATÍSTICAS DO BANCO VETORIAL:")
    stats = em.get_stats()
    print(f"   Total de documentos: {stats['total_documents']}")
    print(f"   Perfis/fontes: {', '.join(stats['profiles'])}")
    print()
    
    # 2. Estatísticas de notícias
    print("📰 ESTATÍSTICAS DE NOTÍCIAS:")
    news_stats = tools.get_news_statistics()
    print(f"   Total de notícias: {news_stats['total_news']}")
    print(f"   Período: {news_stats['date_range']['oldest'][:10]} até {news_stats['date_range']['newest'][:10]}")
    print(f"   Publishers: {len(news_stats['publishers'])} veículos")
    print()
    print("   Top 5 Publishers:")
    for i, pub in enumerate(news_stats['publishers'][:5], 1):
        print(f"     {i}. {pub['name']}: {pub['count']} notícias")
    print()
    
    # 3. Busca por pessoa
    print("🔍 BUSCANDO NOTÍCIAS SOBRE 'ROBERTO SALLES':")
    news = tools.search_news_by_person('Roberto Salles', limit=5)
    print(f"   Encontradas: {len(news)} notícias\n")
    
    for i, article in enumerate(news, 1):
        meta = article['metadata']
        print(f"   {i}. {meta['title']}")
        print(f"      📡 {meta['publisher_name']}")
        print(f"      📅 {meta['timestamp'][:10]}")
        print(f"      🔗 {meta['url']}")
        print()
    
    # 4. Busca semântica combinada
    print("🔎 BUSCA SEMÂNTICA (posts + notícias) sobre 'UFF expansão':")
    results = em.search(
        query="universidade federal fluminense expansão crescimento campus",
        n_results=5
    )
    
    if results and results.get('ids'):
        print(f"   Encontrados: {len(results['ids'][0])} resultados\n")
        for i in range(min(3, len(results['ids'][0]))):
            meta = results['metadatas'][0][i]
            content_type = meta.get('content_type', 'instagram_post')
            
            if content_type == 'news':
                print(f"   {i+1}. 📰 NOTÍCIA: {meta.get('title', 'Sem título')[:60]}...")
                print(f"      Publisher: {meta.get('publisher_name', 'N/A')}")
            else:
                print(f"   {i+1}. 📱 POST: @{meta.get('profile', 'N/A')}")
                print(f"      Curtidas: {meta.get('likesCount', 0)}, Comentários: {meta.get('commentsCount', 0)}")
            print()
    
    print("=" * 60)
    print("  ✅ TESTE CONCLUÍDO")
    print("=" * 60)
    print()
    print("💡 Agora você pode:")
    print("   - Iniciar a aplicação: ./start.sh ou uv run app.py")
    print("   - Fazer perguntas sobre Roberto Salles e notícias!")
    print()


if __name__ == "__main__":
    main()
