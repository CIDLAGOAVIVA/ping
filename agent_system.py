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
import llm_chat
from config import DEFAULT_PROVIDER, DEEPSEEK_MODEL, OLLAMA_GENERATION_MODEL

from query_tools import QueryTools
from embedding_manager import EmbeddingManager


class RAGAgent:
    """
    Agente inteligente que usa LLM para decidir quais ferramentas usar.
    """
    
    # Perfis válidos no sistema
    PERFIS_VALIDOS = ['reitor', 'vicereitor', 'dceuff']
    
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
        self.query_tools = QueryTools(self.embedding_manager, llm_model=generation_model)
        self.generation_model = generation_model
        self.planning_model = planning_model
        
        print(f"✓ Agente RAG inicializado")
        print(f"  - Modelo de planejamento: {planning_model}")
        print(f"  - Modelo de geração: {generation_model}")
    
    def validar_perfil(self, profile: Optional[str]) -> tuple[bool, str]:
        """
        Valida se um perfil existe antes de buscar.
        
        Args:
            profile: Nome do perfil a validar
            
        Returns:
            Tupla (está_válido, mensagem)
        """
        if not profile:
            return True, ""
        
        profile_clean = profile.replace('@', '').lower()
        if profile_clean not in self.PERFIS_VALIDOS:
            msg = f"Perfil @{profile_clean} não encontrado. Perfis disponíveis: {', '.join(['@' + p for p in self.PERFIS_VALIDOS])}"
            return False, msg
        
        return True, profile_clean
    
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

4. **get_bottom_posts_by_likes**
   - Uso: Encontrar posts com MENOS curtidas
   - Parâmetros: limit (int), profile (str, opcional)
   - Exemplo: {"tool": "get_bottom_posts_by_likes", "limit": 10, "profile": "dceuff"}

5. **get_bottom_posts_by_comments**
   - Uso: Encontrar posts com MENOS comentários
   - Parâmetros: limit (int), profile (str, opcional)
   - Exemplo: {"tool": "get_bottom_posts_by_comments", "limit": 5}

6. **get_recent_posts**
   - Uso: Encontrar posts publicados recentemente
   - Parâmetros: days (int), limit (int), profile (str, opcional)
   - Exemplo: {"tool": "get_recent_posts", "days": 7, "limit": 5}

7. **get_profile_statistics**
   - Uso: Obter estatísticas agregadas de um perfil
   - Parâmetros: profile (str, opcional - se omitido, retorna todos)
   - Exemplo: {"tool": "get_profile_statistics", "profile": "reitor"}

8. **compare_profiles**
   - Uso: Comparar estatísticas entre todos os perfis
   - Parâmetros: nenhum
   - Exemplo: {"tool": "compare_profiles"}

9. **count_term_occurrences**
   - Uso: QUANTIFICAR quantos posts mencionam um termo específico (consulta TODA a base)
   - Quando usar: "quantos posts falam sobre X", "quantas vezes mencionaram Y", "frequência de Z"
   - Parâmetros: term (str - termo a buscar), profile (str, opcional), case_sensitive (bool, default=False)
   - Exemplo: {"tool": "count_term_occurrences", "term": "greve", "profile": "dceuff"}
   - IMPORTANTE: Esta ferramenta CONTA ocorrências, não retorna os posts mais relevantes

10. **analyze_sentiment**
   - Uso: ANALISAR SENTIMENTO e percepção sobre um tópico/entidade usando LLM
   - Quando usar: "como é visto X?", "percepção sobre Y", "o que pensam sobre Z", "análise de sentimento", "avaliação de X"
   - Parâmetros: topic (str - tópico/entidade), profile (str, opcional), n_posts (int, default=20)
   - Exemplo: {"tool": "analyze_sentiment", "topic": "reitor", "profile": "dceuff", "n_posts": 20}
   - Retorna: Contagem positivo/negativo/neutro, aspectos positivos/negativos, resumo qualitativo

11. **semantic_search**
   - Uso: Buscar posts/notícias/DEBATES por CONTEÚDO/TEMA usando busca semântica vetorial
   - Quando usar: Perguntas sobre "o que foi dito", "posts sobre X", "aparições", "mencionou", "posicionamento sobre Y", etc.
   - Parâmetros: 
     * query (str - reformule para otimizar busca)
     * n_results (int)
     * profile (str, opcional)
     * content_type_filter (str, opcional: 'news', 'instagram_post' ou 'debate')
   - Exemplo: {"tool": "semantic_search", "params": {"query": "HUAP hospital atendimento saúde", "n_results": 8}}
   - Exemplo com filtro de notícias: {"tool": "semantic_search", "params": {"query": "cotas ações afirmativas", "n_results": 10, "content_type_filter": "news"}}
   - Exemplo com filtro de debates: {"tool": "semantic_search", "params": {"query": "Roberto Salles teletrabalho 30 horas servidor", "n_results": 15, "content_type_filter": "debate"}}
   - IMPORTANTE: Reformule a query do usuário para termos mais específicos e relevantes
   - IMPORTANTE: Use content_type_filter='news' quando buscar sobre ex-reitor ou período histórico (2009-2018)
   - IMPORTANTE: Use content_type_filter='debate' quando buscar POSICIONAMENTO POLÍTICO, PROPOSTAS, ARGUMENTOS
   - IMPORTANTE: A LLM LÊ O CAMPO "trecho" dos debates, que contém as FALAS LITERAIS de Roberto Salles

