"""
Sistema RAG (Retrieval-Augmented Generation) para análise de posts do Instagram.
"""

import llm_chat
from config import DEFAULT_PROVIDER, DEEPSEEK_MODEL, OLLAMA_GENERATION_MODEL
from typing import List, Dict, Any, Tuple
from datetime import datetime, timedelta
from dateutil import parser as date_parser
import json
from embedding_manager import EmbeddingManager
from data_loader import InstagramDataLoader
from query_tools import QueryTools, TOOL_DEFINITIONS


class RAGSystem:
    """Sistema RAG completo para consulta de posts do Instagram."""

    def __init__(
        self,
        embedding_model: str = "mxbai-embed-large",
        generation_model: str = "qwen3:30b",
        data_dir: str = "data",
        chroma_dir: str = "./chroma_db"
    ):
        """
        Inicializa o sistema RAG.
        
        Args:
            embedding_model: Modelo para embeddings
            generation_model: Modelo para geração de respostas
            data_dir: Diretório com dados JSON
            chroma_dir: Diretório do ChromaDB
        """
        self.generation_model = generation_model
        self.data_loader = InstagramDataLoader(data_dir)
        self.embedding_manager = EmbeddingManager(
            embedding_model=embedding_model,
            persist_dir=chroma_dir
        )
        
        # Inicializa ferramentas de consulta
        self.query_tools = QueryTools(self.embedding_manager)
        
        print(f"✓ Sistema RAG inicializado")
        print(f"  - Modelo de embedding: {embedding_model}")
        print(f"  - Modelo de geração: {generation_model}")
    
    def index_all_posts(self, force_reindex: bool = False):
        """
        Indexa todos os posts no banco vetorial.
        
        Args:
            force_reindex: Se True, limpa e re-indexa todos os posts
        """
        current_count = self.embedding_manager.collection.count()
        
        if current_count > 0 and not force_reindex:
            print(f"✓ Banco já contém {current_count} posts indexados")
            return
        
        if force_reindex:
            print("🔄 Limpando índice existente...")
            self.embedding_manager.clear_collection()
        
        # Carrega posts
        posts = self.data_loader.load_all_posts()
        
        # Indexa
        self.embedding_manager.add_posts(posts)
    
    def format_post_for_context(self, post_data: Dict[str, Any]) -> str:
        """
        Formata um post/documento para incluir no contexto da resposta.
        Suporta tanto posts do Instagram quanto documentos injetados.
        
        Args:
            post_data: Dados do post/documento
            
        Returns:
            String formatada do post/documento
        """
        metadata = post_data
        
        # Detecta tipo de fonte
        is_instagram = 'likesCount' in metadata
        is_document = metadata.get('source') == 'upload'
        
        if is_document:
            # Formata documento injetado
            filename = metadata.get('filename', 'Documento')
            doc_id = metadata.get('doc_id', 'ID desconhecido')
            content_type = metadata.get('content_type', 'Desconhecido')
            author = metadata.get('author', 'Desconhecido')
            chunk_index = metadata.get('chunk_index', '?')
            total_chunks = metadata.get('total_chunks', '?')
            
            doc_info = f"""
[📄 {content_type}]
Arquivo: {filename}
Autor: {author}
Chunk: {chunk_index}/{total_chunks}
ID: {doc_id}
---
"""
            return doc_info
        else:
            # Formata post do Instagram
            profile = metadata.get('profile', 'Perfil desconhecido')
            
            # Parse da data
            try:
                timestamp = date_parser.parse(metadata['timestamp'])
                date_str = timestamp.strftime('%d/%m/%Y')
            except:
                date_str = "Data não disponível"
            
            # Formata caption
            caption = metadata.get('caption', '')
            if len(caption) > 200:
                caption = caption[:200] + "..."
            
            likes = metadata.get('likesCount', 0)
            comments = metadata.get('commentsCount', 0)
            url = metadata.get('url', '#')
            
            post_info = f"""
[Post do perfil @{profile}]
Data: {date_str}
Legenda: {caption}
Engajamento: {likes} curtidas, {comments} comentários
Link: {url}
---
"""
            return post_info
    
    def retrieve_relevant_posts(
        self, 
        query: str, 
        n_results: int = 5,
        profile_filter: str = None
    ) -> List[Dict[str, Any]]:
        """
        Recupera posts relevantes para uma query.
        
        Args:
            query: Pergunta ou busca do usuário
            n_results: Número de posts a recuperar
            profile_filter: Filtrar por perfil específico
            
        Returns:
            Lista de posts relevantes com metadados
        """
        results = self.embedding_manager.search(
            query=query,
            n_results=n_results,
            profile_filter=profile_filter
        )
        
        # Formata resultados
        posts = []
        for i in range(len(results['ids'][0])):
            post = {
                'id': results['ids'][0][i],
                'text': results['documents'][0][i],
                'metadata': results['metadatas'][0][i],
                'distance': results['distances'][0][i] if 'distances' in results else None
            }
            posts.append(post)
        
        return posts
    
    def generate_response(
        self, 
        query: str, 
        context_posts: List[Dict[str, Any]],
        stream: bool = False
    ) -> str:
        """
        Gera resposta usando o modelo de linguagem com contexto dos posts/documentos.
        
        Args:
            query: Pergunta do usuário
            context_posts: Posts/documentos relevantes recuperados
            stream: Se True, retorna generator para streaming
            
        Returns:
            Resposta gerada ou generator
        """
        # Detecta tipos de fonte nos resultados
        has_documents = any(p['metadata'].get('source') == 'upload' for p in context_posts)
        has_instagram = any('likesCount' in p['metadata'] for p in context_posts)
        
        # Monta contexto com título dinâmico
        if has_documents and has_instagram:
            context = "## Contexto Relevante (Posts do Instagram + Documentos):\n\n"
        elif has_documents:
            context = "## Contexto Relevante (Documentos Injetados):\n\n"
        else:
            context = "## Posts Relevantes do Instagram:\n\n"
        
        for i, post in enumerate(context_posts, 1):
            context += f"({i}) " + self.format_post_for_context(post['metadata'])
            context += f"Conteúdo: {post['text'][:500]}\n\n"
        
        # Prompt do sistema - adaptado para múltiplas fontes
        system_prompt = """Você é um assistente especializado em analisar informações da UFF (Universidade Federal Fluminense).

TAREFA CRÍTICA:
1. Responda APENAS com informações do contexto fornecido
2. Se há documentos (📄) no contexto, EXTRAIA deles a resposta com prioridade absoluta
3. Os documentos contêm informações oficiais - use-os como fonte primária
4. Posts do Instagram são secundários - use apenas se documentos não tiverem a resposta
5. Cite SEMPRE a fonte: nome do arquivo, tipo de conteúdo, e se possível o número do parágrafo/artigo

RESTRIÇÕES OBRIGATÓRIAS:
- NÃO invente nada. Use apenas o que está no contexto
- Se não encontrar a resposta exata, diga "NÃO ENCONTRADO" e cite o que está no contexto
- Se a pergunta é sobre regulamento/estatuto, PRIORIZE documentos oficiais
- Sempre identifique se a resposta vem de um documento ou post

FORMATO DE RESPOSTA:
- Comece com a informação encontrada
- Cite a fonte no final: "Fonte: [Tipo de Documento] | [Nome do Arquivo]"
- Se fragmentado em chunks, mencione: "Encontrado em múltiplos trechos do documento"
"""

        # Prompt do usuário - com instruções mais explícitas
        user_prompt = f"""{context}

## Pergunta do Usuário:
{query}

## INSTRUÇÕES CRÍTICAS PARA RESPOSTA:
1. Se a pergunta é sobre "estatuto", "regulamento", "Art." (artigo), "§" (parágrafo), ou "eleição":
   - PROCURE NOS DOCUMENTOS (marcados com 📄)
   - Extraia exatamente o texto do documento
   - Cite o Artigo/Parágrafo completo
   
2. Se encontrar o conteúdo em múltiplos chunks, MESCLE as informações

3. NUNCA diga "não encontrei nos posts" se houver documentos (📄) no contexto:
   - Os documentos contêm Estatuto/Regimento da UFF
   - O texto pode estar em um dos chunks listados

4. Formato de resposta:
   - [RESPOSTA DIRETA]
   - Fonte: [tipo] | [arquivo] | [localização no documento]

5. Se a informação solicitada está incompleta ou truncada nos chunks, 
   monte a resposta com os fragmentos disponíveis indicando que foi compilada de múltiplos trechos
"""

        # Gera resposta com suporte a provider (DeepSeek ou Ollama)
        try:
            if DEFAULT_PROVIDER == 'deepseek':
                model_to_use = DEEPSEEK_MODEL
            else:
                model_to_use = self.generation_model
                
            response = llm_chat.chat(
                model=model_to_use,
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_prompt}
                ],
                stream=stream
            )
            
            if stream:
                return response
            else:
                return response['message']['content']
        
        except Exception as e:
            return f"❌ Erro ao gerar resposta: {e}"
    
    def query(
        self, 
        question: str, 
        n_results: int = 10,
        profile_filter: str = None,
        stream: bool = False
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Executa query completa no sistema RAG com suporte a ferramentas.
        
        Args:
            question: Pergunta do usuário
            n_results: Número de posts/documentos a recuperar (padrão: 10)
            profile_filter: Filtrar por perfil
            stream: Se True, streaming de resposta
            
        Returns:
            Tupla (resposta, posts_recuperados)
        """
        # Primeiro, tenta identificar se deve usar ferramentas especializadas
        tools_result, used_tools = self._try_use_tools(question, profile_filter)
        
        if tools_result:
            # Se ferramentas foram usadas, cria contexto a partir delas
            response = self._generate_response_from_tools(
                question, 
                tools_result, 
                used_tools,
                stream
            )
            return response, tools_result
        
        # Caso contrário, usa RAG semântico normal
        posts = self.retrieve_relevant_posts(
            query=question,
            n_results=n_results,
            profile_filter=profile_filter
        )
        
        if not posts:
            return "Não encontrei posts relevantes para sua pergunta. Tente reformular ou fazer uma pergunta diferente.", []
        
        # Gera resposta
        response = self.generate_response(
            query=question,
            context_posts=posts,
            stream=stream
        )
        
        return response, posts
    
    def _try_use_tools(
        self, 
        question: str, 
        profile_filter: str = None
    ) -> Tuple[List[Dict[str, Any]], List[str]]:
        """
        Tenta identificar e usar ferramentas especializadas baseado na pergunta.
        
        Args:
            question: Pergunta do usuário
            profile_filter: Filtro de perfil
            
        Returns:
            Tupla (resultados, nomes_das_ferramentas_usadas)
        """
        question_lower = question.lower()
        results = []
        used_tools = []
        
        # Detecta queries de curtidas
        if any(word in question_lower for word in ['curtida', 'curtidas', 'like', 'likes', 'populares', 'popular', 'mais curtido', 'mais curtidos']):
            posts = self.query_tools.get_top_posts_by_likes(
                limit=10, 
                profile=profile_filter
            )
            results = posts
            used_tools.append('get_top_posts_by_likes')
        
        # Detecta queries de comentários
        elif any(word in question_lower for word in ['comentário', 'comentários', 'comment', 'comments', 'mais comentado', 'mais comentados']):
            posts = self.query_tools.get_top_posts_by_comments(
                limit=10,
                profile=profile_filter
            )
            results = posts
            used_tools.append('get_top_posts_by_comments')
        
        # Detecta queries de engajamento
        elif any(word in question_lower for word in ['engajamento', 'engagement', 'interação', 'interacao', 'engaja', 'mais engajado', 'maior engajamento']):
            posts = self.query_tools.get_posts_by_engagement(
                limit=10,
                profile=profile_filter
            )
            results = posts
            used_tools.append('get_posts_by_engagement')
        
        # Detecta queries recentes
        elif any(word in question_lower for word in ['recente', 'recentes', 'último', 'últimos', 'ultimo', 'ultimos', 'recentemente', 'publicado', 'publicados']):
            # Tenta extrair número de dias
            days = 30
            if 'última semana' in question_lower or 'ultima semana' in question_lower:
                days = 7
            elif 'último mês' in question_lower or 'ultimo mes' in question_lower:
                days = 30
            
            posts = self.query_tools.get_recent_posts(
                days=days,
                limit=10,
                profile=profile_filter
            )
            results = posts
            used_tools.append('get_recent_posts')
        
        # Detecta queries de estatísticas
        elif any(word in question_lower for word in ['estatísticas', 'estatisticas', 'média', 'media', 'total', 'quantos']):
            stats = self.query_tools.get_profile_statistics(profile=profile_filter)
            # Converte estatísticas em formato de posts para exibição
            results = [{'metadata': stats, 'is_stats': True}]
            used_tools.append('get_profile_statistics')
        
        # Detecta comparações entre perfis
        elif any(word in question_lower for word in ['comparar', 'comparação', 'comparacao', 'diferença', 'diferenca']):
            comparison = self.query_tools.compare_profiles()
            results = [{'metadata': comparison, 'is_comparison': True}]
            used_tools.append('compare_profiles')
        
        return results, used_tools
    
    def _generate_response_from_tools(
        self,
        question: str,
        tools_result: List[Dict[str, Any]],
        used_tools: List[str],
        stream: bool = False
    ) -> str:
        """
        Gera resposta usando resultados de ferramentas.
        
        Args:
            question: Pergunta original
            tools_result: Resultados das ferramentas
            used_tools: Nomes das ferramentas usadas
            stream: Streaming ou não
            
        Returns:
            Resposta gerada
        """
        # Prepara contexto com resultados das ferramentas
        if tools_result and tools_result[0].get('is_stats'):
            # Estatísticas
            stats = tools_result[0]['metadata']
            context = f"""
## Estatísticas do Perfil

Os dados mostram:
- **Total de posts**: {stats.get('total_posts', 0)}
- **Total de curtidas**: {stats.get('total_likes', 0)}
- **Total de comentários**: {stats.get('total_comments', 0)}
- **Média de curtidas por post**: {stats.get('avg_likes_per_post', 0)}
- **Média de comentários por post**: {stats.get('avg_comments_per_post', 0)}
- **Engajamento total**: {stats.get('total_engagement', 0)}
"""
            if stats.get('top_post'):
                top = stats['top_post']
                context += f"\n**Post com maior engajamento**: {top['engagement']} ({top['likes']} curtidas + {top['comments']} comentários)\nLink: {top['url']}"
        
        elif tools_result and tools_result[0].get('is_comparison'):
            # Comparação entre perfis
            comparison = tools_result[0]['metadata']
            context = "## Comparação Entre Perfis\n\n"
            for profile, stats in comparison.items():
                context += f"### @{profile}\n"
                context += f"- Posts: {stats['total_posts']}\n"
                context += f"- Curtidas totais: {stats['total_likes']}\n"
                context += f"- Comentários totais: {stats['total_comments']}\n"
                context += f"- Média de curtidas: {stats['avg_likes']}\n"
                context += f"- Média de comentários: {stats['avg_comments']}\n"
                context += f"- Engajamento total: {stats['total_engagement']}\n\n"
        
        else:
            # Posts regulares
            context = f"## Resultados da ferramenta: {', '.join(used_tools)}\n\n"
            for i, post in enumerate(tools_result[:10], 1):
                metadata = post.get('metadata', {})
                context += f"""
**Post {i}** (@{metadata.get('profile', 'unknown')}):
- Curtidas: {metadata.get('likesCount', 0)}
- Comentários: {metadata.get('commentsCount', 0)}
- Data: {metadata.get('timestamp', 'N/A')[:10]}
- Link: {metadata.get('url', '')}
- Legenda: {metadata.get('caption', '')[:200]}...
---
"""
        
        # Prompt do sistema
        system_prompt = """Você é um assistente especializado em analisar posts do Instagram da UFF.

Use os dados estruturados fornecidos para responder à pergunta do usuário de forma clara e objetiva.

IMPORTANTE:
- Use APENAS os dados fornecidos
- Cite números específicos e links quando disponíveis
- Organize a resposta de forma clara
- Use formatação markdown
- Seja preciso e direto
"""

        user_prompt = f"""{context}

## Pergunta do Usuário:
{question}

Responda de forma clara e objetiva usando os dados acima."""

        # Gera resposta com suporte a provider (DeepSeek ou Ollama)
        try:
            if DEFAULT_PROVIDER == 'deepseek':
                model_to_use = DEEPSEEK_MODEL
            else:
                model_to_use = self.generation_model
                
            response = llm_chat.chat(
                model=model_to_use,
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_prompt}
                ],
                stream=stream
            )
            
            if stream:
                return response
            else:
                return response['message']['content']
        
        except Exception as e:
            return f"❌ Erro ao gerar resposta: {e}"
    
    def get_system_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas do sistema.
        
        Returns:
            Dicionário com estatísticas
        """
        embedding_stats = self.embedding_manager.get_stats()
        
        return {
            'indexed_posts': embedding_stats['total_documents'],
            'profiles': embedding_stats['profiles'],
            'embedding_model': embedding_stats['embedding_model'],
            'generation_model': self.generation_model,
            'collection_name': embedding_stats['collection_name']
        }


def main():
    """Função de teste do sistema RAG."""
    print("=== Inicializando Sistema RAG ===\n")
    
    # Inicializa sistema
    rag = RAGSystem(
        generation_model="qwen2.5:3b"  # Modelo mais leve para teste
    )
    
    # Indexa posts (se necessário)
    print("\n=== Indexando Posts ===\n")
    rag.index_all_posts()
    
    # Estatísticas
    print("\n=== Estatísticas do Sistema ===\n")
    stats = rag.get_system_stats()
    for key, value in stats.items():
        print(f"{key}: {value}")
    
    # Teste de query
    print("\n=== Teste de Query ===\n")
    test_questions = [
        "Quais foram os posts mais recentes do DCE UFF?",
        "Mostre posts sobre o HUAP",
        "Quais posts tiveram mais engajamento?"
    ]
    
    for question in test_questions:
        print(f"\n❓ {question}")
        print("-" * 80)
        
        response, posts = rag.query(question, n_results=3)
        
        print(f"\n📝 Resposta:\n{response}")
        print(f"\n📊 Posts recuperados: {len(posts)}")


if __name__ == "__main__":
    main()
