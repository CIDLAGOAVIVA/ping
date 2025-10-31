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
from sentiment_cache import SentimentCache
from report_exporter import ReportExporter

class DashboardAnalytics:
    """Gerenciador de análises para o dashboard."""
    
    def __init__(self, embedding_manager: EmbeddingManager):
        self.em = embedding_manager
        self.tools = QueryTools(embedding_manager)
        self.collection = embedding_manager.collection
        self.cache = SentimentCache()  # 🆕 Inicializa cache
        self.exporter = ReportExporter()  # 🆕 Exportador
    
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
    
    def get_sentiment_by_profile(
        self,
        profile: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = None,
        use_llm: bool = True,
        use_cache: bool = True,
        content_filter: str = "both"  # 🆕 Filtro de conteúdo
    ) -> Dict[str, Any]:
        """
        Analisa sentimento de um perfil específico.
        
        Args:
            profile: Nome do perfil (@dceuff, @reitor, @vicereitor)
            start_date: Data inicial (ISO format ou None)
            end_date: Data final (ISO format ou None)
            limit: Máximo de posts a analisar (None = todos)
            use_llm: Se True, usa IA avançada; False = palavras-chave
            use_cache: Se True, usa cache (padrão: True)
            content_filter: Tipo de conteúdo a analisar:
                - "both": Legenda + Comentários (padrão)
                - "caption": Apenas legendas
                - "comments": Apenas comentários
        
        Returns:
            Dict com análise de sentimento do perfil
        """
        profile_clean = profile.replace('@', '').lower()
        
        where_clause = {'profile': profile_clean}
        
        results = self.collection.get(
            where=where_clause,
            limit=100000,
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
                'note': f'Nenhum registro encontrado para @{profile_clean}',
                'cached': False,
                'content_filter': content_filter
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
                    # 🆕 Aplica filtro de conteúdo
                    full_text = results['documents'][i]
                    filtered_text = self._filter_content_by_type(full_text, metadata, content_filter)
                    
                    # Só adiciona se houver conteúdo após filtragem
                    if filtered_text and filtered_text.strip():
                        filtered_documents.append({
                            'text': filtered_text,
                            'metadata': metadata
                        })
            
            except Exception as e:
                print(f"⚠️ Erro ao processar metadata: {e}")
                continue
        
        # Aplica limite apenas se especificado
        if limit:
            filtered_documents = filtered_documents[:limit]
        
        total_docs = len(filtered_documents)
        
        # 🆕 Verifica cache
        if use_cache and use_llm:
            cached_result = self.cache.get(
                profile=profile_clean,
                start_date=start_date,
                end_date=end_date,
                total_docs=total_docs,
                content_filter=content_filter  # 🆕 Passa filtro para cache
            )
            
            if cached_result:
                cached_result['cached'] = True
                cached_result['profile'] = profile_clean
                cached_result['display_name'] = f"@{profile_clean}"
                cached_result['content_filter'] = content_filter
                return cached_result
        
        # Análise nova (cache miss ou desabilitado)
        sentiment_data = self._analyze_sentiment_batch(
            filtered_documents,
            [profile_clean],
            use_llm=use_llm
        )
        
        sentiment_data['profile'] = profile_clean
        sentiment_data['display_name'] = f"@{profile_clean}"
        sentiment_data['cached'] = False
        sentiment_data['content_filter'] = content_filter
        
        # 🆕 Salva no cache
        if use_cache and use_llm:
            self.cache.set(
                sentiment_data,
                profile=profile_clean,
                start_date=start_date,
                end_date=end_date,
                total_docs=total_docs,
                content_filter=content_filter  # 🆕 Passa filtro para cache
            )
        
        return sentiment_data
    
    def _filter_content_by_type(
        self,
        full_text: str,
        metadata: Dict[str, Any],
        content_filter: str
    ) -> str:
        """
        🆕 Filtra conteúdo do post baseado no tipo selecionado.
        
        Args:
            full_text: Texto completo do post (legenda + comentários)
            metadata: Metadados do post
            content_filter: Tipo de conteúdo ("both", "caption", "comments")
        
        Returns:
            Texto filtrado conforme seleção
        """
        if content_filter == "both":
            return full_text
        
        # 🔍 DEBUG: Vamos ver o que temos
        print(f"\n🔍 DEBUG _filter_content_by_type:")
        print(f"   content_filter: {content_filter}")
        print(f"   metadata keys: {metadata.keys()}")
        print(f"   full_text preview: {full_text[:200]}...")
        
        # Extrai apenas a legenda
        if content_filter == "caption":
            # Tenta pegar do metadata primeiro (mais confiável)
            caption = metadata.get('caption', '')
            if caption:
                return f"Perfil: {metadata.get('profile', '')}\nData: {metadata.get('timestamp', '')}\n\nLegenda: {caption}"
            
            # Fallback: parse do texto completo
            if "=== LEGENDA ===" in full_text and "=== COMENTÁRIOS ===" in full_text:
                parts = full_text.split("=== COMENTÁRIOS ===")
                return parts[0].strip()
            elif "=== LEGENDA ===" in full_text:
                return full_text.strip()
            else:
                # Se não tem marcadores, considera tudo como legenda
                return full_text
        
        # Extrai apenas os comentários
        if content_filter == "comments":
            # Tenta pegar do metadata primeiro
            comments_text = metadata.get('comments_text', '')
            if comments_text:
                print(f"   ✅ Found comments_text in metadata: {len(comments_text)} chars")
                return f"Perfil: {metadata.get('profile', '')}\nData: {metadata.get('timestamp', '')}\n\nComentários:\n{comments_text}"
            
            # Fallback: parse do texto completo
            if "=== COMENTÁRIOS ===" in full_text:
                parts = full_text.split("=== COMENTÁRIOS ===")
                if len(parts) > 1:
                    comments = parts[1].strip()
                    print(f"   ✅ Parsed comments from text: {len(comments)} chars")
                    return f"Comentários:\n{comments}"
            
            # 🆕 Tenta outro formato comum
            if "\n\n---\n\nComentários:" in full_text:
                parts = full_text.split("\n\n---\n\nComentários:")
                if len(parts) > 1:
                    comments = parts[1].strip()
                    print(f"   ✅ Parsed comments (alt format): {len(comments)} chars")
                    return f"Comentários:\n{comments}"
            
            print(f"   ⚠️ NO COMMENTS FOUND - returning empty")
            return ""  # Sem comentários
        
        return full_text  # Fallback
    
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
    
    def get_date_range_data(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        profile_filter: Optional[List[str]] = None,
        use_llm_sentiment: bool = False,
        use_cache: bool = True,
        content_filter: str = "both"
    ) -> Dict[str, Any]:
        """
        Retorna métricas para um intervalo de datas.
        
        Args:
            start_date: Data inicial (ISO format)
            end_date: Data final (ISO format)
            profile_filter: Lista de perfis para filtrar
            use_llm_sentiment: Se True, usa LLM para análise de sentimento
            use_cache: Se True, usa cache de sentimento
            content_filter: Tipo de conteúdo ("both", "caption", "comments")
        
        Returns:
            Dicionário com métricas agregadas
        """
        # Busca todos os dados
        results = self.collection.get(
            limit=100000,
            include=['documents', 'metadatas']
        )
        
        if not results['ids']:
            return self._empty_metrics()
        
        # Filtra por data e perfil
        filtered_posts = []
        filtered_news = []
        
        for i, metadata in enumerate(results['metadatas']):
            # Filtro de perfil
            if profile_filter and metadata.get('profile') not in profile_filter:
                continue
            
            # Filtro de data
            if start_date or end_date:
                try:
                    post_date = date_parser.parse(metadata['timestamp'])
                    post_date = self._normalize_datetime(post_date)
                    
                    if start_date:
                        start_dt = date_parser.parse(start_date)
                        start_dt = self._normalize_datetime(start_dt)
                        if post_date < start_dt:
                            continue
                    
                    if end_date:
                        end_dt = date_parser.parse(end_date)
                        end_dt = self._normalize_datetime(end_dt)
                        if post_date > end_dt:
                            continue
                except Exception as e:
                    print(f"⚠️ Erro ao parsear data: {e}")
                    continue
            
            # Separa posts e notícias
            content_type = metadata.get('content_type', 'instagram_post')
            doc_data = {
                'text': results['documents'][i],
                'metadata': metadata,
                'profile': metadata.get('profile', ''),
                'url': metadata.get('url', ''),
                'timestamp': metadata.get('timestamp', ''),
                'likesCount': metadata.get('likesCount', 0),
                'commentsCount': metadata.get('commentsCount', 0),
                'caption': metadata.get('caption', ''),
                'hashtags': metadata.get('hashtags', []),
                'mentions': metadata.get('mentions', []),
                'type': metadata.get('type', ''),
                'content_type': content_type
            }
            
            if content_type == 'news':
                doc_data.update({
                    'title': metadata.get('title', ''),
                    'publisher_name': metadata.get('publisher_name', '')
                })
                filtered_news.append(doc_data)
            else:
                filtered_posts.append(doc_data)
        
        # Calcula métricas
        metrics = self._calculate_metrics(filtered_posts, filtered_news)
        
        # 🆕 Detecta tópicos emergentes
        emerging_topics = self._detect_emerging_topics(filtered_posts)
        metrics['emerging_topics'] = emerging_topics
        
        # Análise de sentimento (se solicitada)
        if use_llm_sentiment and filtered_posts:
            sentiment = self._analyze_sentiment_batch(
                [{'text': p['text'], 'metadata': p['metadata']} for p in filtered_posts],
                profiles=profile_filter,
                use_llm=True
            )
            metrics['sentiment'] = sentiment
        elif filtered_posts:
            sentiment = self._analyze_sentiment_batch(
                [{'text': p['text'], 'metadata': p['metadata']} for p in filtered_posts],
                profiles=profile_filter,
                use_llm=False
            )
            metrics['sentiment'] = sentiment
        
        return metrics
    
    def _detect_emerging_topics(self, posts: List[Dict]) -> Dict[str, Any]:
        """
        🆕 Detecta tópicos emergentes através das legendas e hashtags.
        
        Args:
            posts: Lista de posts a analisar
        
        Returns:
            Dicionário com tópicos emergentes e hashtags
        """
        if not posts:
            return {
                'total_topics': 0,
                'total_posts_analyzed': 0,
                'topics': [],
                'top_hashtags': [],
                'total_unique_hashtags': 0,
                'total_hashtag_occurrences': 0
            }
        
        # Palavras comuns a ignorar (stopwords)
        stopwords = {
            'de', 'da', 'do', 'das', 'dos', 'a', 'o', 'as', 'os', 'um', 'uma',
            'e', 'é', 'para', 'com', 'por', 'em', 'no', 'na', 'nos', 'nas',
            'que', 'se', 'não', 'mais', 'como', 'seu', 'sua', 'ou', 'ao',
            'pelos', 'pelas', 'esse', 'essa', 'este', 'esta', 'isso', 'isto',
            'aquele', 'aquela', 'aquilo', 'já', 'também', 'só', 'pelo', 'pela',
            'até', 'sem', 'sob', 'sobre', 'após', 'antes', 'quando', 'onde',
            'quem', 'qual', 'quais', 'quanto', 'quantos', 'foi', 'ser', 'ter',
            'estar', 'fazer', 'ir', 'vir', 'dar', 'ver', 'saber', 'poder',
            'hoje', 'ontem', 'amanhã', 'agora', 'depois', 'sempre', 'nunca',
            'muito', 'pouco', 'tudo', 'nada', 'algo', 'alguém', 'ninguém',
            'https', 'http', 'www', 'com', 'br', 'instagram', 'post', 'foto'
        }
        
        # Contadores
        term_counter = {}
        hashtag_counter = {}
        
        for post in posts:
            # Analisa caption/legenda
            caption = post.get('caption', '')
            if caption:
                # Tokeniza e limpa
                words = caption.lower().split()
                for word in words:
                    # Remove pontuação
                    word = ''.join(c for c in word if c.isalnum() or c in ['á', 'é', 'í', 'ó', 'ú', 'â', 'ê', 'ô', 'ã', 'õ', 'ç'])
                    
                    # Filtra palavras muito curtas ou stopwords
                    if len(word) >= 4 and word not in stopwords:
                        term_counter[word] = term_counter.get(word, 0) + 1
            
            # 🔧 MELHORADO: Analisa hashtags com validação
            hashtags = post.get('hashtags', [])
            if isinstance(hashtags, list):
                for tag in hashtags:
                    # Remove # e limpa
                    tag_clean = tag.lower().replace('#', '').strip()
                    
                    # 🆕 VALIDAÇÃO: Apenas letras, números e acentos
                    tag_valid = ''.join(
                        c for c in tag_clean 
                        if c.isalnum() or c in ['á', 'é', 'í', 'ó', 'ú', 'â', 'ê', 'ô', 'ã', 'õ', 'ç', 'ü', 'ñ']
                    )
                    
                    # Ignora hashtags muito curtas ou apenas números
                    if len(tag_valid) >= 3 and not tag_valid.isdigit():
                        # Verifica se tem pelo menos uma letra
                        if any(c.isalpha() for c in tag_valid):
                            hashtag_counter[tag_valid] = hashtag_counter.get(tag_valid, 0) + 1
        
        # Top termos (ordenados por frequência)
        top_terms = sorted(
            term_counter.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]  # 🔧 Top 10 termos
        
        # 🔧 CORRIGIDO: Top 5 hashtags apenas
        top_hashtags = sorted(
            hashtag_counter.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]  # 🆕 Apenas Top 5
        
        # Calcula "indicador de crescimento"
        total_posts = len(posts)
        topics = []
        for term, count in top_terms:
            percentage = (count / total_posts) * 100
            
            if percentage >= 5.0:
                growth = 75
            elif percentage >= 3.0:
                growth = 50
            elif percentage >= 2.0:
                growth = 30
            elif percentage >= 1.0:
                growth = 10
            else:
                growth = 0
            
            topics.append({
                'term': term,
                'count': count,
                'percentage': round(percentage, 1),
                'growth_indicator': growth
            })
        
        # 🆕 Formata hashtags
        hashtags_list = [
            {
                'tag': tag,
                'count': count,
                'percentage': round((count / total_posts) * 100, 1),
                'posts_with_tag': count
            }
            for tag, count in top_hashtags
        ]
        
        # 🔧 DEBUG: Print para verificar
        print(f"DEBUG: Total hashtags únicas: {len(hashtag_counter)}")
        print(f"DEBUG: Top 5 hashtags: {hashtags_list}")
        
        return {
            'total_topics': len(topics),
            'total_posts_analyzed': total_posts,
            'topics': topics,
            'top_hashtags': hashtags_list,  # 🆕 Agora com apenas 5
            'total_unique_hashtags': len(hashtag_counter),
            'total_hashtag_occurrences': sum(hashtag_counter.values())
        }
    
    def invalidate_cache(
        self,
        profile: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ):
        """
        🆕 Invalida cache de sentimento.
        Usar quando novos posts forem adicionados.
        
        Args:
            profile: Perfil a invalidar (None = todos)
            start_date: Data inicial
            end_date: Data final
        """
        if profile:
            self.cache.invalidate(profile, start_date, end_date)
        else:
            # Invalida todos os perfis
            for prof in ['dceuff', 'reitor', 'vicereitor']:
                self.cache.invalidate(prof, start_date, end_date)
            self.cache.invalidate(None, start_date, end_date)  # Cache geral
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        🆕 Retorna estatísticas do cache.
        
        Returns:
            Dict com estatísticas
        """
        return self.cache.get_stats()
    
    def diagnose_content_structure(self, limit: int = 5) -> Dict[str, Any]:
        """
        🔬 Diagnóstico: Verifica como os dados estão estruturados.
        
        Args:
            limit: Número de documentos a verificar
        
        Returns:
            Dicionário com informações de diagnóstico
        """
        results = self.collection.get(
            limit=limit,
            include=['documents', 'metadatas']
        )
        
        diagnosis = {
            'total_checked': len(results['ids']),
            'samples': [],
            'formats_found': {
                'has_caption_key': 0,
                'has_comments_text_key': 0,
                'has_legenda_marker': 0,
                'has_comentarios_marker': 0,
                'has_alt_format': 0
            }
        }
        
        for i, (doc, meta) in enumerate(zip(results['documents'], results['metadatas'])):
            sample = {
                'index': i,
                'profile': meta.get('profile', 'unknown'),
                'has_caption_key': 'caption' in meta,
                'has_comments_text_key': 'comments_text' in meta,
                'doc_preview': doc[:300] + "..." if len(doc) > 300 else doc,
                'metadata_keys': list(meta.keys())
            }
            
            # Verifica formatos no documento
            if '=== LEGENDA ===' in doc:
                diagnosis['formats_found']['has_legenda_marker'] += 1
                sample['has_legenda_marker'] = True
            
            if '=== COMENTÁRIOS ===' in doc:
                diagnosis['formats_found']['has_comentarios_marker'] += 1
                sample['has_comentarios_marker'] = True
            
            if '\n\n---\n\nComentários:' in doc:
                diagnosis['formats_found']['has_alt_format'] += 1
                sample['has_alt_format'] = True
            
            if 'caption' in meta:
                diagnosis['formats_found']['has_caption_key'] += 1
            
            if 'comments_text' in meta:
                diagnosis['formats_found']['has_comments_text_key'] += 1
            
            diagnosis['samples'].append(sample)
        
        return diagnosis

    def export_report(
        self,
        metrics: Dict[str, Any],
        format: str = 'csv',
        filename: Optional[str] = None
    ) -> Any:
        """
        🆕 Exporta relatório em CSV ou PDF.
        
        Args:
            metrics: Métricas do dashboard
            format: Formato ('csv' ou 'pdf')
            filename: Nome do arquivo (opcional)
        
        Returns:
            String (CSV) ou bytes (PDF)
        """
        if format.lower() == 'csv':
            return self.exporter.export_to_csv(metrics, filename)
        elif format.lower() == 'pdf':
            return self.exporter.export_to_pdf(metrics, filename)
        else:
            raise ValueError(f"Formato inválido: {format}. Use 'csv' ou 'pdf'.")
    
    def generate_policy_recommendations(
        self,
        profile: Optional[str] = None,
        content_filter: str = "both",
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        🆕 Gera recomendações de políticas baseadas em críticas identificadas.
        
        Args:
            profile: Perfil a analisar (None = todos)
            content_filter: Tipo de conteúdo ("both", "caption", "comments")
            use_cache: Se True, usa cache de sentimento
        
        Returns:
            Dicionário com recomendações categorizadas
        """
        from config import DEFAULT_PROVIDER, DEEPSEEK_MODEL
        import llm_chat
        
        print(f"\n🔮 Gerando recomendações de políticas...")
        
        # 1. Obter análise de sentimento
        sentiment = self.get_sentiment_by_profile(
            profile=profile,
            content_filter=content_filter,
            use_llm=True,
            use_cache=use_cache
        )
        
        if sentiment.get('total_analyzed', 0) == 0:
            return {
                'has_recommendations': False,
                'message': 'Não há dados suficientes para gerar recomendações.',
                'recommendations': []
            }
        
        # 2. Coletar posts negativos para análise detalhada
        where_clause = {}
        if profile:
            where_clause['profile'] = profile
        
        results = self.collection.get(
            where=where_clause,
            include=['documents', 'metadatas'],
            limit=500  # Analisa mais posts para ter contexto
        )
        
        # 3. Filtrar e preparar conteúdo negativo
        negative_content = []
        
        for doc, meta in zip(results['documents'], results['metadatas']):
            # Aplica filtro de conteúdo
            filtered_text = self._filter_content_by_type(doc, meta, content_filter)
            
            if not filtered_text.strip():
                continue
            
            negative_content.append({
                'text': filtered_text[:500],  # Limita tamanho
                'profile': meta.get('profile', ''),
                'date': meta.get('timestamp', '')
            })
        
        if not negative_content:
            return {
                'has_recommendations': False,
                'message': 'Nenhum conteúdo disponível para análise.',
                'recommendations': []
            }
        
        # 4. Limitar a 50 posts para não sobrecarregar LLM
        sample = negative_content[:50]
        
        # 5. Construir prompt para análise de críticas
        content_text = "\n\n---\n\n".join([
            f"Post {i+1} (@{item['profile']}):\n{item['text']}"
            for i, item in enumerate(sample)
        ])
        
        prompt = f"""Você é um consultor de políticas públicas e comunicação institucional.

Analise os posts/comentários abaixo sobre perfis institucionais da UFF (Universidade Federal Fluminense).

CONTEÚDO ANALISADO:
{content_text}

ANÁLISE DE SENTIMENTO GERAL:
- Total analisado: {sentiment.get('total_analyzed', 0)} registros
- Negativos: {sentiment.get('negative', 0)} ({sentiment.get('negative_pct', 0)}%)
- Neutros: {sentiment.get('neutral', 0)} ({sentiment.get('neutral_pct', 0)}%)
- Positivos: {sentiment.get('positive', 0)} ({sentiment.get('positive_pct', 0)}%)
- Tendência: {sentiment.get('trend', 'N/A')}

TAREFA:
Identifique as PRINCIPAIS CRÍTICAS e PROBLEMAS mencionados, depois sugira RECOMENDAÇÕES DE POLÍTICAS concretas e viáveis.

Retorne APENAS um JSON no formato:

{{
  "summary": "Resumo das principais críticas identificadas (2-3 frases)",
  "critical_areas": [
    {{
      "area": "Nome da área problemática",
      "frequency": "alta/média/baixa",
      "examples": ["Exemplo de crítica 1", "Exemplo 2"]
    }}
  ],
  "recommendations": [
    {{
      "priority": "alta/média/baixa",
      "area": "Área a melhorar",
      "action": "Ação específica recomendada",
      "expected_impact": "Impacto esperado",
      "implementation_time": "curto/médio/longo prazo",
      "responsible": "Sugestão de responsável"
    }}
  ],
  "positive_aspects": [
    "Aspecto positivo a manter"
  ],
  "general_observations": "Observações gerais sobre comunicação e gestão"
}}

Seja ESPECÍFICO, PRÁTICO e focado em AÇÕES CONCRETAS."""

        try:
            # Usa provider configurado
            if DEFAULT_PROVIDER == 'deepseek':
                model = DEEPSEEK_MODEL
            else:
                model = "qwen3:30b"
            
            print(f"   🤖 Usando {model} para análise...")
            
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
            
            import json
            analysis = json.loads(response_text.strip())
            
            # Adiciona metadados
            analysis['has_recommendations'] = True
            analysis['generated_at'] = datetime.now().isoformat()
            analysis['profile'] = profile or 'todos os perfis'
            analysis['content_filter'] = content_filter
            analysis['sentiment_data'] = {
                'total_analyzed': sentiment.get('total_analyzed', 0),
                'negative_pct': sentiment.get('negative_pct', 0),
                'trend': sentiment.get('trend', 'N/A')
            }
            
            print(f"   ✅ {len(analysis.get('recommendations', []))} recomendações geradas")
            
            return analysis
        
        except Exception as e:
            print(f"   ❌ Erro ao gerar recomendações: {e}")
            return {
                'has_recommendations': False,
                'error': str(e),
                'message': 'Erro ao processar recomendações. Tente novamente.',
                'recommendations': []
            }
    

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