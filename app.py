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
        else:
            # Para o agente, verifica stats do embedding manager
            self.stats = self.embedding_manager.get_stats()
        
        print(f"\n✓ Sistema pronto com {self.stats['indexed_posts']} posts indexados")
    
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
            
            # Card do post
            html += f"""
            <div style='border: 1px solid #ddd; border-radius: 8px; padding: 15px; margin: 10px 0; background-color: #f9f9f9;'>
                <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;'>
                    <strong style='color: #1DA1F2; font-size: 16px;'>@{metadata['profile']}</strong>
                    <span style='color: #666; font-size: 12px;'>{date_str}</span>
                </div>
                <p style='margin: 10px 0; line-height: 1.5;'>{caption}</p>
                <div style='display: flex; gap: 20px; margin: 10px 0; color: #666; font-size: 14px;'>
                    <span>❤️ {metadata['likesCount']} curtidas</span>
                    <span>💬 {metadata['commentsCount']} comentários</span>
                </div>
                <a href='{metadata['url']}' target='_blank' style='color: #1DA1F2; text-decoration: none; font-size: 14px;'>
                    🔗 Ver post no Instagram
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
        stats = self.rag.get_system_stats()
        
        html = f"""
        <div style='padding: 20px; background-color: #f0f8ff; border-radius: 10px; border: 1px solid #1DA1F2;'>
            <h3 style='margin-top: 0; color: #1DA1F2;'>📊 Estatísticas do Sistema</h3>
            <ul style='list-style-type: none; padding: 0;'>
                <li>📝 <strong>Posts indexados:</strong> {stats['indexed_posts']}</li>
                <li>👥 <strong>Perfis:</strong> {', '.join(['@' + p for p in stats['profiles']])}</li>
                <li>🧠 <strong>Modelo de embedding:</strong> {stats['embedding_model']}</li>
                <li>💬 <strong>Modelo de geração:</strong> {stats['generation_model']}</li>
            </ul>
        </div>
        """
        return html
    
    def create_interface(self) -> gr.Blocks:
        """
        Cria interface Gradio.
        
        Returns:
            Interface Gradio configurada
        """
        with gr.Blocks(
            title="Instagram RAG - UFF",
            theme=gr.themes.Soft()
        ) as app:
            
            mode_badge = "🤖 **AGENTE INTELIGENTE**" if self.use_agent else "🔧 **MODO CLÁSSICO**"
            
            gr.Markdown(
                f"""
                # 📱 Instagram RAG - Análise de Posts Institucionais UFF
                
                {mode_badge}
                
                Sistema de busca semântica e análise de posts do Instagram usando RAG (Retrieval-Augmented Generation).
                
                {'O agente inteligente usa LLM para decidir automaticamente quais ferramentas usar!' if self.use_agent else 'Sistema com detecção de palavras-chave para ativar ferramentas.'}
                
                Faça perguntas sobre os posts e receba respostas contextualizadas com links para as fontes.
                """
            )
            
            with gr.Row():
                with gr.Column(scale=2):
                    # Área de chat
                    chatbot = gr.Chatbot(
                        label="Conversa",
                        height=400,
                        show_copy_button=True
                    )
                    
                    with gr.Row():
                        msg = gr.Textbox(
                            label="Sua pergunta",
                            placeholder="Ex: Quais posts do reitor mencionam o HUAP?",
                            lines=2,
                            scale=4
                        )
                        send_btn = gr.Button("Enviar 📤", scale=1, variant="primary")
                    
                    clear_btn = gr.Button("Limpar conversa 🗑️")
                    
                    # Fontes
                    sources = gr.HTML(label="Posts Recuperados")
                
                with gr.Column(scale=1):
                    # Configurações
                    gr.Markdown("### ⚙️ Configurações")
                    
                    n_results = gr.Slider(
                        minimum=1,
                        maximum=10,
                        value=5,
                        step=1,
                        label="Número de posts a recuperar",
                        info="Mais posts = mais contexto (ignorado no modo agente)" if self.use_agent else "Mais posts = mais contexto, mas respostas mais longas",
                        visible=not self.use_agent  # Oculta no modo agente
                    )
                    
                    profile_filter = gr.Dropdown(
                        choices=["Todos"] + ["@" + p for p in self.stats['profiles']],
                        value="Todos",
                        label="Filtrar por perfil",
                        info="Buscar apenas em um perfil específico"
                    )
                    
                    # Exemplos
                    gr.Markdown("### 💡 Perguntas Exemplo")
                    
                    if self.use_agent:
                        example_questions = [
                            "Qual foi o post mais curtido do reitor?",
                            "Compare o engajamento entre os perfis",
                            "Me mostre posts recentes sobre HUAP",
                            "Estatísticas do DCE UFF",
                            "Quais posts tiveram mais comentários na última semana?"
                        ]
                    else:
                        example_questions = [
                            "Quais foram os posts mais recentes do DCE UFF?",
                            "Mostre posts sobre o HUAP",
                            "Quais posts tiveram mais curtidas?",
                            "O que foi publicado sobre pesquisa?",
                            "Posts que mencionam estudantes nos últimos meses"
                        ]
                    
                    for question in example_questions:
                        gr.Button(
                            question,
                            size="sm"
                        ).click(
                            lambda q=question: q,
                            outputs=msg
                        )
                    
                    # Estatísticas
                    gr.Markdown("---")
                    stats_display = gr.HTML(value=self.get_stats_html())
            
            # Lógica do chat
            def respond(message, chat_history, n_res, profile_filt):
                # Gera resposta
                response, sources_html = self.chat_response(
                    message, 
                    chat_history, 
                    n_res, 
                    profile_filt.replace("@", "") if profile_filt != "Todos" else "Todos"
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
            
            # Informações adicionais
            gr.Markdown(
                """
                ---
                ### 📖 Como usar:
                
                1. **Faça perguntas naturais** sobre os posts do Instagram
                2. **Ajuste as configurações** para refinar os resultados
                3. **Clique nos links** dos posts recuperados para ver no Instagram
                4. **Use os exemplos** como inspiração para suas perguntas
                
                ### 🎯 Dicas:
                
                - Seja específico: mencione perfis, datas ou temas
                - Pergunte sobre engajamento, curtidas ou comentários
                - Peça comparações entre perfis ou períodos
                - Use filtros para focar em um perfil específico
                
                ---
                💡 **Sistema desenvolvido com Ollama, ChromaDB e Gradio**
                """
            )
        
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