12. **get_news_articles**
   - Uso: Buscar NOTÍCIAS filtradas por data e/ou publisher
   - Quando usar: "notícias sobre", "reportagens", "imprensa", "mídia", "jornais"
   - Parâmetros: limit (int), min_date (str ISO), max_date (str ISO), publisher (str, opcional)
   - Exemplo: {"tool": "get_news_articles", "limit": 10, "min_date": "2009-01-01", "max_date": "2010-12-31"}

13. **search_news_by_person**
   - Uso: Buscar notícias que mencionam uma PESSOA específica (ex: Roberto Salles, ex-reitor)
   - Quando usar: "notícias sobre Roberto Salles", "o que a imprensa disse sobre X"
   - Parâmetros: person_name (str), limit (int)
   - Exemplo: {"tool": "search_news_by_person", "person_name": "Roberto Salles", "limit": 10}

14. **get_news_statistics**
   - Uso: Estatísticas sobre notícias indexadas (total, publishers, período)
   - Quando usar: "quantas notícias", "quais veículos", "período coberto"
   - Parâmetros: nenhum
   - Exemplo: {"tool": "get_news_statistics"}

15. **web_search**
   - Uso: Buscar na INTERNET usando DuckDuckGo para contexto externo e atualizado
   - Quando usar: "notícias sobre X 2025", "últimas informações sobre Y", "contexto atualizado de Z", "o que está acontecendo com W"
   - IMPORTANTE: Use quando a base local NÃO é suficiente (perguntas sobre atualidades, eventos recentes, contexto nacional/internacional)
   - Parâmetros: query (str - termo de busca), limit (int, default 5)
   - Exemplo: {"tool": "web_search", "query": "educação Brasil 2025 notícias", "limit": 5}
   - Retorna: Resultados com título, resumo, fonte e data (quando disponível)
   - DICA: Combine com semantic_search quando a pergunta tem DUAS partes (contexto externo + conteúdo local)

## PERFIS DISPONÍVEIS (Instagram):
- @dceuff (Diretório Central dos Estudantes)
- @reitor (Reitor ATUAL da UFF - Antônio Cláudio Nóbrega 2023-2025)
- @vicereitor (Vice-Reitor ATUAL da UFF)

## FONTES DE DADOS AUXILIARES:
- **Notícias/Arquivo**: Conteúdo histórico sobre a UFF e ex-reitor Roberto Salles (2009-2018)
  - Use para perguntas sobre Roberto Salles/Sales ou eventos passados
  - Ferramentas: search_news_by_person, get_news_articles, semantic_search com content_type_filter='news'

- **Debates Políticos**: Transcrições de debates eleitorais de Roberto Salles (período 2006-2018)
  - Use para perguntas sobre POSICIONAMENTO POLÍTICO, PROPOSTAS DE CAMPANHA, DEBATES ELEITORAIS
  - Contém argumentos, propostas e posições políticas detalhadas no campo "trecho" (falas literais)
  - Ferramenta: semantic_search com content_type_filter='debate'
  - Palavras-chave: "debate", "eleição", "proposta", "plano de governo", "candidatura", "posicionamento"
  - CAMPOS IMPORTANTES:
    * "trecho": contém a FALA LITERAL de Roberto Salles (ex: "XXX_Roberto SallesNós vamos retornar as 30 horas...")
    * "topicos": temas abordados (ex: "30h/Teletrabalho", "Hospital/EBSERH", "ReUni/Infra")
    * "fonte": qual debate (1o_debate, 2o_debate, etc.)
    * "timecode": momento da fala no debate

## CONTEXTO IMPORTANTE:
- **Roberto Salles (ou Roberto Sales)** foi REITOR DA UFF entre 2009-2018
- Notícias sobre "reitor da UFF" do período 2009-2018 referem-se a Roberto Salles
- Posts atuais (2023-2025) do perfil @reitor referem-se ao REITOR ATUAL (Antônio Cláudio Nóbrega)
- Para perguntas sobre Roberto Salles: SEMPRE buscar em NOTÍCIAS ou DEBATES, nunca em posts atuais

## DIRETRIZES CRÍTICAS:

### Use SEMANTIC_SEARCH quando:
✅ Pergunta sobre CONTEÚDO: "o que foi dito sobre X", "posts que mencionam Y", "falar sobre Z"
✅ Busca por TEMA: "aparições públicas", "eventos", "anúncios", "opiniões sobre"
✅ Perguntas ABERTAS: "como X tratou Y", "qual posicionamento sobre Z"
✅ TEMPORAL + CONTEÚDO: "o que foi dito em 2024 sobre X"
✅ Contexto específico: "última aparição pública", "pronunciamento sobre"

### Use FERRAMENTAS DE NOTÍCIAS quando:
✅ Pergunta sobre IMPRENSA: "o que os jornais disseram", "reportagens sobre"
✅ Menção a PESSOA ESPECÍFICA: "Roberto Salles", "Roberto Sales", "ex-reitor"
✅ Veículos de mídia: "FAPERJ", "BBC", "O Globo", "G1"
✅ Período histórico: notícias de 2009-2018
✅ IMPORTANTE: Perguntas sobre POSICIONAMENTO/OPINIÃO do ex-reitor Roberto Salles SEMPRE usar search_news_by_person + semantic_search em notícias
✅ Exemplos: "o que Roberto Salles achava de X", "posição do ex-reitor sobre Y", "Roberto Salles falou sobre Z"
✅ GATILHOS CRÍTICOS: "ex-reitor", "Roberto", "Salles", "Sales" → buscar em notícias (2009-2018)

