"""
Módulo para carregar e processar posts do Instagram salvos em arquivos JSON.
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
from dateutil import parser as date_parser
import emoji


class InstagramDataLoader:
    """Classe para carregar e processar dados de posts do Instagram e notícias."""

    def __init__(self, data_dir: str = "data"):
        """
        Inicializa o carregador de dados.
        
        Args:
            data_dir: Diretório contendo os arquivos JSON dos posts e notícias
        """
        self.data_dir = Path(data_dir)
        self.news_files = ['_smoking_gun.json']  # Arquivos de notícias
        
    def clean_text(self, text: str) -> str:
        """
        Normaliza e limpa texto removendo emojis, links e caracteres extras.
        
        Args:
            text: Texto a ser limpo
            
        Returns:
            Texto limpo e normalizado
        """
        if not text:
            return ""
        
        # Remove emojis
        text = emoji.replace_emoji(text, replace='')
        
        # Remove URLs
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        # Remove menções (mas mantemos para o metadado)
        # text = re.sub(r'@\w+', '', text)
        
        # Remove múltiplas quebras de linha
        text = re.sub(r'\n+', ' ', text)
        
        # Remove múltiplos espaços
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def extract_post_text(self, post: Dict[str, Any]) -> str:
        """
        Extrai e concatena todo o texto relevante de um post.
        
        Args:
            post: Dicionário contendo os dados de um post
            
        Returns:
            Texto concatenado e limpo do post
        """
        text_parts = []
        
        # Caption
        if caption := post.get('caption'):
            text_parts.append(f"Legenda: {self.clean_text(caption)}")
        
        # Hashtags
        if hashtags := post.get('hashtags', []):
            text_parts.append(f"Hashtags: {' '.join(hashtags)}")
        
        # Menções
        if mentions := post.get('mentions', []):
            text_parts.append(f"Menções: {' '.join(mentions)}")
        
        # Comentários relevantes (primeiros comentários)
        if latest_comments := post.get('latestComments', []):
            comments_text = []
            for comment in latest_comments[:5]:  # Limita a 5 comentários
                if comment_text := comment.get('text'):
                    comments_text.append(self.clean_text(comment_text))
            if comments_text:
                text_parts.append(f"Comentários: {' | '.join(comments_text)}")
        
        return " ".join(text_parts)
    
    def parse_timestamp(self, timestamp_str: str) -> datetime:
        """
        Converte string de timestamp para objeto datetime.
        
        Args:
            timestamp_str: String de timestamp ISO
            
        Returns:
            Objeto datetime
        """
        try:
            return date_parser.parse(timestamp_str)
        except:
            return datetime.now()
    
    def extract_news_text(self, news: Dict[str, Any]) -> str:
        """
        Extrai e concatena texto relevante de uma notícia.
        
        Args:
            news: Dicionário contendo os dados de uma notícia
            
        Returns:
            Texto concatenado e limpo da notícia
        """
        text_parts = []
        
        # Título
        if title := news.get('title'):
            text_parts.append(f"Título: {self.clean_text(title)}")
        
        # Descrição
        if description := news.get('description'):
            text_parts.append(f"Descrição: {self.clean_text(description)}")
        
        # Conteúdo principal
        if content := news.get('content'):
            text_parts.append(f"Conteúdo: {self.clean_text(content)}")
        
        return " ".join(text_parts)
    
    def load_news_articles(self, filename: str = "_smoking_gun.json") -> List[Dict[str, Any]]:
        """
        Carrega notícias de um arquivo JSON.
        
        Args:
            filename: Nome do arquivo JSON com notícias
            
        Returns:
            Lista de notícias processadas
        """
        file_path = self.data_dir / filename
        
        if not file_path.exists():
            print(f"⚠️  Arquivo de notícias não encontrado: {file_path}")
            return []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            news_items = json.load(f)
        
        processed_news = []
        
        for idx, news in enumerate(news_items):
            # Extrai informações relevantes
            # Usa índice para garantir IDs únicos (0, 1, 2, ...)
            news_data = {
                'id': f"news_{idx}",  # ID único baseado no índice
                'profile': 'noticias',  # Identificador especial para notícias
                'content_type': 'news',
                'type': 'Article',
                'text': self.extract_news_text(news),
                'url': news.get('link', ''),
                'title': news.get('title', ''),
                'description': news.get('description', ''),
                'content': news.get('content', ''),
                'timestamp': self.parse_timestamp(news.get('published', '')),
                'publisher_name': news.get('publisher_name', ''),
                'publisher_link': news.get('publisher_link', ''),
                'country': news.get('country', ''),
                'language': news.get('language', ''),
                'likesCount': 0,  # Notícias não têm likes
                'commentsCount': 0,  # Notícias não têm comentários
            }
            
            # Só adiciona notícias com conteúdo textual
            if news_data['text'].strip():
                processed_news.append(news_data)
        
        return processed_news
    
    def load_profile_posts(self, profile_name: str) -> List[Dict[str, Any]]:
        """
        Carrega posts de um perfil específico.
        
        Args:
            profile_name: Nome do arquivo JSON do perfil (sem extensão)
            
        Returns:
            Lista de posts processados
        """
        file_path = self.data_dir / f"{profile_name}.json"
        
        if not file_path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            posts = json.load(f)
        
        processed_posts = []
        
        for post in posts:
            # Extrai informações relevantes
            post_data = {
                'id': post.get('id', ''),
                'profile': profile_name,
                'type': post.get('type', 'Unknown'),
                'text': self.extract_post_text(post),
                'url': post.get('url', ''),
                'shortCode': post.get('shortCode', ''),
                'timestamp': self.parse_timestamp(post.get('timestamp', '')),
                'likesCount': post.get('likesCount', 0),
                'commentsCount': post.get('commentsCount', 0),
                'hashtags': post.get('hashtags', []),
                'mentions': post.get('mentions', []),
                'caption': post.get('caption', ''),
            }
            
            # Só adiciona posts com conteúdo textual
            if post_data['text'].strip():
                processed_posts.append(post_data)
        
        return processed_posts
    
    def load_all_posts(self) -> List[Dict[str, Any]]:
        """
        Carrega posts de todos os perfis disponíveis.
        
        Returns:
            Lista de todos os posts processados
        """
        all_posts = []
        
        # Lista todos os arquivos JSON no diretório (exceto notícias)
        json_files = [f for f in self.data_dir.glob("*.json") 
                      if f.name not in self.news_files]
        
        print(f"Encontrados {len(json_files)} arquivos de perfis")
        
        for json_file in json_files:
            profile_name = json_file.stem
            try:
                posts = self.load_profile_posts(profile_name)
                all_posts.extend(posts)
                print(f"✓ Carregados {len(posts)} posts do perfil: {profile_name}")
            except Exception as e:
                print(f"✗ Erro ao carregar {profile_name}: {e}")
        
        print(f"\nTotal de posts carregados: {len(all_posts)}")
        return all_posts
    
    def load_all_content(self) -> List[Dict[str, Any]]:
        """
        Carrega todo o conteúdo: posts do Instagram e notícias.
        
        Returns:
            Lista de todo o conteúdo processado
        """
        all_content = []
        
        # Carrega posts do Instagram
        all_content.extend(self.load_all_posts())
        
        # Carrega notícias
        for news_file in self.news_files:
            try:
                news_articles = self.load_news_articles(news_file)
                all_content.extend(news_articles)
                print(f"✓ Carregadas {len(news_articles)} notícias de: {news_file}")
            except Exception as e:
                print(f"✗ Erro ao carregar notícias de {news_file}: {e}")
        
        print(f"\n📊 Total de conteúdo carregado: {len(all_content)}")
        return all_content
    
    def get_profile_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas sobre os perfis carregados, incluindo notícias.
        
        Returns:
            Dicionário com estatísticas
        """
        all_content = self.load_all_content()
        
        stats = {}
        for item in all_content:
            profile = item['profile']
            if profile not in stats:
                stats[profile] = {
                    'total_posts': 0,
                    'total_likes': 0,
                    'total_comments': 0,
                    'content_type': item.get('content_type', 'instagram_post'),
                    'date_range': {'oldest': None, 'newest': None}
                }
            
            stats[profile]['total_posts'] += 1
            stats[profile]['total_likes'] += item['likesCount']
            stats[profile]['total_comments'] += item['commentsCount']
            
            # Atualiza intervalo de datas
            post_date = item['timestamp']
            if stats[profile]['date_range']['oldest'] is None or post_date < stats[profile]['date_range']['oldest']:
                stats[profile]['date_range']['oldest'] = post_date
            if stats[profile]['date_range']['newest'] is None or post_date > stats[profile]['date_range']['newest']:
                stats[profile]['date_range']['newest'] = post_date
        
        return stats
    
    def _process_instagram_post(self, post: Dict, profile: str) -> Dict[str, Any]:
        """
        Processa um post do Instagram.
        
        Args:
            post: Dados do post
            profile: Nome do perfil
            
        Returns:
            Dicionário com dados processados
        """
        # Extrai dados principais
        caption = post.get('caption', '')
        hashtags = ' '.join(post.get('hashtags', []))
        mentions = ' '.join(post.get('mentions', []))
        
        # 🆕 Extrai comentários se disponíveis
        comments = post.get('comments', [])
        comments_text = ''
        if comments:
            # Concatena texto de todos os comentários
            comments_list = [c.get('text', '') for c in comments if isinstance(c, dict) and c.get('text')]
            comments_text = '\n'.join(comments_list)
        
        # 🆕 Texto completo: legenda + comentários
        full_text = f"Perfil: {profile}\nData: {post.get('timestamp', '')}\nLegenda: {caption}\nHashtags: {hashtags}"
        
        if comments_text:
            full_text += f"\n\nComentários dos usuários:\n{comments_text}"
        
        return {
            'text': full_text,
            'profile': profile,
            'url': post.get('url', ''),
            'timestamp': post.get('timestamp', ''),
            'likesCount': post.get('likesCount', 0),
            'commentsCount': post.get('commentsCount', 0),
            'caption': caption,
            'hashtags': hashtags,
            'mentions': mentions,
            'comments_text': comments_text,  # 🆕 Armazena comentários separados
            'content_type': 'instagram_post'
        }


def main():
    """Função de teste do módulo."""
    loader = InstagramDataLoader()
    
    print("=== Estatísticas dos Perfis ===\n")
    stats = loader.get_profile_stats()
    
    for profile, data in stats.items():
        print(f"\n📱 Perfil: {profile}")
        print(f"   Posts: {data['total_posts']}")
        print(f"   Likes totais: {data['total_likes']}")
        print(f"   Comentários totais: {data['total_comments']}")
        if data['date_range']['oldest'] and data['date_range']['newest']:
            print(f"   Período: {data['date_range']['oldest'].strftime('%Y-%m-%d')} a {data['date_range']['newest'].strftime('%Y-%m-%d')}")


if __name__ == "__main__":
    main()
