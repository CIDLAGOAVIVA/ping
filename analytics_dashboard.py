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
        self.cache = SentimentCache()
        self.exporter = ReportExporter()
    
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
        # 🆕 Trata profile=None (todos os perfis)
        if profile is None:
            where_clause = None
            profile_clean = None
        else:
            profile_clean = profile.replace('@', '').lower()
            where_clause = {'profile': profile_clean}
        
        results = self.collection.get(
            where=where_clause,
            limit=100000,
            include=['metadatas', 'documents']
        )
        
        if not results['ids']:
            profile_display = f'@{profile_clean}' if profile_clean else 'todos os perfis'
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
                'note': f'Nenhum registro encontrado para {profile_display}',
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
            [profile_clean] if profile_clean else None,
            use_llm=use_llm
        )
        
        sentiment_data['profile'] = profile_clean
        sentiment_data['display_name'] = f"@{profile_clean}" if profile_clean else "Todos os perfis"
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
        
        # Detecta tópicos emergentes
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
        Detecta tópicos emergentes através de análise de temas com LLM.
        
        Args:
            posts: Lista de posts com 'caption' e opcionalmente 'comments_text'
        
        Returns:
            Dicionário com tópicos emergentes baseados em temas extraídos por LLM
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
        
        total_posts = len(posts)
        print(f"🔍 Iniciando análise de temas com LLM para {total_posts} posts...")
        
        # Contadores
        theme_counter = {}
        hashtag_counter = {}
        total_texts_analyzed = 0
        
        # Coleta todos os textos individuais
        all_texts = []
        batch_size = 20
        
        for i, post in enumerate(posts):
            # Legenda
            caption = post.get('caption', '')
            if caption and len(caption.strip()) > 10:
                all_texts.append((caption, 'caption', i))
            
            # Comentários
            comments = post.get('comments_text', '')
            if comments:
                individual_comments = [c.strip() for c in comments.split('\n\n') if len(c.strip()) > 10]
                for comment in individual_comments[:5]:
                    all_texts.append((comment, 'comment', i))
            
            # Processa hashtags
            hashtags = post.get('hashtags', [])
            if isinstance(hashtags, list):
                for tag in hashtags:
                    tag_clean = tag.lower().replace('#', '').strip()
                    tag_valid = ''.join(
                        c for c in tag_clean 
                        if c.isalnum() or c in ['á', 'é', 'í', 'ó', 'ú', 'â', 'ê', 'ô', 'ã', 'õ', 'ç', 'ü', 'ñ']
                    )
                    if len(tag_valid) >= 3 and not tag_valid.isdigit():
                        if any(c.isalpha() for c in tag_valid):
                            hashtag_counter[tag_valid] = hashtag_counter.get(tag_valid, 0) + 1
        
        print(f"   📝 Total de textos coletados: {len(all_texts)}")
        
        # Processa textos em batches com LLM
        for i in range(0, len(all_texts), batch_size):
            batch = all_texts[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(all_texts) + batch_size - 1) // batch_size
            
            print(f"   🔮 Processando lote {batch_num}/{total_batches} ({len(batch)} textos)...")
            
            try:
                import llm_chat
                from config import DEFAULT_PROVIDER, DEEPSEEK_MODEL
                
                texts_numbered = "\n\n".join([
                    f"TEXTO {j+1}:\n{text[:400]}"
                    for j, (text, _, _) in enumerate(batch)
                ])
                
                prompt = f"""Você é um especialista em análise de comunicação universitária.

Analise cada um dos {len(batch)} textos abaixo e extraia o TEMA CENTRAL de cada um.

INSTRUÇÕES:
- Retorne um rótulo de tema CONCISO (2-5 palavras) que capture a essência do texto
- Normalize temas similares para o mesmo rótulo
- Se o texto for muito genérico, use "Outros"
- Seja consistente nos rótulos

TEXTOS:
{texts_numbered}

Retorne APENAS um JSON com o formato:
{{
    "themes": ["Tema 1", "Tema 2", ...]
}}

A lista deve ter EXATAMENTE {len(batch)} elementos."""

                model = DEEPSEEK_MODEL if DEFAULT_PROVIDER == 'deepseek' else "qwen3:30b"
                
                response = llm_chat.chat(
                    model=model,
                    messages=[{'role': 'user', 'content': prompt}]
                )
                
                response_text = response['message']['content']
                
                if '```json' in response_text:
                    response_text = response_text.split('```json')[1].split('```')[0]
                elif '```' in response_text:
                    response_text = response_text.split('```')[1].split('```')[0]
                
                import json
                result = json.loads(response_text.strip())
                themes = result.get('themes', [])
                
                if len(themes) != len(batch):
                    print(f"      ⚠️ LLM retornou {len(themes)} temas, esperado {len(batch)}. Usando fallback.")
                    themes = ["Outros"] * len(batch)
                
                for theme in themes:
                    theme_normalized = ' '.join(word.capitalize() for word in theme.strip().split())
                    theme_counter[theme_normalized] = theme_counter.get(theme_normalized, 0) + 1
                    total_texts_analyzed += 1
                
                print(f"      ✓ Lote processado: {len(themes)} temas extraídos")
            
            except Exception as e:
                print(f"      ❌ Erro ao processar lote {batch_num}: {e}")
                theme_counter["Outros"] = theme_counter.get("Outros", 0) + len(batch)
                total_texts_analyzed += len(batch)
        
        print(f"   ✅ Análise concluída: {len(theme_counter)} temas únicos identificados")
        
        # Remove tema genérico se houver temas específicos
        if len(theme_counter) > 1 and "Outros" in theme_counter:
            if theme_counter["Outros"] < total_texts_analyzed * 0.3:
                del theme_counter["Outros"]
        
        # Top temas
        top_themes = sorted(theme_counter.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Top hashtags
        top_hashtags = sorted(hashtag_counter.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Monta resposta
        topics = []
        
        for theme, count in top_themes:
            percentage = (count / total_texts_analyzed * 100) if total_texts_analyzed > 0 else 0
            
            if percentage >= 15.0:
                growth = 75
            elif percentage >= 10.0:
                growth = 60
            elif percentage >= 5.0:
                growth = 45
            elif percentage >= 3.0:
                growth = 30
            else:
                growth = 10
            
            topics.append({
                'term': theme,
                'count': count,
                'percentage': round(percentage, 1),
                'growth_indicator': growth
            })
        
        hashtags_list = [
            {
                'tag': tag,
                'count': count,
                'percentage': round((count / total_posts) * 100, 1),
                'posts_with_tag': count
            }
            for tag, count in top_hashtags
        ]
        
        print(f"🎯 Resultado final:")
        print(f"   - {len(topics)} temas principais identificados")
        print(f"   - {total_texts_analyzed} textos analisados")
        if topics:
            print(f"   - Top 3 temas: {[t['term'] for t in topics[:3]]}")
        
        return {
            'total_topics': len(topics),
            'total_posts_analyzed': total_posts,
            'topics': topics,
            'top_hashtags': hashtags_list,
            'total_unique_hashtags': len(hashtag_counter),
            'total_hashtag_occurrences': sum(hashtag_counter.values()),
            'analysis_method': 'llm_theme_extraction'
        }