### 🆕 Use BUSCA EM DEBATES quando:
✅ Pergunta sobre PROPOSTAS DE CAMPANHA: "o que Roberto Salles propôs", "plano de governo", "promessas de campanha"
✅ Pergunta sobre DEBATES ELEITORAIS: "debate eleitoral", "discussão política", "confronto eleitoral"
✅ Pergunta sobre POSICIONAMENTO POLÍTICO DETALHADO: "visão política de X", "ideologia", "argumentos defendidos"
✅ Pergunta sobre FALAS ESPECÍFICAS: "o que Roberto Salles disse sobre X no debate", "posicionamento sobre Y"
✅ IMPORTANTE: Para debates, use semantic_search COM content_type_filter='debate'
✅ Exemplos: 
   - "qual o posicionamento de Roberto Salles sobre teletrabalho?" → buscar em debates
   - "o que Roberto Salles defendeu sobre as 30 horas?" → buscar em debates
   - "propostas de Roberto Salles para educação" → buscar em debates
   - "o que Roberto Salles disse sobre hospital/EBSERH?" → buscar em debates
✅ COMBINE com notícias para contexto completo: debates (propostas) + notícias (implementação)
✅ A LLM LEIA o campo "trecho" que contém as falas LITERAIS de Roberto Salles nos debates

### Use WEB_SEARCH quando:
✅ CONTEXTO EXTERNO/ATUALIZADO: "como está X em 2025", "últimas notícias sobre Y", "o que está acontecendo com Z"
✅ NOTÍCIAS RECENTES: "notícias de hoje", "eventos recentes", "informação atualizada"
✅ CONTEXTO NACIONAL/INTERNACIONAL: "economia do Brasil", "educação em SP", "lei federal de X"
✅ BASE LOCAL INSUFICIENTE: Pergunta sobre tópicos não cobertos nos dados da UFF
✅ COMBINE com semantic_search: Quando pergunta tem DUAS partes (contexto externo + conteúdo local)

### Use FERRAMENTAS ESTRUTURADAS quando:
✅ RANKING MAIORES: "mais curtidos", "top 10", "maior engajamento"
✅ RANKING MENORES: "menos curtidos", "posts com menos comentários", "menor engajamento" (use get_bottom_*)
✅ MÉTRICAS: "quantos posts", "média de curtidas", "estatísticas"
✅ COMPARAÇÕES NUMÉRICAS: "qual perfil tem mais X"
✅ FILTROS TEMPORAIS PUROS: "posts da última semana" (sem contexto de conteúdo)
✅ QUANTIFICAÇÃO DE TERMOS: "quantos posts falam sobre X", "frequência de Y" (use count_term_occurrences)
✅ Precisa de CONTEXTO + RANKING: busca semântica + ordenação

### COMBINE FERRAMENTAS quando:
✅ Pergunta tem MÉTRICA + CONTEÚDO: use semantic_search primeiro, depois filtre por métrica
✅ Pergunta tem CONTEXTO EXTERNO + LOCAL: use web_search + semantic_search
✅ Pergunta sobre ROBERTO SALLES (COMPLETA): debates (propostas) + notícias (ações) + semantic_search geral
✅ Precisa de CONTEXTO + RANKING: busca semântica + ordenação

