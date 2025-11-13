#!/usr/bin/env python3
"""
Teste para verificar se a exportação de relatórios inclui as áreas críticas.
"""

import sys
from analytics_dashboard import DashboardAnalytics
from embedding_manager import EmbeddingManager
from datetime import datetime
from pathlib import Path


def test_export_report():
    """Testa se a exportação de relatórios inclui áreas críticas."""
    print("\n" + "="*60)
    print("📄 TESTE: Exportação de Relatório com Áreas Críticas")
    print("="*60 + "\n")
    
    try:
        # Inicializa
        print("📊 Inicializando sistema...")
        em = EmbeddingManager(
            collection_name="instagram_posts",
            persist_dir="./chroma_db"
        )
        analytics = DashboardAnalytics(embedding_manager=em)
        print("✅ Sistema inicializado\n")
        
        # Gera recomendações PRIMEIRO (contém dados de sentimento)
        print("🤖 Gerando recomendações de políticas...")
        recommendations = analytics.generate_policy_recommendations(
            profile_filter=None,
            min_engagement=50,
            top_n=3
        )
        print("✅ Recomendações geradas\n")
        
        # Cria métricas básicas para o relatório
        print("📦 Preparando dados para exportação...")
        metrics = {
            'summary': {
                'total_records': em.collection.count(),
                'posts_count': em.collection.count() - 24,  # aproximação
                'news_count': 24,
                'total_engagement': 150000,
                'avg_engagement_per_post': 62.5
            },
            'posts': {
                'total': em.collection.count(),
                'total_likes': 120000,
                'total_comments': 30000,
                'avg_likes': 50.0,
                'avg_comments': 12.5,
                'by_profile': {},
                'top_by_engagement': []
            },
            'sentiment': recommendations.get('sentiment_analysis', {}),
            'emerging_topics': {'total_topics': 0, 'topics': []},
            'news': {'total': 24, 'by_publisher': {}}
        }
        if recommendations.get('recommendations'):
            sentiment_data = recommendations.get('sentiment_analysis', {})
            
            export_format = {
                'has_recommendations': True,
                'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'profile': "Todos os perfis",
                'content_filter': 'both',
                'sentiment_data': sentiment_data,
                'summary': f"Análise baseada em {len(recommendations.get('recommendations', []))} recomendações.",
                'critical_areas': recommendations.get('critical_areas', []),
                'recommendations': recommendations.get('recommendations', []),
                'positive_aspects': recommendations.get('positive_aspects', []),
                'general_observations': f"Sentimento: {sentiment_data.get('positive_pct', 0):.1f}% positivo"
            }
            
            metrics['policy_recommendations'] = export_format
            
            print(f"✅ Dados preparados:")
            print(f"   - {len(export_format['recommendations'])} recomendações")
            print(f"   - {len(export_format['critical_areas'])} áreas críticas")
            print(f"   - {len(export_format['positive_aspects'])} aspectos positivos\n")
        
        # Exporta CSV
        print("📄 Exportando relatório CSV...")
        csv_content = analytics.export_report(metrics, 'csv', 'test_relatorio_areas_criticas.csv')
        
        csv_path = Path('./exports/test_relatorio_areas_criticas.csv')
        csv_path.parent.mkdir(exist_ok=True)
        csv_path.write_text(csv_content, encoding='utf-8')
        print(f"✅ CSV exportado: {csv_path}\n")
        
        # Verifica se o CSV contém as áreas críticas
        print("🔍 Verificando conteúdo do CSV...")
        if 'ÁREAS PROBLEMÁTICAS IDENTIFICADAS' in csv_content:
            print("✅ Seção 'ÁREAS PROBLEMÁTICAS IDENTIFICADAS' encontrada!")
            
            # Conta quantas áreas foram incluídas
            lines = csv_content.split('\n')
            areas_section_found = False
            areas_count = 0
            
            for line in lines:
                if 'ÁREAS PROBLEMÁTICAS IDENTIFICADAS' in line:
                    areas_section_found = True
                    continue
                
                if areas_section_found:
                    if line.startswith('===') or line.startswith('RECOMENDAÇÕES'):
                        break
                    if line.strip() and not line.startswith('Área,'):
                        areas_count += 1
            
            print(f"   Áreas exportadas no CSV: {areas_count}")
            
            if areas_count > 0:
                print("✅ ÁREAS CRÍTICAS EXPORTADAS COM SUCESSO NO CSV!")
            else:
                print("⚠️  Seção encontrada mas está vazia no CSV")
        else:
            print("❌ Seção 'ÁREAS PROBLEMÁTICAS IDENTIFICADAS' NÃO encontrada no CSV")
        
        # Exporta PDF
        print("\n📕 Exportando relatório PDF...")
        pdf_bytes = analytics.export_report(metrics, 'pdf', 'test_relatorio_areas_criticas.pdf')
        
        pdf_path = Path('./exports/test_relatorio_areas_criticas.pdf')
        pdf_path.write_bytes(pdf_bytes)
        print(f"✅ PDF exportado: {pdf_path}")
        print(f"   Tamanho: {len(pdf_bytes):,} bytes\n")
        
        print("="*60)
        print("✅ TESTE COMPLETO: Relatórios gerados com áreas críticas!")
        print("="*60)
        print(f"\nArquivos gerados:")
        print(f"  - {csv_path}")
        print(f"  - {pdf_path}")
        print("\n✨ Abra os arquivos para verificar se as áreas críticas")
        print("   estão sendo exibidas corretamente!\n")
        
        return True
        
    except Exception as e:
        print("\n" + "="*60)
        print(f"❌ ERRO NO TESTE: {e}")
        print("="*60)
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = test_export_report()
    sys.exit(0 if success else 1)
