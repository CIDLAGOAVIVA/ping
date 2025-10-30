"""
Gerador de HTML/CSS para visualizações do dashboard.
Cria gráficos e cards usando CSS puro (sem dependências JS).
"""

from typing import Dict, Any, List
from datetime import datetime


class DashboardVisualizer:
    """Gerador de visualizações HTML para o dashboard."""
    
    @staticmethod
    def generate_dashboard_html(metrics: Dict[str, Any]) -> str:
        """
        Gera HTML completo do dashboard com métricas.
        
        Args:
            metrics: Dicionário de métricas do DashboardAnalytics
        
        Returns:
            HTML formatado
        """
        summary = metrics.get('summary', {})
        posts_data = metrics.get('posts', {})
        news_data = metrics.get('news', {})
        
        html = f"""
        <div style='padding: 2rem; background: var(--bg-primary); color: var(--text-primary);'>
            <!-- Header -->
            <div style='margin-bottom: 2rem;'>
                <h2 style='margin: 0 0 0.5rem 0; color: var(--text-primary); font-size: 2rem;'>
                    📊 Dashboard de Análise
                </h2>
                <p style='margin: 0; color: var(--text-secondary); font-size: 0.95rem;'>
                    Atualizado em {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}
                </p>
            </div>
            
            <!-- Cards Principais -->
            {DashboardVisualizer._generate_summary_cards(summary, posts_data)}
            
            <!-- Gráficos de Engajamento -->
            {DashboardVisualizer._generate_engagement_charts(posts_data)}
            
            <!-- Distribuição por Perfil -->
            {DashboardVisualizer._generate_profile_distribution(posts_data)}
            
            <!-- Top Posts -->
            {DashboardVisualizer._generate_top_posts(posts_data)}
            
            <!-- Notícias -->
            {DashboardVisualizer._generate_news_section(news_data)}
        </div>
        """
        
        return html
    
    @staticmethod
    def _generate_summary_cards(summary: Dict, posts_data: Dict) -> str:
        """Gera cards de resumo."""
        return f"""
        <div style='display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1.5rem; margin-bottom: 2.5rem;'>
            <!-- Total de Registros -->
            <div style='
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 1.5rem;
                border-radius: 12px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            '>
                <p style='margin: 0; font-size: 0.9rem; opacity: 0.9;'>📝 Total de Registros</p>
                <h3 style='margin: 0.5rem 0 0 0; font-size: 2.5rem;'>{summary.get('total_records', 0):,}</h3>
                <p style='margin: 0.5rem 0 0 0; font-size: 0.85rem; opacity: 0.8;'>
                    {summary.get('posts_count', 0)} posts + {summary.get('news_count', 0)} notícias
                </p>
            </div>
            
            <!-- Engajamento Total -->
            <div style='
                background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                color: white;
                padding: 1.5rem;
                border-radius: 12px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            '>
                <p style='margin: 0; font-size: 0.9rem; opacity: 0.9;'>❤️ Engajamento Total</p>
                <h3 style='margin: 0.5rem 0 0 0; font-size: 2.5rem;'>{summary.get('total_engagement', 0):,}</h3>
                <p style='margin: 0.5rem 0 0 0; font-size: 0.85rem; opacity: 0.8;'>
                    Curtidas + Comentários
                </p>
            </div>
            
            <!-- Média de Curtidas -->
            <div style='
                background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
                color: white;
                padding: 1.5rem;
                border-radius: 12px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            '>
                <p style='margin: 0; font-size: 0.9rem; opacity: 0.9;'>👍 Média de Curtidas</p>
                <h3 style='margin: 0.5rem 0 0 0; font-size: 2.5rem;'>{posts_data.get('avg_likes', 0):.1f}</h3>
                <p style='margin: 0.5rem 0 0 0; font-size: 0.85rem; opacity: 0.8;'>
                    Por post
                </p>
            </div>
            
            <!-- Média de Comentários -->
            <div style='
                background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
                color: white;
                padding: 1.5rem;
                border-radius: 12px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            '>
                <p style='margin: 0; font-size: 0.9rem; opacity: 0.9;'>💬 Média de Comentários</p>
                <h3 style='margin: 0.5rem 0 0 0; font-size: 2.5rem;'>{posts_data.get('avg_comments', 0):.1f}</h3>
                <p style='margin: 0.5rem 0 0 0; font-size: 0.85rem; opacity: 0.8;'>
                    Por post
                </p>
            </div>
        </div>
        """
    
    @staticmethod
    def _generate_engagement_charts(posts_data: Dict) -> str:
        """Gera gráfico de barras de engajamento."""
        if not posts_data.get('by_profile'):
            return ""
        
        # Calcula valores máximos para escala
        max_engagement = max(
            [p['engagement'] for p in posts_data['by_profile'].values()],
            default=1
        )
        
        bars_html = ""
        for profile, data in sorted(
            posts_data['by_profile'].items(),
            key=lambda x: x[1]['engagement'],
            reverse=True
        ):
            percentage = (data['engagement'] / max_engagement) * 100 if max_engagement > 0 else 0
            
            bars_html += f"""
            <div style='margin-bottom: 1.5rem;'>
                <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;'>
                    <span style='font-weight: 600; color: var(--text-primary);'>@{profile}</span>
                    <span style='color: var(--text-secondary); font-size: 0.9rem;'>
                        {data['engagement']:,} interações
                    </span>
                </div>
                <div style='background: var(--border-primary); height: 32px; border-radius: 8px; overflow: hidden; position: relative;'>
                    <div style='
                        background: linear-gradient(90deg, var(--primary), var(--primary-dark));
                        height: 100%;
                        width: {percentage}%;
                        display: flex;
                        align-items: center;
                        justify-content: flex-end;
                        padding-right: 0.75rem;
                        color: white;
                        font-weight: 600;
                        font-size: 0.85rem;
                        transition: width 0.5s ease;
                    '>
                        {data['count']} posts
                    </div>
                </div>
                <div style='display: flex; gap: 1.5rem; margin-top: 0.5rem; font-size: 0.85rem; color: var(--text-secondary);'>
                    <span>👍 {data['likes']:,}</span>
                    <span>💬 {data['comments']:,}</span>
                    <span>📊 Média: {(data['engagement'] / data['count']):.1f}</span>
                </div>
            </div>
            """
        
        return f"""
        <div style='background: var(--bg-secondary); border-radius: 12px; padding: 1.5rem; margin-bottom: 2rem; border: 1px solid var(--border-primary);'>
            <h3 style='margin: 0 0 1.5rem 0; color: var(--text-primary);'>📈 Engajamento por Fonte</h3>
            {bars_html}
        </div>
        """
    
    @staticmethod
    def _generate_profile_distribution(posts_data: Dict) -> str:
        """Gera distribuição de posts por perfil."""
        if not posts_data.get('by_profile'):
            return ""
        
        total_posts = posts_data.get('total', 1)
        
        items_html = ""
        for profile, data in sorted(
            posts_data['by_profile'].items(),
            key=lambda x: x[1]['count'],
            reverse=True
        ):
            percentage = (data['count'] / total_posts) * 100 if total_posts > 0 else 0
            
            items_html += f"""
            <div style='display: flex; justify-content: space-between; align-items: center; padding: 1rem; background: var(--bg-primary); border-radius: 8px; margin-bottom: 0.75rem;'>
                <div>
                    <span style='font-weight: 600; color: var(--text-primary);'>@{profile}</span>
                    <div style='font-size: 0.85rem; color: var(--text-secondary); margin-top: 0.25rem;'>
                        {data['count']} posts ({percentage:.1f}%)
                    </div>
                </div>
                <div style='text-align: right;'>
                    <div style='font-size: 1.2rem; font-weight: 600; color: var(--primary);'>
                        {data['engagement']:,}
                    </div>
                    <div style='font-size: 0.75rem; color: var(--text-secondary);'>
                        engajamento
                    </div>
                </div>
            </div>
            """
        
        return f"""
        <div style='background: var(--bg-secondary); border-radius: 12px; padding: 1.5rem; margin-bottom: 2rem; border: 1px solid var(--border-primary);'>
            <h3 style='margin: 0 0 1.5rem 0; color: var(--text-primary);'>📊 Distribuição por Perfil</h3>
            {items_html}
        </div>
        """
    
    @staticmethod
    def _generate_top_posts(posts_data: Dict) -> str:
        """Gera lista de top posts."""
        top_posts = posts_data.get('top_by_engagement', [])[:5]
        
        if not top_posts:
            return ""
        
        posts_html = ""
        for i, post in enumerate(top_posts, 1):
            posts_html += f"""
            <div style='padding: 1rem; background: var(--bg-primary); border-radius: 8px; border-left: 4px solid var(--primary); margin-bottom: 1rem;'>
                <div style='display: flex; justify-content: space-between; align-items: start; margin-bottom: 0.5rem;'>
                    <div>
                        <span style='background: var(--primary); color: white; padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.75rem; font-weight: 600;'>
                            #{i}
                        </span>
                        <span style='margin-left: 0.5rem; font-weight: 600; color: var(--text-primary);'>
                            @{post['profile']}
                        </span>
                    </div>
                    <div style='text-align: right;'>
                        <div style='font-size: 1.1rem; font-weight: 600; color: var(--primary);'>
                            {post['engagement']:,}
                        </div>
                        <div style='font-size: 0.75rem; color: var(--text-secondary);'>
                            👍 {post['likes']} | 💬 {post['comments']}
                        </div>
                    </div>
                </div>
                <p style='margin: 0.5rem 0; color: var(--text-secondary); font-size: 0.9rem;'>
                    {post['caption']}
                </p>
                <a href='{post['url']}' target='_blank' style='color: var(--primary); font-size: 0.85rem; text-decoration: none;'>
                    Ver post →
                </a>
            </div>
            """
        
        return f"""
        <div style='background: var(--bg-secondary); border-radius: 12px; padding: 1.5rem; margin-bottom: 2rem; border: 1px solid var(--border-primary);'>
            <h3 style='margin: 0 0 1.5rem 0; color: var(--text-primary);'>🏆 Top 5 Posts por Engajamento</h3>
            {posts_html}
        </div>
        """
    
    @staticmethod
    def _generate_news_section(news_data: Dict) -> str:
        """Gera seção de notícias."""
        if not news_data.get('total'):
            return ""
        
        publishers = news_data.get('by_publisher', {})
        
        pubs_html = ""
        for pub, count in sorted(publishers.items(), key=lambda x: x[1], reverse=True)[:10]:
            pubs_html += f"""
            <div style='display: flex; justify-content: space-between; padding: 0.75rem; background: var(--bg-primary); border-radius: 6px; margin-bottom: 0.5rem;'>
                <span style='color: var(--text-primary);'>{pub}</span>
                <span style='color: var(--primary); font-weight: 600;'>{count}</span>
            </div>
            """
        
        return f"""
        <div style='background: var(--bg-secondary); border-radius: 12px; padding: 1.5rem; border: 1px solid var(--border-primary);'>
            <h3 style='margin: 0 0 1rem 0; color: var(--text-primary);'>📰 Notícias no Período</h3>
            <div style='margin-bottom: 1rem;'>
                <span style='font-size: 2rem; font-weight: 600; color: var(--primary);'>
                    {news_data['total']:,}
                </span>
                <span style='color: var(--text-secondary); margin-left: 0.5rem;'>
                    notícias indexadas
                </span>
            </div>
            <h4 style='margin: 1.5rem 0 1rem 0; color: var(--text-primary); font-size: 1rem;'>
                Top Publishers
            </h4>
            {pubs_html}
        </div>
        """


