"""
Aplicação Gradio para Chat RAG de Posts do Instagram.
Agora usando sistema de agente inteligente!
"""

import gradio as gr
from agent_system import RAGAgent
from rag_system import RAGSystem
from datetime import datetime
from typing import List, Tuple
import json


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
                'embedding_model': em_stats.get('embedding_model', 'unknown'),
                'collection_name': em_stats.get('collection_name', 'unknown')
            }
            posts_count = self.stats['indexed_posts']
            print(f"📊 Perfis detectados: {self.stats['profiles']}")
        
        print(f"\n✓ Sistema pronto com {posts_count} posts indexados")
    
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
        
        html += "<h3>📌 Posts Recuperados:</h3>"
        
        for i, post in enumerate(posts, 1):
            metadata = post['metadata']
            
            # Parse data
            try:
                from dateutil import parser as date_parser
                timestamp = date_parser.parse(metadata['timestamp'])
                date_str = timestamp.strftime('%d/%m/%Y às %H:%M')
            except:
                date_str = "Data não disponível"
            
            # Formata caption
            caption = metadata.get('caption', 'Sem legenda')
            if len(caption) > 300:
                caption = caption[:300] + "..."
            
            # Card do post moderno
            engagement = metadata.get('likesCount', 0) + metadata.get('commentsCount', 0)
            html += f"""
            <div style='
                border: 1px solid #e0e0e0; 
                border-radius: 12px; 
                padding: 1.2rem; 
                margin: 0.8rem 0; 
                background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
                box-shadow: 0 2px 8px rgba(0,0,0,0.08);
                transition: transform 0.2s;
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
                    transition: opacity 0.2s;
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
            profile_filter: Filtro de perfil
            
        Returns:
            Tupla (resposta, fontes_html)
        """
        if not message.strip():
            return "Por favor, faça uma pergunta.", ""
        
        # Processa filtro de perfil
        profile = profile_filter if profile_filter != "Todos" else None
        
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
        
        # Formata fontes
        sources_html = self.format_sources(posts)
        
        return response, sources_html
    
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
    
    def create_interface(self) -> gr.Blocks:
        """
        Cria interface Gradio moderna e amigável.
        
        Returns:
            Interface Gradio configurada
        """
        # CSS customizado para deixar mais bonito
        custom_css = """
        .header-container {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 2rem;
            border-radius: 15px;
            margin-bottom: 2rem;
            color: white;
            text-align: center;
        }
        .stats-box {
            background: #f8f9fa;
            border-left: 4px solid #667eea;
            padding: 1rem;
            border-radius: 8px;
            margin: 1rem 0;
        }
        .example-btn {
            margin: 0.3rem !important;
            background: white !important;
            border: 1px solid #e0e0e0 !important;
        }
        .example-btn:hover {
            background: #f0f0f0 !important;
            border-color: #667eea !important;
        }
        """
        
        with gr.Blocks(
            title="UFF Instagram RAG - Análise Inteligente",
            theme=gr.themes.Soft(
                primary_hue="purple",
                secondary_hue="blue",
                font=["Inter", "sans-serif"]
            ),
            css=custom_css
        ) as app:
            
            # Header limpo e moderno
            with gr.Row():
                with gr.Column():
                    gr.HTML(f"""
                    <div class="header-container" style="color: #ffffff !important;">
                        <h1 style="margin: 0; font-size: 2.5rem; color: #ffffff !important;">📱 UFF Instagram Analytics</h1>
                        <p style="margin: 0.8rem 0 0 0; font-size: 1rem; opacity: 0.85; color: #ffffff !important;">
                            Faça perguntas sobre os {self.stats['indexed_posts']:,} posts dos perfis oficiais da UFF
                        </p>
                    </div>
                    """)
            
            with gr.Row():
                with gr.Column(scale=7):
                    # Área de chat principal
                    chatbot = gr.Chatbot(
                        label="💬 Conversa",
                        height=500,
                        show_copy_button=True,
                        avatar_images=(None, "assets/agent_avatar.png"),
                        bubble_full_width=False
                    )
                    
                    # Input melhorado
                    with gr.Row():
                        msg = gr.Textbox(
                            label="",
                            placeholder="Digite sua pergunta... Ex: Qual foi a última aparição do reitor?",
                            lines=2,
                            scale=9,
                            show_label=False
                        )
                        send_btn = gr.Button(
                            "Enviar 🚀", 
                            scale=1, 
                            variant="primary",
                            size="lg"
                        )
                    
                    with gr.Row():
                        clear_btn = gr.Button("🗑️ Limpar Conversa", size="sm", variant="secondary")
                        gr.Markdown("<div style='flex-grow: 1;'></div>")  # Spacer
                    
                                        # Fontes com accordion
                    with gr.Accordion("📚 Posts Recuperados (Fontes)", open=False):
                        sources = gr.HTML()
                
                with gr.Column(scale=3):
                    # Painel lateral simplificado
                    gr.Markdown("### ⚙️ Configurações")
                    
                    profile_filter = gr.Dropdown(
                        choices=["🌐 Todos os Perfis"] + ["@" + p for p in self.stats['profiles']],
                        value="🌐 Todos os Perfis",
                        label="Filtrar por Perfil"
                    )
                    
                    if not self.use_agent:
                        n_results = gr.Slider(
                            minimum=1,
                            maximum=10,
                            value=5,
                            step=1,
                            label="Posts a recuperar"
                        )
                    else:
                        n_results = gr.Number(value=5, visible=False)
                    
                    # Estatísticas compactas
                    with gr.Accordion("📊 Estatísticas", open=False):
                        gr.HTML(value=self.get_stats_html())
                    
                    # Exemplos compactos
                    gr.Markdown("---")
                    gr.Markdown("### 💡 Exemplos")
                    
                    if self.use_agent:
                        example_questions = [
                            ("🏆", "Post mais curtido do reitor"),
                            ("📊", "Compare os perfis"),
                            ("🔍", "Posts sobre HUAP"),
                            ("🗓️", "Publicações em 2024"),
                            ("💬", "Última aparição do reitor")
                        ]
                    else:
                        example_questions = [
                            ("📝", "Posts recentes do DCE"),
                            ("🏥", "Posts sobre HUAP"),
                            ("❤️", "Posts mais curtidos"),
                            ("🔬", "Sobre pesquisa"),
                            ("🎓", "Mencionam estudantes")
                        ]
                    
                    for emoji, question in example_questions:
                        btn = gr.Button(
                            f"{emoji} {question}",
                            size="sm",
                            elem_classes="example-btn"
                        )
                        btn.click(
                            lambda q=question: q,
                            outputs=msg
                        )
            
            # Lógica do chat
            def respond(message, chat_history, n_res, profile_filt):
                if not message.strip():
                    return message, chat_history, ""
                
                # Processa filtro de perfil
                if profile_filt.startswith("🌐"):
                    profile = None
                else:
                    profile = profile_filt.replace("@", "")
                
                # Gera resposta
                response, sources_html = self.chat_response(
                    message, 
                    chat_history, 
                    n_res, 
                    profile if profile else "Todos"
                )
                
                # Atualiza histórico
                chat_history.append((message, response))
                
                return "", chat_history, sources_html
            
            # Eventos
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
            
            # Rodapé limpo
            gr.Markdown("---")
            gr.HTML(f"""
            <div style="text-align: center; padding: 1rem; color: #999; font-size: 0.85rem;">
                <p style="margin: 0.3rem 0;">
                    🎓 Universidade Federal Fluminense • 
                    {self.stats['indexed_posts']:,} posts • 
                    {len(self.stats['profiles'])} perfis
                </p>
                <p style="margin: 0.3rem 0; font-size: 0.75rem; color: #bbb;">
                    Powered by Ollama • ChromaDB • Gradio
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
