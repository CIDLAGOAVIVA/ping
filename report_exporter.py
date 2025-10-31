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
        
        # 🆕 Recomendações de Políticas
        recommendations = metrics.get('policy_recommendations', {})
        if recommendations.get('has_recommendations', False):
            writer.writerow(['=== RECOMENDAÇÕES DE POLÍTICAS ==='])
            writer.writerow(['Gerado em:', recommendations.get('generated_at', 'N/A')])
            writer.writerow(['Perfil:', recommendations.get('profile', 'N/A')])
            writer.writerow([])
            
            writer.writerow(['RESUMO DAS CRÍTICAS:'])
            writer.writerow([recommendations.get('summary', '')])
            writer.writerow([])
            
            # Áreas críticas
            writer.writerow(['ÁREAS PROBLEMÁTICAS IDENTIFICADAS:'])
            writer.writerow(['Área', 'Frequência', 'Exemplos'])
            for area in recommendations.get('critical_areas', []):
                examples = ' | '.join(area.get('examples', [])[:2])
                writer.writerow([
                    area.get('area', ''),
                    area.get('frequency', ''),
                    examples
                ])
            writer.writerow([])
            
            # Recomendações
            writer.writerow(['RECOMENDAÇÕES DE AÇÕES:'])
            writer.writerow(['Prioridade', 'Área', 'Ação', 'Impacto Esperado', 'Prazo', 'Responsável'])
            for rec in recommendations.get('recommendations', []):
                writer.writerow([
                    rec.get('priority', ''),
                    rec.get('area', ''),
                    rec.get('action', ''),
                    rec.get('expected_impact', ''),
                    rec.get('implementation_time', ''),
                    rec.get('responsible', '')
                ])
            writer.writerow([])
            
            # Aspectos positivos
            if recommendations.get('positive_aspects'):
                writer.writerow(['ASPECTOS POSITIVOS A MANTER:'])
                for aspect in recommendations.get('positive_aspects', []):
                    writer.writerow(['•', aspect])
                writer.writerow([])
            
            # Observações gerais
            writer.writerow(['OBSERVAÇÕES GERAIS:'])
            writer.writerow([recommendations.get('general_observations', '')])
            writer.writerow([])
        
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
        
        # 🆕 Recomendações de Políticas
        recommendations = metrics.get('policy_recommendations', {})
        if recommendations.get('has_recommendations', False):
            elements.append(PageBreak())
            elements.append(Paragraph("RECOMENDAÇÕES DE POLÍTICAS", heading_style))
            
            # Resumo
            summary_text = f"""
            <b>Resumo das Críticas:</b><br/>
            {recommendations.get('summary', 'N/A')}
            """
            elements.append(Paragraph(summary_text, styles['Normal']))
            elements.append(Spacer(1, 0.2*inch))
            
            # Áreas Críticas
            elements.append(Paragraph("Áreas Problemáticas Identificadas", styles['Heading3']))
            
            areas_data = [['Área', 'Frequência', 'Exemplos']]
            for area in recommendations.get('critical_areas', []):
                examples = ' | '.join(area.get('examples', [])[:2])
                areas_data.append([
                    area.get('area', ''),
                    area.get('frequency', '').upper(),
                    examples[:100]
                ])
            
            areas_table = Table(areas_data, colWidths=[1.5*inch, 1*inch, 3*inch])
            areas_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f44336')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#ffcdd2')),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            elements.append(areas_table)
            elements.append(Spacer(1, 0.3*inch))
            
            # 🆕 Recomendações em CARDS (texto corrido, mais legível)
            elements.append(PageBreak())
            elements.append(Paragraph("Ações Recomendadas", styles['Heading3']))
            elements.append(Spacer(1, 0.2*inch))
            
            # Estilo para cards de recomendações
            card_style = ParagraphStyle(
                'CardStyle',
                parent=styles['Normal'],
                fontSize=10,
                leading=14,
                spaceAfter=6,
                leftIndent=10,
                rightIndent=10
            )
            
            card_title_style = ParagraphStyle(
                'CardTitle',
                parent=styles['Heading3'],
                fontSize=12,
                textColor=colors.HexColor('#4caf50'),
                spaceAfter=8,
                spaceBefore=0
            )
            
            # Itera sobre cada recomendação criando um card
            for i, rec in enumerate(recommendations.get('recommendations', []), 1):
                priority = rec.get('priority', '').upper()
                area = rec.get('area', 'N/A')
                action = rec.get('action', 'N/A')
                impact = rec.get('expected_impact', 'N/A')
                time = rec.get('implementation_time', 'N/A')
                responsible = rec.get('responsible', 'N/A')
                reasoning = rec.get('reasoning', '')
                
                # Define cor da prioridade
                if priority == 'ALTA':
                    priority_color = colors.HexColor('#f44336')
                    bg_color = colors.HexColor('#ffebee')
                elif priority == 'MÉDIA':
                    priority_color = colors.HexColor('#ff9800')
                    bg_color = colors.HexColor('#fff3e0')
                else:
                    priority_color = colors.HexColor('#2196f3')
                    bg_color = colors.HexColor('#e3f2fd')
                
                # Card container (tabela com fundo colorido)
                card_header = f"""
                <para align="center">
                    <b><font size="11" color="{priority_color.hexval()}">
                    🎯 RECOMENDAÇÃO {i} - PRIORIDADE {priority}
                    </font></b>
                </para>
                """
                
                card_content = f"""
                <b>Área de Atuação:</b><br/>
                {area}<br/>
                <br/>
                <b>Ação Recomendada:</b><br/>
                {action}<br/>
                <br/>
                <b>Impacto Esperado:</b><br/>
                {impact}<br/>
                <br/>
                <b>Prazo de Implementação:</b> {time.title()}<br/>
                <b>Responsável:</b> {responsible}<br/>
                """
                
                if reasoning:
                    card_content += f"""
                    <br/>
                    <b>Justificativa:</b><br/>
                    <i>{reasoning}</i>
                    """
                
                # Adiciona elementos do card
                elements.append(Paragraph(card_header, card_title_style))
                
                # Cria card com borda e fundo colorido
                card_data = [[Paragraph(card_content, card_style)]]
                card_table = Table(card_data, colWidths=[6.5*inch])
                card_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), bg_color),
                    ('BORDER', (0, 0), (-1, -1), 2, priority_color),
                    ('TOPPADDING', (0, 0), (-1, -1), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                    ('LEFTPADDING', (0, 0), (-1, -1), 15),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 15),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ]))
                
                elements.append(card_table)
                elements.append(Spacer(1, 0.25*inch))
            
            # Espaço após recomendações
            elements.append(Spacer(1, 0.2*inch))
            
            # Aspectos positivos
            if recommendations.get('positive_aspects'):
                elements.append(Paragraph("Aspectos Positivos a Manter", styles['Heading3']))
                positive_text = "<br/>".join([f"• {asp}" for asp in recommendations.get('positive_aspects', [])])
                elements.append(Paragraph(positive_text, styles['Normal']))
                elements.append(Spacer(1, 0.2*inch))
        
        # Rodapé
        elements.append(Spacer(1, 0.5*inch))
        footer = Paragraph(
            "Desenvolvido pelo CID - Centro de Inovação em Dados",
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
            ]
        },
        'news': {
            'total': 100,
            'by_publisher': {
                'G1': 30,
                'Folha': 25
            }
        },
        'policy_recommendations': {
            'has_recommendations': True,
            'generated_at': '2023-10-10 10:00:00',
            'profile': 'dceuff',
            'summary': 'Críticas construtivas sobre a gestão de conteúdo.',
            'critical_areas': [
                {
                    'area': 'Falta de interatividade',
                    'frequency': 'Alta',
                    'examples': ['Post sem enquetes', 'Stories sem perguntas']
                },
                {
                    'area': 'Baixo engajamento em posts',
                    'frequency': 'Média',
                    'examples': ['Posts com menos de 10 curtidas']
                }
            ],
            'recommendations': [
                {
                    'priority': 'Alta',
                    'area': 'Conteúdo',
                    'action': 'Criar enquetes nos stories',
                    'expected_impact': 'Aumentar a interatividade',
                    'implementation_time': 'Imediato',
                    'responsible': 'Equipe de Conteúdo'
                },
                {
                    'priority': 'Média',
                    'area': 'Postagens',
                    'action': 'Revisar horários de postagem',
                    'expected_impact': 'Aumentar o alcance',
                    'implementation_time': '1 semana',
                    'responsible': 'Social Media'
                }
            ],
            'positive_aspects': [
                'Bom uso de imagens',
                'Legendas criativas'
            ],
            'general_observations': 'Continuar o bom trabalho!'
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
    
    # 🆕 Mock de recomendações
    mock_metrics['policy_recommendations'] = {
        'has_recommendations': True,
        'generated_at': '2025-10-27T14:30:00',
        'profile': 'dceuff',
        'content_filter': 'both',
        'sentiment_data': {
            'total_analyzed': 100,
            'negative_pct': 45.0,
            'trend': 'negative'
        },
        'summary': 'As principais críticas giram em torno de demora nas respostas institucionais, falta de transparência e problemas estruturais no HUAP.',
        'critical_areas': [
            {
                'area': 'Comunicação Institucional',
                'frequency': 'alta',
                'examples': [
                    'Falta de resposta aos questionamentos',
                    'Informações desencontradas'
                ]
            },
            {
                'area': 'Infraestrutura',
                'frequency': 'média',
                'examples': [
                    'HUAP sem condições adequadas',
                    'Falta de equipamentos'
                ]
            }
        ],
        'recommendations': [
            {
                'priority': 'alta',
                'area': 'Comunicação',
                'action': 'Implementar canal de respostas em até 48h',
                'expected_impact': 'Redução de 40% nas reclamações sobre falta de resposta',
                'implementation_time': 'curto prazo',
                'responsible': 'Assessoria de Comunicação'
            },
            {
                'priority': 'alta',
                'area': 'Transparência',
                'action': 'Criar dashboard público de acompanhamento de demandas',
                'expected_impact': 'Aumento de confiança e engajamento positivo',
                'implementation_time': 'médio prazo',
                'responsible': 'Diretoria de TI + Comunicação'
            },
            {
                'priority': 'média',
                'area': 'HUAP',
                'action': 'Divulgar calendário de melhorias e investimentos',
                'expected_impact': 'Redução de especulações negativas',
                'implementation_time': 'curto prazo',
                'responsible': 'Administração do HUAP'
            }
        ],
        'positive_aspects': [
            'Diálogo com movimentos estudantis',
            'Transparência em eventos públicos'
        ],
        'general_observations': 'A gestão atual tem boa receptividade em eventos presenciais, mas precisa melhorar a comunicação digital e o tempo de resposta a questionamentos.'
    }
    
    # Testa CSV com novas recomendações
    print("\n📄 Gerando CSV com Recomendações...")
    csv_content = ReportExporter.export_to_csv(mock_metrics)
    with open('test_relatorio_recomendacoes.csv', 'w', encoding='utf-8') as f:
        f.write(csv_content)
    print("✅ CSV gerado: test_relatorio_recomendacoes.csv")
    
    # Testa PDF com novas recomendações
    print("\n📕 Gerando PDF com Recomendações...")
    pdf_bytes = ReportExporter.export_to_pdf(mock_metrics)
    with open('test_relatorio_recomendacoes.pdf', 'wb') as f:
        f.write(pdf_bytes)
    print("✅ PDF gerado: test_relatorio_recomendacoes.pdf")


if __name__ == '__main__':
    main()