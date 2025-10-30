"""
Módulo para análises e métricas do dashboard.
Processa dados de posts e notícias para visualização.
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta, timezone
from dateutil import parser as date_parser
from embedding_manager import EmbeddingManager
from query_tools import QueryTools
from config import DEFAULT_PROVIDER, DEEPSEEK_MODEL
import llm_chat
import json


class DashboardAnalytics:
    """Gerenciador de análises para o dashboard."""
    
    def __init__(self, embedding_manager: EmbeddingManager):
        self.em = embedding_manager
        self.tools = QueryTools(embedding_manager)
        self.collection = embedding_manager.collection
    
    def _normalize_datetime(self, dt: datetime) -> datetime:
        """
        Normaliza datetime para ter timezone UTC.
        
        Args:
            dt: Datetime a normalizar
        
        Returns:
            Datetime com timezone UTC
        """
        if dt.tzinfo is None:
            # Se não tem timezone, assume UTC
            return dt.replace(tzinfo=timezone.utc)
        else:
            # Converte para UTC se tiver outro timezone
            return dt.astimezone(timezone.utc)
    
    def get_date_range_data(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        profile_filter: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Retorna dados agregados para um período específico.
        
        Args:
            start_date: Data inicial (ISO format ou None para sem limite)
            end_date: Data final (ISO format ou None para sem limite)
            profile_filter: Lista de perfis para filtrar (ex: ["dceuff", "reitor"])
        
        Returns:
            Dicionário com métricas agregadas
        """
        # Busca todos os documentos
        where_clause = {}
        
        if profile_filter:
            where_clause['profile'] = {'$in': profile_filter}
        
        results = self.collection.get(
            where=where_clause if where_clause else None,
            limit=10000,
            include=['metadatas', 'documents']  # 🆕 Incluir documents para sentimento
        )
        
        if not results['ids']:
            return self._empty_metrics()
        
        # Normaliza datas de filtro
        start_filter = None
        end_filter = None
        
        if start_date:
            try:
                start_filter = self._normalize_datetime(date_parser.parse(start_date))
            except Exception as e:
                print(f"⚠️ Erro ao parsear start_date '{start_date}': {e}")
        
        if end_date:
            try:
                end_filter = self._normalize_datetime(date_parser.parse(end_date))
            except Exception as e:
                print(f"⚠️ Erro ao parsear end_date '{end_date}': {e}")
        
        # Filtra por data
        filtered_posts = []
        filtered_news = []
        filtered_documents = []  # 🆕 Para análise de sentimento
        
        for i, metadata in enumerate(results['metadatas']):
            try:
                # Parse e normaliza data do post
                post_date = date_parser.parse(metadata['timestamp'])
                post_date = self._normalize_datetime(post_date)
                
                # Aplica filtros de data
                if start_filter and post_date < start_filter:
                    continue
                
                if end_filter and post_date > end_filter:
                    continue
                
                # Separa posts e notícias
                if metadata.get('content_type') == 'news':
                    filtered_news.append(metadata)
                else:
                    filtered_posts.append(metadata)
                    # 🆕 Armazena documento para sentimento
                    if i < len(results['documents']):
                        filtered_documents.append({
                            'text': results['documents'][i],
                            'metadata': metadata
                        })
            
            except Exception as e:
                print(f"⚠️ Erro ao processar metadata: {e}")
                print(f"   Timestamp: {metadata.get('timestamp', 'N/A')}")
                continue
        
        # 🆕 Análise de sentimento nos dados filtrados
        sentiment_data = self._analyze_sentiment_batch(
            filtered_documents,
            profile_filter
        )
        
        metrics = self._calculate_metrics(filtered_posts, filtered_news)
        
        # 🆕 Adiciona sentimento às métricas
        metrics['sentiment'] = sentiment_data
        
        return metrics
    
    def _analyze_sentiment_batch(
        self,
        documents: List[Dict[str, Any]],
        profiles: Optional[List[str]] = None,
        use_llm: bool = True  # 🆕 Usar LLM por padrão
    ) -> Dict[str, Any]:
        """
        Analisa sentimento agregado de um conjunto de documentos.
        
        Args:
            documents: Lista de dicts com 'text' e 'metadata'
            profiles: Lista de perfis filtrados
            use_llm: Se True, usa LLM para análise mais precisa (padrão: True)
        
        Returns:
            Dict com análise de sentimento agregada
        """
        if not documents:
            return {
                'total_analyzed': 0,
                'positive': 0,
                'negative': 0,
                'neutral': 0,
                'positive_pct': 0,
                'negative_pct': 0,
                'neutral_pct': 0,
                'trend': 'neutral',
                'profiles': profiles or [],
                'note': 'Nenhum registro para analisar'
            }
        
        total_docs = len(documents)
        print(f"🎭 Analisando sentimento de {total_docs} registros...")
        
        # 🆕 ANÁLISE COM LLM (mais precisa)
        if use_llm:
            return self._analyze_sentiment_with_llm(documents, profiles)
        
        # 🔧 FALLBACK: Análise por palavras-chave (mais rápida)
        return self._analyze_sentiment_with_keywords(documents, profiles)
    
    def _analyze_sentiment_with_llm(
        self,
        documents: List[Dict[str, Any]],
        profiles: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        🆕 Análise de sentimento usando LLM em batch.
        
        Processa todos os documentos em lotes para análise precisa.
        """
        total_docs = len(documents)
        batch_size = 50  # Processa 50 posts por vez
        
        positive_count = 0
        negative_count = 0
        neutral_count = 0
        
        # Processa em batches
        for i in range(0, total_docs, batch_size):
            batch = documents[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (total_docs + batch_size - 1) // batch_size
            
            print(f"   📦 Processando lote {batch_num}/{total_batches} ({len(batch)} posts)...")
            
            # Prepara texto do batch
            batch_text = "\n\n---POST---\n\n".join([
                f"POST {j+1}:\n{doc['text'][:800]}"  # Limita cada post a 800 chars
                for j, doc in enumerate(batch)
            ])
            
            # Prompt para análise em batch
            prompt = f"""Analise o sentimento de cada um dos {len(batch)} posts abaixo.

INSTRUÇÕES:
- Classifique cada post como: POSITIVO, NEGATIVO ou NEUTRO
- Considere tanto a legenda quanto os comentários dos usuários
- Analise o tom geral da conversa
- Se houver divergência entre legenda e comentários, priorize o sentimento dominante

POSTS:
{batch_text}

Retorne APENAS um JSON com o formato:
{{
    "sentiments": ["POSITIVO", "NEGATIVO", "NEUTRO", ...],
    "reasoning": "Breve explicação da análise geral"
}}

A lista "sentiments" deve ter EXATAMENTE {len(batch)} elementos, um para cada post."""

            try:
                # Usa provider configurado (DeepSeek ou Ollama)
                if DEFAULT_PROVIDER == 'deepseek':
                    model = DEEPSEEK_MODEL
                else:
                    model = "qwen3:30b"
                
                response = llm_chat.chat(
                    model=model,
                    messages=[{'role': 'user', 'content': prompt}]
                )
                
                response_text = response['message']['content']
                
                # Parse JSON
                if '```json' in response_text:
                    response_text = response_text.split('```json')[1].split('```')[0]
                elif '```' in response_text:
                    response_text = response_text.split('```')[1].split('```')[0]
                
                result = json.loads(response_text.strip())
                sentiments = result.get('sentiments', [])
                
                # Conta sentimentos
                for s in sentiments:
                    s_upper = s.upper()
                    if 'POSITIV' in s_upper:
                        positive_count += 1
                    elif 'NEGATIV' in s_upper:
                        negative_count += 1
                    else:
                        neutral_count += 1
                
                print(f"      ✓ Lote analisado com sucesso")
            
            except Exception as e:
                print(f"      ⚠️ Erro no lote {batch_num}: {e}")
                # Fallback: marca todos como neutros
                neutral_count += len(batch)
        
        # Calcula percentuais
        total = positive_count + negative_count + neutral_count
        pos_pct = (positive_count / total * 100) if total > 0 else 0
        neg_pct = (negative_count / total * 100) if total > 0 else 0
        neu_pct = (neutral_count / total * 100) if total > 0 else 0
        
        # Define tendência
        if pos_pct > neg_pct and pos_pct > neu_pct:
            trend = 'positive'
        elif neg_pct > pos_pct and neg_pct > neu_pct:
            trend = 'negative'
        else:
            trend = 'neutral'
        
        return {
            'total_analyzed': total_docs,
            'positive': positive_count,
            'negative': negative_count,
            'neutral': neutral_count,
            'positive_pct': round(pos_pct, 1),
            'negative_pct': round(neg_pct, 1),
            'neutral_pct': round(neu_pct, 1),
            'trend': trend,
            'profiles': profiles or [],
            'note': f'Análise usando IA (modelo: {DEFAULT_PROVIDER.upper()}) - {total_docs} registros completos'
        }
    
    def _analyze_sentiment_with_keywords(
        self,
        documents: List[Dict[str, Any]],
        profiles: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        🔧 FALLBACK: Análise simplificada por palavras-chave.
        Usado quando LLM não está disponível ou para análises rápidas.
        """
        positive_keywords = [
            'parabéns', 'excelente', 'ótimo', 'maravilhoso', 'sucesso',
            'conquista', 'vitória', 'alegria', 'feliz', 'orgulho',
            'gratidão', 'obrigado', 'apoio', 'solidariedade', 'esperança',
            'incrível', 'fantástico', 'perfeito', 'adorei', 'amei'
        ]
        
        negative_keywords = [
            'problema', 'crítica', 'péssimo', 'ruim', 'revolta',
            'absurdo', 'inadmissível', 'vergonha', 'indignação', 'protesto',
            'denúncia', 'descaso', 'abandono', 'precário', 'injustiça',
            'horrível', 'terrível', 'lamentável', 'triste', 'decepção'
        ]
        
        positive_count = 0
        negative_count = 0
        neutral_count = 0
        
        for doc in documents:
            text_lower = doc['text'].lower()
            
            pos_score = sum(1 for kw in positive_keywords if kw in text_lower)
            neg_score = sum(1 for kw in negative_keywords if kw in text_lower)
            
            if pos_score > neg_score and pos_score > 0:
                positive_count += 1
            elif neg_score > pos_score and neg_score > 0:
                negative_count += 1
            else:
                neutral_count += 1
        
        total = len(documents)
        pos_pct = (positive_count / total * 100) if total > 0 else 0
        neg_pct = (negative_count / total * 100) if total > 0 else 0
        neu_pct = (neutral_count / total * 100) if total > 0 else 0
        
        if pos_pct > neg_pct and pos_pct > neu_pct:
            trend = 'positive'
        elif neg_pct > pos_pct and neg_pct > neu_pct:
            trend = 'negative'
        else:
            trend = 'neutral'
        
        return {
            'total_analyzed': total,
            'positive': positive_count,
            'negative': negative_count,
            'neutral': neutral_count,
            'positive_pct': round(pos_pct, 1),
            'negative_pct': round(neg_pct, 1),
            'neutral_pct': round(neu_pct, 1),
            'trend': trend,
            'profiles': profiles or [],
            'note': f'Análise rápida por palavras-chave - {total} registros'
        }
    
    def _calculate_metrics(
        self,
        posts: List[Dict],
        news: List[Dict]
    ) -> Dict[str, Any]:
        """Calcula métricas agregadas."""
        
        if not posts and not news:
            return self._empty_metrics()
        
        # Métricas de posts
        total_likes = sum(p.get('likesCount', 0) for p in posts)
        total_comments = sum(p.get('commentsCount', 0) for p in posts)
        total_engagement = total_likes + total_comments
        
        # Médias
        avg_likes = total_likes / len(posts) if posts else 0
        avg_comments = total_comments / len(posts) if posts else 0
        avg_engagement = total_engagement / len(posts) if posts else 0
        
        # Top posts
        top_by_likes = sorted(posts, key=lambda x: x.get('likesCount', 0), reverse=True)[:5]
        top_by_engagement = sorted(
            posts,
            key=lambda x: x.get('likesCount', 0) + x.get('commentsCount', 0),
            reverse=True
        )[:5]
        
        # Distribuição por perfil
        profile_dist = {}
        for post in posts:
            profile = post.get('profile', 'unknown')
            if profile not in profile_dist:
                profile_dist[profile] = {
                    'count': 0,
                    'likes': 0,
                    'comments': 0,
                    'engagement': 0
                }
            profile_dist[profile]['count'] += 1
            profile_dist[profile]['likes'] += post.get('likesCount', 0)
            profile_dist[profile]['comments'] += post.get('commentsCount', 0)
            profile_dist[profile]['engagement'] += (
                post.get('likesCount', 0) + post.get('commentsCount', 0)
            )
        
        # Análise temporal (posts por dia)
        daily_posts = {}
        for post in posts:
            try:
                post_date = date_parser.parse(post['timestamp'])
                post_date = self._normalize_datetime(post_date)
                date_str = post_date.date().isoformat()
                
                if date_str not in daily_posts:
                    daily_posts[date_str] = {
                        'count': 0,
                        'likes': 0,
                        'comments': 0
                    }
                daily_posts[date_str]['count'] += 1
                daily_posts[date_str]['likes'] += post.get('likesCount', 0)
                daily_posts[date_str]['comments'] += post.get('commentsCount', 0)
            except Exception as e:
                print(f"⚠️ Erro ao processar data para análise temporal: {e}")
        
        # Análise de notícias
        news_publishers = {}
        for article in news:
            pub = article.get('publisher_name', 'Desconhecido')
            news_publishers[pub] = news_publishers.get(pub, 0) + 1
        
        return {
            'posts': {
                'total': len(posts),
                'total_likes': total_likes,
                'total_comments': total_comments,
                'total_engagement': total_engagement,
                'avg_likes': round(avg_likes, 2),
                'avg_comments': round(avg_comments, 2),
                'avg_engagement': round(avg_engagement, 2),
                'top_by_likes': [
                    {
                        'profile': p.get('profile'),
                        'likes': p.get('likesCount', 0),
                        'comments': p.get('commentsCount', 0),
                        'url': p.get('url'),
                        'caption': p.get('caption', '')[:100] + '...'
                    }
                    for p in top_by_likes
                ],
                'top_by_engagement': [
                    {
                        'profile': p.get('profile'),
                        'likes': p.get('likesCount', 0),
                        'comments': p.get('commentsCount', 0),
                        'engagement': p.get('likesCount', 0) + p.get('commentsCount', 0),
                        'url': p.get('url'),
                        'caption': p.get('caption', '')[:100] + '...'
                    }
                    for p in top_by_engagement
                ],
                'by_profile': profile_dist,
                'daily_distribution': daily_posts
            },
            'news': {
                'total': len(news),
                'by_publisher': news_publishers
            },
            'summary': {
                'total_records': len(posts) + len(news),
                'posts_count': len(posts),
                'news_count': len(news),
                'total_engagement': total_engagement,
                'avg_engagement_per_post': round(avg_engagement, 2)
            }
        }
    
    def _empty_metrics(self) -> Dict[str, Any]:
        """Retorna estrutura vazia quando não há dados."""
        return {
            'posts': {
                'total': 0,
                'total_likes': 0,
                'total_comments': 0,
                'total_engagement': 0,
                'avg_likes': 0,
                'avg_comments': 0,
                'avg_engagement': 0,
                'top_by_likes': [],
                'top_by_engagement': [],
                'by_profile': {},
                'daily_distribution': {}
            },
            'news': {
                'total': 0,
                'by_publisher': {}
            },
            'summary': {
                'total_records': 0,
                'posts_count': 0,
                'news_count': 0,
                'total_engagement': 0,
                'avg_engagement_per_post': 0
            },
            'sentiment': {  # 🆕
                'total_analyzed': 0,
                'positive': 0,
                'negative': 0,
                'neutral': 0,
                'positive_pct': 0,
                'negative_pct': 0,
                'neutral_pct': 0,
                'trend': 'neutral',
                'profiles': [],
                'note': 'Nenhum dado disponível'
            }
        }
    
    def get_sentiment_distribution(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        profile_filter: Optional[List[str]] = None
    ) -> Dict[str, int]:
        """
        Analisa distribuição de sentimento (DEPRECATED - usar get_date_range_data).
        
        TODO: Remover em versão futura.
        """
        # Redireciona para novo método
        metrics = self.get_date_range_data(start_date, end_date, profile_filter)
        return metrics.get('sentiment', {
            'positive': 0,
            'negative': 0,
            'neutral': 0,
            'note': 'Use get_date_range_data para análise completa'
        })
    
    def get_trending_topics(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Identifica tópicos mais mencionados no período.
        
        Args:
            start_date: Data inicial
            end_date: Data final
            limit: Número máximo de tópicos
        
        Returns:
            Lista de tópicos com contagem
        """
        # TODO: Implementar extração de tópicos via NLP
        # Por enquanto, analisa hashtags mais usadas
        
        where_clause = {}
        results = self.collection.get(
            where=where_clause,
            limit=10000,
            include=['metadatas']
        )
        
        # Normaliza datas de filtro
        start_filter = None
        end_filter = None
        
        if start_date:
            try:
                start_filter = self._normalize_datetime(date_parser.parse(start_date))
            except:
                pass
        
        if end_date:
            try:
                end_filter = self._normalize_datetime(date_parser.parse(end_date))
            except:
                pass
        
        hashtag_count = {}
        
        for metadata in results['metadatas']:
            # Filtra por data se necessário
            try:
                if start_filter or end_filter:
                    post_date = date_parser.parse(metadata['timestamp'])
                    post_date = self._normalize_datetime(post_date)
                    
                    if start_filter and post_date < start_filter:
                        continue
                    if end_filter and post_date > end_filter:
                        continue
            except:
                pass
            
            # Conta hashtags
            hashtags = metadata.get('hashtags', [])
            if isinstance(hashtags, list):
                for tag in hashtags:
                    hashtag_count[tag] = hashtag_count.get(tag, 0) + 1
        
        # Ordena e retorna top N
        sorted_tags = sorted(
            hashtag_count.items(),
            key=lambda x: x[1],
            reverse=True
        )[:limit]
        
        return [
            {'topic': tag, 'count': count}
            for tag, count in sorted_tags
        ]
    
    def get_sentiment_by_profile(
        self,
        profile: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = None,  # 🆕 None = sem limite (usa todos)
        use_llm: bool = True  # 🆕 Usar LLM por padrão
    ) -> Dict[str, Any]:
        """
        Analisa sentimento de um perfil específico.
        
        Args:
            profile: Nome do perfil (@dceuff, @reitor, @vicereitor)
            start_date: Data inicial (ISO format ou None)
            end_date: Data final (ISO format ou None)
            limit: Máximo de posts a analisar (None = todos)
            use_llm: Se True, usa IA avançada; False = palavras-chave
        
        Returns:
            Dict com análise de sentimento do perfil
        """
        profile_clean = profile.replace('@', '').lower()
        
        where_clause = {'profile': profile_clean}
        
        results = self.collection.get(
            where=where_clause,
            limit=100000,  # 🆕 Busca tudo
            include=['metadatas', 'documents']
        )
        
        if not results['ids']:
            return {
                'profile': profile_clean,
                'total_analyzed': 0,
                'positive': 0,
                'negative': 0,
                'neutral': 0,
                'positive_pct': 0,
                'negative_pct': 0,
                'neutral_pct': 0,
                'trend': 'neutral',
                'note': f'Nenhum registro encontrado para @{profile_clean}'
            }
        
        # Normaliza datas de filtro
        start_filter = None
        end_filter = None
        
        if start_date:
            try:
                start_filter = self._normalize_datetime(date_parser.parse(start_date))
            except Exception as e:
                print(f"⚠️ Erro ao parsear start_date '{start_date}': {e}")
        
        if end_date:
            try:
                end_filter = self._normalize_datetime(date_parser.parse(end_date))
            except Exception as e:
                print(f"⚠️ Erro ao parsear end_date '{end_date}': {e}")
        
        # Filtra por data e coleta documentos
        filtered_documents = []
        
        for i, metadata in enumerate(results['metadatas']):
            try:
                if metadata.get('content_type') == 'news':
                    continue
                
                post_date = date_parser.parse(metadata['timestamp'])
                post_date = self._normalize_datetime(post_date)
                
                if start_filter and post_date < start_filter:
                    continue
                
                if end_filter and post_date > end_filter:
                    continue
                
                if i < len(results['documents']):
                    filtered_documents.append({
                        'text': results['documents'][i],
                        'metadata': metadata
                    })
            
            except Exception as e:
                print(f"⚠️ Erro ao processar metadata: {e}")
                continue
        
        # 🆕 Aplica limite apenas se especificado
        if limit:
            filtered_documents = filtered_documents[:limit]
        
        # Analisa sentimento (com LLM ou keywords)
        sentiment_data = self._analyze_sentiment_batch(
            filtered_documents,
            [profile_clean],
            use_llm=use_llm  # 🆕 Passa modo de análise
        )
        
        sentiment_data['profile'] = profile_clean
        sentiment_data['display_name'] = f"@{profile_clean}"
        
        return sentiment_data

def main():
    """Função de teste."""
    print("=== Testando Dashboard Analytics ===\n")
    
    em = EmbeddingManager()
    analytics = DashboardAnalytics(em)
    
    # Teste: últimos 30 dias
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    print("📊 Métricas dos últimos 30 dias:\n")
    metrics = analytics.get_date_range_data(
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat()
    )
    
    print(f"Total de registros: {metrics['summary']['total_records']}")
    print(f"Registros: {metrics['posts']['total']}")
    print(f"Notícias: {metrics['news']['total']}")
    print(f"Engajamento total: {metrics['posts']['total_engagement']}")
    print(f"Média de engajamento: {metrics['posts']['avg_engagement']}")
    
    # 🆕 Teste de sentimento
    print("\n🎭 Análise de Sentimento:")
    sentiment = metrics.get('sentiment', {})
    print(f"Total analisado: {sentiment.get('total_analyzed', 0)}")
    print(f"✅ Positivo: {sentiment.get('positive', 0)} ({sentiment.get('positive_pct', 0)}%)")
    print(f"❌ Negativo: {sentiment.get('negative', 0)} ({sentiment.get('negative_pct', 0)}%)")
    print(f"⚪ Neutro: {sentiment.get('neutral', 0)} ({sentiment.get('neutral_pct', 0)}%)")
    print(f"📊 Tendência: {sentiment.get('trend', 'N/A')}")
    
    print("\n#️⃣ Top 5 hashtags:")
    topics = analytics.get_trending_topics(limit=5)
    for i, topic in enumerate(topics, 1):
        print(f"{i}. #{topic['topic']}: {topic['count']} menções")


if __name__ == '__main__':
    main()