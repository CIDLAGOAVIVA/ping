"""
Módulo para gerenciar embeddings de posts usando Ollama e ChromaDB.
"""

import ollama
from typing import List, Dict, Any
from chromadb import Client, Settings
from chromadb.config import Settings as ChromaSettings
import chromadb
from pathlib import Path
import json


class EmbeddingManager:
    """Classe para gerenciar embeddings e armazenamento vetorial."""

    def __init__(
        self, 
        collection_name: str = "instagram_posts",
        embedding_model: str = "mxbai-embed-large",
        persist_dir: str = "./chroma_db"
    ):
        """
        Inicializa o gerenciador de embeddings.
        
        Args:
            collection_name: Nome da coleção no ChromaDB
            embedding_model: Modelo Ollama para embeddings
            persist_dir: Diretório para persistir o banco vetorial
        """
        self.embedding_model = embedding_model
        self.collection_name = collection_name
        self.persist_dir = Path(persist_dir)
        
        # Cria diretório se não existir
        self.persist_dir.mkdir(exist_ok=True)
        
        # Inicializa ChromaDB
        self.client = chromadb.PersistentClient(path=str(self.persist_dir))
        
        # Cria ou recupera coleção
        try:
            self.collection = self.client.get_collection(name=collection_name)
            print(f"✓ Coleção '{collection_name}' carregada com {self.collection.count()} documentos")
        except:
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            print(f"✓ Nova coleção '{collection_name}' criada")
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Gera embedding para um texto usando Ollama.
        
        Args:
            text: Texto para gerar embedding
            
        Returns:
            Lista de floats representando o embedding
        """
        try:
            response = ollama.embeddings(
                model=self.embedding_model,
                prompt=text
            )
            return response['embedding']
        except Exception as e:
            print(f"Erro ao gerar embedding: {e}")
            raise
    
    def add_posts(self, posts: List[Dict[str, Any]], batch_size: int = 100):
        """
        Adiciona posts e notícias ao banco vetorial.
        
        Args:
            posts: Lista de posts/notícias processados
            batch_size: Tamanho do lote para processamento
        """
        total = len(posts)
        print(f"\nIniciando indexação de {total} documentos...")
        
        for i in range(0, total, batch_size):
            batch = posts[i:i + batch_size]
            
            documents = []
            metadatas = []
            ids = []
            embeddings = []
            
            for post in batch:
                # Prepara documento
                doc_text = post['text']
                
                # Metadados base
                metadata = {
                    'profile': post['profile'],
                    'url': post['url'],
                    'timestamp': post['timestamp'].isoformat(),
                    'likesCount': post['likesCount'],
                    'commentsCount': post['commentsCount'],
                    'type': post['type'],
                    'content_type': post.get('content_type', 'instagram_post'),
                }
                
                # Metadados específicos por tipo de conteúdo
                if post.get('content_type') == 'news':
                    # Metadados de notícias
                    metadata.update({
                        'title': post.get('title', '')[:500],
                        'description': post.get('description', '')[:500],
                        'publisher_name': post.get('publisher_name', ''),
                        'publisher_link': post.get('publisher_link', ''),
                        'country': post.get('country', ''),
                        'language': post.get('language', ''),
                    })
                else:
                    # Metadados de posts do Instagram
                    metadata.update({
                        'caption': post.get('caption', '')[:500],
                        'hashtags': json.dumps(post.get('hashtags', [])),
                        'mentions': json.dumps(post.get('mentions', [])),
                    })
                
                # Gera embedding
                embedding = self.generate_embedding(doc_text)
                
                documents.append(doc_text)
                metadatas.append(metadata)
                ids.append(f"{post['profile']}_{post['id']}")
                embeddings.append(embedding)
            
            # Adiciona lote ao ChromaDB
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids,
                embeddings=embeddings
            )
            
            progress = min(i + batch_size, total)
            print(f"Progresso: {progress}/{total} documentos indexados ({(progress/total)*100:.1f}%)")
        
        print(f"✓ Indexação concluída! Total de documentos: {self.collection.count()}")
    
    def add_documents(
        self,
        documents: List[str],
        ids: List[str],
        metadatas: List[Dict[str, Any]],
        batch_size: int = 100
    ):
        """
        Adiciona documentos genéricos ao banco vetorial.
        Método usado pelo pipeline de ingestão de dados.
        
        Args:
            documents: Lista de textos dos documentos
            ids: Lista de IDs únicos para cada documento
            metadatas: Lista de metadados para cada documento
            batch_size: Tamanho do lote para processamento
        """
        if not documents or not ids or not metadatas:
            raise ValueError("documents, ids e metadatas não podem estar vazios")
        
        if len(documents) != len(ids) or len(documents) != len(metadatas):
            raise ValueError("documents, ids e metadatas devem ter o mesmo tamanho")
        
        total = len(documents)
        print(f"\n📥 Indexando {total} documento(s)...")
        
        for i in range(0, total, batch_size):
            batch_docs = documents[i:i + batch_size]
            batch_ids = ids[i:i + batch_size]
            batch_metas = metadatas[i:i + batch_size]
            
            # Gera embeddings
            embeddings = []
            for doc in batch_docs:
                embedding = self.generate_embedding(doc)
                embeddings.append(embedding)
            
            # Adiciona ao ChromaDB
            self.collection.add(
                documents=batch_docs,
                metadatas=batch_metas,
                ids=batch_ids,
                embeddings=embeddings
            )
            
            progress = min(i + batch_size, total)
            print(f"Progresso: {progress}/{total} documentos indexados ({(progress/total)*100:.1f}%)")
        
        print(f"✅ Indexação concluída! Total na coleção: {self.collection.count()}")
    
    def search(
        self, 
        query: str, 
        n_results: int = 5,
        profile_filter: str = None,
        content_type_filter: str = None
    ) -> Dict[str, Any]:
        """
        Busca posts/notícias relevantes baseado em uma query.
        
        Args:
            query: Texto da busca
            n_results: Número de resultados a retornar
            profile_filter: Filtrar por perfil específico (opcional)
            content_type_filter: Filtrar por tipo de conteúdo: 'instagram_post' ou 'news' (opcional)
            
        Returns:
            Dicionário com resultados da busca
        """
        # Gera embedding da query
        query_embedding = self.generate_embedding(query)
        
        # Prepara filtros
        where = {}
        if profile_filter:
            where['profile'] = profile_filter
        if content_type_filter:
            where['content_type'] = content_type_filter
        
        # Busca no ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where if where else None
        )
        
        return results
    
    def clear_collection(self):
        """Remove todos os documentos da coleção."""
        try:
            self.client.delete_collection(name=self.collection_name)
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            print(f"✓ Coleção '{self.collection_name}' limpa")
        except Exception as e:
            print(f"Erro ao limpar coleção: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas sobre a coleção.
        
        Returns:
            Dicionário com estatísticas
        """
        count = self.collection.count()
        
        # Pega TODOS os documentos para garantir que obtém todos os perfis/fontes
        if count > 0:
            # Busca todos os documentos (só metadados, não documentos completos)
            all_data = self.collection.get(
                limit=count,  # Pega todos
                include=['metadatas']  # Só metadados para ser mais rápido
            )
            
            profiles = set()
            sources = set()
            content_types = set()
            
            for metadata in all_data['metadatas']:
                # Posts do Instagram têm 'profile'
                if 'profile' in metadata:
                    profiles.add(metadata['profile'])
                
                # Documentos injetados e outros têm 'source'
                if 'source' in metadata:
                    sources.add(metadata['source'])
                
                # Todos têm 'content_type'
                if 'content_type' in metadata:
                    content_types.add(metadata['content_type'])
            
            # Ordena alfabeticamente
            profiles_list = sorted(list(profiles))
            sources_list = sorted(list(sources))
            content_types_list = sorted(list(content_types))
            
            return {
                'total_documents': count,
                'profiles': profiles_list,  # Perfis do Instagram
                'sources': sources_list,     # Fontes (upload, web_search, etc)
                'content_types': content_types_list,  # Tipos de conteúdo
                'collection_name': self.collection_name,
                'embedding_model': self.embedding_model
            }
        
        return {
            'total_documents': 0,
            'profiles': [],
            'sources': [],
            'content_types': [],
            'collection_name': self.collection_name,
            'embedding_model': self.embedding_model
        }