def main():
    """Função de teste."""
    print("=== Testando Dashboard Visualizer ===\n")
    
    # Mock data para teste
    mock_metrics = {
        'summary': {
            'total_records': 2500,
            'posts_count': 2400,
            'news_count': 100,
            'total_engagement': 150000,
            'avg_engagement_per_post': 62.5
        },
        'posts': {
            'total': 2400,
            'total_likes': 120000,
            'total_comments': 30000,
            'total_engagement': 150000,
            'avg_likes': 50.0,
            'avg_comments': 12.5,
            'avg_engagement': 62.5,
            'top_by_engagement': [
                {
                    'profile': 'dceuff',
                    'likes': 500,
                    'comments': 120,
                    'engagement': 620,
                    'url': 'https://instagram.com/p/test1',
                    'caption': 'Post de teste sobre greve estudantil...'
                }
            ],
            'by_profile': {
                'dceuff': {'count': 1500, 'likes': 75000, 'comments': 18000, 'engagement': 93000},
                'reitor': {'count': 600, 'likes': 30000, 'comments': 8000, 'engagement': 38000},
                'vicereitor': {'count': 300, 'likes': 15000, 'comments': 4000, 'engagement': 19000}
            }
        },
        'news': {
            'total': 100,
            'by_publisher': {
                'BBC Brasil': 30,
                'G1': 25,
                'Folha': 20,
                'O Globo': 15,
                'Estadão': 10
            }
        }
    }
    
    html = DashboardVisualizer.generate_dashboard_html(mock_metrics)
    
    # Salva para teste visual
    with open('test_dashboard.html', 'w', encoding='utf-8') as f:
        f.write(f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                :root {{
                    --bg-primary: #ffffff;
                    --bg-secondary: #f8f9fa;
                    --text-primary: #1a1a1a;
                    --text-secondary: #666666;
                    --border-primary: #e0e0e0;
                    --primary: #667eea;
                    --primary-dark: #764ba2;
                }}
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; }}
            </style>
        </head>
        <body>
            {html}
        </body>
        </html>
        """)
    
    print("✅ HTML de teste gerado: test_dashboard.html")


if __name__ == '__main__':
    main()