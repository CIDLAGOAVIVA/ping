"""
Aplicação Gradio para Chat RAG de Posts do Instagram.
Agora usando sistema de agente inteligente com interface profissional!
"""

import gradio as gr
from datetime import datetime, timedelta
from typing import List, Tuple, Dict, Optional, Any
import json
import os
from pathlib import Path
import tempfile
from data_ingestion import DataIngestion

# 🔧 Configurar diretório temporário do Gradio para evitar problemas de permissão
custom_temp_dir = Path.home() / ".cache" / "gradio"
custom_temp_dir.mkdir(parents=True, exist_ok=True)
os.environ["GRADIO_TEMP_DIR"] = str(custom_temp_dir)

# 🔧 IMPORTS CORRIGIDOS - usar agent_system e rag_system
from agent_system import RAGAgent
from rag_system import RAGSystem
from embedding_manager import EmbeddingManager
from analytics_dashboard import DashboardAnalytics
from dashboard_visualizer import DashboardVisualizer
from report_exporter import ReportExporter
from ping_theme import ping_theme


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
        Inicializa o sistema RAG.
        
        Args:
            embedding_model: Modelo de embeddings
            generation_model: Modelo de geração
            use_agent: Se True, usa sistema de agentes
        """
        # 🔧 Armazena modelos
        self.embedding_model = embedding_model
        self.generation_model = generation_model
        self.use_agent = use_agent
        
        # 🔧 Inicializa sistema apropriado (Agente ou RAG Clássico)
        if use_agent:
            # Modo Agente - passa os nomes dos modelos (não o EmbeddingManager)
            from agent_system import RAGAgent
            
            self.agent = RAGAgent(
                embedding_model=embedding_model,
                generation_model=generation_model,
                planning_model=generation_model  # Usa mesmo modelo para planejamento
            )
            
            # Pega referência ao embedding_manager do agente
            self.embedding_manager = self.agent.embedding_manager
            
            self.query_engine = self.agent  # Compatibilidade
            print("   ✅ RAGAgent inicializado")
        else:
            # Modo RAG Clássico
            from rag_system import RAGSystem
            from embedding_manager import EmbeddingManager
            
            # Cria embedding_manager primeiro
            self.embedding_manager = EmbeddingManager(embedding_model)
            
            try:
                self.rag = RAGSystem(
                    embedding_manager=self.embedding_manager,
                    generation_model=generation_model
                )
            except TypeError:
                # Fallback: cria stub simples
                class SimpleRAGSystem:
                    def __init__(self, embedding_manager, generation_model):
                        self.embedding_manager = embedding_manager
                        self.generation_model = generation_model
                        self.collection = embedding_manager.collection
                    
                    def query(self, question, n_results=5, profile_filter=None):
                        import llm_chat
                        results = self.embedding_manager.search(
                            query=question,
                            n_results=n_results,
                            profile_filter=profile_filter
                        )
                        context = "\n\n".join([
                            f"@{d['metadata']['profile']}: {d['document'][:300]}"
                            for d in results['documents']
                        ])
                        prompt = f"Pergunta: {question}\n\nContexto:\n{context}\n\nResposta:"
                        response = llm_chat.chat(
                            model=self.generation_model,
                            messages=[{'role': 'user', 'content': prompt}]
                        )
                        return response['message']['content'], results['documents']
                
                self.rag = SimpleRAGSystem(
                    self.embedding_manager,
                    generation_model
                )
            
            self.query_engine = self.rag  # Compatibilidade
            print("   ✅ RAGSystem inicializado")
        
        # Histórico
        self.history_manager = HistoryManager()
        
        # 🆕 Analytics (usa o embedding_manager já criado)
        from analytics_dashboard import DashboardAnalytics
        from dashboard_visualizer import DashboardVisualizer
        
        self.analytics = DashboardAnalytics(self.embedding_manager)
        self.dashboard_visualizer = DashboardVisualizer()
        
        # Adiciona referência ao analytics no app para dashboard
        self.dashboard_analytics = self.analytics
        
        # 🔧 Stats - agora com fallback para estrutura correta
        raw_stats = self.embedding_manager.get_stats()
        
        # Normaliza estrutura de stats (compatibilidade)
        self.stats = {
            'total': raw_stats.get('total', raw_stats.get('indexed_posts', 0)),
            'indexed_posts': raw_stats.get('indexed_posts', raw_stats.get('total', 0)),
            'profiles': raw_stats.get('profiles', []),
            'embedding_model': raw_stats.get('embedding_model', embedding_model)
        }
        
        print(f"✅ Sistema inicializado")
        print(f"   📊 Registros indexados: {self.stats['total']}")
        print(f"   🤖 Modelo: {generation_model}")
        print(f"   🎯 Modo: {'Agente' if use_agent else 'RAG Simples'}")
        
        # Inicializa gerenciador de ingestão
        self.data_ingestion = DataIngestion()
    
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
                                '>@{metadata['profile']}</span>
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
            
            # ⭐ NOVA SEÇÃO: Análise de Hashtags
            if data.get('hashtag_analysis') and data['hashtag_analysis'].get('total_unique', 0) > 0:
                hashtag_data = data['hashtag_analysis']
                html += f"""
                <div style='border: 1px solid #4CAF50; border-radius: 8px; padding: 15px; margin: 10px 0; background-color: #f1f8f4;'>
                    <h4 style='margin-top: 0; color: #4CAF50;'>🏷️ Análise de Hashtags</h4>
                    <ul style='list-style-type: none; padding: 0;'>
                        <li><strong>Total de hashtags únicas:</strong> {hashtag_data['total_unique']}</li>
                        <li><strong>Total de ocorrências:</strong> {hashtag_data['total_occurrences']}</li>
                        <li><strong>Média por post:</strong> {hashtag_data['avg_per_post']}</li>
                    </ul>
                    <h5>Top Hashtags:</h5>
                    <div style='display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px;'>
                """
                
                for tag_data in hashtag_data['top_hashtags'][:5]:
                    html += f"""
                        <span style='
                            background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
                            color: white;
                            padding: 6px 12px;
                            border-radius: 20px;
                            font-size: 0.9rem;
                            font-weight: 600;
                        '>
                            #{tag_data['tag']} ({tag_data['count']} • {tag_data['percentage']}%)
                        </span>
                    """
                
                html += """
                    </div>
                </div>
                """
            
            # ⭐ NOVA SEÇÃO: Análise de Menções
            if data.get('mention_analysis') and data['mention_analysis'].get('total_unique', 0) > 0:
                mention_data = data['mention_analysis']
                html += f"""
                <div style='border: 1px solid #2196F3; border-radius: 8px; padding: 15px; margin: 10px 0; background-color: #e3f2fd;'>
                    <h4 style='margin-top: 0; color: #2196F3;'>👥 Análise de Menções</h4>
                    <ul style='list-style-type: none; padding: 0;'>
                        <li><strong>Total de menções únicas:</strong> {mention_data['total_unique']}</li>
                        <li><strong>Total de ocorrências:</strong> {mention_data['total_occurrences']}</li>
                        <li><strong>Média por post:</strong> {mention_data['avg_per_post']}</li>
                    </ul>
                    <h5>Top Menções:</h5>
                    <div style='display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px;'>
                """
                
                for mention_data_item in mention_data['top_mentions'][:5]:
                    html += f"""
                        <span style='
                            background: linear-gradient(135deg, #2196F3 0%, #1976D2 100%);
                            color: white;
                            padding: 6px 12px;
                            border-radius: 20px;
                            font-size: 0.9rem;
                            font-weight: 600;
                        '>
                            {mention_data_item['username']} ({mention_data_item['count']} • {mention_data_item['percentage']}%)
                        </span>
                    """
                
                html += """
                    </div>
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
                        <div style='flex: 1; background: #e0e0e0; border-radius: 4px; height: 24px; overflow: hidden;'>
                            <div style='background: linear-gradient(to right, #4caf50, #45a049); width: {pos_pct}%; height: 100%; display: flex; align-items: center; justify-content: flex-end; padding-right: 8px;'>
                                <span style='color: white; font-weight: bold; font-size: 0.85rem;'>{data['positive_count']} ({pos_pct:.1f}%)</span>
                            </div>
                        </div>
                    </div>
                    <div style='display: flex; align-items: center; margin: 5px 0;'>
                        <span style='width: 100px;'>❌ Negativo:</span>
                        <div style='flex: 1; background: #e0e0e0; border-radius: 4px; height: 24px; overflow: hidden;'>
                            <div style='background: linear-gradient(to right, #f44336, #d32f2f); width: {neg_pct}%; height: 100%; display: flex; align-items: center; justify-content: flex-end; padding-right: 8px;'>
                                <span style='color: white; font-weight: bold; font-size: 0.85rem;'>{data['negative_count']} ({neg_pct:.1f}%)</span>
                            </div>
                        </div>
                    </div>
                    <div style='display: flex; align-items: center; margin: 5px 0;'>
                        <span style='width: 100px;'>⚪ Neutro:</span>
                        <div style='flex: 1; background: #e0e0e0; border-radius: 4px; height: 24px; overflow: hidden;'>
                            <div style='background: linear-gradient(to right, #9e9e9e, #757575); width: {neu_pct}%; height: 100%; display: flex; align-items: center; justify-content: flex-end; padding-right: 8px;'>
                                <span style='color: white; font-weight: bold; font-size: 0.85rem;'>{data['neutral_count']} ({neu_pct:.1f}%)</span>
                            </div>
                        </div>
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
            
            if content_type == 'news':
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
                            '>@{metadata['profile']}</span>
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
        profile_filter: str
    ) -> Tuple[str, str]:
        """
        Processa mensagem do chat e retorna resposta.
        
        Args:
            message: Mensagem do usuário
            history: Histórico do chat
            n_results: Número de posts a recuperar (ignorado no modo agente)
            profile_filter: Filtro de perfil (string com um ou múltiplos perfis separados por vírgula)
            
        Returns:
            Tupla (resposta, fontes_html)
        """
        if not message.strip():
            return "Por favor, faça uma pergunta.", ""
        
        # Processa filtro de perfil
        # Se múltiplos perfis selecionados (ex: "dceuff, reitor"), 
        # não filtra por perfil (busca em todos)
        # Se um único perfil, passa para filtro
        profile = None
        if profile_filter and profile_filter != "Todos":
            if "," in profile_filter:
                # Múltiplos perfis: não filtra (busca em todos os selecionados)
                profile = None
            else:
                # Um único perfil: filtra
                profile = profile_filter.strip()
        
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
        self.history_manager.add(
            question=message,
            response=response,
            profile_filter=profile_filter,
            posts_count=posts_count
        )
        
        # Formata fontes
        sources_html = self.format_sources(posts)
        
        return response, sources_html
    
    def get_analytics_dashboard_html(
        self,
        start_date: str = None,
        end_date: str = None,
        profile_filter: list = None,
        content_filter: str = "both"  # 🆕 Parâmetro de filtro de conteúdo
    ) -> str:
        """
        Retorna HTML do dashboard de análise com filtros aplicados.
        
        Args:
            start_date: Data inicial (YYYY-MM-DD)
            end_date: Data final (YYYY-MM-DD)
            profile_filter: Lista de perfis selecionados
            content_filter: Tipo de conteúdo ("both", "caption", "comments")
        
        Returns:
            HTML formatado
        """
        try:
            # Converte perfis (remove @ se necessário)
            if profile_filter:
                profile_filter = [p.replace('@', '') for p in profile_filter]
            
            # Busca métricas (🆕 passa content_filter)
            metrics = self.dashboard_analytics.get_date_range_data(
                start_date=start_date,
                end_date=end_date,
                profile_filter=profile_filter,
                content_filter=content_filter  # 🆕
            )
            
            # Gera HTML
            return self.dashboard_visualizer.generate_dashboard_html(metrics)
        
        except Exception as e:
            return f"""
            <div style='padding: 2rem; text-align: center; color: var(--text-secondary);'>
                <h3>❌ Erro ao carregar dashboard</h3>
                <p>{str(e)}</p>
            </div>
            """
    
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
    
    def get_sentiment_card_html(
        self,
        profile_filter: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        use_cache: bool = True,
        content_filter: str = "both"  # 🆕 Filtro de conteúdo
    ) -> str:
        """
        Retorna HTML do card de análise de sentimento.
        
        Args:
            profile_filter: Perfil específico para analisar (ex: "dceuff")
            start_date: Data inicial
            end_date: Data final
            use_cache: Se True, usa cache (padrão: True)
            content_filter: Tipo de conteúdo ("both", "caption", "comments")
        
        Returns:
            HTML formatado com análise de sentimento
        """
        from analytics_dashboard import DashboardAnalytics
        
        analytics = DashboardAnalytics(
            self.agent.embedding_manager if self.use_agent else self.rag.embedding_manager
        )
        
        # Se tem filtro de perfil, usa método específico
        if profile_filter and profile_filter != "Todos":
            sentiment = analytics.get_sentiment_by_profile(
                profile=profile_filter,
                start_date=start_date,
                end_date=end_date,
                use_cache=use_cache,
                content_filter=content_filter  # 🆕 Passa filtro
            )
        else:
            # Análise geral
            metrics = analytics.get_date_range_data(
                start_date=start_date,
                end_date=end_date,
                use_cache=use_cache,
                content_filter=content_filter  # 🆕 Passa filtro
            )
            sentiment = metrics.get('sentiment', {})
        
        # Dados do sentimento
        total = sentiment.get('total_analyzed', 0)
        positive = sentiment.get('positive', 0)
        negative = sentiment.get('negative', 0)
        neutral = sentiment.get('neutral', 0)
        
        pos_pct = sentiment.get('positive_pct', 0)
        neg_pct = sentiment.get('negative_pct', 0)
        neu_pct = sentiment.get('neutral_pct', 0)
        
        trend = sentiment.get('trend', 'neutral')
        profile_name = sentiment.get('display_name', 'Todos os perfis')
        
        # 🆕 Status do cache
        cached = sentiment.get('cached', False)
        cache_icon = "💾" if cached else "🆕"
        cache_text = "Dados do cache" if cached else "Análise nova"
        
        # 🆕 Tipo de conteúdo analisado
        content_type_label = {
            "both": "Legendas + Comentários",
            "caption": "Apenas Legendas",
            "comments": "Apenas Comentários"
        }.get(content_filter, "Legendas + Comentários")
        
        # Emoji da tendência
        trend_emoji = {
            'positive': '😊',
            'negative': '😟',
            'neutral': '😐'
        }.get(trend, '😐')
        
        # Cor da tendência
        trend_color = {
            'positive': '#4caf50',
            'negative': '#f44336',
            'neutral': '#9e9e9e'
        }.get(trend, '#9e9e9e')
        
        html = f"""
        <div style='
            background: var(--bg-secondary);
            border-radius: 12px;
            padding: 1.5rem;
            border: 1px solid var(--border-primary);
            margin-bottom: 1.5rem;
        '>
            <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;'>
                <h3 style='margin: 0; color: var(--text-primary);'>🎭 Análise de Sentimento</h3>
                <span style='
                    font-size: 2rem;
                    background: {trend_color};
                    width: 50px;
                    height: 50px;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                '>{trend_emoji}</span>
            </div>
            
            <p style='color: var(--text-secondary); margin: 0.5rem 0 0.5rem 0;'>
                <strong>{profile_name}</strong> • {total} registros analisados
            </p>
            
            <!-- 🆕 Tipo de conteúdo -->
            <p style='color: var(--text-secondary); margin: 0 0 1rem 0; font-size: 0.9rem;'>
                📝 <strong>Analisando:</strong> {content_type_label}
            </p>
            
            <!-- Status do cache -->
            <div style='
                background: {'#e8f5e9' if cached else '#fff3e0'};
                border-left: 4px solid {'#4caf50' if cached else '#ff9800'};
                padding: 0.5rem 1rem;
                margin: 0.5rem 0 1rem 0;
                border-radius: 4px;
            '>
                <span style='color: var(--text-secondary); font-size: 0.9rem;'>
                    {cache_icon} <strong>{cache_text}</strong>
                </span>
            </div>
            
            <!-- Barras de progresso -->
            <div style='margin: 1rem 0;'>
                <div style='display: flex; align-items: center; margin: 0.8rem 0;'>
                    <span style='width: 100px; color: var(--text-primary);'>✅ Positivo:</span>
                    <div style='flex: 1; background: #e0e0e0; border-radius: 4px; height: 24px; margin: 0 10px; overflow: hidden;'>
                        <div style='background: #4caf50; height: 100%; width: {pos_pct}%; transition: width 0.3s ease;'></div>
                    </div>
                    <span style='width: 100px; text-align: right; color: var(--text-primary);'>{positive} ({pos_pct}%)</span>
                </div>
                
                <div style='display: flex; align-items: center; margin: 0.8rem 0;'>
                    <span style='width: 100px; color: var(--text-primary);'>❌ Negativo:</span>
                    <div style='flex: 1; background: #e0e0e0; border-radius: 4px; height: 24px; margin: 0 10px; overflow: hidden;'>
                        <div style='background: #f44336; height: 100%; width: {neg_pct}%; transition: width 0.3s ease;'></div>
                    </div>
                    <span style='width: 100px; text-align: right; color: var(--text-primary);'>{negative} ({neg_pct}%)</span>
                </div>
                
                <div style='display: flex; align-items: center; margin: 0.8rem 0;'>
                    <span style='width: 100px; color: var(--text-primary);'>⚪ Neutro:</span>
                    <div style='flex: 1; background: #e0e0e0; border-radius: 4px; height: 24px; margin: 0 10px; overflow: hidden;'>
                        <div style='background: #9e9e9e; height: 100%; width: {neu_pct}%; transition: width 0.3s ease;'></div>
                    </div>
                    <span style='width: 100px; text-align: right; color: var(--text-primary);'>{neutral} ({neu_pct}%)</span>
                </div>
            </div>
            
            <p style='
                margin: 1rem 0 0 0;
                padding: 0.8rem;
                background: var(--bg-terciary);
                border-radius: 8px;
                color: var(--text-secondary);
                font-size: 0.85rem;
            '>
                💡 {sentiment.get('note', 'Análise baseada em palavras-chave')}
            </p>
        </div>
        """
        
        return html

    def export_dashboard_report(
        self,
        format: str,
        start_date: str = None,
        end_date: str = None,
        profile_filter: list = None,
        content_filter: str = "both"
    ) -> Tuple[str, Any]:
        """
        🆕 Exporta relatório do dashboard.
        
        Args:
            format: Formato ('csv' ou 'pdf')
            start_date: Data inicial
            end_date: Data final
            profile_filter: Lista de perfis
            content_filter: Tipo de conteúdo
        
        Returns:
            Tuple (filepath, content)
        """
        try:
            # Limpa perfis
            if profile_filter:
                profile_filter = [p.replace('@', '') for p in profile_filter]
            
            # Busca métricas
            metrics = self.dashboard_analytics.get_date_range_data(
                start_date=start_date,
                end_date=end_date,
                profile_filter=profile_filter,
                use_llm_sentiment=False,  # Usa cache
                use_cache=True,
                content_filter=content_filter
            )
            
            # 🆕 ADICIONA RECOMENDAÇÕES DE POLÍTICA ao relatório
            try:
                print("\n🔮 Gerando recomendações de políticas para o relatório...")
                profile = profile_filter[0] if profile_filter and len(profile_filter) == 1 else None
                
                recommendations = self.dashboard_analytics.generate_policy_recommendations(
                    profile_filter=profile,
                    min_engagement=100,
                    top_n=5
                )
                
                # 🔧 TRANSFORMA formato LLM para formato do exportador
                if recommendations and recommendations.get('recommendations'):
                    from datetime import datetime
                    
                    # Extrai dados de sentimento
                    sentiment_data = recommendations.get('sentiment_analysis', {})
                    
                    # Monta formato esperado pelo exportador
                    export_format = {
                        'has_recommendations': True,
                        'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'profile': f"@{profile}" if profile else "Todos os perfis",
                        'content_filter': content_filter,
                        'sentiment_data': sentiment_data,
                        'summary': f"Análise baseada em {len(recommendations.get('recommendations', []))} recomendações geradas automaticamente.",
                        'critical_areas': recommendations.get('critical_areas', []),
                        'recommendations': recommendations.get('recommendations', []),
                        'positive_aspects': recommendations.get('positive_aspects', []),
                        'general_observations': f"Sentimento: {sentiment_data.get('positive_pct', 0):.1f}% positivo, {sentiment_data.get('negative_pct', 0):.1f}% negativo"
                    }
                    
                    metrics['policy_recommendations'] = export_format
                    print(f"✅ {len(recommendations['recommendations'])} recomendações incluídas no relatório")
                else:
                    print("⚠️ Nenhuma recomendação gerada (dados insuficientes)")
            except Exception as e:
                print(f"⚠️ Erro ao gerar recomendações: {e}")
                import traceback
                traceback.print_exc()
            
            # 🔧 CORRIGIDO: Usa diretório local em vez de /tmp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"relatorio_uff_{timestamp}.{format}"
            
            content = self.dashboard_analytics.export_report(metrics, format, filename)
            
            # Cria diretório de exports se não existir
            exports_dir = Path('./exports')
            exports_dir.mkdir(exist_ok=True)
            
            # Salva arquivo local
            filepath = exports_dir / filename
            if format == 'csv':
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
            else:  # PDF
                with open(filepath, 'wb') as f:
                    f.write(content)
            
            print(f"✅ Relatório salvo: {filepath}")
            return str(filepath), content
        
        except Exception as e:
            print(f"❌ Erro ao exportar relatório: {e}")
            import traceback
            traceback.print_exc()
            return None, None
    
    def process_upload(
        self,
        file,
        profile_name: str,
        text_column: str = "text",
        auto_index: bool = True
    ) -> tuple[str, str]:
        """
        Processa arquivo enviado pelo usuário.
        
        Returns:
            (status_html, preview_html)
        """
        if file is None:
            return "⚠️ Nenhum arquivo selecionado", ""
        
        import shutil
        from pathlib import Path
        
        # Salva arquivo temporário
        temp_path = Path(self.data_ingestion.temp_dir) / Path(file.name).name
        shutil.copy(file.name, temp_path)
        
        # Processa arquivo
        documents, status = self.data_ingestion.process_file(
            temp_path,
            profile_name=profile_name,
            text_column=text_column
        )
        
        if not documents:
            return f"<div style='color: red;'>{status}</div>", ""
        
        # Preview dos primeiros documentos
        preview_html = self._generate_preview_html(documents[:5])
        
        # Se auto-index ativado, indexa no ChromaDB
        if auto_index and documents:
            try:
                if self.use_agent:
                    self.agent.embedding_manager.add_posts(documents)
                else:
                    self.embedding_manager.add_posts(documents)
                
                status += f"<br>✅ {len(documents)} documentos indexados no ChromaDB"
                
                # Atualiza stats
                self._refresh_stats()
            except Exception as e:
                status += f"<br>⚠️ Erro ao indexar: {e}"
        
        status_html = f"<div style='color: green; padding: 1rem; background: #f0f8ff; border-radius: 8px;'>{status}</div>"
        
        # DEPOIS (preserva o arquivo)
        final_path = self.data_ingestion.data_dir / f"{profile_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{temp_path.name}"
        shutil.move(temp_path, final_path)
        status += f"<br>💾 Arquivo salvo em: {final_path}"
        
        return status_html, preview_html

    def _generate_preview_html(self, documents: List[Dict]) -> str:
        """Gera HTML de preview dos documentos."""
        html = "<div style='padding: 1rem;'>"
        html += "<h3>📄 Preview dos Documentos</h3>"
        
        for i, doc in enumerate(documents, 1):
            html += f"""
            <div style='border: 1px solid #ddd; border-radius: 8px; padding: 1rem; margin: 0.5rem 0; background: #fafafa;'>
                <p><strong>Documento {i}</strong></p>
                <p style='color: #666; font-size: 0.85rem;'>
                    ID: {doc['id']}<br>
                    Perfil: {doc['profile']}<br>
                    Tipo: {doc['content_type']}
                </p>
                <p style='margin-top: 0.5rem;'>
                    <strong>Texto:</strong><br>
                    {doc['text'][:300]}{'...' if len(doc['text']) > 300 else ''}
                </p>
            </div>
            """
        
        if len(documents) > 5:
            html += f"<p style='color: #888;'>... e mais {len(documents) - 5} documentos</p>"
        
        html += "</div>"
        return html

    def _refresh_stats(self):
        """Atualiza estatísticas após ingestão."""
        if self.use_agent:
            em_stats = self.agent.embedding_manager.get_stats()
        else:
            em_stats = self.embedding_manager.get_stats()
        
        self.stats['indexed_posts'] = em_stats.get('total_documents', 0)
        self.stats['profiles'] = em_stats.get('profiles', [])

    def create_interface(self) -> gr.Blocks:
        """
        Cria interface Gradio profissional com abas navegáveis.
        Tema claro como padrão com suporte total a dark mode.
        
        Returns:
            Interface Gradio configurada
        """
        with gr.Blocks(
            title="PING - UFF ANALYTICS",
            theme=ping_theme
        ) as app:
            
            # Header principal
            gr.HTML(f"""
            <div class="header-container">
                <h1>🎓 PING - UFF ANALYTICS</h1>
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
                            
                            # Botões de perfil como checkboxes
                            profile_filter = gr.CheckboxGroup(
                                choices=["@" + p for p in self.stats['profiles']],
                                value=["@" + p for p in self.stats['profiles']],  # Todos selecionados por padrão
                                label="📊 Filtro de Perfis (selecione um ou mais)",
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
                with gr.TabItem("📊 Dashboard"):
                    with gr.Row():
                        with gr.Column(scale=9):
                            dashboard_display = gr.HTML(value=self.get_analytics_dashboard_html())
                        
                        with gr.Column(scale=3, elem_classes="sidebar-config"):
                            gr.Markdown("### 🎯 Filtros de Análise")
                            
                            # Filtro de período
                            gr.Markdown("**📅 Período**")
                            
                            from datetime import datetime, timedelta
                            today = datetime.now()
                            default_start = (today - timedelta(days=30)).strftime('%Y-%m-%d')
                            default_end = today.strftime('%Y-%m-%d')
                            
                            date_start = gr.Textbox(
                                label="Data Inicial (YYYY-MM-DD)",
                                value=default_start,
                                placeholder="2024-01-01"
                            )
                            
                            date_end = gr.Textbox(
                                label="Data Final (YYYY-MM-DD)",
                                value=default_end,
                                placeholder="2024-12-31"
                            )
                            
                            # Botões de período rápido
                            gr.Markdown("**⚡ Períodos Rápidos**")
                            
                            with gr.Row():
                                btn_7days = gr.Button("Últimos 7 dias", size="sm")
                                btn_30days = gr.Button("Últimos 30 dias", size="sm")
                            
                            with gr.Row():
                                btn_90days = gr.Button("Últimos 90 dias", size="sm")
                                btn_all = gr.Button("Tudo", size="sm")
                            
                            gr.Markdown("---")
                            
                            # Filtro de perfis
                            dashboard_profile_filter = gr.CheckboxGroup(
                                choices=["@" + p for p in self.stats['profiles']],
                                value=["@" + p for p in self.stats['profiles']],
                                label="📊 Fontes",
                                interactive=True
                            )
                            
                            gr.Markdown("---")
                            
                            # 🆕 FILTRO DE CONTEÚDO PARA SENTIMENTO
                            gr.Markdown("**🎭 Análise de Sentimento**")
                            
                            sentiment_content_filter = gr.Radio(
                                choices=[
                                    ("📝 Legendas + Comentários", "both"),
                                    ("🏷️ Apenas Legendas", "caption"),
                                    ("💬 Apenas Comentários", "comments")
                                ],
                                value="both",
                                label="Tipo de Conteúdo",
                                interactive=True,
                                info="Escolha qual conteúdo analisar"
                            )
                            
                            gr.Markdown("---")
                            
                            # Botão de atualizar
                            update_dashboard_btn = gr.Button(
                                "🔄 Atualizar Dashboard",
                                variant="primary",
                                size="lg"
                            )
                            
                            gr.Markdown("---")
                            
                            # 🆕 SEÇÃO DE EXPORTAÇÃO
                            gr.Markdown("### 📥 Exportar Relatório")
                            
                            export_format = gr.Radio(
                                choices=[
                                    ("📄 CSV (Excel)", "csv"),
                                    ("📕 PDF (Documento)", "pdf")
                                ],
                                value="csv",
                                label="Formato",
                                interactive=True
                            )
                            
                            export_btn = gr.Button(
                                "📥 Baixar Relatório",
                                variant="secondary",
                                size="lg"
                            )
                            
                            export_status = gr.Textbox(
                                label="Status",
                                interactive=False,
                                visible=False
                            )
                            
                            export_file = gr.File(
                                label="Arquivo Gerado",
                                visible=False
                            )
                            
                            gr.Markdown("---")
                            
                            gr.Markdown("""
                            ### 💡 Dica
                            
                            Selecione o período, fontes e tipo de conteúdo,
                            depois clique em **Atualizar Dashboard** 
                            para visualizar as métricas.
                            
                            **Tipos de Conteúdo:**
                            - **Legendas + Comentários**: Análise completa
                            - **Apenas Legendas**: Sentimento do autor
                            - **Apenas Comentários**: Sentimento da comunidade
                            
                            **Exportação:**
                            Escolha CSV ou PDF e clique em **Baixar Relatório**
                            para gerar um arquivo com todas as métricas.
                            """)
                    
                    # Funções de atualização do dashboard
                    def set_period(days: int):
                        """Define período rápido."""
                        end = datetime.now()
                        start = end - timedelta(days=days)
                        return start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d')
                    
                    def set_all_time():
                        """Define período total."""
                        return "2000-01-01", datetime.now().strftime('%Y-%m-%d')
                    
                    def update_dashboard(start: str, end: str, profiles: list, content_filter: str):
                        """Atualiza dashboard com filtros."""
                        return self.get_analytics_dashboard_html(
                            start_date=start if start else None,
                            end_date=end if end else None,
                            profile_filter=profiles if profiles else None,
                            content_filter=content_filter
                        )
                    
                    # 🆕 Função de exportação
                    def handle_export(fmt, start, end, profiles, content_filter):
                        """Processa exportação de relatório."""
                        filepath, content = self.export_dashboard_report(
                            format=fmt,
                            start_date=start,
                            end_date=end,
                            profile_filter=profiles,
                            content_filter=content_filter
                        )
                        
                        if filepath:
                            filename = filepath.split('/')[-1]
                            return (
                                gr.update(value=f"✅ Relatório gerado: {filename}", visible=True),
                                gr.update(value=filepath, visible=True)
                            )
                        else:
                            return (
                                gr.update(value="❌ Erro ao gerar relatório", visible=True),
                                gr.update(visible=False)
                            )
                    
                    # Conecta botões de período rápido
                    btn_7days.click(
                        lambda: set_period(7),
                        outputs=[date_start, date_end]
                    )
                    
                    btn_30days.click(
                        lambda: set_period(30),
                        outputs=[date_start, date_end]
                    )
                    
                    btn_90days.click(
                        lambda: set_period(90),
                        outputs=[date_start, date_end]
                    )
                    
                    btn_all.click(
                        set_all_time,
                        outputs=[date_start, date_end]
                    )
                    
                    # Conecta botão de atualizar
                    update_dashboard_btn.click(
                        update_dashboard,
                        inputs=[date_start, date_end, dashboard_profile_filter, sentiment_content_filter],
                        outputs=dashboard_display
                    )
                    
                    # 🆕 Conecta botão de exportação
                    export_btn.click(
                        fn=handle_export,
                        inputs=[
                            export_format,
                            date_start,
                            date_end,
                            dashboard_profile_filter,
                            sentiment_content_filter
                        ],
                        outputs=[export_status, export_file]
                    )

                    # 🆕 Botão de recomendações
                    gr.Markdown("---")
                    
                    generate_recommendations_btn = gr.Button(
                        "🔮 Gerar Recomendações de Políticas",
                        variant="secondary",
                        size="lg"
                    )
                    
                    gr.Markdown("""
                    **ℹ️ Sobre as recomendações:**
                    
                    A IA analisa críticas e comentários negativos para sugerir
                    ações concretas de melhoria. Usa a mesma análise de sentimento
                    já realizada.
                    """)
                    
                    # Adicionar callback do botão:

                    def generate_recommendations(
                        start, end, profiles, sent_filter
                    ):
                        """Gera recomendações baseadas em análise de sentimento."""
                        try:
                            print("\n🔮 Gerando recomendações de políticas...")
                            profile = profiles[0] if profiles and len(profiles) == 1 else None
                            
                            recommendations = self.analytics.generate_policy_recommendations(
                                profile_filter=profile,
                                min_engagement=100,
                                top_n=5
                            )
                            
                            # 🔍 DEBUG
                            print(f"🔍 DEBUG recommendations: {recommendations}")
                            print(f"   Tem 'recommendations' key? {('recommendations' in recommendations)}")
                            if 'recommendations' in recommendations:
                                print(f"   Quantidade: {len(recommendations['recommendations'])}")
                            
                            if not recommendations or not recommendations.get('recommendations') or len(recommendations.get('recommendations', [])) == 0:
                                return f"""
                                <div style='padding: 2rem; text-align: center;'>
                                    <h3>⚠️ Sem Recomendações</h3>
                                    <p>Dados insuficientes para gerar recomendações.</p>
                                </div>
                                """
                            
                            # Gera HTML das recomendações
                            from dashboard_visualizer import DashboardVisualizer
                            html = DashboardVisualizer._generate_policy_recommendations_card(recommendations)
                            
                            return html
                        
                        except Exception as e:
                            print(f"Erro ao gerar recomendações: {e}")
                            import traceback
                            traceback.print_exc()
                            return f"<div style='padding: 2rem; color: red;'>❌ Erro: {str(e)}</div>"
                    
                    # Conecta botão
                    generate_recommendations_btn.click(
                        fn=generate_recommendations,
                        inputs=[
                            date_start,
                            date_end,
                            dashboard_profile_filter,
                            sentiment_content_filter
                        ],
                        outputs=dashboard_display
                    )

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
                
                # ===== ABA 4: INGESTÃO DE DADOS (ATUALIZADA) =====
                with gr.TabItem("📥 Ingestão de Dados"):
                    gr.HTML("""
                    <div style='padding: 2rem;'>
                        <h2 style='color: #667eea;'>📥 Gerenciar Dados</h2>
                        <p style='color: #666; font-size: 0.95rem;'>
                            Adicione novos dados ou gerencie fontes existentes no banco vetorial.
                        </p>
                    </div>
                    """)
                    
                    with gr.Tabs():
                        # Sub-aba: Upload
                        with gr.TabItem("📤 Upload de Novos Dados"):
                            with gr.Row():
                                with gr.Column(scale=7):
                                    # Upload de arquivo
                                    file_upload = gr.File(
                                        label="📁 Selecione o Arquivo",
                                        file_types=['.json', '.csv', '.txt', '.pdf'],
                                        type="filepath"
                                    )
                                    
                                    # Configurações
                                    with gr.Row():
                                        profile_name_input = gr.Textbox(
                                            label="Nome da Fonte/Perfil",
                                            placeholder="Ex: pesquisa_alunos, relatorio_2024",
                                            value="custom_data"
                                        )
                                        text_column_input = gr.Textbox(
                                            label="Coluna de Texto (CSV)",
                                            placeholder="Nome da coluna com texto principal",
                                            value="text"
                                        )
                                    
                                    auto_index_checkbox = gr.Checkbox(
                                        label="✅ Indexar automaticamente no ChromaDB",
                                        value=True
                                    )
                                    
                                    process_btn = gr.Button(
                                        "🚀 Processar e Indexar",
                                        variant="primary",
                                        size="lg"
                                    )
                                    
                                    # Status
                                    status_output = gr.HTML()
                                    
                                    # Preview
                                    preview_output = gr.HTML()
                                
                                # Painel lateral com informações
                                with gr.Column(scale=3):
                                    gr.Markdown("### 📋 Formatos Suportados")
                                    gr.Markdown("""
                                    - **JSON**: Posts, documentos, arrays
                                    - **CSV**: Tabelas com dados estruturados
                                    - **TXT**: Texto simples (divide por parágrafos)
                                    - **PDF**: Extração de texto por página
                                    
                                    **Limite:** 50MB por arquivo
                                    """)
                                    
                                    gr.Markdown("### 💡 Dicas")
                                    gr.Markdown("""
                                    1. **JSON**: Pode ser lista ou objeto único
                                    2. **CSV**: Especifique a coluna com texto principal
                                    3. **TXT**: Será dividido por parágrafos vazios
                                    4. **PDF**: Cada página vira um documento
                                    
                                    Após indexar, os dados ficam disponíveis no chat!
                                    """)
                                    
                                    gr.Markdown("### ⚙️ Estrutura Esperada (JSON)")
                                    gr.Code(
                                        value='''[
  {
    "text": "Conteúdo...",
    "title": "Título",
    "date": "2025-01-01",
    "metadata": {...}
  }
]''',
                                        language="json"
                                    )
                            
                            # Eventos
                            process_btn.click(
                                self.process_upload,
                                inputs=[
                                    file_upload,
                                    profile_name_input,
                                    text_column_input,
                                    auto_index_checkbox
                                ],
                                outputs=[status_output, preview_output]
                            )
                        
                        # 🆕 Sub-aba: Fontes Existentes
                        with gr.TabItem("📚 Fontes Indexadas"):
                            with gr.Row():
                                with gr.Column(scale=8):
                                    sources_display = gr.HTML(value=self.generate_sources_html())
                                
                                with gr.Column(scale=2):
                                    gr.Markdown("### 🔧 Ações")
                                    
                                    refresh_sources_btn = gr.Button(
                                        "🔄 Atualizar",
                                        variant="secondary",
                                        size="lg"
                                    )
                                    
                                    gr.Markdown("---")
                                    gr.Markdown("### 🗑️ Remover Fonte")
                                    
                                    # Dropdown com fontes disponíveis
                                    def get_sources_list():
                                        data = self.get_chromadb_sources()
                                        if data['sources']:
                                            return ["Selecione..."] + list(data['sources'].keys())
                                        return ["Selecione..."]
                                    
                                    source_to_delete = gr.Dropdown(
                                        choices=get_sources_list(),
                                        value="Selecione...",
                                        label="Escolha a fonte",
                                        interactive=True
                                    )
                                    
                                    delete_btn = gr.Button(
                                        "🗑️ Remover Fonte",
                                        variant="stop",
                                        size="lg"
                                    )
                                    
                                    delete_status = gr.HTML()
                                    
                                    gr.Markdown("""
                                    ---
                                    **⚠️ Atenção:**
                                    
                                    Remover uma fonte é **irreversível**!
                                    Todos os documentos dessa fonte serão deletados do ChromaDB.
                                    """)
                            
                            # Eventos
                            refresh_sources_btn.click(
                                lambda: (
                                    self.generate_sources_html(),
                                    gr.update(choices=get_sources_list())
                                ),
                                outputs=[sources_display, source_to_delete]
                            )
                            
                            delete_btn.click(
                                self.delete_source,
                                inputs=[source_to_delete],
                                outputs=[delete_status, sources_display]
                            ).then(
                                lambda: (
                                    gr.update(choices=get_sources_list(), value="Selecione..."),
                                    ""
                                ),
                                outputs=[source_to_delete, delete_status]
                            )
                
                # ===== ABA 5: DOCUMENTAÇÃO =====
                with gr.TabItem("📖 Documentação"):
                    gr.HTML(f"""
                    <div style='padding: 2rem;'>
                        <h2 style='color: #333;'>📖 Como Usar o Sistema</h2>
                        
                        <div style='background: #f0f4ff; border-left: 4px solid #667eea; padding: 1rem; border-radius: 8px; margin: 1rem 0;'>
                            <h3 style='margin-top: 0; color: #667eea;'>✨ Perguntas Suportadas</h3>
                            <ul>
                                <li><strong>Estatísticas:</strong> "Qual é o post mais curtido?" "Quantos posts tem?"</li>
                                <li><strong>Busca:</strong> "Posts sobre HUAP" "Mencione iniciativas ambientais"</li>
                                <li><strong>Comparações:</strong> "Compare @reitor e @dceuff" "Qual perfil tem mais engajamento?"</li>
                                <li><strong>Análise:</strong> "Qual é o sentimento geral?" "Que tópicos mais aparecem?"</li>
                                <li><strong>Tendências:</strong> "Posts mais comentados" "Conteúdo de 2024"</li>
                            </ul>
                        </div>
                        
                        <div style='background: #f1f8f4; border-left: 4px solid #4caf50; padding: 1rem; border-radius: 8px; margin: 1rem 0;'>
                            <h3 style='margin-top: 0; color: #4caf50;'>💚 Dicas</h3>
                                                       <ul>
                                <li>Use linguagem natural - não precisa ser exato</li>
                                <li>Combine filtros de perfil com perguntas para resultados mais específicos</li>
                                <li>Verifique o histórico para rever respostas anteriores</li>
                                <li>O sistema entende perguntas em português natural</li>
                            </ul>
                        </div>
                        
                        <div style='background: #fff8f0; border-left: 4px solid #ff9800; padding: 1rem; border-radius: 8px; margin: 1rem 0;'>
                            <h3 style='margin-top: 0; color: #ff9800;'>🔧 Configurações</h3>
                            <p>
                                <strong>Filtro de Perfis:</strong> Selecione um ou mais perfis clicando nos botões. Todos os selecionados serão incluídos na busca<br>
                                <strong>Nº Posts:</strong> Ajuste quantos posts recuperar (se em modo clássico)<br>
                                <strong>Abas:</strong> Navigate entre Chat, Estatísticas, Histórico e esta Documentação
                            </p>
                        </div>
                        
                        <div style='background: #f0f0f0; border-radius: 8px; padding: 1.5rem; margin-top: 2rem;'>
                            <h3 style='margin-top: 0; color: #333;'>ℹ️ Sobre o Sistema</h3>
                            <ul style='color: #666; font-size: 0.9rem;'>
                                <li><strong>Posts Indexados:</strong> {self.stats['indexed_posts']:,}</li>
                                <li><strong>Perfis Monitorados:</strong> {', '.join(['@' + p for p in self.stats['profiles']])}</li>
                                <li><strong>Modelo de Embedding:</strong> {self.stats['embedding_model']}</li>
                                <li><strong>Modelo de Geração:</strong> Local via Ollama</li>
                                <li><strong>Banco de Dados:</strong> ChromaDB (Vetorial)</li>
                                <li><strong>Interface:</strong> Gradio 4.x</li>
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
                    {self.stats['indexed_posts']:,} posts • 
                    {len(self.stats['profiles'])} perfis
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

    def get_chromadb_sources(self) -> Dict[str, Any]:
        """
        Retorna informações sobre as fontes/arquivos no ChromaDB.
        
        Returns:
            Dict com estatísticas por fonte
        """
        try:
            # Busca todos os documentos
            if self.use_agent:
                collection = self.agent.embedding_manager.collection
            else:
                collection = self.embedding_manager.collection
            
            # Pega todos os documentos
            results = collection.get(
                limit=100000,
                include=['metadatas']
            )
            
            if not results['ids']:
                return {
                    'total': 0,
                    'sources': {},
                    'error': None
                }
            
            # Agrupa por fonte/perfil
            sources = {}
            for metadata in results['metadatas']:
                profile = metadata.get('profile', 'unknown')
                content_type = metadata.get('content_type', 'instagram_post')
                
                if profile not in sources:
                    sources[profile] = {
                        'name': profile,
                        'count': 0,
                        'types': {},
                        'oldest': None,
                        'newest': None
                    }
                
                sources[profile]['count'] += 1
                sources[profile]['types'][content_type] = sources[profile]['types'].get(content_type, 0) + 1
                
                # Atualiza datas
                timestamp = metadata.get('timestamp')
                if timestamp:
                    try:
                        from dateutil import parser as date_parser
                        dt = date_parser.parse(timestamp)
                        
                        if sources[profile]['oldest'] is None or dt < sources[profile]['oldest']:
                            sources[profile]['oldest'] = dt
                        
                        if sources[profile]['newest'] is None or dt > sources[profile]['newest']:
                            sources[profile]['newest'] = dt
                    except:
                        pass
            
            return {
                'total': len(results['ids']),
                'sources': sources,
                'error': None
            }
        
        except Exception as e:
            return {
                'total': 0,
                'sources': {},
                'error': str(e)
            }

    def generate_sources_html(self) -> str:
        """
        Gera HTML com lista de fontes/arquivos no ChromaDB.
        
        Returns:
            HTML formatado
        """
        data = self.get_chromadb_sources()
        
        if data['error']:
            return f"""
            <div style='padding: 2rem; text-align: center; color: red;'>
                <h3>❌ Erro ao carregar fontes</h3>
                <p>{data['error']}</p>
            </div>
            """
        
        if data['total'] == 0:
            return """
            <div style='padding: 2rem; text-align: center; color: var(--text-secondary);'>
                <h3>📭 Nenhum dado indexado</h3>
                <p>Faça upload de arquivos para começar!</p>
            </div>
            """
        
        html = f"""
        <div style='padding: 2rem; background: var(--bg-primary); color: var(--text-primary);'>
            <div style='margin-bottom: 2rem;'>
                <h2 style='margin: 0 0 0.5rem 0; color: var(--text-primary);'>📚 Fontes Indexadas</h2>
                <p style='margin: 0; color: var(--text-secondary);'>Total: <strong>{data['total']:,}</strong> documentos</p>
            </div>
            
            <div style='display: grid; gap: 1rem;'>
        """
        
        # Cards por fonte
        for source_name, source_data in sorted(data['sources'].items(), key=lambda x: x[1]['count'], reverse=True):
            # Formata datas
            oldest = source_data['oldest'].strftime('%d/%m/%Y') if source_data['oldest'] else "Desconhecida"
            newest = source_data['newest'].strftime('%d/%m/%Y') if source_data['newest'] else "Desconhecida"
            
            # Tipos de conteúdo
            types_html = ""
            for content_type, count in source_data['types'].items():
                icon = {
                    'instagram_post': '📷',
                    'news': '📰',
                    'custom': '📄'
                }.get(content_type, '📄')
                
                types_html += f"""
                <span style='
                    background: var(--bg-tertiary);
                    padding: 0.3rem 0.8rem;
                    border-radius: 20px;
                    font-size: 0.85rem;
                    margin-right: 0.5rem;
                    display: inline-block;
                '>
                    {icon} {content_type}: {count}
                </span>
                """
            
            html += f"""
            <div style='
                background: var(--bg-secondary);
                border: 1px solid var(--border-primary);
                border-radius: 12px;
                padding: 1.5rem;
                box-shadow: var(--shadow-sm);
                transition: all 0.3s ease;
            ' onmouseover="this.style.boxShadow='var(--shadow-md)'; this.style.transform='translateY(-2px)'" 
               onmouseout="this.style.boxShadow='var(--shadow-sm)'; this.style.transform='translateY(0)'">
                
                <div style='display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1rem;'>
                    <div>
                        <h3 style='margin: 0; color: var(--primary);'>@{source_name}</h3>
                        <p style='margin: 0.5rem 0 0 0; color: var(--text-secondary); font-size: 0.9rem;'>
                            📊 {source_data['count']:,} documentos
                        </p>
                    </div>
                    <span style='
                        background: linear-gradient(135deg, #667eea, #764ba2);
                        color: white;
                        padding: 0.5rem 1rem;
                        border-radius: 20px;
                        font-weight: 600;
                        font-size: 0.9rem;
                    '>
                        {((source_data['count'] / data['total']) * 100):.1f}%
                    </span>
                </div>
                
                <div style='margin: 1rem 0;'>
                    {types_html}
                </div>
                
                <div style='
                    display: flex;
                    gap: 2rem;
                    margin-top: 1rem;
                    padding-top: 1rem;
                    border-top: 1px solid var(--border-primary);
                    font-size: 0.85rem;
                    color: var(--text-secondary);
                '>
                    <div>
                        <strong>📅 Mais antigo:</strong> {oldest}
                    </div>
                    <div>
                        <strong>🆕 Mais recente:</strong> {newest}
                    </div>
                </div>
            </div>
            """
        
        html += """
            </div>
        </div>
        """
        
        return html

    def delete_source(self, source_name: str) -> Tuple[str, str]:
        """
        Remove uma fonte/perfil do ChromaDB.
        
        Args:
            source_name: Nome da fonte a ser removida
    
        Returns:
            Tuple (status_html, sources_html_atualizado)
        """
        try:
            if not source_name or source_name == "Selecione...":
                return (
                    "<div style='color: orange;'>⚠️ Selecione uma fonte para remover</div>",
                    self.generate_sources_html()
                )
            
            # Remove perfil do ChromaDB
            if self.use_agent:
                collection = self.agent.embedding_manager.collection
            else:
                collection = self.embedding_manager.collection
            
            # Busca IDs da fonte
            results = collection.get(
                where={'profile': source_name},
                limit=100000
            )
            
            if not results['ids']:
                return (
                    f"<div style='color: orange;'>⚠️ Fonte '{source_name}' não encontrada</div>",
                    self.generate_sources_html()
                )
            
            # Deleta documentos
            collection.delete(ids=results['ids'])
            
            # Atualiza stats
            self._refresh_stats()
            
            return (
                f"<div style='color: green; padding: 1rem; background: #f0f8ff; border-radius: 8px;'>✅ Fonte '@{source_name}' removida com sucesso! {len(results['ids'])} documentos deletados.</div>",
                self.generate_sources_html()
            )
        
        except Exception as e:
            return (
                f"<div style='color: red;'>❌ Erro ao remover fonte: {str(e)}</div>",
                self.generate_sources_html()
            )


if __name__ == "__main__":
    import argparse
    
    # Parse de argumentos
    parser = argparse.ArgumentParser(description="PING - UFF ANALYTICS")
    parser.add_argument("--port", type=int, default=7860, help="Porta do servidor (padrão: 7860)")
    parser.add_argument("--share", action="store_true", help="Criar link público compartilhável")
    parser.add_argument("--embedding-model", type=str, default="mxbai-embed-large", help="Modelo de embeddings")
    parser.add_argument("--generation-model", type=str, default="qwen3:30b", help="Modelo de geração")
    parser.add_argument("--no-agent", action="store_true", help="Desabilita modo agente (usa RAG clássico)")
    
    args = parser.parse_args()
    
    print("\n" + "="*60)
    print("🎓 PING - UFF ANALYTICS".center(60))
    print("="*60)
    
    # Inicializa aplicação
    print("\n📦 Inicializando sistema...")
    app = InstagramRAGApp(
        embedding_model=args.embedding_model,
        generation_model=args.generation_model,
        use_agent=not args.no_agent
    )
    
    print("\n🚀 Iniciando servidor Gradio...")
    print(f"   🌐 Porta: {args.port}")
    print(f"   🔗 URL: http://localhost:{args.port}")
    if args.share:
        print("   🌍 Link público será gerado...")
    
    print("\n" + "="*60)
    print("✨ Aplicação pronta! Acesse no navegador.".center(60))
    print("="*60 + "\n")
    
    # Lança interface
    try:
        app.launch(
            server_port=args.port,
            share=args.share,
            server_name="0.0.0.0",  # Aceita conexões externas
            show_error=True,
            quiet=False
        )
    except KeyboardInterrupt:
        print("\n\n👋 Encerrando aplicação...")
    except Exception as e:
        print(f"\n❌ Erro ao iniciar: {e}")
        import traceback
        traceback.print_exc()
