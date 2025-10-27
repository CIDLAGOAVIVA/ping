"""
Ferramentas de consulta especializadas para análise de posts do Instagram.
Estas ferramentas fornecem queries estruturadas que complementam o RAG semântico.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from dateutil import parser as date_parser
import json
import llm_chat
from config import DEFAULT_PROVIDER, DEEPSEEK_MODEL, OLLAMA_GENERATION_MODEL

try:
    from ddgs import DDGS
    DDGS_AVAILABLE = True
except ImportError:
    DDGS_AVAILABLE = False


class QueryTools:
    """Ferramentas de consulta para análise estruturada de posts."""
    
    def __init__(self, embedding_manager, llm_model: str = "qwen3:30b"):
        """
        Inicializa as ferramentas com acesso ao banco de dados.
        
        Args:
            embedding_manager: Instância do EmbeddingManager com a coleção
            llm_model: Modelo LLM para análise de sentimento
        """
        self.collection = embedding_manager.collection
        self.llm_model = llm_model
    
    def _filter_instagram_posts(self, results: Dict, profile: Optional[str] = None) -> List[Dict]:
        """
        Filtra apenas posts do Instagram a partir dos resultados do ChromaDB.
        Posts do Instagram têm campos 'likesCount' e 'commentsCount'.
        
        Args:
            results: Resultado do collection.get()
            profile: Filtrar por perfil específico (opcional)
            
        Returns:
            Lista de posts do Instagram com metadados
        """
        posts = []
        for i in range(len(results['ids'])):
            metadata = results['metadatas'][i]
            
            # Filtra apenas posts do Instagram (têm likesCount)
            if 'likesCount' not in metadata:
                continue
            
            # Filtro de perfil se especificado
            if profile and metadata.get('profile') != profile:
                continue
            
            posts.append({
                'id': results['ids'][i],
                'metadata': metadata,
                'document': results['documents'][i]
            })
        
        return posts
    
    def get_top_posts_by_likes(
        self, 
        limit: int = 10, 
        profile: Optional[str] = None,
        min_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retorna os posts com mais curtidas (apenas posts do Instagram).
        
        Args:
            limit: Número de posts a retornar
            profile: Filtrar por perfil específico (opcional)
            min_date: Data mínima no formato ISO (opcional)
            
        Returns:
            Lista de posts ordenados por curtidas (decrescente)
        """
        # Busca apenas posts do Instagram (que têm source=None ou content_type=instagram_post)
        where_conditions = []
        
        # ChromaDB não suporta ordenação nativa, então pegamos todos e ordenamos
        results = self.collection.get(
            limit=10000  # Pega muitos para ordenar
        )
        
        # Converte para lista de dicts - apenas posts Instagram com likesCount
        posts = []
        for i in range(len(results['ids'])):
            metadata = results['metadatas'][i]
            
            # Filtra apenas posts do Instagram (tem likesCount)
            if 'likesCount' not in metadata:
                continue
            
            # Filtro de perfil se especificado
            if profile and metadata.get('profile') != profile:
                continue
            
            # Aplica filtro de data se especificado
            if min_date:
                try:
                    post_date = date_parser.parse(metadata.get('timestamp', ''))
                    min_date_obj = date_parser.parse(min_date)
                    if post_date < min_date_obj:
                        continue
                except:
                    pass
            
            posts.append({
                'id': results['ids'][i],
                'metadata': metadata,
                'document': results['documents'][i]
            })
        
        # Ordena por curtidas (decrescente)
        posts.sort(key=lambda x: x['metadata'].get('likesCount', 0), reverse=True)
        
        return posts[:limit]
    
    def get_top_posts_by_comments(
        self, 
        limit: int = 10, 
        profile: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retorna os posts com mais comentários (apenas posts do Instagram).
        
        Args:
            limit: Número de posts a retornar
            profile: Filtrar por perfil específico (opcional)
            
        Returns:
            Lista de posts ordenados por comentários (decrescente)
        """
        results = self.collection.get(limit=10000)
        
        posts = []
        for i in range(len(results['ids'])):
            metadata = results['metadatas'][i]
            
            # Filtra apenas posts do Instagram (tem commentsCount)
            if 'commentsCount' not in metadata:
                continue
            
            # Filtro de perfil se especificado
            if profile and metadata.get('profile') != profile:
                continue
            
            posts.append({
                'id': results['ids'][i],
                'metadata': metadata,
                'document': results['documents'][i]
            })
        
        posts.sort(key=lambda x: x['metadata'].get('commentsCount', 0), reverse=True)
        return posts[:limit]
    
    def get_posts_by_engagement(
        self, 
        limit: int = 10, 
        profile: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retorna os posts com maior engajamento (curtidas + comentários, apenas Instagram).
        
        Args:
            limit: Número de posts a retornar
            profile: Filtrar por perfil específico (opcional)
            
        Returns:
            Lista de posts ordenados por engajamento total
        """
        results = self.collection.get(limit=10000)
        
        posts = []
        for i in range(len(results['ids'])):
            metadata = results['metadatas'][i]
            
            # Filtra apenas posts do Instagram (tem ambos os campos)
            if 'likesCount' not in metadata or 'commentsCount' not in metadata:
                continue
            
            # Filtro de perfil se especificado
            if profile and metadata.get('profile') != profile:
                continue
            
            engagement = metadata.get('likesCount', 0) + metadata.get('commentsCount', 0)
            posts.append({
                'id': results['ids'][i],
                'metadata': metadata,
                'engagement': engagement,
                'document': results['documents'][i]
            })
        
        posts.sort(key=lambda x: x['engagement'], reverse=True)
        return posts[:limit]
    
    def get_bottom_posts_by_likes(
        self, 
        limit: int = 10, 
        profile: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retorna os posts com MENOS curtidas (apenas Instagram).
        
        Args:
            limit: Número de posts a retornar
            profile: Filtrar por perfil específico (opcional)
            
        Returns:
            Lista de posts ordenados por curtidas (crescente)
        """
        results = self.collection.get(limit=10000)
        posts = self._filter_instagram_posts(results, profile)
        
        # Ordena por curtidas (CRESCENTE - menos curtidas primeiro)
        posts.sort(key=lambda x: x['metadata'].get('likesCount', 0), reverse=False)
        return posts[:limit]
    
    def get_bottom_posts_by_comments(
        self, 
        limit: int = 10, 
        profile: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retorna os posts com MENOS comentários (apenas Instagram).
        
        Args:
            limit: Número de posts a retornar
            profile: Filtrar por perfil específico (opcional)
            
        Returns:
            Lista de posts ordenados por comentários (crescente)
        """
        results = self.collection.get(limit=10000)
        posts = self._filter_instagram_posts(results, profile)
        
        # Ordena por comentários (CRESCENTE - menos comentários primeiro)
        posts.sort(key=lambda x: x['metadata'].get('commentsCount', 0), reverse=False)
        return posts[:limit]
    
    def get_recent_posts(
        self, 
        days: int = 30, 
        limit: int = 10,
        profile: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retorna os posts mais recentes.
        
        Args:
            days: Número de dias para considerar
            limit: Número de posts a retornar
            profile: Filtrar por perfil específico (opcional)
            
        Returns:
            Lista de posts recentes ordenados por data
        """
        where = {}
        if profile:
            where['profile'] = profile
        
        results = self.collection.get(
            where=where if where else None,
            limit=10000
        )
        
        # Cria cutoff_date com timezone UTC para comparação correta
        from datetime import timezone
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        posts = []
        for i in range(len(results['ids'])):
            metadata = results['metadatas'][i]
            try:
                post_date = date_parser.parse(metadata['timestamp'])
                # Garante que post_date tem timezone para comparação
                if post_date.tzinfo is None:
                    post_date = post_date.replace(tzinfo=timezone.utc)
                
                if post_date >= cutoff_date:
                    posts.append({
                        'id': results['ids'][i],
                        'metadata': metadata,
                        'document': results['documents'][i],
                        'date': post_date
                    })
            except:
                continue
        
        posts.sort(key=lambda x: x['date'], reverse=True)
        return posts[:limit]
    
    def get_posts_with_keyword(
        self, 
        keyword: str, 
        limit: int = 10,
        profile: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Busca posts que contenham uma palavra-chave específica.
        
        Args:
            keyword: Palavra-chave a buscar
            limit: Número de posts a retornar
            profile: Filtrar por perfil específico (opcional)
            
        Returns:
            Lista de posts que contém a palavra-chave
        """
        where = {}
        if profile:
            where['profile'] = profile
        
        results = self.collection.get(
            where=where if where else None,
            limit=10000
        )
        
        keyword_lower = keyword.lower()
        posts = []
        
        for i in range(len(results['ids'])):
            doc = results['documents'][i].lower()
            caption = results['metadatas'][i].get('caption', '').lower()
            
            if keyword_lower in doc or keyword_lower in caption:
                posts.append({
                    'id': results['ids'][i],
                    'metadata': results['metadatas'][i],
                    'document': results['documents'][i]
                })
        
        return posts[:limit]
    
    def get_profile_statistics(
        self, 
        profile: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Retorna estatísticas agregadas de um perfil.
        
        Args:
            profile: Nome do perfil (se None, retorna de todos)
            
        Returns:
            Dicionário com estatísticas
        """
        where = {}
        if profile:
            where['profile'] = profile
        
        results = self.collection.get(
            where=where if where else None,
            limit=10000
        )
        
        # Filtra apenas posts do Instagram
        posts = self._filter_instagram_posts(results, profile)
        
        if not posts:
            return {'error': 'Nenhum post encontrado'}
        
        total_posts = len(posts)
        total_likes = sum(p['metadata'].get('likesCount', 0) for p in posts)
        total_comments = sum(p['metadata'].get('commentsCount', 0) for p in posts)
        
        # Calcula médias
        avg_likes = total_likes / total_posts if total_posts > 0 else 0
        avg_comments = total_comments / total_posts if total_posts > 0 else 0
        
        # Encontra post com mais engajamento
        posts_with_engagement = []
        for p in posts:
            metadata = p['metadata']
            engagement = metadata.get('likesCount', 0) + metadata.get('commentsCount', 0)
            posts_with_engagement.append({
                'url': metadata.get('url', ''),
                'engagement': engagement,
                'likes': metadata.get('likesCount', 0),
                'comments': metadata.get('commentsCount', 0)
            })
        
        posts_with_engagement.sort(key=lambda x: x['engagement'], reverse=True)
        top_post = posts_with_engagement[0] if posts_with_engagement else None
        
        return {
            'profile': profile or 'todos',
            'total_posts': total_posts,
            'total_likes': total_likes,
            'total_comments': total_comments,
            'avg_likes_per_post': round(avg_likes, 2),
            'avg_comments_per_post': round(avg_comments, 2),
            'total_engagement': total_likes + total_comments,
            'top_post': top_post
        }
    
    def compare_profiles(self) -> Dict[str, Any]:
        """
        Compara estatísticas entre todos os perfis do Instagram.
        
        Returns:
            Dicionário com comparação entre perfis
        """
        results = self.collection.get(limit=10000)
        posts = self._filter_instagram_posts(results)  # Filtra apenas Instagram
        
        profiles = {}
        for p in posts:
            metadata = p['metadata']
            profile = metadata.get('profile', 'desconhecido')
            
            if profile not in profiles:
                profiles[profile] = {
                    'posts': 0,
                    'likes': 0,
                    'comments': 0
                }
            
            profiles[profile]['posts'] += 1
            profiles[profile]['likes'] += metadata.get('likesCount', 0)
            profiles[profile]['comments'] += metadata.get('commentsCount', 0)
        
        # Calcula médias
        comparison = {}
        for profile, stats in profiles.items():
            comparison[profile] = {
                'total_posts': stats['posts'],
                'total_likes': stats['likes'],
                'total_comments': stats['comments'],
                'avg_likes': round(stats['likes'] / stats['posts'], 2) if stats['posts'] > 0 else 0,
                'avg_comments': round(stats['comments'] / stats['posts'], 2) if stats['posts'] > 0 else 0,
                'total_engagement': stats['likes'] + stats['comments']
            }
        
        return comparison
    
    def count_term_occurrences(
        self,
        term: str,
        profile: Optional[str] = None,
        case_sensitive: bool = False
    ) -> Dict[str, Any]:
        """
        Quantifica quantos posts mencionam um termo específico.
        
        Diferente da busca semântica que retorna os posts MAIS relevantes,
        esta ferramenta conta TODOS os posts que mencionam o termo.
        
        Args:
            term: Termo a buscar (pode ser palavra ou frase)
            profile: Perfil específico ou None para todos
            case_sensitive: Se True, considera maiúsculas/minúsculas
            
        Returns:
            Dict com:
            - count: Número de posts que mencionam o termo
            - percentage: Porcentagem do total de posts
            - total_posts: Total de posts analisados
            - matching_posts: Lista de posts que mencionam o termo
        """
        try:
            # Prepara filtro de perfil
            where_filter = {"profile": profile} if profile else None
            
            # Busca TODOS os posts (limite alto)
            results = self.collection.get(
                where=where_filter,
                limit=10000,  # Consulta toda a base
                include=["documents", "metadatas"]
            )
            
            total_posts = len(results['documents'])
            
            # Normaliza o termo de busca
            search_term = term if case_sensitive else term.lower()
            
            # Filtra posts que contêm o termo
            matching_posts = []
            for i, doc in enumerate(results['documents']):
                # Texto completo do post
                text = doc if case_sensitive else doc.lower()
                
                # Verifica se o termo aparece no texto
                if search_term in text:
                    metadata = results['metadatas'][i]
                    matching_posts.append({
                        'document': results['documents'][i],
                        'metadata': metadata
                    })
            
            count = len(matching_posts)
            percentage = (count / total_posts * 100) if total_posts > 0 else 0
            
            return {
                'count': count,
                'percentage': round(percentage, 2),
                'total_posts': total_posts,
                'term': term,
                'profile': profile or 'todos os perfis',
                'matching_posts': matching_posts
            }
            
        except Exception as e:
            print(f"❌ Erro ao contar ocorrências: {str(e)}")
            return {
                'count': 0,
                'percentage': 0.0,
                'total_posts': 0,
                'term': term,
                'profile': profile or 'todos os perfis',
                'matching_posts': [],
                'error': str(e)
            }
    
    def analyze_sentiment(
        self,
        topic: str,
        profile: Optional[str] = None,
        n_posts: int = 20
    ) -> Dict[str, Any]:
        """
        Analisa o sentimento de posts sobre um tópico específico usando LLM.
        
        Args:
            topic: Tópico ou entidade a analisar (ex: "reitor", "greve", "HUAP")
            profile: Perfil específico ou None para todos
            n_posts: Número de posts a analisar (padrão: 20)
            
        Returns:
            Dict com:
            - topic: Tópico analisado
            - profile: Perfil(s) analisado(s)
            - total_posts: Total de posts analisados
            - sentiment_summary: Resumo geral do sentimento
            - positive_count: Número de posts positivos
            - negative_count: Número de posts negativos
            - neutral_count: Número de posts neutros
            - key_points: Pontos-chave identificados
            - examples: Exemplos de posts por sentimento
        """
        try:
            # Busca posts relacionados ao tópico
            where_filter = {"profile": profile} if profile else None
            
            results = self.collection.get(
                where=where_filter,
                limit=10000,
                include=["documents", "metadatas"]
            )
            
            # Filtra posts que mencionam o tópico (case-insensitive)
            topic_lower = topic.lower()
            relevant_posts = []
            
            for i, doc in enumerate(results['documents']):
                if topic_lower in doc.lower():
                    relevant_posts.append({
                        'document': doc,
                        'metadata': results['metadatas'][i]
                    })
            
            if not relevant_posts:
                return {
                    'topic': topic,
                    'profile': profile or 'todos os perfis',
                    'total_posts': 0,
                    'sentiment_summary': f"Nenhum post encontrado sobre '{topic}'",
                    'positive_count': 0,
                    'negative_count': 0,
                    'neutral_count': 0,
                    'key_points': [],
                    'examples': {'positive': [], 'negative': [], 'neutral': []}
                }
            
            # Limita ao número solicitado
            posts_to_analyze = relevant_posts[:n_posts]
            
            # Prepara contexto para o LLM
            posts_text = "\n\n".join([
                f"Post {i+1} (@{p['metadata']['profile']}):\n{p['document'][:500]}"
                for i, p in enumerate(posts_to_analyze)
            ])
            
            # Prompt para análise de sentimento
            prompt = f"""Analise o sentimento dos posts abaixo sobre o tópico "{topic}".

POSTS:
{posts_text}

Forneça uma análise estruturada em formato JSON com:
1. sentiment_summary: Resumo geral do sentimento (2-3 frases)
2. positive_count: Número de posts com tom positivo/favorável
3. negative_count: Número de posts com tom negativo/crítico
4. neutral_count: Número de posts com tom neutro/informativo
5. key_points: Lista de 3-5 pontos-chave sobre como o tópico é abordado
6. positive_aspects: Lista de aspectos positivos mencionados
7. negative_aspects: Lista de aspectos negativos/críticas mencionadas

Retorne APENAS o JSON, sem texto adicional."""

            # Chama o LLM com suporte a provider (DeepSeek ou Ollama)
            if DEFAULT_PROVIDER == 'deepseek':
                model_to_use = DEEPSEEK_MODEL
            else:
                model_to_use = self.llm_model
                
            response = llm_chat.chat(
                model=model_to_use,
                messages=[{
                    'role': 'user',
                    'content': prompt
                }]
            )
            
            # Parse da resposta
            try:
                # Extrai JSON da resposta
                response_text = response['message']['content']
                
                # Remove markdown se presente
                if '```json' in response_text:
                    response_text = response_text.split('```json')[1].split('```')[0]
                elif '```' in response_text:
                    response_text = response_text.split('```')[1].split('```')[0]
                
                analysis = json.loads(response_text.strip())
                
                # Categoriza posts em exemplos
                examples = {
                    'positive': [],
                    'negative': [],
                    'neutral': []
                }
                
                # Seleciona exemplos (simplificado - usa os primeiros de cada categoria)
                positive_needed = min(analysis.get('positive_count', 0), 2)
                negative_needed = min(analysis.get('negative_count', 0), 2)
                neutral_needed = min(analysis.get('neutral_count', 0), 2)
                
                for post in posts_to_analyze[:6]:  # Analisa até 6 posts como exemplos
                    if len(examples['positive']) < positive_needed:
                        examples['positive'].append(post)
                    elif len(examples['negative']) < negative_needed:
                        examples['negative'].append(post)
                    elif len(examples['neutral']) < neutral_needed:
                        examples['neutral'].append(post)
                
                return {
                    'topic': topic,
                    'profile': profile or 'todos os perfis',
                    'total_posts': len(posts_to_analyze),
                    'total_relevant': len(relevant_posts),
                    'sentiment_summary': analysis.get('sentiment_summary', ''),
                    'positive_count': analysis.get('positive_count', 0),
                    'negative_count': analysis.get('negative_count', 0),
                    'neutral_count': analysis.get('neutral_count', 0),
                    'key_points': analysis.get('key_points', []),
                    'positive_aspects': analysis.get('positive_aspects', []),
                    'negative_aspects': analysis.get('negative_aspects', []),
                    'examples': examples
                }
                
            except json.JSONDecodeError as e:
                print(f"⚠️ Erro ao parsear JSON do LLM: {e}")
                print(f"Resposta: {response_text[:500]}")
                
                # Fallback: retorna análise básica
                return {
                    'topic': topic,
                    'profile': profile or 'todos os perfis',
                    'total_posts': len(posts_to_analyze),
                    'total_relevant': len(relevant_posts),
                    'sentiment_summary': f"Analisados {len(posts_to_analyze)} posts sobre '{topic}'. Análise detalhada não disponível.",
                    'positive_count': 0,
                    'negative_count': 0,
                    'neutral_count': len(posts_to_analyze),
                    'key_points': [f"{len(relevant_posts)} posts mencionam '{topic}'"],
                    'positive_aspects': [],
                    'negative_aspects': [],
                    'examples': {'positive': posts_to_analyze[:2], 'negative': [], 'neutral': []},
                    'error': 'LLM response parsing failed'
                }
            
        except Exception as e:
            print(f"❌ Erro na análise de sentimento: {str(e)}")
            return {
                'topic': topic,
                'profile': profile or 'todos os perfis',
                'total_posts': 0,
                'sentiment_summary': f"Erro ao analisar sentimento: {str(e)}",
                'positive_count': 0,
                'negative_count': 0,
                'neutral_count': 0,
                'key_points': [],
                'positive_aspects': [],
                'negative_aspects': [],
                'examples': {'positive': [], 'negative': [], 'neutral': []},
                'error': str(e)
            }


    def get_news_articles(
        self,
        limit: int = 10,
        min_date: Optional[str] = None,
        max_date: Optional[str] = None,
        publisher: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retorna notícias filtradas por data e/ou publisher.
        
        Args:
            limit: Número de notícias a retornar
            min_date: Data mínima no formato ISO (opcional)
            max_date: Data máxima no formato ISO (opcional)
            publisher: Nome do publisher para filtrar (opcional)
            
        Returns:
            Lista de notícias ordenadas por data (mais recentes primeiro)
        """
        # Busca apenas notícias
        where = {'content_type': 'news'}
        
        results = self.collection.get(
            where=where,
            limit=10000
        )
        
        news_articles = []
        for i in range(len(results['ids'])):
            metadata = results['metadatas'][i]
            
            # Aplica filtros de data
            try:
                news_date = date_parser.parse(metadata['timestamp'])
                
                if min_date:
                    min_date_obj = date_parser.parse(min_date)
                    if news_date < min_date_obj:
                        continue
                
                if max_date:
                    max_date_obj = date_parser.parse(max_date)
                    if news_date > max_date_obj:
                        continue
            except:
                pass
            
            # Aplica filtro de publisher
            if publisher and publisher.lower() not in metadata.get('publisher_name', '').lower():
                continue
            
            news_articles.append({
                'id': results['ids'][i],
                'metadata': metadata,
                'document': results['documents'][i]
            })
        
        # Ordena por data (mais recentes primeiro)
        news_articles.sort(
            key=lambda x: date_parser.parse(x['metadata']['timestamp']),
            reverse=True
        )
        
        return news_articles[:limit]
    
    def search_news_by_person(
        self,
        person_name: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Busca notícias que mencionam uma pessoa específica (ex: Roberto Salles).
        
        Args:
            person_name: Nome da pessoa a buscar
            limit: Número de notícias a retornar
            
        Returns:
            Lista de notícias que mencionam a pessoa
        """
        # Busca apenas notícias
        where = {'content_type': 'news'}
        
        results = self.collection.get(
            where=where,
            limit=10000
        )
        
        # Filtra notícias que mencionam a pessoa
        relevant_news = []
        person_name_lower = person_name.lower()
        
        # Variações comuns de nomes (ex: Salles vs Sales)
        name_variations = [person_name_lower]
        if 'salles' in person_name_lower:
            name_variations.append(person_name_lower.replace('salles', 'sales'))
        elif 'sales' in person_name_lower:
            name_variations.append(person_name_lower.replace('sales', 'salles'))
        
        for i in range(len(results['ids'])):
            document = results['documents'][i].lower()
            metadata = results['metadatas'][i]
            
            # Verifica se QUALQUER variação do nome completo aparece no documento
            # Procura o nome completo, não apenas partes separadas
            if any(variation in document for variation in name_variations):
                relevant_news.append({
                    'id': results['ids'][i],
                    'metadata': metadata,
                    'document': results['documents'][i]
                })
        
        # Ordena por data (mais antigas primeiro para contexto histórico)
        relevant_news.sort(
            key=lambda x: date_parser.parse(x['metadata']['timestamp']),
            reverse=False  # Histórico: mais antigas primeiro
        )
        
        return relevant_news[:limit]
    
    def get_news_statistics(self) -> Dict[str, Any]:
        """
        Retorna estatísticas sobre as notícias indexadas.
        
        Returns:
            Dicionário com estatísticas
        """
        # Busca todas as notícias
        where = {'content_type': 'news'}
        
        results = self.collection.get(
            where=where,
            limit=10000
        )
        
        if not results['ids']:
            return {
                'total_news': 0,
                'publishers': [],
                'date_range': {'oldest': None, 'newest': None},
                'error': 'Nenhuma notícia encontrada'
            }
        
        # Coleta estatísticas
        publishers = {}
        dates = []
        
        for metadata in results['metadatas']:
            # Contagem por publisher
            pub = metadata.get('publisher_name', 'Desconhecido')
            publishers[pub] = publishers.get(pub, 0) + 1
            
            # Coleta datas
            try:
                dates.append(date_parser.parse(metadata['timestamp']))
            except:
                pass
        
        return {
            'total_news': len(results['ids']),
            'publishers': [{'name': k, 'count': v} for k, v in sorted(publishers.items(), key=lambda x: x[1], reverse=True)],
            'date_range': {
                'oldest': min(dates).isoformat() if dates else None,
                'newest': max(dates).isoformat() if dates else None
            }
        }
    
    def web_search(
        self, 
        query: str, 
        limit: int = 5,
        timeout: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Busca na internet usando DuckDuckGo para contexto externo.
        
        Útil quando o agente precisa de informações atuais ou contexto
        que não está nos registros locais da UFF.
        
        Args:
            query: Termo de busca
            limit: Número de resultados (padrão: 5)
            timeout: Timeout em segundos
            
        Returns:
            Lista com resultados da busca contendo:
            - title: Título do resultado
            - body: Texto resumido do resultado
            - source: URL da fonte
            - date: Data (se disponível)
            - profile: 'web_search' (para compatibilidade com outras ferramentas)
        """
        
        if not DDGS_AVAILABLE:
            return [{
                'title': 'Web search indisponível',
                'body': 'Módulo duckduckgo-search não está instalado',
                'source': 'local',
                'date': None,
                'profile': 'web_search'
            }]
        
        try:
            results = []
            filtered_count = 0
            
            # Busca com DuckDuckGo
            try:
                with DDGS(timeout=timeout) as ddgs:
                    search_results = ddgs.text(
                        query,  # Novo ddgs: query como posicional
                        max_results=limit * 2,  # Busca mais para compensar filtros
                        region='br-pt'  # Região Brasil
                    )
                    
                    for result in search_results:
                        if len(results) >= limit:
                            break
                            
                        # Filtra resultados muito genéricos/inúteis
                        title = result.get('title', '').lower()
                        body = result.get('body', '').lower()
                        href = result.get('href', '')
                        
                        # Rejeita apenas os muito óbviamente inúteis
                        reject_patterns = [
                            'wikipedia.org',  # Wikipedia (muito genérico)
                            'dicionario', 'significado', 'sinônimo',  # Dicionários
                            'pinterest', 'instagram.com', 'facebook.com',  # Redes sociais
                        ]
                        
                        # Verifica se deve rejeitar
                        should_reject = False
                        for pattern in reject_patterns:
                            if pattern in href.lower() or pattern in title:
                                should_reject = True
                                filtered_count += 1
                                break
                        
                        if should_reject:
                            continue
                        
                        # Também rejeita se o body é muito curto
                        if len(body.strip()) < 50:
                            filtered_count += 1
                            continue
                        
                        results.append({
                            'title': result.get('title', 'Sem título'),
                            'body': result.get('body', ''),
                            'source': result.get('href', ''),
                            'date': result.get('date', None),
                            'profile': 'web_search'  # Compatibilidade com outras ferramentas
                        })
            
            except Exception as search_error:
                print(f"⚠️ Erro na busca DuckDuckGo: {search_error}")
                # Retorna mensagem de erro sem quebrar
                return [{
                    'title': 'Erro ao buscar na internet',
                    'body': f'Não foi possível conectar ao DuckDuckGo. Tente novamente mais tarde.',
                    'source': 'web',
                    'date': None,
                    'profile': 'web_search'
                }]
            
            # Se conseguiu resultados após filtros, retorna
            if results:
                print(f"✅ Web search: {len(results)} resultado(s) encontrado(s) (filtrados: {filtered_count})")
                return results
            else:
                # Se nenhum resultado passou pelo filtro, retorna sem filtro rigoroso
                print(f"⚠️ Web search: Todos os {filtered_count} resultado(s) foram filtrados, tentando novamente sem filtro...")
                
                try:
                    with DDGS(timeout=timeout) as ddgs:
                        search_results = ddgs.text(
                            query,  # Novo ddgs: query como posicional
                            max_results=3,
                            region='br-pt'
                        )
                        
                        # Retorna sem filtro rigoroso
                        for result in search_results:
                            results.append({
                                'title': result.get('title', 'Sem título'),
                                'body': result.get('body', ''),
                                'source': result.get('href', ''),
                                'date': result.get('date', None),
                                'profile': 'web_search'
                            })
                        
                        if results:
                            return results
                except:
                    pass
                
                # Se ainda assim não retornar nada, retorna mensagem
                return [{
                    'title': 'Nenhum resultado encontrado',
                    'body': f'Infelizmente, a busca por "{query}" não retornou resultados na internet. Tente com termos diferentes.',
                    'source': 'web',
                    'date': None,
                    'profile': 'web_search'
                }]
        
        except Exception as e:
            return [{
                'title': 'Erro ao buscar na web',
                'body': f'Erro: {str(e)}. Tente novamente mais tarde.',
                'source': 'error',
                'date': None,
                'profile': 'web_search'
            }]


# Definições de ferramentas para function calling
TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "get_top_posts_by_likes",
            "description": "Retorna os posts com mais curtidas. Use esta ferramenta quando o usuário perguntar sobre posts mais curtidos, populares ou com maior número de likes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Número de posts a retornar (padrão: 10)",
                        "default": 10
                    },
                    "profile": {
                        "type": "string",
                        "description": "Nome do perfil para filtrar (opcional: dceuff, reitor, vicereitor)",
                        "enum": ["dceuff", "reitor", "vicereitor"]
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_top_posts_by_comments",
            "description": "Retorna os posts com mais comentários. Use quando o usuário perguntar sobre posts com mais interação ou comentários.",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Número de posts a retornar",
                        "default": 10
                    },
                    "profile": {
                        "type": "string",
                        "description": "Nome do perfil para filtrar",
                        "enum": ["dceuff", "reitor", "vicereitor"]
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_posts_by_engagement",
            "description": "Retorna posts com maior engajamento total (curtidas + comentários). Use para perguntas sobre engajamento geral.",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Número de posts a retornar",
                        "default": 10
                    },
                    "profile": {
                        "type": "string",
                        "description": "Nome do perfil para filtrar",
                        "enum": ["dceuff", "reitor", "vicereitor"]
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_recent_posts",
            "description": "Retorna os posts mais recentes. Use quando o usuário perguntar sobre posts recentes ou publicações dos últimos dias.",
            "parameters": {
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "Número de dias para considerar (padrão: 30)",
                        "default": 30
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Número de posts a retornar",
                        "default": 10
                    },
                    "profile": {
                        "type": "string",
                        "description": "Nome do perfil para filtrar",
                        "enum": ["dceuff", "reitor", "vicereitor"]
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_profile_statistics",
            "description": "Retorna estatísticas agregadas de um perfil (total de posts, curtidas, comentários, médias). Use para perguntas sobre estatísticas ou comparações numéricas.",
            "parameters": {
                "type": "object",
                "properties": {
                    "profile": {
                        "type": "string",
                        "description": "Nome do perfil (deixe vazio para todos os perfis)",
                        "enum": ["dceuff", "reitor", "vicereitor", ""]
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "compare_profiles",
            "description": "Compara estatísticas entre todos os perfis disponíveis. Use quando o usuário pedir comparações entre perfis.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "count_term_occurrences",
            "description": "Quantifica quantos posts mencionam um termo específico consultando TODA a base de dados. Use para perguntas do tipo 'quantos posts falam sobre X', 'quantas vezes mencionaram Y', 'qual a frequência de Z'. Diferente da busca semântica que retorna os posts MAIS relevantes, esta ferramenta CONTA todos os posts que contêm o termo.",
            "parameters": {
                "type": "object",
                "properties": {
                    "term": {
                        "type": "string",
                        "description": "Termo ou frase a buscar nos posts"
                    },
                    "profile": {
                        "type": "string",
                        "description": "Nome do perfil (deixe vazio para buscar em todos os perfis)",
                        "enum": ["dceuff", "reitor", "vicereitor", ""]
                    },
                    "case_sensitive": {
                        "type": "boolean",
                        "description": "Se True, diferencia maiúsculas de minúsculas",
                        "default": False
                    }
                },
                "required": ["term"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_sentiment",
            "description": "Analisa o sentimento e percepção sobre um tópico/entidade nos posts usando LLM. Retorna análise qualitativa com contagem de posts positivos/negativos/neutros, aspectos positivos e negativos identificados, e exemplos. Use para perguntas como 'como o reitor é visto?', 'qual a percepção sobre X?', 'o que pensam sobre Y?', 'análise de sentimento sobre Z'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "Tópico ou entidade a analisar (ex: 'reitor', 'greve', 'HUAP', 'universidade')"
                    },
                    "profile": {
                        "type": "string",
                        "description": "Nome do perfil (deixe vazio para analisar em todos os perfis)",
                        "enum": ["dceuff", "reitor", "vicereitor", ""]
                    },
                    "n_posts": {
                        "type": "integer",
                        "description": "Número de posts a analisar (padrão: 20, máx: 50)",
                        "default": 20
                    }
                },
                "required": ["topic"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_news_articles",
            "description": "Retorna notícias filtradas por data e/ou publisher. Use para buscar notícias de um período específico ou de um veículo específico.",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Número de notícias a retornar (padrão: 10)",
                        "default": 10
                    },
                    "min_date": {
                        "type": "string",
                        "description": "Data mínima no formato ISO (ex: 2009-01-01)"
                    },
                    "max_date": {
                        "type": "string",
                        "description": "Data máxima no formato ISO (ex: 2010-12-31)"
                    },
                    "publisher": {
                        "type": "string",
                        "description": "Nome do publisher/veículo (ex: FAPERJ, BBC, O Globo)"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_news_by_person",
            "description": "Busca notícias que mencionam uma pessoa específica, como o ex-reitor Roberto Salles. Use quando o usuário perguntar sobre alguém em notícias.",
            "parameters": {
                "type": "object",
                "properties": {
                    "person_name": {
                        "type": "string",
                        "description": "Nome da pessoa a buscar (ex: Roberto Salles, Roberto Sales)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Número de notícias a retornar (padrão: 10)",
                        "default": 10
                    }
                },
                "required": ["person_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_news_statistics",
            "description": "Retorna estatísticas sobre as notícias indexadas (total, publishers, período). Use quando o usuário pedir informações gerais sobre notícias.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Busca na internet usando DuckDuckGo. Use quando precisar de contexto atualizado ou informações não disponíveis no banco de dados local. Ideal para notícias recentes, eventos atuais, ou contexto externo.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Termo de busca (ex: 'UFF notícias 2025', 'educação Brasil')"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Número de resultados a retornar (padrão: 5, máx: 10)",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        }
    }
]


def main():
    """Função de teste."""
    from embedding_manager import EmbeddingManager
    
    print("=== Testando Query Tools ===\n")
    
    # Inicializa
    em = EmbeddingManager()
    tools = QueryTools(em)
    
    # Testa top posts por curtidas
    print("📊 Top 5 posts por curtidas:")
    top_likes = tools.get_top_posts_by_likes(limit=5)
    for i, post in enumerate(top_likes, 1):
        meta = post['metadata']
        print(f"{i}. @{meta['profile']}: {meta['likesCount']} curtidas - {meta['url']}")
    
    # Testa estatísticas
    print("\n📈 Estatísticas por perfil:")
    comparison = tools.compare_profiles()
    for profile, stats in comparison.items():
        print(f"\n@{profile}:")
        print(f"  Posts: {stats['total_posts']}")
        print(f"  Média de curtidas: {stats['avg_likes']}")
        print(f"  Engajamento total: {stats['total_engagement']}")
    
    # Web search
    print("\n🌐 Teste de busca na web:")
    web_results = tools.web_search("UFF Universidade Federal Fluminense notícias", limit=3)
    for i, result in enumerate(web_results, 1):
        print(f"{i}. {result['title']}")
        print(f"   {result['body'][:100]}...")
        print(f"   Fonte: {result['source']}\n")


if __name__ == "__main__":
    main()