def check_ollama_model(model_name: str) -> bool:
    """
    Verifica se um modelo está disponível no Ollama.
    
    Args:
        model_name: Nome do modelo
        
    Returns:
        True se o modelo está disponível
    """
    try:
        models = ollama.list()
        available_models = [model['name'] for model in models.get('models', [])]
        
        # Verifica se o modelo ou uma variante está disponível
        for available in available_models:
            if model_name in available:
                return True
        
        return False
    except Exception as e:
        print(f"Erro ao verificar modelos Ollama: {e}")
        return False


def install_embedding_model(model_name: str = "mxbai-embed-large"):
    """
    Instala modelo de embedding via Ollama.
    
    Args:
        model_name: Nome do modelo a instalar
    """
    print(f"\n📥 Instalando modelo de embedding: {model_name}")
    print("Isso pode levar alguns minutos...")
    
    try:
        ollama.pull(model_name)
        print(f"✓ Modelo {model_name} instalado com sucesso!")
    except Exception as e:
        print(f"✗ Erro ao instalar modelo: {e}")
        print("\nTente instalar manualmente com:")
        print(f"  ollama pull {model_name}")


def main():
    """Função de teste do módulo."""
    import sys
    
    # Verifica se modelo de embedding está instalado
    embedding_model = "mxbai-embed-large"
    
    print("=== Verificando Modelos Ollama ===\n")
    
    if not check_ollama_model(embedding_model):
        print(f"⚠️  Modelo {embedding_model} não encontrado")
        response = input("Deseja instalar agora? (s/n): ")
        if response.lower() == 's':
            install_embedding_model(embedding_model)
        else:
            print("Operação cancelada. Execute 'ollama pull mxbai-embed-large' manualmente.")
            sys.exit(1)
    else:
        print(f"✓ Modelo {embedding_model} disponível")
    
    # Teste básico
    manager = EmbeddingManager()
    print(f"\n=== Estatísticas da Coleção ===\n")
    stats = manager.get_stats()
    for key, value in stats.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
