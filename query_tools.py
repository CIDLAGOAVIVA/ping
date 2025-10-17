"""
Ferramentas de consulta especializadas para análise de posts do Instagram.
Estas ferramentas fornecem queries estruturadas que complementam o RAG semântico.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from dateutil import parser as date_parser
import json


class QueryTools:
    """Ferramentas de consulta para análise estruturada de posts."""
    
    def __init__(self, embedding_manager):
        """
        Inicializa as ferramentas com acesso ao banco de dados.
        
        Args:
            embedding_manager: Instância do EmbeddingManager com a coleção
        """
        self.collection = embedding_manager.collection
    
    def get_top_posts_by_likes(
        self, 
        limit: int = 10, 
        profile: Optional[str] = None,
        min_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retorna os posts com mais curtidas.
        
        Args:
            limit: Número de posts a retornar
            profile: Filtrar por perfil específico (opcional)
            min_date: Data mínima no formato ISO (opcional)
            
        Returns:
            Lista de posts ordenados por curtidas (decrescente)
        """
        # Busca todos os posts (ou filtrados)
        where = {}
        if profile:
            where['profile'] = profile
        
        # ChromaDB não suporta ordenação nativa, então pegamos todos e ordenamos
        results = self.collection.get(
            where=where if where else None,
            limit=10000  # Pega muitos para ordenar
        )
        
        # Converte para lista de dicts
        posts = []
        for i in range(len(results['ids'])):
            metadata = results['metadatas'][i]
            
            # Aplica filtro de data se especificado
            if min_date:
                try:
                    post_date = date_parser.parse(metadata['timestamp'])
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
        posts.sort(key=lambda x: x['metadata']['likesCount'], reverse=True)
        
        return posts[:limit]
    
    def get_top_posts_by_comments(
        self, 
        limit: int = 10, 
        profile: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retorna os posts com mais comentários.
        
        Args:
            limit: Número de posts a retornar
            profile: Filtrar por perfil específico (opcional)
            
        Returns:
            Lista de posts ordenados por comentários (decrescente)
        """
        where = {}
        if profile:
            where['profile'] = profile
        
        results = self.collection.get(
            where=where if where else None,
            limit=10000
        )
        
        posts = []
        for i in range(len(results['ids'])):
            posts.append({
                'id': results['ids'][i],
                'metadata': results['metadatas'][i],
                'document': results['documents'][i]
            })
        
        posts.sort(key=lambda x: x['metadata']['commentsCount'], reverse=True)
        return posts[:limit]
    
    def get_posts_by_engagement(
        self, 
        limit: int = 10, 
        profile: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retorna os posts com maior engajamento (curtidas + comentários).
        
        Args:
            limit: Número de posts a retornar
            profile: Filtrar por perfil específico (opcional)
            
        Returns:
            Lista de posts ordenados por engajamento total
        """
        where = {}
        if profile:
            where['profile'] = profile
        
        results = self.collection.get(
            where=where if where else None,
            limit=10000
        )
        
        posts = []
        for i in range(len(results['ids'])):
            metadata = results['metadatas'][i]
            engagement = metadata['likesCount'] + metadata['commentsCount']
            posts.append({
                'id': results['ids'][i],
                'metadata': metadata,
                'document': results['documents'][i],
                'engagement': engagement
            })
        
        posts.sort(key=lambda x: x['engagement'], reverse=True)
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
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        posts = []
        for i in range(len(results['ids'])):
            metadata = results['metadatas'][i]
            try:
                post_date = date_parser.parse(metadata['timestamp'])
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
        
        if not results['ids']:
            return {'error': 'Nenhum post encontrado'}
        
        total_posts = len(results['ids'])
        total_likes = sum(m['likesCount'] for m in results['metadatas'])
        total_comments = sum(m['commentsCount'] for m in results['metadatas'])
        
        # Calcula médias
        avg_likes = total_likes / total_posts if total_posts > 0 else 0
        avg_comments = total_comments / total_posts if total_posts > 0 else 0
        
        # Encontra post com mais engajamento
        posts_with_engagement = []
        for i in range(len(results['ids'])):
            metadata = results['metadatas'][i]
            engagement = metadata['likesCount'] + metadata['commentsCount']
            posts_with_engagement.append({
                'url': metadata['url'],
                'engagement': engagement,
                'likes': metadata['likesCount'],
                'comments': metadata['commentsCount']
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
        Compara estatísticas entre todos os perfis disponíveis.
        
        Returns:
            Dicionário com comparação entre perfis
        """
        results = self.collection.get(limit=10000)
        
        profiles = {}
        for i in range(len(results['ids'])):
            metadata = results['metadatas'][i]
            profile = metadata['profile']
            
            if profile not in profiles:
                profiles[profile] = {
                    'posts': 0,
                    'likes': 0,
                    'comments': 0
                }
            
            profiles[profile]['posts'] += 1
            profiles[profile]['likes'] += metadata['likesCount']
            profiles[profile]['comments'] += metadata['commentsCount']
        
        # Calcula médias
        comparison = {}
        for profile, stats in profiles.items():
            comparison[profile] = {
                'total_posts': stats['posts'],
                'total_likes': stats['likes'],
                'total_comments': stats['comments'],
                'avg_likes': round(stats['likes'] / stats['posts'], 2),
                'avg_comments': round(stats['comments'] / stats['posts'], 2),
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


if __name__ == "__main__":
    main()
