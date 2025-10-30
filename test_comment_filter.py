"""
Teste de diagnóstico: verifica estrutura dos dados para filtro de comentários.
"""

from embedding_manager import EmbeddingManager
from analytics_dashboard import DashboardAnalytics
import json

def main():
    print("=" * 60)
    print("🔬 DIAGNÓSTICO: Estrutura de Dados para Comentários")
    print("=" * 60)
    
    em = EmbeddingManager()
    analytics = DashboardAnalytics(em)
    
    # Diagnóstico da estrutura
    print("\n📊 Verificando estrutura dos primeiros 10 posts...\n")
    diagnosis = analytics.diagnose_content_structure(limit=10)
    
    print(f"Total verificado: {diagnosis['total_checked']} posts\n")
    
    print("📈 Formatos encontrados:")
    for format_name, count in diagnosis['formats_found'].items():
        percentage = (count / diagnosis['total_checked'] * 100) if diagnosis['total_checked'] > 0 else 0
        print(f"   - {format_name}: {count} ({percentage:.1f}%)")
    
    print("\n📋 Amostras dos documentos:\n")
    
    for sample in diagnosis['samples']:
        print(f"\n--- Post {sample['index'] + 1} (@{sample['profile']}) ---")
        print(f"Chaves no metadata: {sample['metadata_keys']}")
        print(f"Tem 'caption' no metadata: {sample['has_caption_key']}")
        print(f"Tem 'comments_text' no metadata: {sample['has_comments_text_key']}")
        print(f"Tem marcador '=== LEGENDA ===': {sample.get('has_legenda_marker', False)}")
        print(f"Tem marcador '=== COMENTÁRIOS ===': {sample.get('has_comentarios_marker', False)}")
        print(f"Tem formato alternativo: {sample.get('has_alt_format', False)}")
        print(f"\nPreview do documento:")
        print(sample['doc_preview'])
        print("-" * 50)
    
    # Teste de filtro com cada tipo
    print("\n\n" + "=" * 60)
    print("🧪 TESTE: Filtro de Sentimento por Tipo de Conteúdo")
    print("=" * 60)
    
    profile = "dceuff"  # Ajuste conforme necessário
    
    print(f"\n📊 Testando filtros para @{profile}:\n")
    
    # Teste 1: Both
    print("1️⃣ Filtro: BOTH (legendas + comentários)")
    sentiment_both = analytics.get_sentiment_by_profile(
        profile=profile,
        content_filter="both",
        use_cache=False,
        use_llm=False  # Usa keywords para ser rápido
    )
    print(f"   ✅ Analisados: {sentiment_both.get('total_analyzed', 0)} registros")
    
    # Teste 2: Caption only
    print("\n2️⃣ Filtro: CAPTION (apenas legendas)")
    sentiment_caption = analytics.get_sentiment_by_profile(
        profile=profile,
        content_filter="caption",
        use_cache=False,
        use_llm=False
    )
    print(f"   ✅ Analisados: {sentiment_caption.get('total_analyzed', 0)} registros")
    
    # Teste 3: Comments only
    print("\n3️⃣ Filtro: COMMENTS (apenas comentários)")
    sentiment_comments = analytics.get_sentiment_by_profile(
        profile=profile,
        content_filter="comments",
        use_cache=False,
        use_llm=False
    )
    print(f"   ✅ Analisados: {sentiment_comments.get('total_analyzed', 0)} registros")
    
    print("\n" + "=" * 60)
    print("📝 CONCLUSÃO:")
    print("=" * 60)
    
    if sentiment_comments.get('total_analyzed', 0) == 0:
        print("\n⚠️ PROBLEMA DETECTADO:")
        print("   Filtro de comentários retornou 0 registros!")
        print("\n💡 Possíveis causas:")
        print("   1. Posts não têm comentários no banco")
        print("   2. Formato de armazenamento diferente do esperado")
        print("   3. Metadata 'comments_text' não existe")
        print("\n🔧 Próximos passos:")
        print("   1. Verificar data_loader.py (como posts são indexados)")
        print("   2. Verificar se comentários estão sendo salvos")
        print("   3. Reindexar dados se necessário")
    else:
        print(f"\n✅ Filtro funcionando! {sentiment_comments.get('total_analyzed', 0)} comentários encontrados")
    
    print("\n" + "=" * 60)


if __name__ == '__main__':
    main()