## INSTRUÇÕES:
- Analise se a pergunta é sobre CONTEÚDO (use semantic_search), MÉTRICAS (use tools estruturadas) ou CONTEXTO EXTERNO (use web_search)
- Para perguntas sobre Roberto Salles, SEMPRE considere usar MÚLTIPLAS fontes: debates + notícias
- Para perguntas sobre POSICIONAMENTO/FALAS de Roberto Salles, PRIORIZE busca em debates com content_type_filter='debate'
- Você pode usar MÚLTIPLAS ferramentas em sequência
- Ao usar semantic_search, REFORMULE a query para termos mais específicos
- A LLM deve LER o campo "trecho" dos debates que contém as falas literais
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
        # Validação de perfil
        perfil_ok, perfil_msg = self.validar_perfil(profile_filter)
        if not perfil_ok:
            # Retorna ação especial para erro de perfil
            return [{
                "tool": "error",
                "params": {"message": perfil_msg}
            }]
        
        tools_desc = self._create_tools_description()
        
        planning_prompt = f"""{tools_desc}

## CONTEXTO:
Pergunta do usuário: "{user_question}"
{f'Perfil filtrado: {profile_filter}' if profile_filter else 'Sem filtro de perfil'}

## ⚠️ IMPORTANTE - PERFIS vs FONTES:
**PERFIS (Instagram - Posts atuais):**
- @dceuff (Diretório Central dos Estudantes)
- @reitor (Reitor ATUAL: Antônio Cláudio Nóbrega 2023-2025)
- @vicereitor (Vice-Reitor ATUAL: Fábio Barbosa Passos)

**FONTES AUXILIARES (NÃO são perfis):**
- **Notícias/Arquivo**: Para perguntas sobre ex-reitor Roberto Salles ou eventos históricos (2009-2018)
  - Ferramentas: search_news_by_person, get_news_articles, semantic_search com content_type_filter='news'
- **Debates Políticos**: Para perguntas sobre propostas, argumentos e posicionamento político de Roberto Salles
  - Ferramenta: semantic_search sem filtro ou genérico (busca em transcrições de debates)

## 📅 DATAS CRÍTICAS (NÃO CONFUNDA!):
- **Roberto de Souza Salles**: Reitor de **23 de novembro de 2006 até 18 de novembro de 2014**
  - Saiu do cargo em 2014, NÃO foi reeleito
  - Depois de 2014, foi apenas candidato em eleições (NÃO reitor)
- **Antônio Cláudio da Nóbrega**: Reitor de 2014-2018 (eleito em 2014)
- **Reitor ATUAL (2023-2025)**: Antônio Cláudio Nóbrega

INFORMAÇÃO CRÍTICA:
- Perguntas sobre "o que Roberto Salles fez" referem-se ao período 2006-2014
- Perguntas sobre "candidato Roberto Salles" referem-se a 2018 (quando disputou mas perdeu)
- Roberto Salles NUNCA foi reitor em 2015, 2016, 2017, 2018+ (alucinação comum)
- Perguntas sobre ele DEVEM buscar em NOTÍCIAS históricas
- NÃO confundir com o reitor atual (posts @reitor são de 2023-2025)

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
    "reasoning": "Ranking numérico por curtidas - métrica pura",
    "actions": [
        {{"tool": "get_top_posts_by_likes", "params": {{"limit": 5}}}}
    ]
}}

Pergunta: "Quais posts do DCE tiveram menos curtidas?"
{{
    "reasoning": "Ranking INVERSO - posts com MENOS curtidas, não mais",
    "actions": [
        {{"tool": "get_bottom_posts_by_likes", "params": {{"limit": 10, "profile": "dceuff"}}}}
    ]
}}

Pergunta: "Me fale sobre posts do HUAP"
{{
    "reasoning": "Pergunta sobre CONTEÚDO específico (HUAP), precisa busca semântica",
    "actions": [
        {{"tool": "semantic_search", "params": {{"query": "HUAP hospital universitário atendimento saúde", "n_results": 8}}}}
    ]
}}

Pergunta: "Qual foi a última aparição pública do reitor?"
{{
    "reasoning": "Pergunta sobre CONTEÚDO (aparição pública) com filtro temporal e de perfil. Usar busca semântica com query otimizada",
    "actions": [
        {{"tool": "semantic_search", "params": {{"query": "reitor aparição pública evento pronunciamento presença cerimônia", "n_results": 10, "profile": "reitor"}}}}
    ]
}}

Pergunta: "O que estão falando do reitor em 2024?"
{{
    "reasoning": "Pergunta sobre CONTEÚDO relacionado ao reitor. Busca semântica com filtro de perfil",
    "actions": [
        {{"tool": "semantic_search", "params": {{"query": "reitor UFF ações gestão decisões anúncios", "n_results": 10}}}}
    ]
}}

Pergunta: "O que o ex-reitor Roberto Salles achava das cotas?"
{{
    "reasoning": "Pergunta sobre OPINIÃO/POSICIONAMENTO do ex-reitor (2009-2018). Deve buscar em NOTÍCIAS, não em posts atuais. Combinar busca por pessoa + busca semântica APENAS EM NOTÍCIAS (content_type_filter='news')",
    "actions": [
        {{"tool": "search_news_by_person", "params": {{"person_name": "Roberto Salles", "limit": 15}}}},
        {{"tool": "semantic_search", "params": {{"query": "cotas ações afirmativas política racial reserva vagas lei educação", "n_results": 15, "content_type_filter": "news"}}}}
    ]
}}

Pergunta: "O que Roberto Sales fez quando era reitor?"
{{
    "reasoning": "Pergunta sobre AÇÕES do ex-reitor Roberto Sales (variação do nome Salles). Período histórico 2009-2018. Buscar em NOTÍCIAS",
    "actions": [
        {{"tool": "search_news_by_person", "params": {{"person_name": "Roberto Salles", "limit": 20}}}},
        {{"tool": "search_news_by_person", "params": {{"person_name": "Roberto Sales", "limit": 20}}}}
    ]
}}

Pergunta: "Compare o engajamento entre reitor e DCE"
{{
    "reasoning": "Comparação de MÉTRICAS estatísticas entre perfis",
    "actions": [
        {{"tool": "compare_profiles", "params": {{}}}}
    ]
}}

Pergunta: "Qual foi o post mais curtido recente do reitor?"
{{
    "reasoning": "Combina MÉTRICA (curtidas) + temporal (recente) + perfil. Ferramenta estruturada resolve",
    "actions": [
        {{"tool": "get_top_posts_by_likes", "params": {{"limit": 1, "profile": "reitor"}}}}
    ]
}}

Pergunta: "Posts sobre pesquisa científica que tiveram mais engajamento"
{{
    "reasoning": "Combina CONTEÚDO (pesquisa) + MÉTRICA (engajamento). Usar busca semântica primeiro",
    "actions": [
        {{"tool": "semantic_search", "params": {{"query": "pesquisa científica ciência laboratório estudo investigação", "n_results": 20}}}},
        {{"tool": "get_posts_by_engagement", "params": {{"limit": 5}}}}
    ]
}}

Pergunta: "O que o DCE publicou sobre greve na última semana?"
{{
    "reasoning": "CONTEÚDO (greve) + temporal (última semana) + perfil. Busca semântica com filtro temporal",
    "actions": [
        {{"tool": "get_recent_posts", "params": {{"days": 7, "limit": 30, "profile": "dceuff"}}}},
        {{"tool": "semantic_search", "params": {{"query": "greve paralisação mobilização protesto reivindicação", "n_results": 10, "profile": "dceuff"}}}}
    ]
}}

Pergunta: "Qual é a situação da educação no Brasil?"
{{
    "reasoning": "Pergunta vaga sobre tema amplo que requer contexto externo/nacional. Reformular para query específica de busca e usar web_search",
    "actions": [
        {{"tool": "web_search", "params": {{"query": "educação Brasil 2025 situação atualizado", "limit": 5}}}}
    ]
}}

Pergunta: "Quais são as notícias mais recentes sobre educação no Brasil?"
{{
    "reasoning": "Pergunta sobre contexto EXTERNO (notícias atuais do Brasil). Base local não é suficiente, usar web_search para contexto atualizado",
    "actions": [
        {{"tool": "web_search", "params": {{"query": "educação Brasil notícias 2025", "limit": 5}}}}
    ]
}}

Pergunta: "Como está a inflação? E o DCE falou sobre isso?"
{{
    "reasoning": "Pergunta com DUAS partes: 1) contexto externo (inflação) 2) conteúdo local. Combinar web_search + semantic_search",
    "actions": [
        {{"tool": "web_search", "params": {{"query": "inflação Brasil 2025 notícias economia", "limit": 3}}}},
        {{"tool": "semantic_search", "params": {{"query": "inflação economia custo de vida preços", "n_results": 10, "profile": "dceuff"}}}}
    ]
}}

🆕 Pergunta: "Quais eram as propostas de Roberto Salles para a educação?"
{{
    "reasoning": "Pergunta sobre PROPOSTAS DE CAMPANHA do ex-reitor. Deve buscar em DEBATES (propostas políticas) + NOTÍCIAS (implementação). Usar semantic_search genérico para debates e com filtro para notícias",
    "actions": [
        {{"tool": "semantic_search", "params": {{"query": "Roberto Salles educação ensino proposta plano universidade", "n_results": 15}}}},
        {{"tool": "search_news_by_person", "params": {{"person_name": "Roberto Salles", "limit": 10}}}}
    ]
}}

🆕 Pergunta: "O que Roberto Salles defendeu nos debates eleitorais?"
{{
    "reasoning": "Pergunta sobre DEBATES ELEITORAIS. Foco primário em transcrições de debates. Usar semantic_search genérico com termos relacionados a debates e propostas",
    "actions": [
        {{"tool": "semantic_search", "params": {{"query": "Roberto Salles debate eleitoral candidato propostas argumentos defende eleição", "n_results": 20}}}}
    ]
}}

🆕 Pergunta: "Qual era a visão política de Roberto Salles sobre pesquisa científica?"
{{
    "reasoning": "Pergunta sobre POSICIONAMENTO POLÍTICO detalhado. Combinar debates (visão política) + notícias (ações). Usar múltiplas buscas semânticas",
    "actions": [
        {{"tool": "semantic_search", "params": {{"query": "Roberto Salles pesquisa científica ciência tecnologia inovação desenvolvimento", "n_results": 15}}}},
        {{"tool": "search_news_by_person", "params": {{"person_name": "Roberto Salles", "limit": 10}}}},
        {{"tool": "semantic_search", "params": {{"query": "pesquisa ciência universidade UFF política científica", "n_results": 10, "content_type_filter": "news"}}}}
    ]
}}

IMPORTANTE: 
- Para CONTEÚDO/TEMA → semantic_search (sempre reformule query)
- Para MÉTRICAS/RANKING → ferramentas estruturadas
- Para CONTEXTO EXTERNO/ATUALIZADO → web_search (notícias recentes, eventos atuais)
- Para ROBERTO SALLES:
  - PROPOSTAS/DEBATES → semantic_search genérico (debates)
  - NOTÍCIAS/AÇÕES → search_news_by_person + semantic_search com content_type_filter='news'
  - ANÁLISE COMPLETA → combine ambas as fontes
- DICAS para web_search: transforme perguntas como "qual é a situação de X?" em "X Brasil 2025" ou "X notícias recentes"
- Retorne APENAS o JSON, nada mais!
"""

        try:
            # Chama o LLM para planejar (usa DeepSeek ou Ollama conforme config)
            model_to_use = DEEPSEEK_MODEL if DEFAULT_PROVIDER == 'deepseek' else self.planning_model
            response = llm_chat.chat(
                model=model_to_use,
                messages=[
                    {
                        'role': 'system',
                        'content': 'Você é um planejador especializado em análise de dados do Instagram. Retorne APENAS JSON válido, sem markdown ou texto adicional.'
                    },
                    {
                        'role': 'user',
                        'content': planning_prompt
                    }
                ]
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
            
            elif tool == 'get_bottom_posts_by_likes':
                return self.query_tools.get_bottom_posts_by_likes(
                    limit=params.get('limit', 10),
                    profile=params.get('profile')
                )
            
            elif tool == 'get_bottom_posts_by_comments':
                return self.query_tools.get_bottom_posts_by_comments(
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
            
            elif tool == 'count_term_occurrences':
                result = self.query_tools.count_term_occurrences(
                    term=params.get('term', ''),
                    profile=params.get('profile'),
                    case_sensitive=params.get('case_sensitive', False)
                )
                return [{'metadata': result, 'is_term_count': True}]
            
            elif tool == 'analyze_sentiment':
                result = self.query_tools.analyze_sentiment(
                    topic=params.get('topic', ''),
                    profile=params.get('profile'),
                    n_posts=params.get('n_posts', 20)
                )
                return [{'metadata': result, 'is_sentiment': True}]
            
            elif tool == 'get_news_articles':
                return self.query_tools.get_news_articles(
                    limit=params.get('limit', 10),
                    min_date=params.get('min_date'),
                    max_date=params.get('max_date'),
                    publisher=params.get('publisher')
                )
            
            elif tool == 'search_news_by_person':
                return self.query_tools.search_news_by_person(
                    person_name=params.get('person_name', ''),
                    limit=params.get('limit', 10)
                )
            
            elif tool == 'get_news_statistics':
                stats = self.query_tools.get_news_statistics()
                return [{'metadata': stats, 'is_news_stats': True}]
            
            elif tool == 'semantic_search':
                query = params.get('query', '')
                n_results = params.get('n_results', 5)
                profile = params.get('profile')
                content_type = params.get('content_type_filter')  # Novo parâmetro
                
                # Busca no embedding manager
                raw_results = self.embedding_manager.search(
                    query=query,
                    n_results=n_results,
                    profile_filter=profile,
                    content_type_filter=content_type  # Passa filtro de tipo
                )
                
                # Converte para formato padrão (lista de dicts)
                if not raw_results or 'ids' not in raw_results or not raw_results['ids']:
                    return []
                
                formatted_results = []
                for i in range(len(raw_results['ids'][0])):
                    formatted_results.append({
                        'id': raw_results['ids'][0][i],
                        'metadata': raw_results['metadatas'][0][i],
                        'document': raw_results['documents'][0][i],
                        'distance': raw_results['distances'][0][i] if 'distances' in raw_results else None
                    })
                
                return formatted_results
            
            elif tool == 'web_search':
                query = params.get('query', '')
                limit = params.get('limit', 5)
                
                # Executa busca na web
                web_results = self.query_tools.web_search(
                    query=query,
                    limit=limit
                )
                
                # Converte para formato padrão com 'profile' para compatibilidade
                formatted_results = []
                for i, result in enumerate(web_results):
                    formatted_results.append({
                        'id': f'web_{i}',
                        'metadata': {
                            'source': result.get('source', ''),
                            'date': result.get('date', ''),
                            'type': 'web_search',
                            'profile': result.get('profile', 'web_search')  # IMPORTANTE para evitar KeyError
                        },
                        'document': f"**{result.get('title', '')}**\n\n{result.get('body', '')}"
                    })
                
                return formatted_results
            
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
        
        # Verifica se é contagem de termo
        if results[0].get('is_term_count'):
            data = results[0]['metadata']
            text = f"## Contagem de Termo: '{data['term']}'\n"
            text += f"- Perfil(s): {data['profile']}\n"
            text += f"- Posts encontrados: {data['count']} de {data['total_posts']} ({data['percentage']}%)\n\n"
            
            # Se houver erro
            if data.get('error'):
                text += f"⚠️ Erro: {data['error']}\n"
                return text
            
            # Lista alguns posts que contêm o termo
            if data['matching_posts']:
                text += "### Exemplos de posts que mencionam o termo:\n\n"
                for i, post in enumerate(data['matching_posts'][:5], 1):
                    meta = post.get('metadata', {})
                    doc = post.get('document', '')
                    text += f"**Post {i}** (@{meta.get('profile', 'unknown')})\n"
                    text += f"- Curtidas: {meta.get('likesCount', 0)}, Comentários: {meta.get('commentsCount', 0)}\n"
                    text += f"- Data: {meta.get('timestamp', 'N/A')[:10]}\n"
                    text += f"- Link: {meta.get('url', 'N/A')}\n"
                    if doc:
                        # Mostra trecho com o termo
                        text += f"- Trecho: {doc[:250]}...\n"
                    text += "\n"
            
            return text
        
        # Verifica se é análise de sentimento
        if results[0].get('is_sentiment'):
            data = results[0]['metadata']
            text = f"## Análise de Sentimento: '{data['topic']}'\n"
            text += f"- Perfil(s): {data['profile']}\n"
            text += f"- Posts analisados: {data['total_posts']}\n\n"
            
            # Se houver erro
            if data.get('error'):
                text += f"⚠️ Erro: {data['error']}\n"
                return text
            
            # Resumo do sentimento
            text += f"### Resumo Geral:\n{data['sentiment_summary']}\n\n"
            
            # Distribuição de sentimentos
            text += "### Distribuição de Sentimentos:\n"
            text += f"- ✅ Positivos: {data['positive_count']} posts\n"
            text += f"- ❌ Negativos: {data['negative_count']} posts\n"
            text += f"- ⚪ Neutros: {data['neutral_count']} posts\n\n"
            
            # Aspectos positivos
            if data.get('positive_aspects'):
                text += "### Aspectos Positivos Identificados:\n"
                for aspect in data['positive_aspects']:
                    text += f"- {aspect}\n"
                text += "\n"
            
            # Aspectos negativos
            if data.get('negative_aspects'):
                text += "### Aspectos Negativos/Críticas:\n"
                for aspect in data['negative_aspects']:
                    text += f"- {aspect}\n"
                text += "\n"
            
            # Pontos-chave
            if data.get('key_points'):
                text += "### Pontos-Chave:\n"
                for point in data['key_points']:
                    text += f"- {point}\n"
                text += "\n"
            
            # Exemplos de posts
            examples = data.get('examples', {})
            if examples.get('positive'):
                text += "### Exemplos de Posts Positivos:\n"
                for i, post in enumerate(examples['positive'][:2], 1):
                    meta = post.get('metadata', {})
                    doc = post.get('document', '')[:200]
                    text += f"{i}. @{meta.get('profile')}: {doc}... [{meta.get('url')}]\n"
                text += "\n"
            
            if examples.get('negative'):
                text += "### Exemplos de Posts Negativos:\n"
                for i, post in enumerate(examples['negative'][:2], 1):
                    meta = post.get('metadata', {})
                    doc = post.get('document', '')[:200]
                    text += f"{i}. @{meta.get('profile')}: {doc}... [{meta.get('url')}]\n"
                text += "\n"
            
            return text
        
        # Verifica se é estatística de notícias
        if results[0].get('is_news_stats'):
            stats = results[0]['metadata']
            text = "## Estatísticas de Notícias:\n\n"
            text += f"- Total de notícias: {stats.get('total_news', 0)}\n"
            
            if stats.get('date_range'):
                dr = stats['date_range']
                text += f"- Período coberto: {dr.get('oldest', 'N/A')[:10]} até {dr.get('newest', 'N/A')[:10]}\n"
            
            text += "\n### Publishers/Veículos:\n"
            for pub in stats.get('publishers', [])[:10]:
                text += f"- {pub['name']}: {pub['count']} notícias\n"
            
            return text
        
        # Posts/notícias normais
        text = f"## Resultados de {tool_name}:\n\n"
        for i, post in enumerate(results[:10], 1):
            meta = post.get('metadata', {})
            doc = post.get('document', '')
            content_type = meta.get('content_type', 'instagram_post')
            
            # Formatação específica por tipo de conteúdo
            if content_type == 'news':
                # Formatação para notícias
                text += f"**Notícia {i}**\n"
                text += f"- Título: {meta.get('title', 'N/A')}\n"
                text += f"- Publisher: {meta.get('publisher_name', 'N/A')}\n"
                text += f"- Data: {meta.get('timestamp', 'N/A')[:10]}\n"
                text += f"- Link: {meta.get('url', 'N/A')}\n"
                
                # Para notícias, incluir MAIS conteúdo para o LLM ter contexto completo
                if meta.get('description'):
                    text += f"- Descrição: {meta['description'][:500]}...\n"
                if doc:
                    text += f"- Conteúdo: {doc[:800]}...\n"
            else:
                # Formatação para posts do Instagram
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
    
    def _clean_response(self, response: str) -> str:
        """
        Remove possíveis vazamentos de prompt ou instruções da resposta.
        Também detecta e marca alucinações de datas.
        
        Args:
            response: Resposta bruta do LLM
            
        Returns:
            Resposta limpa
        """
        import re
        
        # Remove seções de "Importante sobre Roberto Salles" que não devem estar na resposta
        # Remove bloco inteiro de "⚠️ Importante" se não foi perguntado sobre Roberto Salles
        pattern = r'\n⚠️\s+Importante sobre Roberto Salles.*?(?=\n##|\n[❌✅]|$)'
        response = re.sub(pattern, '', response, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove "Dados exclusivamente baseados" se não é contexto relevante
        pattern = r'\n✅\s+Dados exclusivamente baseados.*?(?=\n##|\n[❌✅]|$)'
        response = re.sub(pattern, '', response, flags=re.DOTALL)
        
        # VALIDADOR DE DATAS: Detecta erros temporais
        date_errors = [
            (r'Roberto Salles.*?reitor.*?2012.*?2018', 'Roberto Salles foi reitor de 2006-2014, NÃO 2012-2018'),
            (r'Roberto Salles.*?reitor.*?2015.*?2019', 'Roberto Salles foi reitor de 2006-2014, NÃO 2015-2019'),
            (r'Salles.*?reitor.*?eleito em 2015', 'Roberto Salles foi reitor de 2006-2014. Em 2014 saiu do cargo'),
            (r'Salles.*?reeleito em 2018', 'Roberto Salles não foi reeleito em 2018 - seu mandato terminou em 2014'),
        ]
        
        has_date_error = False
        for pattern, correction in date_errors:
            if re.search(pattern, response, re.IGNORECASE):
                has_date_error = True
                print(f"⚠️ DETECÇÃO: Alucinação de data encontrada - {correction}")
                # Remove linhas que contêm o erro
                response = re.sub(pattern, f'[CORRIGIDO: {correction}]', response, flags=re.IGNORECASE)
        
        # Remove linhas de diretrizes que não devem estar na resposta final
        lines = response.split('\n')
        filtered_lines = []
        for line in lines:
            # Pula linhas que parecem ser instruções vazadas
            if any(x in line.lower() for x in ['diretrizes:', 'sua tarefa:', 'regra importante', 'não invente']):
                continue
            filtered_lines.append(line)
        
        response = '\n'.join(filtered_lines)
        
        # Remove múltiplas linhas em branco consecutivas
        response = re.sub(r'\n\n\n+', '\n\n', response)
        
        # Se encontrou erro de data, adiciona aviso ao final
        if has_date_error:
            response += (
                "\n\n⚠️ **AVISO DE CORRIGIR ALUCINAÇÃO**:\n"
                "A resposta acima foi corrigida automaticamente por conter erros de datas.\n"
                "**DATA CORRETA**: Roberto de Souza Salles foi reitor da UFF de **23 de novembro de 2006 até 18 de novembro de 2014**.\n"
                "Qualquer menção a outros períodos contém alucinação do modelo."
            )
        
        return response.strip()
    
    def _validate_source_relevance(
        self, 
        user_question: str, 
        all_results: List[Tuple[str, List[Dict[str, Any]]]]
    ) -> Tuple[bool, Optional[str]]:
        """
        Valida se as fontes recuperadas são REALMENTE relevantes para a pergunta.
        Aceita cenários com pessoas reais nos dados, rejeita apenas fictícios.
        
        Args:
            user_question: Pergunta do usuário
            all_results: Resultados retornados
            
        Returns:
            Tupla (é_válido, warning_message ou None)
        """
        question_lower = user_question.lower()
        
        # Pessoas REAIS mencionadas nos dados
        real_people_patterns = [
            (r'fabio\s+(?:barbosa\s+)?passos?', 'Fábio Barbosa Passos', 'vice-reitor'),
            (r'fábio\s+(?:barbosa\s+)?passos?', 'Fábio Barbosa Passos', 'vice-reitor'),
            (r'roberto\s+salles?', 'Roberto Salles', 'ex-reitor 2009-2018'),
            (r'antonio\s+claudio', 'Antonio Claudio Nóbrega', 'reitor atual'),
        ]
        
        # Detecta menção a pessoas reais
        import re
        mentioned_people = []
        for pattern, name, role in real_people_patterns:
            if re.search(pattern, question_lower):
                mentioned_people.append((name, role))
        
        # Se menciona pessoas reais, é um cenário válido
        if mentioned_people:
            # Verifica se recuperou dados sobre essas pessoas
            all_context = ""
            for tool_name, results in all_results:
                for result in results:
                    if isinstance(result, dict):
                        all_context += str(result).lower()
            
            # Se recuperou dados relevantes, é válido
            if len(all_results) > 0 and all_context.strip():
                return True, None
            
            # Se não encontrou dados sobre pessoas reais, indica falta de informação
            people_str = " e ".join([f"{name} ({role})" for name, role in mentioned_people])
            return False, (
                f"⚠️ **Sem informações suficientes**\n\n"
                f"A pergunta menciona: {people_str}\n\n"
                f"Porém, os dados indexados não contêm informações adequadas para responder sobre "
                f"esse cenário específico.\n\n"
                f"Tente reformular a pergunta com temas ou contextos disponíveis nos dados."
            )
        
        return True, None
    
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
        # Valida relevância das fontes e detecta cenários fictícios
        is_valid, simulation_warning = self._validate_source_relevance(user_question, all_results)
        
        if not is_valid:
            return "❌ Não encontrei informações suficientes para responder sua pergunta com os dados disponíveis."
            return hallucination_warning
        
        # Monta contexto com todos os resultados
        context = ""
        for tool_name, results in all_results:
            context += self._format_results_for_llm(results, tool_name)
            context += "\n---\n\n"
        
        # Atualiza o prompt de síntese com instruções críticas
        synthesis_prompt = f"""Você é um assistente especializado da Universidade Federal Fluminense (UFF).

Pergunta do usuário: "{user_question}"

Dados recuperados:
{context}

## INSTRUÇÕES CRÍTICAS:

1. **CITE AS FONTES CORRETAMENTE**:
   - Para debates: "Segundo Roberto Salles no [fonte do debate], ele afirmou: '[trecho da fala]'"
   - Para notícias: "De acordo com [publisher] em [data]..."
   - Para posts: "Em post de @[profile] em [data]..."

2. **USE AS FALAS LITERAIS DOS DEBATES**:
   - O campo "trecho" contém as FALAS LITERAIS de Roberto Salles
   - Cite textualmente quando relevante (ex: "Roberto Salles afirmou: 'Nós vamos retornar as 30 horas'")
   - Identifique o contexto do debate (1o_debate, 2o_debate, etc.)

3. **ESTRUTURE A RESPOSTA**:
   - Responda diretamente à pergunta
   - Use citações literais dos debates quando disponível
   - Contextualize com informações de notícias se houver
   - Seja preciso sobre datas e eventos

4. **EVITE**:
   - Inventar informações não presentes nos dados
   - Misturar contextos temporais (ex: não confunda ações de 2009-2018 com 2023-2025)
   - Atribuir falas de uma fonte a outra

Responda em português brasileiro de forma clara e objetiva.
"""

        try:
            # Usa DeepSeek se configurado, senão Ollama
            if DEFAULT_PROVIDER == 'deepseek':
                model_to_use = DEEPSEEK_MODEL
                response = llm_chat.chat(
                    model=model_to_use,
                    messages=[
                        {
                            'role': 'system',
                            'content': '''Você é um assistente especializado em análise de posts do Instagram da UFF.

INFORMAÇÕES CRÍTICAS - DATAS EXATAS:
- Reitor ATUAL (2023-2025): Antônio Cláudio Nóbrega
- Ex-reitor (23 de novembro de 2006 até 18 de novembro de 2014): Roberto de Souza Salles
- NÃO confunda: Roberto Salles saiu do cargo em 2014, NÃO foi reitor de 2015 em diante
- Em 2018, Salles foi CANDIDATO mas perdeu a eleição (não era reitor)

REGRA IMPORTANTE: Se mencionar Roberto Salles, SEMPRE:
1. Use período CORRETO: 2006-2014 (quando foi reitor)
2. Se for sobre 2018: mencione que foi CANDIDATO, não reitor
3. Indique que ele não tem posts atuais no Instagram
4. Use dados apenas de arquivo histórico

Responda de forma clara, objetiva e bem formatada usando APENAS os dados fornecidos.'''
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
                # Limpa a resposta de possíveis vazamentos de prompt
                response_text = response['message']['content']
                response_text = self._clean_response(response_text)
                
                # Adiciona disclaimer se for simulação com contexto fictício
                if simulation_warning:
                    response_text += simulation_warning
                
                return response_text
        
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
