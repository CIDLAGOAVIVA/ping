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
        sentiment_data = metrics.get('sentiment', {})
        emerging_topics_data = metrics.get('emerging_topics', {})  # 🆕
        
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
            {DashboardVisualizer._generate_summary_cards(summary, posts_data, sentiment_data)}
            
            <!-- Card de Sentimento (Destaque) -->
            {DashboardVisualizer._generate_sentiment_card(sentiment_data)}
            
            <!-- 🆕 Card de Tópicos Emergentes -->
            {DashboardVisualizer._generate_emerging_topics_card(emerging_topics_data)}
            
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
    def _generate_summary_cards(summary: Dict, posts_data: Dict, sentiment_data: Dict) -> str:
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
    def _generate_sentiment_card(sentiment_data: Dict) -> str:
        """🆕 Gera card de análise de sentimento agregado."""
        if not sentiment_data or sentiment_data.get('total_analyzed', 0) == 0:
            return ""
        
        trend = sentiment_data.get('trend', 'neutral')
        
        # Define cor e emoji baseado na tendência
        if trend == 'positive':
            gradient = 'linear-gradient(135deg, #4caf50 0%, #66bb6a 100%)'
            emoji = '😊'
            trend_text = 'Positiva'
            trend_color = '#4caf50'
        elif trend == 'negative':
            gradient = 'linear-gradient(135deg, #f44336 0%, #e57373 100%)'
            emoji = '😟'
            trend_text = 'Negativa'
            trend_color = '#f44336'
        else:
            gradient = 'linear-gradient(135deg, #9e9e9e 0%, #bdbdbd 100%)'
            emoji = '😐'
            trend_text = 'Neutra'
            trend_color = '#9e9e9e'
        
        pos_pct = sentiment_data.get('positive_pct', 0)
        neg_pct = sentiment_data.get('negative_pct', 0)
        neu_pct = sentiment_data.get('neutral_pct', 0)
        
        total = sentiment_data.get('total_analyzed', 0)
        pos_count = sentiment_data.get('positive', 0)
        neg_count = sentiment_data.get('negative', 0)
        neu_count = sentiment_data.get('neutral', 0)
        
        profiles = sentiment_data.get('profiles', [])
        profiles_text = ', '.join([f'@{p}' for p in profiles]) if profiles else 'Todas as fontes'
        
        return f"""
        <div style='background: var(--bg-secondary); border-radius: 12px; padding: 2rem; margin-bottom: 2rem; border: 1px solid var(--border-primary);'>
            <h3 style='margin: 0 0 1.5rem 0; color: var(--text-primary); display: flex; align-items: center; gap: 0.5rem;'>
                🎭 Análise de Sentimento do Período
                <span style='font-size: 0.75rem; font-weight: normal; background: {trend_color}; color: white; padding: 0.25rem 0.75rem; border-radius: 12px;'>
                    {emoji} Tendência: {trend_text}
                </span>
            </h3>
            
            <!-- Card Principal de Tendência -->
            <div style='
                background: {gradient};
                color: white;
                padding: 2rem;
                border-radius: 12px;
                margin-bottom: 1.5rem;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                text-align: center;
            '>
                <div style='font-size: 4rem; margin-bottom: 1rem;'>{emoji}</div>
                <h2 style='margin: 0 0 0.5rem 0; font-size: 2rem;'>Sentimento {trend_text}</h2>
                <p style='margin: 0; font-size: 1rem; opacity: 0.9;'>
                    Baseado em {total:,} registros analisados
                </p>
                <p style='margin: 0.5rem 0 0 0; font-size: 0.85rem; opacity: 0.8;'>
                    📊 Fontes: {profiles_text}
                </p>
            </div>
            
            <!-- Gráficos de Barras por Sentimento -->
            <div style='margin-bottom: 1.5rem;'>
                <h4 style='margin: 0 0 1rem 0; color: var(--text-primary);'>📊 Distribuição Detalhada</h4>
                
                <!-- Barra Positiva -->
                <div style='margin-bottom: 1rem;'>
                    <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;'>
                        <span style='font-weight: 600; color: #4caf50;'>✅ Positivo</span>
                        <span style='color: var(--text-secondary); font-size: 0.9rem;'>
                            {pos_count} posts ({pos_pct}%)
                        </span>
                    </div>
                    <div style='background: #e8f5e9; height: 24px; border-radius: 6px; overflow: hidden;'>
                        <div style='
                            background: #4caf50;
                            height: 100%;
                            width: {pos_pct}%;
                            transition: width 0.5s ease;
                        '></div>
                    </div>
                </div>
                
                <!-- Barra Negativa -->
                <div style='margin-bottom: 1rem;'>
                    <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;'>
                        <span style='font-weight: 600; color: #f44336;'>❌ Negativo</span>
                        <span style='color: var(--text-secondary); font-size: 0.9rem;'>
                            {neg_count} posts ({neg_pct}%)
                        </span>
                    </div>
                    <div style='background: #ffebee; height: 24px; border-radius: 6px; overflow: hidden;'>
                        <div style='
                            background: #f44336;
                            height: 100%;
                            width: {neg_pct}%;
                            transition: width 0.5s ease;
                        '></div>
                    </div>
                </div>
                
                <!-- Barra Neutra -->
                <div style='margin-bottom: 1rem;'>
                    <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;'>
                        <span style='font-weight: 600; color: #9e9e9e;'>⚪ Neutro</span>
                        <span style='color: var(--text-secondary); font-size: 0.9rem;'>
                            {neu_count} posts ({neu_pct}%)
                        </span>
                    </div>
                    <div style='background: #f5f5f5; height: 24px; border-radius: 6px; overflow: hidden;'>
                        <div style='
                            background: #9e9e9e;
                            height: 100%;
                            width: {neu_pct}%;
                            transition: width 0.5s ease;
                        '></div>
                    </div>
                </div>
            </div>
            
            <!-- Nota Metodológica -->
            <div style='
                background: var(--bg-primary);
                padding: 1rem;
                border-radius: 8px;
                border-left: 4px solid var(--primary);
                font-size: 0.85rem;
                color: var(--text-secondary);
            '>
                <strong>ℹ️ Metodologia:</strong> {sentiment_data.get('note', 'Análise de sentimento baseada em palavras-chave')}
            </div>
        </div>
        """
    
    @staticmethod
    def _generate_emerging_topics_card(emerging_topics_data: Dict) -> str:
        """🆕 Gera card com tópicos emergentes detectados."""
        if not emerging_topics_data or emerging_topics_data.get('total_topics', 0) == 0:
            return ""
        
        topics = emerging_topics_data.get('topics', [])
        total_analyzed = emerging_topics_data.get('total_posts_analyzed', 0)
        
        # Gera lista de tópicos
        topics_html = ""
        for i, topic in enumerate(topics[:10], 1):
            term = topic['term']
            count = topic['count']
            percentage = topic['percentage']
            growth = topic.get('growth_indicator', 0)
            
            # Define cor baseada no crescimento
            if growth > 50:
                trend_emoji = '🔥'
                trend_text = 'Em alta'
                trend_color = '#ff5722'
            elif growth > 0:
                trend_emoji = '📈'
                trend_text = 'Crescendo'
                trend_color = '#ff9800'
            else:
                trend_emoji = '📊'
                trend_text = 'Estável'
                trend_color = '#2196f3'
            
            topics_html += f"""
            <div style='
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 1rem;
                background: var(--bg-primary);
                border-radius: 8px;
                margin-bottom: 0.75rem;
                border-left: 4px solid {trend_color};
                transition: transform 0.2s ease;
            '>
                <div style='flex: 1;'>
                    <div style='display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.25rem;'>
                        <span style='font-size: 1.5rem;'>{trend_emoji}</span>
                        <span style='font-weight: 600; color: var(--text-primary); font-size: 1.05rem;'>
                            {term}
                        </span>
                        <span style='
                            background: {trend_color};
                            color: white;
                            padding: 0.15rem 0.5rem;
                            border-radius: 12px;
                            font-size: 0.7rem;
                            font-weight: 600;
                        '>
                            {trend_text}
                        </span>
                    </div>
                    <div style='font-size: 0.8rem; color: var(--text-secondary);'>
                        Mencionado em <strong>{count}</strong> posts ({percentage}% do período)
                    </div>
                </div>
                <div style='text-align: right;'>
                    <div style='font-size: 1.5rem; font-weight: 700; color: {trend_color};'>
                        #{i}
                    </div>
                </div>
            </div>
            """
        
        # Hashtags mais usadas
        hashtags_html = ""
        top_hashtags = emerging_topics_data.get('top_hashtags', [])
        if top_hashtags:
            hashtags_html = """
            <div style='margin-top: 1.5rem; padding-top: 1.5rem; border-top: 1px solid var(--border-primary);'>
                <h4 style='margin: 0 0 1rem 0; color: var(--text-primary);'>🏷️ Hashtags em Destaque</h4>
                <div style='display: flex; flex-wrap: wrap; gap: 0.75rem;'>
            """
            
            for hashtag in top_hashtags[:15]:
                tag = hashtag['tag']
                count = hashtag['count']
                
                # Tamanho proporcional à frequência
                font_size = min(1.2 + (count / 10), 2.0)
                
                hashtags_html += f"""
                <span style='
                    background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
                    color: white;
                    padding: 0.5rem 1rem;
                    border-radius: 20px;
                    font-size: {font_size}rem;
                    font-weight: 600;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                '>
                    #{tag} <span style='opacity: 0.8; font-size: 0.75rem;'>({count})</span>
                </span>
                """
            
            hashtags_html += """
                </div>
            </div>
            """
        
        return f"""
        <div style='background: var(--bg-secondary); border-radius: 12px; padding: 2rem; margin-bottom: 2rem; border: 1px solid var(--border-primary);'>
            <h3 style='margin: 0 0 1.5rem 0; color: var(--text-primary); display: flex; align-items: center; gap: 0.5rem;'>
                🔍 Tópicos Emergentes
                <span style='font-size: 0.75rem; font-weight: normal; background: var(--primary); color: white; padding: 0.25rem 0.75rem; border-radius: 12px;'>
                    {total_analyzed:,} posts analisados
                </span>
            </h3>
            
            <div style='
                background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%);
                padding: 1rem;
                border-radius: 8px;
                margin-bottom: 1.5rem;
                border-left: 4px solid var(--primary);
            '>
                <p style='margin: 0; font-size: 0.9rem; color: var(--text-secondary);'>
                    <strong>ℹ️ Sobre esta análise:</strong> Identificamos automaticamente os termos e temas mais mencionados nas legendas e hashtags dos posts no período selecionado, considerando frequência e contexto.
                </p>
            </div>
            
            {topics_html}
            
            {hashtags_html}
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
        },
        'sentiment': {  # 🆕 Mock de sentimento
            'total_analyzed': 100,
            'positive': 35,
            'negative': 45,
            'neutral': 20,
            'positive_pct': 35.0,
            'negative_pct': 45.0,
            'neutral_pct': 20.0,
            'trend': 'negative',
            'profiles': ['dceuff', 'reitor'],
            'note': 'Análise baseada em amostra de 100 registros'
        },
        'emerging_topics': {  # 🆕 Mock de tópicos emergentes
            'total_topics': 8,
            'total_posts_analyzed': 2400,
            'topics': [
                {'term': 'greve', 'count': 156, 'percentage': 6.5, 'growth_indicator': 75},
                {'term': 'HUAP', 'count': 134, 'percentage': 5.6, 'growth_indicator': 60},
                {'term': 'educação', 'count': 98, 'percentage': 4.1, 'growth_indicator': 45},
                {'term': 'reitoria', 'count': 87, 'percentage': 3.6, 'growth_indicator': 30},
                {'term': 'estudantes', 'count': 76, 'percentage': 3.2, 'growth_indicator': 20},
                {'term': 'universidade', 'count': 65, 'percentage': 2.7, 'growth_indicator': 10},
                {'term': 'campus', 'count': 54, 'percentage': 2.3, 'growth_indicator': 5},
                {'term': 'pesquisa', 'count': 43, 'percentage': 1.8, 'growth_indicator': 0}
            ],
            'top_hashtags': [
                {'tag': 'UFF', 'count': 245},
                {'tag': 'GreveNaUFF', 'count': 156},
                {'tag': 'HUAP', 'count': 134},
                {'tag': 'EducaçãoPública', 'count': 98},
                {'tag': 'UniversidadePública', 'count': 87},
                {'tag': 'DCE', 'count': 76},
                {'tag': 'MovimentoEstudantil', 'count': 65},
                {'tag': 'Niterói', 'count': 54},
                {'tag': 'ForaReitor', 'count': 43},
                {'tag': 'DefendaUFF', 'count': 38}
            ]
        }
    }
    
    html = DashboardVisualizer.generate_dashboard_html(mock_metrics)
    
    # Salva para teste visual
    with open('test_dashboard_with_sentiment.html', 'w', encoding='utf-8') as f:
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
    
    print("✅ HTML de teste gerado: test_dashboard_with_sentiment.html")


if __name__ == '__main__':
    main()