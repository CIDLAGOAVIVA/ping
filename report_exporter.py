"""
Módulo para exportação de relatórios do dashboard.
Suporta formatos PDF e CSV.
"""

from typing import Dict, Any, Optional
from datetime import datetime
import csv
import io
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT


class ReportExporter:
    """Exportador de relatórios do dashboard."""
    
    @staticmethod
    def export_to_csv(metrics: Dict[str, Any], filename: Optional[str] = None) -> str:
        """
        Exporta métricas para CSV.
        
        Args:
            metrics: Dicionário de métricas do DashboardAnalytics
            filename: Nome do arquivo (None = gera automaticamente)
        
        Returns:
            Conteúdo CSV como string
        """
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"relatorio_uff_{timestamp}.csv"
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Cabeçalho
        writer.writerow(['RELATÓRIO DE ANÁLISE - PING UFF ANALYTICS'])
        writer.writerow(['Gerado em:', datetime.now().strftime('%d/%m/%Y às %H:%M:%S')])
        writer.writerow([])
        
        # Resumo Geral
        summary = metrics.get('summary', {})
        writer.writerow(['=== RESUMO GERAL ==='])
        writer.writerow(['Total de Registros:', summary.get('total_records', 0)])
        writer.writerow(['Posts:', summary.get('posts_count', 0)])
        writer.writerow(['Notícias:', summary.get('news_count', 0)])
        writer.writerow(['Engajamento Total:', summary.get('total_engagement', 0)])
        writer.writerow(['Média de Engajamento:', summary.get('avg_engagement_per_post', 0)])
        writer.writerow([])
        
        # Métricas de Posts
        posts_data = metrics.get('posts', {})
        writer.writerow(['=== MÉTRICAS DE POSTS ==='])
        writer.writerow(['Total de Curtidas:', posts_data.get('total_likes', 0)])
        writer.writerow(['Total de Comentários:', posts_data.get('total_comments', 0)])
        writer.writerow(['Média de Curtidas:', posts_data.get('avg_likes', 0)])
        writer.writerow(['Média de Comentários:', posts_data.get('avg_comments', 0)])
        writer.writerow([])
        
        # Distribuição por Perfil
        writer.writerow(['=== DISTRIBUIÇÃO POR PERFIL ==='])
        writer.writerow(['Perfil', 'Posts', 'Curtidas', 'Comentários', 'Engajamento'])
        for profile, data in posts_data.get('by_profile', {}).items():
            writer.writerow([
                f"@{profile}",
                data.get('count', 0),
                data.get('likes', 0),
                data.get('comments', 0),
                data.get('engagement', 0)
            ])
        writer.writerow([])
        
        # Top Posts por Engajamento
        writer.writerow(['=== TOP 5 POSTS POR ENGAJAMENTO ==='])
        writer.writerow(['Perfil', 'Curtidas', 'Comentários', 'Engajamento', 'Legenda', 'URL'])
        for post in posts_data.get('top_by_engagement', [])[:5]:
            writer.writerow([
                f"@{post.get('profile', '')}",
                post.get('likes', 0),
                post.get('comments', 0),
                post.get('engagement', 0),
                post.get('caption', '')[:100],
                post.get('url', '')
            ])
        writer.writerow([])
        
        # Análise de Sentimento
        sentiment = metrics.get('sentiment', {})
        if sentiment.get('total_analyzed', 0) > 0:
            writer.writerow(['=== ANÁLISE DE SENTIMENTO ==='])
            writer.writerow(['Total Analisado:', sentiment.get('total_analyzed', 0)])
            writer.writerow(['Positivo:', f"{sentiment.get('positive', 0)} ({sentiment.get('positive_pct', 0)}%)"])
            writer.writerow(['Negativo:', f"{sentiment.get('negative', 0)} ({sentiment.get('negative_pct', 0)}%)"])
            writer.writerow(['Neutro:', f"{sentiment.get('neutral', 0)} ({sentiment.get('neutral_pct', 0)}%)"])
            writer.writerow(['Tendência:', sentiment.get('trend', 'N/A').upper()])
            writer.writerow([])
        
        # Tópicos Emergentes
        emerging = metrics.get('emerging_topics', {})
        if emerging.get('total_topics', 0) > 0:
            writer.writerow(['=== TÓPICOS EMERGENTES ==='])
            writer.writerow(['Termo', 'Menções', 'Percentual', 'Indicador'])
            for topic in emerging.get('topics', [])[:10]:
                writer.writerow([
                    topic.get('term', ''),
                    topic.get('count', 0),
                    f"{topic.get('percentage', 0)}%",
                    topic.get('growth_indicator', 0)
                ])
            writer.writerow([])
            
            # 🔧 CORRIGIDO: Top 5 Hashtags
            writer.writerow(['=== TOP 5 HASHTAGS ==='])
            total_unique = emerging.get('total_unique_hashtags', 0)
            total_occurrences = emerging.get('total_hashtag_occurrences', 0)
            writer.writerow(['Total de hashtags únicas:', total_unique])
            writer.writerow(['Total de ocorrências:', total_occurrences])
            writer.writerow([])
            writer.writerow(['Ranking', 'Hashtag', 'Menções', 'Percentual'])
            for i, hashtag in enumerate(emerging.get('top_hashtags', [])[:5], 1):  # 🆕 Apenas 5
                writer.writerow([
                    i,
                    f"#{hashtag.get('tag', '')}",
                    hashtag.get('count', 0),
                    f"{hashtag.get('percentage', 0)}%"
                ])
            writer.writerow([])
        
        # Notícias
        news_data = metrics.get('news', {})
        if news_data.get('total', 0) > 0:
            writer.writerow(['=== NOTÍCIAS ==='])
            writer.writerow(['Total de Notícias:', news_data.get('total', 0)])
            writer.writerow([])
            writer.writerow(['Publisher', 'Quantidade'])
            for publisher, count in sorted(
                news_data.get('by_publisher', {}).items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]:
                writer.writerow([publisher, count])
        
        content = output.getvalue()
        output.close()
        
        return content
    
    @staticmethod
    def export_to_pdf(metrics: Dict[str, Any], filename: Optional[str] = None) -> bytes:
        """
        Exporta métricas para PDF.
        
        Args:
            metrics: Dicionário de métricas do DashboardAnalytics
            filename: Nome do arquivo (None = gera automaticamente)
        
        Returns:
            Bytes do PDF
        """
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"relatorio_uff_{timestamp}.pdf"
        
        # Buffer de memória
        buffer = io.BytesIO()
        
        # Cria documento
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Estilos
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#667eea'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#764ba2'),
            spaceAfter=12,
            spaceBefore=12
        )
        
        # Elementos do PDF
        elements = []
        
        # Título
        elements.append(Paragraph("📊 RELATÓRIO DE ANÁLISE", title_style))
        elements.append(Paragraph("PING - UFF ANALYTICS", title_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # Data de geração
        date_text = f"Gerado em: {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}"
        elements.append(Paragraph(date_text, styles['Normal']))
        elements.append(Spacer(1, 0.3*inch))
        
        # Resumo Geral
        summary = metrics.get('summary', {})
        elements.append(Paragraph("RESUMO GERAL", heading_style))
        
        summary_data = [
            ['Métrica', 'Valor'],
            ['Total de Registros', f"{summary.get('total_records', 0):,}"],
            ['Posts', f"{summary.get('posts_count', 0):,}"],
            ['Notícias', f"{summary.get('news_count', 0):,}"],
            ['Engajamento Total', f"{summary.get('total_engagement', 0):,}"],
            ['Média de Engajamento', f"{summary.get('avg_engagement_per_post', 0):.2f}"]
        ]
        
        summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(summary_table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Distribuição por Perfil
        posts_data = metrics.get('posts', {})
        if posts_data.get('by_profile'):
            elements.append(Paragraph("DISTRIBUIÇÃO POR PERFIL", heading_style))
            
            profile_data = [['Perfil', 'Posts', 'Curtidas', 'Comentários', 'Engajamento']]
            for profile, data in sorted(
                posts_data.get('by_profile', {}).items(),
                key=lambda x: x[1]['engagement'],
                reverse=True
            ):
                profile_data.append([
                    f"@{profile}",
                    f"{data.get('count', 0):,}",
                    f"{data.get('likes', 0):,}",
                    f"{data.get('comments', 0):,}",
                    f"{data.get('engagement', 0):,}"
                ])
            
            profile_table = Table(profile_data, colWidths=[1.5*inch, 1*inch, 1*inch, 1*inch, 1.2*inch])
            profile_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#764ba2')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lavender),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            elements.append(profile_table)
            elements.append(Spacer(1, 0.3*inch))
        
        # Análise de Sentimento
        sentiment = metrics.get('sentiment', {})
        if sentiment.get('total_analyzed', 0) > 0:
            elements.append(Paragraph("ANÁLISE DE SENTIMENTO", heading_style))
            
            sentiment_data = [
                ['Categoria', 'Quantidade', 'Percentual'],
                ['Positivo', f"{sentiment.get('positive', 0):,}", f"{sentiment.get('positive_pct', 0)}%"],
                ['Negativo', f"{sentiment.get('negative', 0):,}", f"{sentiment.get('negative_pct', 0)}%"],
                ['Neutro', f"{sentiment.get('neutral', 0):,}", f"{sentiment.get('neutral_pct', 0)}%"],
                ['TENDÊNCIA', sentiment.get('trend', 'N/A').upper(), '-']
            ]
            
            sentiment_table = Table(sentiment_data, colWidths=[2*inch, 1.5*inch, 1.5*inch])
            sentiment_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4caf50')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightgreen),
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#ffd54f')),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            elements.append(sentiment_table)
            elements.append(Spacer(1, 0.3*inch))
        
        # Tópicos Emergentes
        emerging = metrics.get('emerging_topics', {})
        if emerging.get('total_topics', 0) > 0:
            elements.append(PageBreak())
            elements.append(Paragraph("TÓPICOS EMERGENTES", heading_style))
            
            topics_data = [['#', 'Termo', 'Menções', '%']]
            for i, topic in enumerate(emerging.get('topics', [])[:10], 1):
                topics_data.append([
                    str(i),
                    topic.get('term', ''),
                    f"{topic.get('count', 0):,}",
                    f"{topic.get('percentage', 0)}%"
                ])
            
            topics_table = Table(topics_data, colWidths=[0.5*inch, 2*inch, 1.2*inch, 1*inch])
            topics_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ff9800')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#ffe0b2')),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            elements.append(topics_table)
            elements.append(Spacer(1, 0.3*inch))
            
            # 🔧 CORRIGIDO: Top 5 Hashtags
            elements.append(Paragraph("TOP 5 HASHTAGS", heading_style))
            
            # Card de estatísticas
            total_unique = emerging.get('total_unique_hashtags', 0)
            total_occurrences = emerging.get('total_hashtag_occurrences', 0)
            avg_per_post = round(total_occurrences / emerging.get('total_posts_analyzed', 1), 2)
            
            stats_text = f"""
            <b>Estatísticas Gerais:</b><br/>
            • Total de hashtags únicas: <b>{total_unique}</b><br/>
            • Total de ocorrências: <b>{total_occurrences}</b><br/>
            • Média por post: <b>{avg_per_post}</b>
            """
            elements.append(Paragraph(stats_text, styles['Normal']))
            elements.append(Spacer(1, 0.2*inch))
            
            hashtags_data = [['#', 'Hashtag', 'Menções', '%']]
            for i, hashtag in enumerate(emerging.get('top_hashtags', [])[:5], 1):  # 🆕 Apenas 5
                hashtags_data.append([
                    str(i),
                    f"#{hashtag.get('tag', '')}",
                    f"{hashtag.get('count', 0):,}",
                    f"{hashtag.get('percentage', 0)}%"
                ])
            
            hashtags_table = Table(hashtags_data, colWidths=[0.5*inch, 2*inch, 1.2*inch, 1*inch])
            hashtags_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2196f3')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#bbdefb')),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            elements.append(hashtags_table)
        
        # Rodapé
        elements.append(Spacer(1, 0.5*inch))
        footer = Paragraph(
            "Desenvolvido com ❤️ para a comunidade UFF<br/>PING - UFF ANALYTICS",
            styles['Normal']
        )
        elements.append(footer)
        
        # Constrói PDF
        doc.build(elements)
        
        # Retorna bytes
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        return pdf_bytes


