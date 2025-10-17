"""
Sistema de Agente RAG com LLM que decide quais ferramentas usar.

O LLM recebe a pergunta do usuário e decide:
1. Se deve usar ferramentas estruturadas (query_tools)
2. Se deve usar busca semântica (RAG)
3. Quais parâmetros usar
4. Como combinar múltiplas ferramentas

Fluxo:
Usuario → LLM Planejador → Ferramentas → LLM Sintetizador → Resposta
"""

import json
from typing import Dict, Any, List, Tuple, Optional
import ollama

from query_tools import QueryTools
from embedding_manager import EmbeddingManager


class RAGAgent:
    """
    Agente inteligente que usa LLM para decidir quais ferramentas usar.
    """
    
    def __init__(
        self,
        embedding_model: str = "mxbai-embed-large",
        generation_model: str = "qwen3:30b",
        planning_model: str = "qwen3:30b"
    ):
        """
        Inicializa o agente RAG.
        
        Args:
            embedding_model: Modelo para embeddings
            generation_model: Modelo para gerar resposta final
            planning_model: Modelo para planejar ações (pode ser menor/mais rápido)
        """
        self.embedding_manager = EmbeddingManager(embedding_model=embedding_model)
        self.query_tools = QueryTools(self.embedding_manager)
        self.generation_model = generation_model
        self.planning_model = planning_model
        
        print(f"✓ Agente RAG inicializado")
        print(f"  - Modelo de planejamento: {planning_model}")
        print(f"  - Modelo de geração: {generation_model}")
    
    def _create_tools_description(self) -> str:
        """
        Cria descrição das ferramentas disponíveis para o LLM.
        
        Returns:
            String com descrição de todas as ferramentas
        """
        return """
## FERRAMENTAS DISPONÍVEIS:

1. **get_top_posts_by_likes**
   - Uso: Encontrar posts com mais curtidas
   - Parâmetros: limit (int), profile (str, opcional)
   - Exemplo: {"tool": "get_top_posts_by_likes", "limit": 10, "profile": "reitor"}

2. **get_top_posts_by_comments**
   - Uso: Encontrar posts com mais comentários
   - Parâmetros: limit (int), profile (str, opcional)
   - Exemplo: {"tool": "get_top_posts_by_comments", "limit": 5}

3. **get_posts_by_engagement**
   - Uso: Encontrar posts com maior engajamento total (curtidas + comentários)
   - Parâmetros: limit (int), profile (str, opcional)
   - Exemplo: {"tool": "get_posts_by_engagement", "limit": 10, "profile": "dceuff"}

4. **get_recent_posts**
   - Uso: Encontrar posts publicados recentemente
   - Parâmetros: days (int), limit (int), profile (str, opcional)
   - Exemplo: {"tool": "get_recent_posts", "days": 7, "limit": 5}

5. **get_profile_statistics**
   - Uso: Obter estatísticas agregadas de um perfil
   - Parâmetros: profile (str, opcional - se omitido, retorna todos)
   - Exemplo: {"tool": "get_profile_statistics", "profile": "reitor"}

6. **compare_profiles**
   - Uso: Comparar estatísticas entre todos os perfis
   - Parâmetros: nenhum
   - Exemplo: {"tool": "compare_profiles"}

7. **semantic_search**
   - Uso: Buscar posts por conteúdo/tema usando busca semântica
   - Parâmetros: query (str), n_results (int), profile (str, opcional)
   - Exemplo: {"tool": "semantic_search", "query": "HUAP hospital", "n_results": 5}

## PERFIS DISPONÍVEIS:
- dceuff (Diretório Central dos Estudantes)
- reitor (Reitor da UFF)
- vicereitor (Vice-Reitor da UFF)

## INSTRUÇÕES:
- Escolha a(s) ferramenta(s) mais apropriada(s) para responder a pergunta
- Você pode usar MÚLTIPLAS ferramentas se necessário
- Para perguntas sobre quantidade/ranking, prefira ferramentas estruturadas
- Para perguntas sobre conteúdo/tema, use semantic_search
- Retorne APENAS um JSON válido, sem texto adicional
"""

    def _plan_action(
        self,
        user_question: str,
        profile_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        LLM decide quais ferramentas usar e com quais parâmetros.
        
        Args:
            user_question: Pergunta do usuário
            profile_filter: Filtro de perfil (opcional)
            
        Returns:
            Lista de ações (ferramentas) a executar
        """
        tools_desc = self._create_tools_description()
        
        planning_prompt = f"""{tools_desc}

## CONTEXTO:
Pergunta do usuário: "{user_question}"
{f'Perfil filtrado: {profile_filter}' if profile_filter else 'Sem filtro de perfil'}

## SUA TAREFA:
Analise a pergunta e decida qual(is) ferramenta(s) usar para respondê-la da melhor forma.

RETORNE APENAS UM JSON no seguinte formato:
{{
    "reasoning": "Breve explicação do seu raciocínio",
    "actions": [
        {{"tool": "nome_da_ferramenta", "params": {{"param1": "valor1"}}}}
    ]
}}

EXEMPLOS:

Pergunta: "Quais foram os 5 posts mais curtidos?"
{{
    "reasoning": "Usuário quer ranking por curtidas, usar ferramenta estruturada",
    "actions": [
        {{"tool": "get_top_posts_by_likes", "params": {{"limit": 5}}}}
    ]
}}

Pergunta: "Me fale sobre posts do HUAP"
{{
    "reasoning": "Pergunta sobre conteúdo específico, usar busca semântica",
    "actions": [
        {{"tool": "semantic_search", "params": {{"query": "HUAP hospital", "n_results": 5}}}}
    ]
}}

Pergunta: "Compare o engajamento entre reitor e DCE"
{{
    "reasoning": "Comparação de estatísticas entre perfis",
    "actions": [
        {{"tool": "compare_profiles", "params": {{}}}}
    ]
}}

Pergunta: "Qual foi o post mais curtido recente do reitor?"
{{
    "reasoning": "Combina recente + curtidas + filtro de perfil",
    "actions": [
        {{"tool": "get_recent_posts", "params": {{"days": 30, "limit": 20, "profile": "reitor"}}}},
        {{"tool": "get_top_posts_by_likes", "params": {{"limit": 1, "profile": "reitor"}}}}
    ]
}}

IMPORTANTE: Retorne APENAS o JSON, nada mais!
"""

        try:
            # Chama o LLM para planejar
            response = ollama.chat(
                model=self.planning_model,
                messages=[
                    {
                        'role': 'system',
                        'content': 'Você é um planejador especializado em análise de dados do Instagram. Retorne APENAS JSON válido, sem markdown ou texto adicional.'
                    },
                    {
                        'role': 'user',
                        'content': planning_prompt
                    }
                ],
                format='json'  # Força saída em JSON
            )
            
            # Parse da resposta
            plan_text = response['message']['content']
            
            # Tenta parsear o JSON
            try:
                plan = json.loads(plan_text)
            except json.JSONDecodeError:
                # Se falhar, tenta extrair JSON do texto
                import re
                json_match = re.search(r'\{.*\}', plan_text, re.DOTALL)
                if json_match:
                    plan = json.loads(json_match.group())
                else:
                    raise ValueError("LLM não retornou JSON válido")
            
            print(f"\n🤔 Raciocínio do agente: {plan.get('reasoning', 'N/A')}")
            print(f"🔧 Ações planejadas: {len(plan.get('actions', []))} ferramenta(s)")
            
            return plan.get('actions', [])
            
        except Exception as e:
            print(f"⚠️ Erro no planejamento: {e}")
            # Fallback: busca semântica simples
            return [{
                'tool': 'semantic_search',
                'params': {
                    'query': user_question,
                    'n_results': 5,
                    'profile': profile_filter
                }
            }]
    
    def _execute_action(
        self,
        action: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Executa uma ação (ferramenta).
        
        Args:
            action: Dicionário com tool e params
            
        Returns:
            Resultados da ferramenta
        """
        tool = action.get('tool')
        params = action.get('params', {})
        
        print(f"  ⚙️ Executando: {tool} com params {params}")
        
        try:
            if tool == 'get_top_posts_by_likes':
                return self.query_tools.get_top_posts_by_likes(
                    limit=params.get('limit', 10),
                    profile=params.get('profile')
                )
            
            elif tool == 'get_top_posts_by_comments':
                return self.query_tools.get_top_posts_by_comments(
                    limit=params.get('limit', 10),
                    profile=params.get('profile')
                )
            
            elif tool == 'get_posts_by_engagement':
                return self.query_tools.get_posts_by_engagement(
                    limit=params.get('limit', 10),
                    profile=params.get('profile')
                )
            
            elif tool == 'get_recent_posts':
                return self.query_tools.get_recent_posts(
                    days=params.get('days', 30),
                    limit=params.get('limit', 10),
                    profile=params.get('profile')
                )
            
            elif tool == 'get_profile_statistics':
                stats = self.query_tools.get_profile_statistics(
                    profile=params.get('profile')
                )
                return [{'metadata': stats, 'is_stats': True}]
            
            elif tool == 'compare_profiles':
                comparison = self.query_tools.compare_profiles()
                return [{'metadata': comparison, 'is_comparison': True}]
            
            elif tool == 'semantic_search':
                query = params.get('query', '')
                n_results = params.get('n_results', 5)
                profile = params.get('profile')
                
                return self.embedding_manager.search(
                    query_text=query,
                    n_results=n_results,
                    profile_filter=profile
                )
            
            else:
                print(f"⚠️ Ferramenta desconhecida: {tool}")
                return []
        
        except Exception as e:
            print(f"❌ Erro ao executar {tool}: {e}")
            return []
    
    def _format_results_for_llm(
        self,
        results: List[Dict[str, Any]],
        tool_name: str
    ) -> str:
        """
        Formata resultados das ferramentas para o LLM sintetizar.
        
        Args:
            results: Resultados das ferramentas
            tool_name: Nome da ferramenta usada
            
        Returns:
            String formatada com os resultados
        """
        if not results:
            return f"## Resultado de {tool_name}:\nNenhum resultado encontrado."
        
        # Verifica se é estatísticas
        if results[0].get('is_stats'):
            stats = results[0]['metadata']
            return f"""## Estatísticas:
- Total de posts: {stats.get('total_posts', 0)}
- Total de curtidas: {stats.get('total_likes', 0)}
- Total de comentários: {stats.get('total_comments', 0)}
- Média de curtidas por post: {stats.get('avg_likes_per_post', 0):.2f}
- Média de comentários por post: {stats.get('avg_comments_per_post', 0):.2f}
- Engajamento total: {stats.get('total_engagement', 0)}
{f"- Post mais engajado: {stats['top_post']['url']} ({stats['top_post']['engagement']} engajamentos)" if stats.get('top_post') else ''}
"""
        
        # Verifica se é comparação
        if results[0].get('is_comparison'):
            comparison = results[0]['metadata']
            text = "## Comparação Entre Perfis:\n\n"
            for profile, stats in comparison.items():
                text += f"### @{profile}\n"
                text += f"- Posts: {stats['total_posts']}\n"
                text += f"- Curtidas: {stats['total_likes']} (média: {stats['avg_likes']:.1f})\n"
                text += f"- Comentários: {stats['total_comments']} (média: {stats['avg_comments']:.1f})\n"
                text += f"- Engajamento total: {stats['total_engagement']}\n\n"
            return text
        
        # Posts regulares
        text = f"## Resultados de {tool_name}:\n\n"
        for i, post in enumerate(results[:10], 1):
            meta = post.get('metadata', {})
            doc = post.get('document', '')
            
            text += f"**Post {i}** (@{meta.get('profile', 'unknown')})\n"
            text += f"- Curtidas: {meta.get('likesCount', 0)}\n"
            text += f"- Comentários: {meta.get('commentsCount', 0)}\n"
            text += f"- Data: {meta.get('timestamp', 'N/A')[:10]}\n"
            text += f"- Link: {meta.get('url', 'N/A')}\n"
            
            # Adiciona trecho do texto/legenda
            if doc:
                text += f"- Conteúdo: {doc[:200]}...\n"
            elif meta.get('caption'):
                text += f"- Legenda: {meta['caption'][:200]}...\n"
            
            text += "\n"
        
        return text
    
    def _synthesize_response(
        self,
        user_question: str,
        all_results: List[Tuple[str, List[Dict[str, Any]]]],
        stream: bool = False
    ) -> str:
        """
        LLM sintetiza todos os resultados em uma resposta coerente.
        
        Args:
            user_question: Pergunta original do usuário
            all_results: Lista de (nome_ferramenta, resultados)
            stream: Se True, retorna generator para streaming
            
        Returns:
            Resposta final sintetizada
        """
        # Monta contexto com todos os resultados
        context = ""
        for tool_name, results in all_results:
            context += self._format_results_for_llm(results, tool_name)
            context += "\n---\n\n"
        
        synthesis_prompt = f"""{context}

## Pergunta Original do Usuário:
{user_question}

## Sua Tarefa:
Sintetize os dados acima em uma resposta clara, completa e bem formatada para o usuário.

DIRETRIZES:
1. Use APENAS os dados fornecidos acima
2. Seja objetivo e direto
3. Cite números específicos e links quando relevante
4. Use formatação markdown para melhor legibilidade
5. Organize a informação de forma lógica
6. Se múltiplas ferramentas foram usadas, integre os resultados de forma coerente
7. Sempre inclua links dos posts quando disponível

NÃO invente informações que não estão no contexto!
"""

        try:
            response = ollama.chat(
                model=self.generation_model,
                messages=[
                    {
                        'role': 'system',
                        'content': 'Você é um assistente especializado em análise de posts do Instagram da UFF. Responda de forma clara, objetiva e bem formatada.'
                    },
                    {
                        'role': 'user',
                        'content': synthesis_prompt
                    }
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
        profile_filter: Optional[str] = None,
        stream: bool = False
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Processa query completa usando o agente inteligente.
        
        Fluxo:
        1. LLM planeja quais ferramentas usar
        2. Executa as ferramentas
        3. LLM sintetiza os resultados
        
        Args:
            question: Pergunta do usuário
            profile_filter: Filtro de perfil (opcional)
            stream: Streaming da resposta
            
        Returns:
            Tupla (resposta, todos_os_posts_recuperados)
        """
        print(f"\n{'='*60}")
        print(f"🎯 Nova consulta: {question}")
        if profile_filter:
            print(f"👤 Perfil: {profile_filter}")
        print(f"{'='*60}\n")
        
        # Fase 1: Planejamento
        print("📋 Fase 1: Planejamento de ações...")
        actions = self._plan_action(question, profile_filter)
        
        if not actions:
            return "Não consegui determinar como responder sua pergunta. Tente reformular.", []
        
        # Fase 2: Execução
        print(f"\n⚙️ Fase 2: Executando {len(actions)} ação(ões)...")
        all_results = []
        all_posts = []
        
        for i, action in enumerate(actions, 1):
            print(f"\n  Ação {i}/{len(actions)}:")
            results = self._execute_action(action)
            
            if results:
                tool_name = action.get('tool', 'unknown')
                all_results.append((tool_name, results))
                all_posts.extend(results)
                print(f"  ✓ {len(results)} resultado(s) obtido(s)")
            else:
                print(f"  ⚠️ Nenhum resultado")
        
        if not all_results:
            return "Não encontrei informações relevantes para sua pergunta.", []
        
        # Fase 3: Síntese
        print(f"\n🎨 Fase 3: Sintetizando resposta final...")
        response = self._synthesize_response(
            user_question=question,
            all_results=all_results,
            stream=stream
        )
        
        print(f"\n✓ Resposta gerada!")
        print(f"{'='*60}\n")
        
        return response, all_posts


if __name__ == "__main__":
    """
    Teste do sistema de agente.
    """
    print("🧪 Testando Sistema de Agente RAG\n")
    
    # Inicializa agente
    agent = RAGAgent()
    
    # Testes diversos
    test_queries = [
        ("Qual foi o post mais curtido do reitor?", "reitor"),
        ("Me fale sobre posts do HUAP", None),
        ("Compare o engajamento entre os perfis", None),
        ("Quais foram os últimos 5 posts do DCE?", "dceuff"),
        ("Estatísticas do vice-reitor", "vicereitor"),
    ]
    
    for question, profile in test_queries:
        print(f"\n{'='*80}")
        response, posts = agent.query(question, profile_filter=profile)
        
        print(f"\n📄 RESPOSTA:")
        print(response)
        print(f"\n📊 Total de posts recuperados: {len(posts)}")
        
        input("\n▶️ Pressione ENTER para próximo teste...")
