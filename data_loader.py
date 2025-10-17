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
    """Classe para carregar e processar dados de posts do Instagram."""

    def __init__(self, data_dir: str = "data"):
        """
        Inicializa o carregador de dados.
        
        Args:
            data_dir: Diretório contendo os arquivos JSON dos posts
        """
        self.data_dir = Path(data_dir)
        
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
        
        # Lista todos os arquivos JSON no diretório
        json_files = list(self.data_dir.glob("*.json"))
        
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
    
    def get_profile_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas sobre os perfis carregados.
        
        Returns:
            Dicionário com estatísticas
        """
        all_posts = self.load_all_posts()
        
        stats = {}
        for post in all_posts:
            profile = post['profile']
            if profile not in stats:
                stats[profile] = {
                    'total_posts': 0,
                    'total_likes': 0,
                    'total_comments': 0,
                    'date_range': {'oldest': None, 'newest': None}
                }
            
            stats[profile]['total_posts'] += 1
            stats[profile]['total_likes'] += post['likesCount']
            stats[profile]['total_comments'] += post['commentsCount']
            
            # Atualiza intervalo de datas
            post_date = post['timestamp']
            if stats[profile]['date_range']['oldest'] is None or post_date < stats[profile]['date_range']['oldest']:
                stats[profile]['date_range']['oldest'] = post_date
            if stats[profile]['date_range']['newest'] is None or post_date > stats[profile]['date_range']['newest']:
                stats[profile]['date_range']['newest'] = post_date
        
        return stats


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