def main():
    """Função de teste."""
    print("=== Testando Report Exporter ===\n")
    
    # Mock data
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
            'avg_likes': 50.0,
            'avg_comments': 12.5,
            'by_profile': {
                'dceuff': {'count': 1500, 'likes': 75000, 'comments': 18000, 'engagement': 93000},
                'reitor': {'count': 600, 'likes': 30000, 'comments': 8000, 'engagement': 38000},
                'vicereitor': {'count': 300, 'likes': 15000, 'comments': 4000, 'engagement': 19000}
            },
            'top_by_engagement': [
                {
                    'profile': 'dceuff',
                    'likes': 500,
                    'comments': 120,
                    'engagement': 620,
                    'url': 'https://instagram.com/p/test1',
                    'caption': 'Post de teste...'
                }
            ]
        },
        'sentiment': {
            'total_analyzed': 100,
            'positive': 35,
            'negative': 45,
            'neutral': 20,
            'positive_pct': 35.0,
            'negative_pct': 45.0,
            'neutral_pct': 20.0,
            'trend': 'negative'
        },
        'emerging_topics': {
            'total_topics': 5,
            'topics': [
                {'term': 'greve', 'count': 156, 'percentage': 6.5},
                {'term': 'HUAP', 'count': 134, 'percentage': 5.6}
            ],
            'top_hashtags': [
                {'tag': 'UFF', 'count': 245},
                {'tag': 'GreveNaUFF', 'count': 156}
            ]
        },
        'news': {
            'total': 100,
            'by_publisher': {
                'G1': 30,
                'Folha': 25
            }
        }
    }
    
    # Testa CSV
    print("📄 Gerando CSV...")
    csv_content = ReportExporter.export_to_csv(mock_metrics)
    with open('test_relatorio.csv', 'w', encoding='utf-8') as f:
        f.write(csv_content)
    print("✅ CSV gerado: test_relatorio.csv")
    
    # Testa PDF
    print("\n📕 Gerando PDF...")
    pdf_bytes = ReportExporter.export_to_pdf(mock_metrics)
    with open('test_relatorio.pdf', 'wb') as f:
        f.write(pdf_bytes)
    print("✅ PDF gerado: test_relatorio.pdf")


if __name__ == '__main__':
    main()