"""
Aplicação Gradio para Chat RAG de Posts do Instagram.
Agora usando sistema de agente inteligente com interface profissional!
"""

import gradio as gr
from agent_system import RAGAgent
from rag_system import RAGSystem
from ping_theme import ping_theme
from data_injestion import DataInjestionPipeline, ContentType
from datetime import datetime
from typing import List, Tuple, Dict
import json
import os
from pathlib import Path
import traceback


class HistoryManager:
    """Gerencia o histórico de perguntas e respostas."""
    
    def __init__(self, history_file: str = "chat_history.json"):
        """
        Inicializa o gerenciador de histórico.
        
        Args:
            history_file: Arquivo para armazenar o histórico
        """
        self.history_file = history_file
        self.history: List[Dict] = self._load_history()
    
    def _load_history(self) -> List[Dict]:
        """Carrega histórico do arquivo."""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def _save_history(self):
        """Salva histórico no arquivo."""
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(self.history, f, ensure_ascii=False, indent=2)
    
    def add(self, question: str, response: str, profile_filter: str = None, posts_count: int = 0):
        """
        Adiciona entrada ao histórico.
        
        Args:
            question: Pergunta do usuário
            response: Resposta do sistema
            profile_filter: Filtro de perfil usado
            posts_count: Número de posts recuperados
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "question": question,
            "response": response[:500],  # Armazena resumo
            "profile_filter": profile_filter,
            "posts_count": posts_count
        }
        self.history.insert(0, entry)  # Mais recente no topo
        # Mantém apenas os últimos 500 registros
        if len(self.history) > 500:
            self.history = self.history[:500]
        self._save_history()
    
    def search(self, query: str) -> List[Dict]:
        """
        Busca no histórico.
        
        Args:
            query: Termo de busca
            
        Returns:
            Lista de entradas correspondentes
        """
        query_lower = query.lower()
        return [
            h for h in self.history
            if query_lower in h['question'].lower() or 
               query_lower in h['response'].lower()
        ]
    
    def get_stats(self) -> Dict:
        """Retorna estatísticas do histórico."""
        if not self.history:
            return {"total": 0, "profiles": {}, "avg_response_length": 0}
        
        profiles = {}
        total_response_length = 0
        
        for entry in self.history:
            profile = entry.get('profile_filter', 'Todos')
            profiles[profile] = profiles.get(profile, 0) + 1
            total_response_length += len(entry.get('response', ''))
        
        return {
            "total": len(self.history),
            "profiles": profiles,
            "avg_response_length": int(total_response_length / len(self.history)) if self.history else 0
        }


class InstagramRAGApp:
    """Aplicação de chat RAG com interface Gradio usando agente inteligente."""

    def __init__(
        self,
        embedding_model: str = "mxbai-embed-large",
        generation_model: str = "qwen3:30b",
        use_agent: bool = True
    ):
        """
        Inicializa a aplicação.
        
        Args:
            embedding_model: Modelo para embeddings
            generation_model: Modelo para geração
            use_agent: Se True, usa sistema de agente (recomendado)
        """
        print("🚀 Iniciando aplicação RAG...")
        
        self.use_agent = use_agent
        self.history_manager = HistoryManager()
        
        # Inicializa pipeline de ingestão
        print("📥 Inicializando pipeline de ingestão de dados...")
        
        if use_agent:
            # Inicializa sistema de agente inteligente
            print("🤖 Modo: Agente Inteligente (LLM decide quais ferramentas usar)")
            self.agent = RAGAgent(
                embedding_model=embedding_model,
                generation_model=generation_model,
                planning_model=generation_model  # Pode usar modelo mais leve aqui
            )
            # Mantém referência ao embedding_manager para stats
            self.embedding_manager = self.agent.embedding_manager
        else:
            # Sistema antigo com detecção de keywords
            print("🔧 Modo: Sistema Clássico (detecção por palavras-chave)")
            self.rag = RAGSystem(
                embedding_model=embedding_model,
                generation_model=generation_model
            )
            self.embedding_manager = self.rag.embedding_manager
        
        # Indexa posts na inicialização (se não usar agente)
        if not use_agent:
            print("\n📊 Verificando índice de posts...")
            self.rag.index_all_posts()
            self.stats = self.rag.get_system_stats()
            posts_count = self.stats.get('indexed_posts', 0)
        else:
            # Para o agente, verifica stats do embedding manager
            em_stats = self.embedding_manager.get_stats()
            # Adapta estrutura para compatibilidade
            self.stats = {
                'indexed_posts': em_stats.get('total_documents', 0),
                'profiles': em_stats.get('profiles', []),
                'sources': em_stats.get('sources', []),
                'content_types': em_stats.get('content_types', []),
                'embedding_model': em_stats.get('embedding_model', 'unknown'),
                'collection_name': em_stats.get('collection_name', 'unknown')
            }
            posts_count = self.stats['indexed_posts']
            print(f"📊 Perfis detectados: {self.stats['profiles']}")
            print(f"📂 Tipos de conteúdo: {self.stats['content_types']}")
        
        print(f"\n✓ Sistema pronto com {posts_count} posts indexados")
        
        # Pipeline de ingestão
        self.injestion_pipeline = DataInjestionPipeline(
            embedding_manager=self.embedding_manager,
            data_dir="data/injected"
        )
        print("✓ Pipeline de ingestão pronto")
    
    def format_sources(self, posts: List[dict]) -> str:
        """
        Formata posts recuperados para exibição.
        
        Args:
            posts: Lista de posts recuperados
            
        Returns:
            HTML formatado dos posts
        """
        if not posts:
            return "<p>Nenhum post encontrado.</p>"
        
        html = "<div style='margin-top: 20px;'>"
        
        # Verifica se é resultado de estatísticas ou comparação
        if posts and posts[0].get('is_stats'):
            stats = posts[0]['metadata']
            html += "<h3>📊 Estatísticas Calculadas:</h3>"
            html += f"""
            <div style='border: 1px solid #ddd; border-radius: 8px; padding: 15px; margin: 10px 0; background-color: #f0f8ff;'>
                <ul style='list-style-type: none; padding: 0;'>
                    <li><strong>Total de posts:</strong> {stats.get('total_posts', 0)}</li>
                    <li><strong>Total de curtidas:</strong> {stats.get('total_likes', 0):,}</li>
                    <li><strong>Total de comentários:</strong> {stats.get('total_comments', 0):,}</li>
                    <li><strong>Média de curtidas/post:</strong> {stats.get('avg_likes_per_post', 0):.2f}</li>
                    <li><strong>Média de comentários/post:</strong> {stats.get('avg_comments_per_post', 0):.2f}</li>
                    <li><strong>Engajamento total:</strong> {stats.get('total_engagement', 0):,}</li>
                </ul>
            </div>
            """
            return html + "</div>"
        
        if posts and posts[0].get('is_comparison'):
            comparison = posts[0]['metadata']
            html += "<h3>📊 Comparação Entre Perfis:</h3>"
            for profile, stats in comparison.items():
                html += f"""
                <div style='border: 1px solid #ddd; border-radius: 8px; padding: 15px; margin: 10px 0; background-color: #f9f9f9;'>
                    <h4 style='color: #1DA1F2; margin-top: 0;'>@{profile}</h4>
                    <ul style='list-style-type: none; padding: 0;'>
                        <li>Posts: {stats['total_posts']}</li>
                        <li>Curtidas: {stats['total_likes']:,} (média: {stats['avg_likes']:.1f})</li>
                        <li>Comentários: {stats['total_comments']:,} (média: {stats['avg_comments']:.1f})</li>
                        <li><strong>Engajamento total: {stats['total_engagement']:,}</strong></li>
                    </ul>
                </div>
                """
            return html + "</div>"
        
        # Verifica se é contagem de termo
        if posts and posts[0].get('is_term_count'):
            data = posts[0]['metadata']
            html += f"<h3>🔍 Contagem de Termo: '{data['term']}'</h3>"
            html += f"""
            <div style='border: 1px solid #667eea; border-radius: 8px; padding: 15px; margin: 10px 0; background-color: #f0f4ff;'>
                <ul style='list-style-type: none; padding: 0;'>
                    <li><strong>📊 Posts encontrados:</strong> {data['count']} de {data['total_posts']} ({data['percentage']}%)</li>
                    <li><strong>👥 Perfil(s):</strong> {data['profile']}</li>
                </ul>
            </div>
            """
            
            # Se houver erro
            if data.get('error'):
                html += f"<p style='color: red;'>⚠️ Erro: {data['error']}</p>"
                return html + "</div>"
            
            # Lista alguns posts que contêm o termo
            if data.get('matching_posts') and len(data['matching_posts']) > 0:
                html += "<h3>📌 Exemplos de Posts que Mencionam o Termo:</h3>"
                
                for i, post in enumerate(data['matching_posts'][:5], 1):
                    metadata = post.get('metadata', {})
                    doc = post.get('document', '')
                    
                    # Parse data
                    try:
                        from dateutil import parser as date_parser
                        timestamp = date_parser.parse(metadata['timestamp'])
                        date_str = timestamp.strftime('%d/%m/%Y às %H:%M')
                    except:
                        date_str = "Data não disponível"
                    
                    # Formata caption/documento
                    caption = doc if doc else metadata.get('caption', 'Sem legenda')
                    if len(caption) > 300:
                        caption = caption[:300] + "..."
                    
                    # Card do post
                    engagement = metadata.get('likesCount', 0) + metadata.get('commentsCount', 0)
                    html += f"""
                    <div style='
                        border: 1px solid #e0e0e0; 
                        border-radius: 12px; 
                        padding: 1.2rem; 
                        margin: 0.8rem 0; 
                        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
                        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
                    '>
                        <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.8rem;'>
                            <div style='display: flex; align-items: center; gap: 0.5rem;'>
                                <span style='
                                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                                    color: white;
                                    padding: 0.3rem 0.8rem;
                                    border-radius: 20px;
                                    font-weight: 600;
                                    font-size: 0.9rem;
                                '>@{metadata.get('profile', 'Desconhecido')}</span>
                            </div>
                            <span style='color: #888; font-size: 0.85rem;'>📅 {date_str}</span>
                        </div>
                        <p style='margin: 0.8rem 0; line-height: 1.6; color: #333;'>{caption}</p>
                        <div style='
                            display: flex; 
                            gap: 1.5rem; 
                            margin: 1rem 0; 
                            padding: 0.8rem; 
                            background: rgba(102, 126, 234, 0.05); 
                            border-radius: 8px;
                        '>
                            <span style='color: #666; font-size: 0.9rem; font-weight: 500;'>
                                ❤️ <strong style='color: #e91e63;'>{metadata['likesCount']:,}</strong> curtidas
                            </span>
                            <span style='color: #666; font-size: 0.9rem; font-weight: 500;'>
                                💬 <strong style='color: #2196f3;'>{metadata['commentsCount']:,}</strong> comentários
                            </span>
                            <span style='color: #666; font-size: 0.9rem; font-weight: 500;'>
                                📊 <strong style='color: #667eea;'>{engagement:,}</strong> engajamento
                            </span>
                        </div>
                        <a href='{metadata['url']}' target='_blank' style='
                            display: inline-flex;
                            align-items: center;
                            gap: 0.5rem;
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                            color: white;
                            text-decoration: none;
                            padding: 0.6rem 1.2rem;
                            border-radius: 8px;
                            font-size: 0.9rem;
                            font-weight: 600;
                        '>
                            🔗 Ver no Instagram
                        </a>
                    </div>
                    """
            
            return html + "</div>"
        
        # Verifica se é análise de sentimento
        if posts and posts[0].get('is_sentiment'):
            data = posts[0]['metadata']
            html += f"<h3>🎭 Análise de Sentimento: '{data['topic']}'</h3>"
            html += f"""
            <div style='border: 1px solid #667eea; border-radius: 8px; padding: 15px; margin: 10px 0; background-color: #f0f4ff;'>
                <ul style='list-style-type: none; padding: 0;'>
                    <li><strong>👥 Perfil(s):</strong> {data['profile']}</li>
                    <li><strong>📊 Posts analisados:</strong> {data['total_posts']}</li>
                </ul>
            </div>
            """
            
            # Se houver erro
            if data.get('error'):
                html += f"<p style='color: red;'>⚠️ Erro: {data['error']}</p>"
                return html + "</div>"
            
            # Resumo do sentimento
            html += f"""
            <div style='border-left: 4px solid #667eea; padding: 15px; margin: 10px 0; background-color: #f9f9f9;'>
                <h4 style='margin-top: 0;'>📝 Resumo Geral:</h4>
                <p>{data['sentiment_summary']}</p>
            </div>
            """
            
            # Distribuição de sentimentos (gráfico visual)
            total = data['positive_count'] + data['negative_count'] + data['neutral_count']
            pos_pct = (data['positive_count'] / total * 100) if total > 0 else 0
            neg_pct = (data['negative_count'] / total * 100) if total > 0 else 0
            neu_pct = (data['neutral_count'] / total * 100) if total > 0 else 0
            
            html += f"""
            <div style='border: 1px solid #ddd; border-radius: 8px; padding: 15px; margin: 10px 0;'>
                <h4 style='margin-top: 0;'>📊 Distribuição de Sentimentos:</h4>
                <div style='margin: 10px 0;'>
                    <div style='display: flex; align-items: center; margin: 5px 0;'>
                        <span style='width: 100px;'>✅ Positivo:</span>
                        <div style='flex: 1; background: #e0e0e0; border-radius: 4px; height: 20px; margin: 0 10px;'>
                            <div style='background: #4caf50; height: 100%; border-radius: 4px; width: {pos_pct}%;'></div>
                        </div>
                        <span style='width: 80px;'>{data['positive_count']} ({pos_pct:.1f}%)</span>
                    </div>
                    <div style='display: flex; align-items: center; margin: 5px 0;'>
                        <span style='width: 100px;'>❌ Negativo:</span>
                        <div style='flex: 1; background: #e0e0e0; border-radius: 4px; height: 20px; margin: 0 10px;'>
                            <div style='background: #f44336; height: 100%; border-radius: 4px; width: {neg_pct}%;'></div>
                        </div>
                        <span style='width: 80px;'>{data['negative_count']} ({neg_pct:.1f}%)</span>
                    </div>
                    <div style='display: flex; align-items: center; margin: 5px 0;'>
                        <span style='width: 100px;'>⚪ Neutro:</span>
                        <div style='flex: 1; background: #e0e0e0; border-radius: 4px; height: 20px; margin: 0 10px;'>
                            <div style='background: #9e9e9e; height: 100%; border-radius: 4px; width: {neu_pct}%;'></div>
                        </div>
                        <span style='width: 80px;'>{data['neutral_count']} ({neu_pct:.1f}%)</span>
                    </div>
                </div>
            </div>
            """
            
            # Aspectos positivos e negativos
            if data.get('positive_aspects') or data.get('negative_aspects'):
                html += "<div style='display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin: 10px 0;'>"
                
                if data.get('positive_aspects'):
                    html += """
                    <div style='border: 1px solid #4caf50; border-radius: 8px; padding: 15px; background-color: #f1f8f4;'>
                        <h4 style='margin-top: 0; color: #4caf50;'>✅ Aspectos Positivos:</h4>
                        <ul>
                    """
                    for aspect in data['positive_aspects']:
                        html += f"<li>{aspect}</li>"
                    html += "</ul></div>"
                
                if data.get('negative_aspects'):
                    html += """
                    <div style='border: 1px solid #f44336; border-radius: 8px; padding: 15px; background-color: #fef1f0;'>
                        <h4 style='margin-top: 0; color: #f44336;'>❌ Críticas/Aspectos Negativos:</h4>
                        <ul>
                    """
                    for aspect in data['negative_aspects']:
                        html += f"<li>{aspect}</li>"
                    html += "</ul></div>"
                
                html += "</div>"
            
            # Pontos-chave
            if data.get('key_points'):
                html += """
                <div style='border: 1px solid #667eea; border-radius: 8px; padding: 15px; margin: 10px 0; background-color: #f0f4ff;'>
                    <h4 style='margin-top: 0; color: #667eea;'>🔑 Pontos-Chave:</h4>
                    <ul>
                """
                for point in data['key_points']:
                    html += f"<li>{point}</li>"
                html += "</ul></div>"
            
            return html + "</div>"
        
        html += "<h3>📌 Posts Recuperados:</h3>"
        
        for i, post in enumerate(posts, 1):
            metadata = post['metadata']
            
            # Verifica se não é um post normal (stats, comparison, term_count, sentiment)
            # Esses tipos já foram renderizados acima
            if any(key in post for key in ['is_stats', 'is_comparison', 'is_term_count', 'is_sentiment']):
                continue
            
            # Parse data
            try:
                from dateutil import parser as date_parser
                timestamp = date_parser.parse(metadata['timestamp'])
                date_str = timestamp.strftime('%d/%m/%Y às %H:%M')
            except:
                date_str = "Data não disponível"
            
            # Detecta tipo de conteúdo
            content_type = metadata.get('content_type', 'instagram_post')
            source = metadata.get('source', 'instagram')
            
            # Documentos injetados via upload
            if source == 'upload' or content_type in ['document', 'article', 'report', 'research', 'manual', 'policy']:
                filename = metadata.get('filename', 'Documento')
                doc_id = metadata.get('doc_id', 'N/A')
                author = metadata.get('author', 'Desconhecido')
                description = metadata.get('description', '')
                tags = metadata.get('tags', '')
                chunk_index = metadata.get('chunk_index', 0)
                total_chunks = metadata.get('total_chunks', 1)
                
                # Texto do documento
                doc_text = post.get('document', '')
                if len(doc_text) > 500:
                    doc_text = doc_text[:500] + "..."
                
                html += f"""
                <div style='
                    border: 1px solid #2196f3; 
                    border-radius: 12px; 
                    padding: 1.2rem; 
                    margin: 0.8rem 0; 
                    background: linear-gradient(135deg, #e3f2fd 0%, #ffffff 100%);
                    box-shadow: 0 2px 8px rgba(33, 150, 243, 0.15);
                ' onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 4px 12px rgba(33, 150, 243, 0.25)'" 
                   onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 2px 8px rgba(33, 150, 243, 0.15)'">
                    <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.8rem;'>
                        <span style='
                            background: linear-gradient(135deg, #2196f3 0%, #1976d2 100%);
                            color: white;
                            padding: 0.3rem 0.8rem;
                            border-radius: 20px;
                            font-weight: 600;
                            font-size: 0.9rem;
                        '>📄 Documento</span>
                        <span style='color: #888; font-size: 0.85rem;'>🔢 Chunk {chunk_index + 1}/{total_chunks}</span>
                    </div>
                    <h4 style='margin: 0.5rem 0; color: #2196f3; font-size: 1.1rem;'>{filename}</h4>
                    <p style='margin: 0.5rem 0; color: #666; font-size: 0.9rem;'><strong>✍️ {author}</strong></p>
                    {f"<p style='margin: 0.5rem 0; color: #666; font-size: 0.85rem; font-style: italic;'>{description}</p>" if description else ""}
                    {f"<p style='margin: 0.5rem 0;'><span style='background: #e3f2fd; color: #1976d2; padding: 0.2rem 0.6rem; border-radius: 12px; font-size: 0.8rem;'>{tags}</span></p>" if tags else ""}
                    <div style='
                        margin: 0.8rem 0; 
                        padding: 1rem; 
                        background: rgba(33, 150, 243, 0.05); 
                        border-left: 3px solid #2196f3; 
                        border-radius: 4px;
                    '>
                        <p style='margin: 0; line-height: 1.6; color: #333; font-family: monospace; font-size: 0.9rem;'>{doc_text}</p>
                    </div>
                    <div style='color: #888; font-size: 0.8rem; margin-top: 0.5rem;'>
                        🆔 ID: {doc_id[:12]}... | 📅 {date_str}
                    </div>
                </div>
                """
            elif content_type == 'news':
                # Formatação para notícias
                title = metadata.get('title', 'Sem título')
                description = metadata.get('description', '')
                publisher = metadata.get('publisher_name', 'Desconhecido')
                
                if len(description) > 400:
                    description = description[:400] + "..."
                
                html += f"""
                <div style='
                    border: 1px solid #ff9800; 
                    border-radius: 12px; 
                    padding: 1.2rem; 
                    margin: 0.8rem 0; 
                    background: linear-gradient(135deg, #fff8f0 0%, #ffffff 100%);
                    box-shadow: 0 2px 8px rgba(255, 152, 0, 0.15);
                ' onmouseover="this.style.boxShadow='0 4px 12px rgba(255, 152, 0, 0.25)'" 
                   onmouseout="this.style.boxShadow='0 2px 8px rgba(255, 152, 0, 0.15)'">
                    <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.8rem;'>
                        <span style='
                            background: linear-gradient(135deg, #ff9800 0%, #f57c00 100%);
                            color: white;
                            padding: 0.3rem 0.8rem;
                            border-radius: 20px;
                            font-weight: 600;
                            font-size: 0.9rem;
                        '>📰 Notícia</span>
                        <span style='color: #888; font-size: 0.85rem;'>📅 {date_str}</span>
                    </div>
                    <h4 style='margin: 0.5rem 0; color: #ff9800; font-size: 1.1rem;'>{title}</h4>
                    <p style='margin: 0.5rem 0; color: #666; font-size: 0.9rem;'><strong>📡 {publisher}</strong></p>
                    <p style='margin: 0.8rem 0; line-height: 1.6; color: #333;'>{description}</p>
                    <a href='{metadata['url']}' target='_blank' style='
                        display: inline-flex;
                        align-items: center;
                        gap: 0.5rem;
                        background: linear-gradient(135deg, #ff9800 0%, #f57c00 100%);
                        color: white;
                        text-decoration: none;
                        padding: 0.6rem 1.2rem;
                        border-radius: 8px;
                        font-size: 0.9rem;
                        font-weight: 600;
                    ' onmouseover="this.style.opacity='0.9'" onmouseout="this.style.opacity='1'">
                        🔗 Ler notícia completa
                    </a>
                </div>
                """
            elif metadata.get('profile') == 'web_search':
                # Formatação para resultados de web_search
                title = metadata.get('title', 'Sem título')
                body = metadata.get('body', '')
                source = metadata.get('source', '#')
                
                if len(body) > 400:
                    body = body[:400] + "..."
                
                html += f"""
                <div style='
                    border: 1px solid #4caf50; 
                    border-radius: 12px; 
                    padding: 1.2rem; 
                    margin: 0.8rem 0; 
                    background: linear-gradient(135deg, #f1f8f4 0%, #ffffff 100%);
                    box-shadow: 0 2px 8px rgba(76, 175, 80, 0.15);
                ' onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 4px 12px rgba(76, 175, 80, 0.25)'" 
                   onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 2px 8px rgba(76, 175, 80, 0.15)'">
                    <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.8rem;'>
                        <span style='
                            background: linear-gradient(135deg, #4caf50 0%, #45a049 100%);
                            color: white;
                            padding: 0.3rem 0.8rem;
                            border-radius: 20px;
                            font-weight: 600;
                            font-size: 0.9rem;
                        '>🌐 Web</span>
                        <span style='color: #888; font-size: 0.85rem;'>{date_str if date_str != "Data não disponível" else "Data não disponível"}</span>
                    </div>
                    <h4 style='margin: 0.5rem 0; color: #4caf50; font-size: 1.1rem;'>{title}</h4>
                    <p style='margin: 0.8rem 0; line-height: 1.6; color: #333;'>{body}</p>
                    <a href='{source}' target='_blank' style='
                        display: inline-flex;
                        align-items: center;
                        gap: 0.5rem;
                        background: linear-gradient(135deg, #4caf50 0%, #45a049 100%);
                        color: white;
                        text-decoration: none;
                        padding: 0.6rem 1.2rem;
                        border-radius: 8px;
                        font-size: 0.9rem;
                        font-weight: 600;
                    ' onmouseover="this.style.opacity='0.9'" onmouseout="this.style.opacity='1'">
                        🔗 Visitar página
                    </a>
                </div>
                """
            else:
                # Formatação para posts do Instagram
                caption = metadata.get('caption', 'Sem legenda')
                if len(caption) > 300:
                    caption = caption[:300] + "..."
                
                engagement = metadata.get('likesCount', 0) + metadata.get('commentsCount', 0)
                html += f"""
                <div style='
                    border: 1px solid #e0e0e0; 
                    border-radius: 12px; 
                    padding: 1.2rem; 
                    margin: 0.8rem 0; 
                    background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
                    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
                ' onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 4px 12px rgba(0,0,0,0.12)'" 
                   onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 2px 8px rgba(0,0,0,0.08)'">
                    <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.8rem;'>
                        <div style='display: flex; align-items: center; gap: 0.5rem;'>
                            <span style='
                                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                                color: white;
                                padding: 0.3rem 0.8rem;
                                border-radius: 20px;
                                font-weight: 600;
                                font-size: 0.9rem;
                            '>@{metadata.get('profile', 'Desconhecido')}</span>
                        </div>
                        <span style='color: #888; font-size: 0.85rem;'>📅 {date_str}</span>
                    </div>
                    <p style='margin: 0.8rem 0; line-height: 1.6; color: #333;'>{caption}</p>
                    <div style='
                        display: flex; 
                        gap: 1.5rem; 
                        margin: 1rem 0; 
                        padding: 0.8rem; 
                        background: rgba(102, 126, 234, 0.05); 
                        border-radius: 8px;
                    '>
                        <span style='color: #666; font-size: 0.9rem; font-weight: 500;'>
                            ❤️ <strong style='color: #e91e63;'>{metadata.get('likesCount', 0):,}</strong> curtidas
                        </span>
                        <span style='color: #666; font-size: 0.9rem; font-weight: 500;'>
                            💬 <strong style='color: #2196f3;'>{metadata.get('commentsCount', 0):,}</strong> comentários
                        </span>
                        <span style='color: #666; font-size: 0.9rem; font-weight: 500;'>
                            📊 <strong style='color: #667eea;'>{engagement:,}</strong> engajamento
                        </span>
                    </div>
                    <a href='{metadata.get('url', '#')}' target='_blank' style='
                        display: inline-flex;
                        align-items: center;
                        gap: 0.5rem;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                        text-decoration: none;
                        padding: 0.6rem 1.2rem;
                        border-radius: 8px;
                        font-size: 0.9rem;
                        font-weight: 600;
                    ' onmouseover="this.style.opacity='0.9'" onmouseout="this.style.opacity='1'">
                        🔗 Ver no Instagram
                    </a>
                </div>
                """
        
        html += "</div>"
        return html
    
    def chat_response(
        self, 
        message: str, 
        history: List[Tuple[str, str]],
        n_results: int,
        profile_filter: List[str]
    ) -> Tuple[str, str]:
        """
        Processa mensagem do chat e retorna resposta.
        
        Args:
            message: Mensagem do usuário
            history: Histórico do chat
            n_results: Número de posts a recuperar (ignorado no modo agente)
            profile_filter: Lista de fontes selecionadas (perfis Instagram com @ ou documentos com 📄)
            
        Returns:
            Tupla (resposta, fontes_html)
        """
        if not message.strip():
            return "Por favor, faça uma pergunta.", ""
        
        # Processa filtro de fontes
        # Extrai perfis Instagram (remover @) e tipos de documentos (remover 📄)
        profiles_selected = [f.replace("@", "").strip() for f in profile_filter if f.startswith("@")]
        content_types_selected = [f.replace("📄", "").strip() for f in profile_filter if f.startswith("📄")]
        
        # Para a compatibilidade com query tools, passa um perfil único ou None
        profile = None
        if profiles_selected and len(profiles_selected) == 1:
            # Um único perfil Instagram selecionado
            profile = profiles_selected[0]
        # Se múltiplos perfis ou mistura de perfis+documentos, não filtra por perfil (busca em todos)
        
        # Executa query
        if self.use_agent:
            # Modo agente: LLM decide tudo
            response, posts = self.agent.query(
                question=message,
                profile_filter=profile
            )
        else:
            # Modo clássico: keywords + n_results
            response, posts = self.rag.query(
                question=message,
                n_results=n_results,
                profile_filter=profile
            )
        
        # Salva no histórico
        posts_count = len(posts) if posts else 0
        # Formata filter_label para histórico (ex: "@dceuff, 📄 Artigo")
        filter_label = ", ".join(profile_filter) if profile_filter else "Todas as fontes"
        self.history_manager.add(
            question=message,
            response=response,
            profile_filter=filter_label,
            posts_count=posts_count
        )
        
        # Formata fontes
        sources_html = self.format_sources(posts)
        
        return response, sources_html
    
    def get_dashboard_html(self) -> str:
        """
        Retorna HTML com dashboard de estatísticas profissional.
        Usa variáveis CSS para compatibilidade com light/dark mode.
        
        Returns:
            HTML formatado com dashboard
        """
        history_stats = self.history_manager.get_stats()
        generation_model = self.agent.generation_model if self.use_agent else self.rag.generation_model
        
        # Estatísticas por perfil do histórico
        profile_stats_html = ""
        if history_stats['profiles']:
            for profile, count in sorted(history_stats['profiles'].items(), key=lambda x: x[1], reverse=True):
                profile_name = profile if profile else "Sem filtro"
                percentage = (count / history_stats['total']) * 100 if history_stats['total'] > 0 else 0
                profile_stats_html += f"""
                <div style='margin: 0.8rem 0;'>
                    <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.3rem;'>
                        <span style='font-weight: 500; color: var(--text-primary);'>{profile_name}</span>
                        <span style='color: var(--primary); font-weight: 600;'>{count}</span>
                    </div>
                    <div style='background: var(--border-primary); height: 8px; border-radius: 4px; overflow: hidden;'>
                        <div style='background: linear-gradient(90deg, var(--primary), var(--primary-dark)); height: 100%; width: {percentage}%;'></div>
                    </div>
                </div>
                """
        
        html = f"""
        <div style='padding: 2rem; background: var(--bg-primary); color: var(--text-primary);'>
            <!-- Header do Dashboard -->
            <div style='margin-bottom: 2rem;'>
                <h2 style='margin: 0 0 0.5rem 0; color: var(--text-primary); font-size: 1.8rem;'>📊 Dashboard de Estatísticas</h2>
                <p style='margin: 0; color: var(--text-secondary); font-size: 0.9rem;'>Atualizado em {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}</p>
            </div>
            
            <!-- Grid de Estatísticas Principais -->
            <div style='display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1.5rem; margin-bottom: 2rem;'>
                <!-- Card: Dados Indexados -->
                <div style='
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 1.5rem;
                    border-radius: 12px;
                    box-shadow: var(--shadow-md);
                    transition: transform 0.3s ease;
                '>
                    <div style='display: flex; justify-content: space-between; align-items: flex-start;'>
                        <div>
                            <p style='margin: 0; font-size: 0.9rem; opacity: 0.9;'>📝 Registros Indexados</p>
                            <h3 style='margin: 0.5rem 0 0 0; font-size: 2.5rem;'>{self.stats['indexed_posts']:,}</h3>
                        </div>
                        <span style='font-size: 2rem; opacity: 0.8;'>📚</span>
                    </div>
                </div>
                
                <!-- Card: Fontes -->
                <div style='
                    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                    color: white;
                    padding: 1.5rem;
                    border-radius: 12px;
                    box-shadow: var(--shadow-md);
                    transition: transform 0.3s ease;
                '>
                    <div style='display: flex; justify-content: space-between; align-items: flex-start;'>
                        <div>
                            <p style='margin: 0; font-size: 0.9rem; opacity: 0.9;'>👥 Fontes de Dados</p>
                            <h3 style='margin: 0.5rem 0 0 0; font-size: 2.5rem;'>{len(self.stats['profiles'])}</h3>
                        </div>
                        <span style='font-size: 2rem; opacity: 0.8;'>�</span>
                    </div>
                </div>
                
                <!-- Card: Consultas Realizadas -->
                <div style='
                    background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
                    color: white;
                    padding: 1.5rem;
                    border-radius: 12px;
                    box-shadow: var(--shadow-md);
                    transition: transform 0.3s ease;
                '>
                    <div style='display: flex; justify-content: space-between; align-items: flex-start;'>
                        <div>
                            <p style='margin: 0; font-size: 0.9rem; opacity: 0.9;'>💬 Consultas Realizadas</p>
                            <h3 style='margin: 0.5rem 0 0 0; font-size: 2.5rem;'>{history_stats['total']}</h3>
                        </div>
                        <span style='font-size: 2rem; opacity: 0.8;'>❓</span>
                    </div>
                </div>
            </div>
            
            <!-- Informações do Sistema -->
            <div style='background: var(--bg-secondary); border-radius: 12px; padding: 1.5rem; margin-bottom: 2rem; border: 1px solid var(--border-primary);'>
                <h3 style='margin: 0 0 1rem 0; color: var(--text-primary);'>🔧 Configuração do Sistema</h3>
                <div style='display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem;'>
                    <div>
                        <p style='margin: 0; color: var(--text-secondary); font-size: 0.85rem; font-weight: 600; text-transform: uppercase;'>Modelo de Embedding</p>
                        <p style='margin: 0.3rem 0 0 0; color: var(--text-primary); font-weight: 500;'>{self.stats['embedding_model']}</p>
                    </div>
                    <div>
                        <p style='margin: 0; color: var(--text-secondary); font-size: 0.85rem; font-weight: 600; text-transform: uppercase;'>Modelo de Geração</p>
                        <p style='margin: 0.3rem 0 0 0; color: var(--text-primary); font-weight: 500;'>{generation_model}</p>
                    </div>
                    <div>
                        <p style='margin: 0; color: var(--text-secondary); font-size: 0.85rem; font-weight: 600; text-transform: uppercase;'>Modo de Operação</p>
                        <p style='margin: 0.3rem 0 0 0; color: var(--text-primary); font-weight: 500;'>{'🤖 Agente Inteligente' if self.use_agent else '🔧 Sistema Clássico'}</p>
                    </div>
                </div>
            </div>
            
            <!-- Fontes de Dados -->
            <div style='background: var(--bg-secondary); border-radius: 12px; padding: 1.5rem; margin-bottom: 2rem; border: 1px solid var(--border-primary);'>
                <h3 style='margin: 0 0 1rem 0; color: var(--text-primary);'>� Fontes de Dados</h3>
                <div style='display: flex; gap: 0.8rem; flex-wrap: wrap;'>
                    {''.join([f"<span style='background: var(--primary); color: white; padding: 0.5rem 1rem; border-radius: 20px; font-size: 0.85rem; font-weight: 600;'>@{profile}</span>" for profile in self.stats['profiles']])}
                </div>
            </div>
            
            <!-- Distribuição de Consultas por Fonte -->
            {f'''<div style='background: var(--bg-secondary); border-radius: 12px; padding: 1.5rem; border: 1px solid var(--border-primary);'>
                <h3 style='margin: 0 0 1rem 0; color: var(--text-primary);'>📈 Distribuição de Consultas por Fonte</h3>
                {profile_stats_html if profile_stats_html else '<p style="color: var(--text-secondary); margin: 0;">Nenhuma consulta realizada ainda.</p>'}
            </div>''' if history_stats['total'] > 0 else ''}
        </div>
        """
        return html
    
    def get_history_html(self, search_query: str = None) -> str:
        """
        Retorna HTML com histórico de perguntas.
        Usa variáveis CSS para compatibilidade com light/dark mode.
        
        Args:
            search_query: Termo para buscar no histórico
            
        Returns:
            HTML formatado com histórico
        """
        # Busca ou obtém todo o histórico
        if search_query:
            entries = self.history_manager.search(search_query)
        else:
            entries = self.history_manager.history[:50]  # Últimos 50
        
        if not entries:
            return """
            <div style='padding: 2rem; text-align: center; color: var(--text-secondary);'>
                <p style='font-size: 1.1rem;'>📭 Nenhuma consulta encontrada no histórico</p>
            </div>
            """
        
        html = f"""
        <div style='padding: 2rem; background: var(--bg-primary); color: var(--text-primary);'>
            <h2 style='margin: 0 0 1.5rem 0; color: var(--text-primary);'>📚 Histórico de Consultas</h2>
            <p style='color: var(--text-secondary); margin: 0 0 1.5rem 0;'>Total: <strong>{len(entries)}</strong> registros</p>
        """
        
        for i, entry in enumerate(entries, 1):
            try:
                timestamp = datetime.fromisoformat(entry['timestamp'])
                date_str = timestamp.strftime('%d/%m/%Y às %H:%M')
            except:
                date_str = "Data desconhecida"
            
            profile_badge = f"@{entry['profile_filter']}" if entry.get('profile_filter') else "🌐 Todos"
            posts_info = f"📊 {entry.get('posts_count', 0)} registros encontrados"
            
            html += f"""
            <div style='
                background: var(--bg-secondary);
                border: 1px solid var(--border-primary);
                border-radius: 12px;
                padding: 1.2rem;
                margin-bottom: 1rem;
                box-shadow: var(--shadow-sm);
                transition: all 0.3s ease;
            ' onmouseover="this.style.boxShadow='var(--shadow-md)'; this.style.transform='translateY(-2px)'" 
               onmouseout="this.style.boxShadow='var(--shadow-sm)'; this.style.transform='translateY(0)'">
                <div style='display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.8rem;'>
                    <div>
                        <span style='background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 0.3rem 0.8rem; border-radius: 20px; font-size: 0.8rem; font-weight: 600; display: inline-block; margin-right: 0.5rem;'>#{i}</span>
                        <span style='background: var(--bg-tertiary); color: var(--text-primary); padding: 0.3rem 0.8rem; border-radius: 20px; font-size: 0.8rem; display: inline-block;'>{profile_badge}</span>
                    </div>
                    <span style='color: var(--text-secondary); font-size: 0.85rem;'>🕐 {date_str}</span>
                </div>
                <p style='margin: 0.8rem 0; font-weight: 600; color: var(--text-primary);'>❓ {entry['question']}</p>
                <p style='margin: 0.5rem 0; color: var(--text-secondary); font-size: 0.9rem; line-height: 1.5;'>{entry['response']}</p>
                <div style='display: flex; gap: 0.5rem; margin-top: 0.8rem; font-size: 0.85rem;'>
                    <span style='color: var(--primary);'>💬</span>
                    <span style='color: var(--text-secondary);'>{posts_info}</span>
                </div>
            </div>
            """
        
        html += "</div>"
        return html
    
    def get_stats_html(self) -> str:
        """
        Retorna HTML com estatísticas do sistema.
        
        Returns:
            HTML formatado com estatísticas
        """
        # self.stats já foi populado no __init__
        generation_model = self.agent.generation_model if self.use_agent else self.rag.generation_model
        
        html = f"""
        <div style='padding: 20px; background-color: #f0f8ff; border-radius: 10px; border: 1px solid #1DA1F2;'>
            <h3 style='margin-top: 0; color: #1DA1F2;'>📊 Estatísticas do Sistema</h3>
            <ul style='list-style-type: none; padding: 0;'>
                <li>📝 <strong>Posts indexados:</strong> {self.stats['indexed_posts']}</li>
                <li>👥 <strong>Perfis:</strong> {', '.join(['@' + p for p in self.stats['profiles']])}</li>
                <li>🧠 <strong>Modelo de embedding:</strong> {self.stats['embedding_model']}</li>
                <li>💬 <strong>Modelo de geração:</strong> {generation_model}</li>
                <li>🤖 <strong>Modo:</strong> {'Agente Inteligente' if self.use_agent else 'Clássico (Keywords)'}</li>
            </ul>
        </div>
        """
        return html
    
    def get_injected_documents_html(self) -> str:
        """
        Retorna HTML com lista de documentos injetados.
        
        Returns:
            HTML formatado com documentos
        """
        docs = self.injestion_pipeline.get_injected_documents()
        stats = self.injestion_pipeline.get_stats()
        
        if not docs:
            return """
            <div style='padding: 2rem; text-align: center; color: var(--text-secondary);'>
                <p style='font-size: 1.1rem;'>📭 Nenhum documento injetado ainda</p>
                <p style='color: var(--text-secondary);'>Use o painel de ingestão para adicionar documentos</p>
            </div>
            """
        
        html = f"""
        <div style='padding: 2rem; background: var(--bg-primary); color: var(--text-primary);'>
            <h2 style='margin: 0 0 1.5rem 0; color: var(--text-primary);'>📂 Documentos Injetados</h2>
            
            <!-- Estatísticas de Ingestão -->
            <div style='display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 2rem;'>
                <div style='background: var(--bg-secondary); border: 1px solid var(--border-primary); border-radius: 8px; padding: 1rem; text-align: center;'>
                    <p style='margin: 0 0 0.5rem 0; color: var(--text-secondary); font-size: 0.85rem;'>📚 Total</p>
                    <h3 style='margin: 0; color: var(--primary); font-size: 1.8rem;'>{stats['total_documents']}</h3>
                </div>
                <div style='background: var(--bg-secondary); border: 1px solid var(--border-primary); border-radius: 8px; padding: 1rem; text-align: center;'>
                    <p style='margin: 0 0 0.5rem 0; color: var(--text-secondary); font-size: 0.85rem;'>📄 Páginas</p>
                    <h3 style='margin: 0; color: var(--primary); font-size: 1.8rem;'>{stats['total_pages']}</h3>
                </div>
                <div style='background: var(--bg-secondary); border: 1px solid var(--border-primary); border-radius: 8px; padding: 1rem; text-align: center;'>
                    <p style='margin: 0 0 0.5rem 0; color: var(--text-secondary); font-size: 0.85rem;'>💾 Tamanho</p>
                    <h3 style='margin: 0; color: var(--primary); font-size: 1.8rem;'>{stats['total_size_mb']:.2f} MB</h3>
                </div>
            </div>
            
            <!-- Lista de Documentos -->
            <div style='display: grid; gap: 1rem;'>
        """
        
        for doc in docs:
            doc_id = doc['id'][:8]
            upload_date = datetime.fromisoformat(doc['upload_date']).strftime('%d/%m/%Y %H:%M')
            content_type = doc['content_type'].upper()
            size_kb = doc['file_size_bytes'] / 1024
            
            tags_html = ""
            if doc.get('custom_tags'):
                tags_html = "".join([
                    f"<span style='background: var(--primary); color: white; padding: 0.25rem 0.6rem; border-radius: 12px; font-size: 0.75rem; margin-right: 0.3rem;'>{tag}</span>"
                    for tag in doc['custom_tags'][:3]
                ])
            
            html += f"""
            <div style='
                background: var(--bg-secondary);
                border: 1px solid var(--border-primary);
                border-radius: 8px;
                padding: 1.2rem;
                box-shadow: var(--shadow-sm);
                transition: all 0.3s ease;
            ' onmouseover="this.style.boxShadow='var(--shadow-md)'" onmouseout="this.style.boxShadow='var(--shadow-sm)'">
                <div style='display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.8rem;'>
                    <div>
                        <span style='background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 0.4rem 0.8rem; border-radius: 6px; font-weight: 600; font-size: 0.85rem; display: inline-block;'>
                            {content_type}
                        </span>
                    </div>
                    <span style='color: var(--text-secondary); font-size: 0.8rem;'>ID: {doc_id}</span>
                </div>
                
                <h4 style='margin: 0.5rem 0; color: var(--text-primary);'>
                    📄 {doc['filename']}
                </h4>
                
                <p style='margin: 0.5rem 0; color: var(--text-secondary); font-size: 0.9rem;'>
                    {doc.get('description', 'Sem descrição')}
                </p>
                
                <div style='display: flex; gap: 1rem; margin: 0.8rem 0; font-size: 0.85rem; color: var(--text-secondary);'>
                    <span>📅 {upload_date}</span>
                    <span>💾 {size_kb:.1f} KB</span>
                    <span>📄 {doc.get('page_count', 1)} página(s)</span>
                    {f"<span>✍️ {doc.get('author', 'N/A')}</span>" if doc.get('author') else ""}
                </div>
                
                {f"<div style='margin: 0.8rem 0;'>{tags_html}</div>" if tags_html else ""}
            </div>
            """
        
        html += """
            </div>
        </div>
        """
        return html
    
    def create_interface(self) -> gr.Blocks:
        """
        Cria interface Gradio profissional com abas navegáveis.
        Tema claro como padrão com suporte total a dark mode.
        
        Returns:
            Interface Gradio configurada
        """
        with gr.Blocks(
            title="VoxCampus - UFF",
            theme=ping_theme
        ) as app:
            
            # Header principal
            gr.HTML(f"""
            <div class="header-container">
                <h1>🎓 VoxCampus - UFF</h1>
            </div>
            """)
            
            # Interface com abas
            with gr.Tabs():
                # ===== ABA 1: CHAT =====
                with gr.TabItem("💬 Chat"):
                    with gr.Row():
                        with gr.Column(scale=7, elem_classes="chat-container"):
                            # Área de chat
                            chatbot = gr.Chatbot(
                                label="Conversa",
                                height=600,
                                show_copy_button=True,
                                show_label=False,
                                type="tuples"
                            )
                            
                            # Input de mensagem
                            with gr.Row():
                                msg = gr.Textbox(
                                    label="",
                                    placeholder="Digite sua pergunta... Ex: Qual foi a última aparição do reitor?",
                                    lines=2,
                                    scale=9,
                                    show_label=False
                                )
                                send_btn = gr.Button(
                                    "✉️ Enviar", 
                                    scale=1, 
                                    variant="primary",
                                    size="lg"
                                )
                            
                            # Botões de ação
                            with gr.Row():
                                clear_btn = gr.Button("🗑️ Limpar", size="sm", variant="secondary", scale=2)
                                copy_btn = gr.Button("📋 Copiar Último", size="sm", scale=2)
                                gr.Markdown("")  # Spacer
                            
                            # Fontes recuperadas
                            with gr.Accordion("📚 Posts Recuperados (Fontes)", open=False):
                                sources = gr.HTML()
                        
                        # Painel lateral
                        with gr.Column(scale=3, elem_classes="sidebar-config"):
                            gr.Markdown("### ⚙️ Configurações")
                            
                            # Construir lista de fontes (perfis Instagram + tipos de documentos)
                            instagram_profiles = ["@" + p for p in self.stats.get('profiles', [])]
                            document_types = ["📄 " + t for t in self.stats.get('content_types', [])]
                            all_sources = instagram_profiles + document_types
                            
                            # Botões de perfil como checkboxes (agora chamado "Lista de Fontes")
                            profile_filter = gr.CheckboxGroup(
                                choices=all_sources if all_sources else ["(nenhuma fonte disponível)"],
                                value=all_sources,  # Todos selecionados por padrão
                                label="📊 Lista de Fontes (selecione uma ou mais)",
                                interactive=True,
                                elem_classes="profile-checkbox-group"
                            )
                            
                            if not self.use_agent:
                                n_results = gr.Slider(
                                    minimum=1,
                                    maximum=15,
                                    value=5,
                                    step=1,
                                    label="Nº Posts"
                                )
                            else:
                                n_results = gr.Number(value=5, visible=False)
                            
                            gr.Markdown("---")
                            gr.Markdown("### 💡 Sugestões")
                            
                            # Exemplos dinâmicos
                            example_questions = [
                                ("🏆", "Post mais curtido"),
                                ("📊", "Comparar perfis"),
                                ("🔍", "Posts sobre HUAP"),
                                ("🎓", "Menções estudantes"),
                                ("❤️", "Tendências")
                            ]
                            
                            for emoji, question in example_questions:
                                gr.Button(
                                    f"{emoji} {question}",
                                    size="sm",
                                    elem_classes="example-btn"
                                ).click(
                                    lambda q=question: q,
                                    outputs=msg
                                )
                            
                            gr.Markdown("---")
                            gr.Markdown("**🔬 Modo de IA:**")
                            mode_text = "🤖 Agente (LLM decide ferramentas)" if self.use_agent else "🔍 Clássico (Keywords)"
                            gr.Markdown(f"__{mode_text}__")
                
                # ===== ABA 2: ESTATÍSTICAS =====
                with gr.TabItem("📊 Estatísticas"):
                    dashboard_html = gr.HTML(value=self.get_dashboard_html())
                
                # ===== ABA 3: HISTÓRICO =====
                with gr.TabItem("📚 Histórico"):
                    with gr.Row():
                        with gr.Column(scale=8):
                            history_html = gr.HTML(value=self.get_history_html())
                        with gr.Column(scale=2):
                            gr.Markdown("### � Buscar")
                            search_box = gr.Textbox(
                                label="",
                                placeholder="Buscar histórico...",
                                show_label=False
                            )
                            search_btn = gr.Button("Buscar", variant="primary", size="lg")
                            
                            def search_history(query):
                                return self.get_history_html(search_query=query if query else None)
                            
                            search_btn.click(
                                search_history,
                                inputs=search_box,
                                outputs=history_html
                            )
                            
                            search_box.submit(
                                search_history,
                                inputs=search_box,
                                outputs=history_html
                            )
                            
                            clear_search = gr.Button("Limpar", size="sm")
                            clear_search.click(
                                lambda: self.get_history_html(),
                                outputs=history_html
                            )
                
                # ===== ABA 4: INGESTÃO DE DADOS =====
                with gr.TabItem("📥 Ingestão de Dados"):
                    with gr.Row():
                        with gr.Column(scale=1):
                            gr.Markdown("### 📤 Upload de Documentos")
                            
                            # Upload de arquivo
                            upload_file = gr.File(
                                label="Selecione um documento",
                                file_types=[".pdf", ".docx", ".pptx", ".txt", ".md", ".html"],
                                file_count="single"
                            )
                            
                            # Tipo de conteúdo
                            content_type = gr.Radio(
                                choices=[
                                    "Documento", 
                                    "Artigo", 
                                    "Relatório", 
                                    "Pesquisa", 
                                    "Manual", 
                                    "Política",
                                    "Outro"
                                ],
                                value="Documento",
                                label="Tipo de Conteúdo"
                            )
                            
                            # Autor
                            author = gr.Textbox(
                                label="Autor/Criador (opcional)",
                                placeholder="Ex: João Silva",
                                lines=1
                            )
                            
                            # Descrição
                            description = gr.Textbox(
                                label="Descrição (opcional)",
                                placeholder="Descreva brevemente o conteúdo",
                                lines=3
                            )
                            
                            # Tags
                            tags = gr.Textbox(
                                label="Tags (separadas por vírgula)",
                                placeholder="Ex: HUAP, Saúde, Medicina",
                                lines=2
                            )
                            
                            # URL (se aplicável)
                            source_url = gr.Textbox(
                                label="URL de origem (opcional)",
                                placeholder="https://...",
                                lines=1
                            )
                            
                            # Botão de ingestão
                            inject_btn = gr.Button(
                                "🚀 Ingerir Documento",
                                variant="primary",
                                size="lg"
                            )
                        
                        with gr.Column(scale=1):
                            gr.Markdown("### 📝 Ou Cole Texto Diretamente")
                            
                            # Texto direto
                            raw_text = gr.Textbox(
                                label="Cole o texto aqui",
                                placeholder="Texto bruto para ingestão...",
                                lines=8
                            )
                            
                            # Nome da fonte
                            text_source_name = gr.Textbox(
                                label="Nome da Fonte",
                                placeholder="Ex: Notícia UFRJ",
                                lines=1
                            )
                            
                            # Tipo de conteúdo para texto
                            text_content_type = gr.Radio(
                                choices=["Artigo", "Notícia", "Conteúdo", "Outro"],
                                value="Artigo",
                                label="Tipo"
                            )
                            
                            # Botão para texto
                            inject_text_btn = gr.Button(
                                "📝 Ingerir Texto",
                                variant="primary",
                                size="lg"
                            )
                    
                    # Resultados
                    with gr.Row():
                        injection_status = gr.HTML(
                            value="<p style='color: var(--text-secondary); text-align: center;'>Aguardando upload...</p>"
                        )
                    
                    gr.Markdown("---")
                    
                    # Documentos injetados
                    with gr.Row():
                        injected_docs_html = gr.HTML(
                            value=self.get_injected_documents_html()
                        )
                    
                    # Funções de ingestão
                    def handle_file_injection(file, ctype, author_name, desc, tag_list, url):
                        """Processa ingestão de arquivo."""
                        if file is None:
                            return "<p style='color: red;'>❌ Nenhum arquivo selecionado</p>", self.get_injected_documents_html()
                        
                        try:
                            # Mapeia tipo de conteúdo
                            ct_map = {
                                "Documento": ContentType.DOCUMENT,
                                "Artigo": ContentType.ARTICLE,
                                "Relatório": ContentType.REPORT,
                                "Pesquisa": ContentType.RESEARCH,
                                "Manual": ContentType.MANUAL,
                                "Política": ContentType.POLICY,
                                "Outro": ContentType.OTHER
                            }
                            
                            content_type_enum = ct_map.get(ctype, ContentType.OTHER)
                            
                            # Processa tags
                            tags_list = [t.strip() for t in tag_list.split(",") if t.strip()] if tag_list else []
                            
                            # Ingere documento
                            success, message, result = self.injestion_pipeline.ingest_document(
                                file_path=file.name,
                                content_type=content_type_enum,
                                custom_tags=tags_list,
                                author=author_name.strip() if author_name else None,
                                description=desc.strip() if desc else None,
                                source_url=url.strip() if url else None
                            )
                            
                            if success:
                                status_html = f"""
                                <div style='
                                    background: linear-gradient(135deg, #4caf50 0%, #45a049 100%);
                                    color: white;
                                    padding: 1.5rem;
                                    border-radius: 8px;
                                    margin: 1rem 0;
                                '>
                                    <h4 style='margin: 0 0 0.5rem 0;'>✅ {message}</h4>
                                    <p style='margin: 0.5rem 0; font-size: 0.9rem;'>
                                        📚 <strong>{result['filename']}</strong><br>
                                        📄 {result['pages']} página(s) • 🔗 {result['chunks_created']} chunks
                                    </p>
                                </div>
                                """
                            else:
                                status_html = f"""
                                <div style='
                                    background: linear-gradient(135deg, #f44336 0%, #e53935 100%);
                                    color: white;
                                    padding: 1.5rem;
                                    border-radius: 8px;
                                    margin: 1rem 0;
                                '>
                                    <h4 style='margin: 0 0 0.5rem 0;'>❌ Erro na Ingestão</h4>
                                    <p style='margin: 0; font-size: 0.9rem;'>{message}</p>
                                </div>
                                """
                            
                            # Atualiza lista de documentos
                            updated_docs_html = self.get_injected_documents_html()
                            
                            return status_html, updated_docs_html
                        
                        except Exception as e:
                            error_html = f"""
                            <div style='
                                background: linear-gradient(135deg, #f44336 0%, #e53935 100%);
                                color: white;
                                padding: 1.5rem;
                                border-radius: 8px;
                                margin: 1rem 0;
                            '>
                                <h4 style='margin: 0 0 0.5rem 0;'>❌ Erro ao Processar</h4>
                                <p style='margin: 0; font-size: 0.9rem;'>{str(e)}</p>
                            </div>
                            """
                            return error_html, self.get_injected_documents_html()
                    
                    def handle_text_injection(text, source_name, text_ctype):
                        """Processa ingestão de texto."""
                        if not text.strip():
                            return "<p style='color: red;'>❌ Texto vazio</p>", self.get_injected_documents_html()
                        
                        if not source_name.strip():
                            return "<p style='color: red;'>❌ Nome da fonte obrigatório</p>", self.get_injected_documents_html()
                        
                        try:
                            ct_map = {
                                "Artigo": ContentType.ARTICLE,
                                "Notícia": ContentType.ARTICLE,
                                "Conteúdo": ContentType.DOCUMENT,
                                "Outro": ContentType.OTHER
                            }
                            
                            content_type_enum = ct_map.get(text_ctype, ContentType.OTHER)
                            
                            success, message, result = self.injestion_pipeline.ingest_raw_text(
                                text=text,
                                source_name=source_name.strip(),
                                content_type=content_type_enum
                            )
                            
                            if success:
                                status_html = f"""
                                <div style='
                                    background: linear-gradient(135deg, #4caf50 0%, #45a049 100%);
                                    color: white;
                                    padding: 1.5rem;
                                    border-radius: 8px;
                                    margin: 1rem 0;
                                '>
                                    <h4 style='margin: 0 0 0.5rem 0;'>✅ {message}</h4>
                                    <p style='margin: 0.5rem 0; font-size: 0.9rem;'>
                                        📝 <strong>{result['filename']}</strong><br>
                                        🔗 {result['chunks_created']} chunk criado
                                    </p>
                                </div>
                                """
                            else:
                                status_html = f"""
                                <div style='
                                    background: linear-gradient(135deg, #f44336 0%, #e53935 100%);
                                    color: white;
                                    padding: 1.5rem;
                                    border-radius: 8px;
                                    margin: 1rem 0;
                                '>
                                    <h4 style='margin: 0 0 0.5rem 0;'>❌ Erro</h4>
                                    <p style='margin: 0; font-size: 0.9rem;'>{message}</p>
                                </div>
                                """
                            
                            updated_docs_html = self.get_injected_documents_html()
                            return status_html, updated_docs_html
                        
                        except Exception as e:
                            error_html = f"""
                            <div style='
                                background: linear-gradient(135deg, #f44336 0%, #e53935 100%);
                                color: white;
                                padding: 1.5rem;
                                border-radius: 8px;
                                margin: 1rem 0;
                            '>
                                <h4 style='margin: 0 0 0.5rem 0;'>❌ Erro ao Processar</h4>
                                <p style='margin: 0; font-size: 0.9rem;'>{str(e)}</p>
                            </div>
                            """
                            return error_html, self.get_injected_documents_html()
                    
                    # Event handlers
                    inject_btn.click(
                        handle_file_injection,
                        inputs=[upload_file, content_type, author, description, tags, source_url],
                        outputs=[injection_status, injected_docs_html]
                    )
                    
                    inject_text_btn.click(
                        handle_text_injection,
                        inputs=[raw_text, text_source_name, text_content_type],
                        outputs=[injection_status, injected_docs_html]
                    )
                
                # ===== ABA 5: DOCUMENTAÇÃO =====
                with gr.TabItem("📖 Documentação"):
                    gr.HTML(f"""
                    <div style='padding: 2rem;'>
                        <h2 style='color: var(--text-primary);'>📖 Como Usar o Sistema</h2>
                        
                        <div style='background: var(--bg-secondary); border-left: 4px solid #667eea; padding: 1rem; border-radius: 8px; margin: 1rem 0;'>
                            <h3 style='margin-top: 0; color: #667eea;'>✨ Perguntas Suportadas</h3>
                            <ul style='color: var(--text-primary);'>
                                <li><strong>Estatísticas:</strong> "Qual é o post mais curtido?" "Quantos posts tem?"</li>
                                <li><strong>Busca:</strong> "Posts sobre HUAP" "Mencione iniciativas ambientais"</li>
                                <li><strong>Comparações:</strong> "Compare @reitor e @dceuff" "Qual perfil tem mais engajamento?"</li>
                                <li><strong>Análise:</strong> "Qual é o sentimento geral?" "Que tópicos mais aparecem?"</li>
                                <li><strong>Tendências:</strong> "Posts mais comentados" "Conteúdo de 2024"</li>
                            </ul>
                        </div>
                        
                        <div style='background: var(--bg-secondary); border-left: 4px solid #4caf50; padding: 1rem; border-radius: 8px; margin: 1rem 0;'>
                            <h3 style='margin-top: 0; color: #4caf50;'>💚 Dicas</h3>
                            <ul style='color: var(--text-primary);'>
                                <li>Use linguagem natural - não precisa ser exato</li>
                                <li>Combine filtros de perfil com perguntas para resultados mais específicos</li>
                                <li>Verifique o histórico para rever respostas anteriores</li>
                                <li>O sistema entende perguntas em português natural</li>
                            </ul>
                        </div>
                        
                        <div style='background: var(--bg-secondary); border-left: 4px solid #ff9800; padding: 1rem; border-radius: 8px; margin: 1rem 0;'>
                            <h3 style='margin-top: 0; color: #ff9800;'>🔧 Configurações e Ingestão</h3>
                            <p style='color: var(--text-primary);'>
                                <strong>Filtro de Perfis:</strong> Selecione um ou mais perfis clicando nos botões. Todos os selecionados serão incluídos na busca<br>
                                <strong>Nº Posts:</strong> Ajuste quantos posts recuperar (se em modo clássico)<br>
                                <strong>Aba Ingestão:</strong> Upload de documentos com conversão automática via Docling e vetorização<br>
                                <strong>Abas:</strong> Navigate entre Chat, Estatísticas, Histórico, Ingestão e esta Documentação
                            </p>
                        </div>
                        
                        <div style='background: var(--bg-secondary); border-left: 4px solid #2196f3; padding: 1rem; border-radius: 8px; margin: 1rem 0;'>
                            <h3 style='margin-top: 0; color: #2196f3;'>📥 Pipeline de Ingestão</h3>
                            <ul style='color: var(--text-primary);'>
                                <li><strong>Formatos Suportados:</strong> PDF, DOCX, PPTX, TXT, MD, HTML</li>
                                <li><strong>Conversão:</strong> Docling extrai texto, tabelas e figuras estruturando tudo em JSON</li>
                                <li><strong>Chunks Automáticos:</strong> Documentos grandes são divididos por página</li>
                                <li><strong>Vetorização:</strong> Cada chunk é vetorizado e indexado no ChromaDB</li>
                                <li><strong>Busca Semântica:</strong> Documentos injetados participam das buscas normais do chat</li>
                                <li><strong>Metadados:</strong> Tags, autor e descrição para melhor organização</li>
                            </ul>
                        </div>
                        
                        <div style='background: var(--bg-secondary); border-radius: 8px; padding: 1.5rem; margin-top: 2rem;'>
                            <h3 style='margin-top: 0; color: var(--text-primary);'>ℹ️ Sobre o Sistema</h3>
                            <ul style='color: var(--text-secondary); font-size: 0.9rem;'>
                                <li><strong>Posts Indexados:</strong> {self.stats['indexed_posts']:,}</li>
                                <li><strong>Perfis Monitorados:</strong> {', '.join(['@' + p for p in self.stats['profiles']])}</li>
                                <li><strong>Modelo de Embedding:</strong> {self.stats['embedding_model']}</li>
                                <li><strong>Modelo de Geração:</strong> Local via Ollama</li>
                                <li><strong>Banco de Dados:</strong> ChromaDB (Vetorial)</li>
                                <li><strong>Ingestão:</strong> Docling (conversão de documentos)</li>
                                <li><strong>Interface:</strong> Gradio 4.x</li>
                                <li><strong>Fontes Suportadas:</strong> Instagram, Notícias, Web Search, Documentos Injetados</li>
                            </ul>
                        </div>
                    </div>
                    """)
            
            # Lógica de chat
            def respond(message, chat_history, n_res, profile_filt):
                if not message.strip():
                    return message, chat_history, ""
                
                # Processa filtro de múltiplos perfis
                if isinstance(profile_filt, list):
                    if len(profile_filt) > 0:
                        # Se múltiplos perfis selecionados
                        profiles = [p.replace("@", "") for p in profile_filt]
                        profile = ", ".join(profiles)  # "dceuff, reitor"
                    else:
                        # Se nenhum selecionado, usa todos como fallback
                        profile = "Todos"
                elif isinstance(profile_filt, str):
                    # Compatibilidade com formato antigo (dropdown)
                    if profile_filt.startswith("🌐"):
                        profile = "Todos"
                    else:
                        profile = profile_filt.replace("@", "")
                else:
                    # Nenhum perfil selecionado
                    profile = "Todos"
                
                # Gera resposta
                response, sources_html = self.chat_response(
                    message, 
                    chat_history, 
                    n_res, 
                    profile
                )
                
                # Atualiza histórico
                chat_history.append((message, response))
                
                return "", chat_history, sources_html
            
            # Eventos do chat
            msg.submit(
                respond,
                inputs=[msg, chatbot, n_results, profile_filter],
                outputs=[msg, chatbot, sources]
            )
            
            send_btn.click(
                respond,
                inputs=[msg, chatbot, n_results, profile_filter],
                outputs=[msg, chatbot, sources]
            )
            
            clear_btn.click(
                lambda: ([], ""),
                outputs=[chatbot, sources]
            )
            
            # Rodapé
            gr.HTML(f"""
            <div class="footer-custom">
                <p style="margin: 0; font-weight: 500;">
                    🎓 Universidade Federal Fluminense • 
                    {self.stats['indexed_posts']:,} documentos • 
                    {len(self.stats.get('profiles', []))} perfis • 
                    {len(self.stats.get('content_types', []))} tipos de conteúdo
                </p>
                <p style="margin: 0.5rem 0 0 0; font-size: 0.75rem;">
                    ⚡ Powered by Ollama • ChromaDB • Gradio
                </p>
            </div>
            """)
        
        return app
    
    def launch(self, **kwargs):
        """
        Inicia a aplicação.
        
        Args:
            **kwargs: Argumentos para gr.Blocks.launch()
        """
        app = self.create_interface()
        app.launch(**kwargs)


def main():
    """Função principal."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Instagram RAG Chat App")
    parser.add_argument(
        "--embedding-model",
        default="mxbai-embed-large",
        help="Modelo Ollama para embeddings"
    )
    parser.add_argument(
        "--generation-model",
        default="qwen3:30b",
        help="Modelo Ollama para geração de respostas"
    )
    parser.add_argument(
        "--share",
        action="store_true",
        help="Criar link público do Gradio"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=7860,
        help="Porta para a aplicação"
    )
    
    args = parser.parse_args()
    
    # Inicializa aplicação
    app = InstagramRAGApp(
        embedding_model=args.embedding_model,
        generation_model=args.generation_model
    )
    
    # Lança interface
    print(f"\n🌐 Iniciando interface web na porta {args.port}...")
    app.launch(
        server_name="0.0.0.0",
        server_port=args.port,
        share=args.share,
        inbrowser=True
    )


if __name__ == "__main__":
    main()
