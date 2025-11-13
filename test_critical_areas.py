#!/usr/bin/env python3
"""
Teste para verificar se as áreas críticas estão sendo geradas corretamente
nas recomendações de políticas.
"""

import sys
from analytics_dashboard import DashboardAnalytics
from embedding_manager import EmbeddingManager
from pathlib import Path


def test_critical_areas():
    """Testa se as áreas críticas são geradas corretamente."""
    print("\n" + "="*60)
    print("🧪 TESTE: Geração de Áreas Críticas")
    print("="*60 + "\n")
    
    try:
        # Inicializa EmbeddingManager
        print("📊 Inicializando EmbeddingManager...")
        em = EmbeddingManager(
            collection_name="instagram_posts",
            persist_dir="./chroma_db"
        )
        print("✅ EmbeddingManager inicializado")
        
        # Inicializa DashboardAnalytics
        print("📊 Inicializando DashboardAnalytics...")
        analytics = DashboardAnalytics(embedding_manager=em)
        print("✅ DashboardAnalytics inicializado\n")
        
        # Gera recomendações (vai testar o método completo)
        print("🤖 Gerando recomendações de políticas...")
        print("   (Isso pode levar alguns segundos...)\n")
        
        result = analytics.generate_policy_recommendations(
            profile_filter=None,  # Todos os perfis
            min_engagement=50,
            top_n=3
        )
        
        print("\n📋 RESULTADO:")
        print("-" * 60)
        
        # Verifica se tem recomendações
        if 'recommendations' in result:
            recommendations = result['recommendations']
            print(f"✅ Recomendações: {len(recommendations)} encontradas")
            for i, rec in enumerate(recommendations, 1):
                print(f"\n   {i}. {rec.get('area', 'N/A')} (Prioridade: {rec.get('priority', 'N/A')})")
                print(f"      Ação: {rec.get('action', 'N/A')[:80]}...")
        else:
            print("❌ Não foram geradas recomendações")
            return False
        
        # VERIFICA ÁREAS CRÍTICAS (o foco deste teste)
        print("\n" + "-" * 60)
        if 'critical_areas' in result:
            critical_areas = result['critical_areas']
            if critical_areas and len(critical_areas) > 0:
                print(f"✅ Áreas Críticas: {len(critical_areas)} identificadas\n")
                for i, area in enumerate(critical_areas, 1):
                    print(f"   {i}. {area.get('area', 'N/A')} (Frequência: {area.get('frequency', 'N/A')})")
                    examples = area.get('examples', [])
                    if examples:
                        print(f"      Exemplos: {len(examples)}")
                        for j, ex in enumerate(examples[:2], 1):
                            print(f"         {j}. {ex[:80]}...")
                    print()
            else:
                print("⚠️  Áreas Críticas: LISTA VAZIA (PROBLEMA!)")
                print("   O LLM não retornou áreas críticas.")
                return False
        else:
            print("❌ Áreas Críticas: CHAVE NÃO ENCONTRADA (PROBLEMA!)")
            print("   O resultado não contém a chave 'critical_areas'")
            return False
        
        # Verifica aspectos positivos
        print("-" * 60)
        if 'positive_aspects' in result:
            positive_aspects = result['positive_aspects']
            if positive_aspects and len(positive_aspects) > 0:
                print(f"✅ Aspectos Positivos: {len(positive_aspects)} encontrados\n")
                for i, aspect in enumerate(positive_aspects, 1):
                    print(f"   {i}. {aspect}")
            else:
                print("⚠️  Aspectos Positivos: lista vazia (ok, pode acontecer)")
        else:
            print("⚠️  Aspectos Positivos: chave não encontrada")
        
        print("\n" + "="*60)
        print("✅ TESTE PASSOU: Áreas críticas estão sendo geradas!")
        print("="*60 + "\n")
        return True
        
    except Exception as e:
        print("\n" + "="*60)
        print(f"❌ ERRO NO TESTE: {e}")
        print("="*60)
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = test_critical_areas()
    sys.exit(0 if success else 1)
