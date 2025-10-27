#!/usr/bin/env python3
"""
Script de Homologação do Sistema RAG Agent.

Testa cenários diversos incluindo:
- Perguntas bem formadas
- Perguntas ambíguas
- Perguntas com informações incorretas
- Perguntas complexas
- Edge cases
"""

from agent_system import RAGAgent
from datetime import datetime
import json
from typing import Dict, List, Any
import time


class HomologacaoRAG:
    """Classe para testes de homologação do sistema RAG."""
    
    def __init__(self):
        """Inicializa o sistema de teste."""
        print("🚀 Inicializando sistema de homologação...")
        self.agent = RAGAgent(
            embedding_model="mxbai-embed-large",
            generation_model="qwen3:30b"
        )
        self.resultados = []
        
    def cenarios_teste(self) -> List[Dict[str, Any]]:
        """Define cenários de teste."""
        return [
            # ========== CATEGORIA 1: Perguntas Básicas (devem funcionar bem) ==========
            {
                "categoria": "Básico - Identidade",
                "pergunta": "Quem é o reitor da UFF?",
                "esperado": "Antonio Claudio Nobrega",
                "perfil_filtro": None,
                "sucesso_esperado": True
            },
            {
                "categoria": "Básico - Identidade",
                "pergunta": "Quem é o vice-reitor?",
                "esperado": "Informação sobre vice-reitor",
                "perfil_filtro": None,
                "sucesso_esperado": True
            },
            {
                "categoria": "Básico - Busca Simples",
                "pergunta": "Me fale sobre o HUAP",
                "esperado": "Informações sobre hospital universitário",
                "perfil_filtro": None,
                "sucesso_esperado": True
            },
            {
                "categoria": "Básico - Ranking",
                "pergunta": "Quais foram os 5 posts mais curtidos?",
                "esperado": "Lista com 5 posts ordenados por curtidas",
                "perfil_filtro": None,
                "sucesso_esperado": True
            },
            
            # ========== CATEGORIA 2: Perguntas Ambíguas ==========
            {
                "categoria": "Ambígua - Temporal",
                "pergunta": "O que aconteceu recentemente?",
                "esperado": "Posts recentes gerais",
                "perfil_filtro": None,
                "sucesso_esperado": True
            },
            {
                "categoria": "Ambígua - Vaga",
                "pergunta": "Me conte sobre a universidade",
                "esperado": "Resposta geral sobre UFF",
                "perfil_filtro": None,
                "sucesso_esperado": True
            },
            {
                "categoria": "Ambígua - Pronome",
                "pergunta": "O que ele postou ontem?",
                "esperado": "Deve pedir esclarecimento ou assumir contexto",
                "perfil_filtro": None,
                "sucesso_esperado": False  # Deve falhar ou pedir esclarecimento
            },
            
            # ========== CATEGORIA 3: Informações Incorretas ==========
            {
                "categoria": "Incorreta - Nome Errado",
                "pergunta": "Quais posts da Maria Silva sobre pesquisa?",
                "esperado": "Deve indicar que não encontrou ou buscar semanticamente",
                "perfil_filtro": None,
                "sucesso_esperado": False
            },
            {
                "categoria": "Incorreta - Perfil Inexistente",
                "pergunta": "Me mostre posts do @naousto",
                "esperado": "Deve indicar que perfil não existe",
                "perfil_filtro": None,
                "sucesso_esperado": False
            },
            {
                "categoria": "Incorreta - Ex-reitor confundido",
                "pergunta": "O que Roberto Salles postou essa semana?",
                "esperado": "Deve esclarecer que Roberto Salles é ex-reitor",
                "perfil_filtro": None,
                "sucesso_esperado": False
            },
            {
                "categoria": "Incorreta - Data Impossível",
                "pergunta": "Me mostre posts de janeiro de 2026",
                "esperado": "Deve indicar que não há posts futuros",
                "perfil_filtro": None,
                "sucesso_esperado": False
            },
            
            # ========== CATEGORIA 4: Perguntas Complexas ==========
            {
                "categoria": "Complexa - Múltiplos Filtros",
                "pergunta": "Quais posts do DCE sobre cotas que tiveram mais de 100 curtidas?",
                "esperado": "Posts filtrados por perfil, tema e métrica",
                "perfil_filtro": "dceuff",
                "sucesso_esperado": True
            },
            {
                "categoria": "Complexa - Comparação",
                "pergunta": "Quem posta mais: reitor ou DCE?",
                "esperado": "Comparação estatística entre perfis",
                "perfil_filtro": None,
                "sucesso_esperado": True
            },
            {
                "categoria": "Complexa - Temporal + Semântica",
                "pergunta": "O que foi dito sobre sustentabilidade nos últimos 6 meses?",
                "esperado": "Posts sobre sustentabilidade recentes",
                "perfil_filtro": None,
                "sucesso_esperado": True
            },
            {
                "categoria": "Complexa - Agregação",
                "pergunta": "Qual perfil tem melhor engajamento médio por post?",
                "esperado": "Cálculo e comparação de médias",
                "perfil_filtro": None,
                "sucesso_esperado": True
            },
            
            # ========== CATEGORIA 5: Edge Cases ==========
            {
                "categoria": "Edge Case - Pergunta Vazia",
                "pergunta": "",
                "esperado": "Deve rejeitar ou pedir pergunta válida",
                "perfil_filtro": None,
                "sucesso_esperado": False
            },
            {
                "categoria": "Edge Case - Só Emoji",
                "pergunta": "😀🎓📚",
                "esperado": "Deve lidar com entrada não textual",
                "perfil_filtro": None,
                "sucesso_esperado": False
            },
            {
                "categoria": "Edge Case - Pergunta Muito Longa",
                "pergunta": "Eu gostaria de saber " + "muito " * 50 + "sobre os posts do reitor",
                "esperado": "Deve processar apesar do tamanho",
                "perfil_filtro": None,
                "sucesso_esperado": True
            },
            {
                "categoria": "Edge Case - Caracteres Especiais",
                "pergunta": "Posts sobre @#$%&*() ???",
                "esperado": "Deve lidar com caracteres especiais",
                "perfil_filtro": None,
                "sucesso_esperado": False
            },
            
            # ========== CATEGORIA 6: Perguntas Fora do Escopo ==========
            {
                "categoria": "Fora de Escopo - Matemática",
                "pergunta": "Quanto é 2 + 2?",
                "esperado": "Deve indicar que está fora do escopo",
                "perfil_filtro": None,
                "sucesso_esperado": False
            },
            {
                "categoria": "Fora de Escopo - Outras Universidades",
                "pergunta": "Quem é o reitor da USP?",
                "esperado": "Deve indicar que só tem dados da UFF",
                "perfil_filtro": None,
                "sucesso_esperado": False
            },
            {
                "categoria": "Fora de Escopo - Política Geral",
                "pergunta": "Quem vai ganhar as eleições?",
                "esperado": "Deve indicar que está fora do escopo",
                "perfil_filtro": None,
                "sucesso_esperado": False
            },
            
            # ========== CATEGORIA 7: Perguntas com Negação ==========
            {
                "categoria": "Negação",
                "pergunta": "Quais posts NÃO falam sobre saúde?",
                "esperado": "Deve lidar com negação (difícil)",
                "perfil_filtro": None,
                "sucesso_esperado": False  # Negação é complexa para RAG
            },
            {
                "categoria": "Negação - Métrica",
                "pergunta": "Quais posts tiveram menos de 10 curtidas?",
                "esperado": "Posts com baixo engajamento",
                "perfil_filtro": None,
                "sucesso_esperado": True
            },
            
            # ========== CATEGORIA 8: Perguntas Meta ==========
            {
                "categoria": "Meta - Sistema",
                "pergunta": "Quantos posts você tem indexados?",
                "esperado": "Estatísticas do sistema",
                "perfil_filtro": None,
                "sucesso_esperado": True
            },
            {
                "categoria": "Meta - Capacidades",
                "pergunta": "O que você pode fazer?",
                "esperado": "Descrição de capacidades",
                "perfil_filtro": None,
                "sucesso_esperado": True
            },
            
            # ========== CATEGORIA 9: Perguntas Sensíveis ==========
            {
                "categoria": "Sensível - Opinião",
                "pergunta": "O reitor é bom ou ruim?",
                "esperado": "Deve ser neutro, mostrar apenas dados factuais",
                "perfil_filtro": None,
                "sucesso_esperado": True
            },
            {
                "categoria": "Sensível - Polêmica",
                "pergunta": "Houve algum escândalo na UFF?",
                "esperado": "Deve buscar semanticamente se houver dados",
                "perfil_filtro": None,
                "sucesso_esperado": True
            },
        ]
    
    def executar_teste(self, cenario: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executa um cenário de teste.
        
        Args:
            cenario: Dicionário com dados do teste
            
        Returns:
            Resultado do teste
        """
        print(f"\n{'='*80}")
        print(f"🧪 TESTE: {cenario['categoria']}")
        print(f"❓ Pergunta: {cenario['pergunta'][:100]}{'...' if len(cenario['pergunta']) > 100 else ''}")
        print(f"{'='*80}")
        
        resultado = {
            "categoria": cenario['categoria'],
            "pergunta": cenario['pergunta'],
            "esperado": cenario['esperado'],
            "sucesso_esperado": cenario['sucesso_esperado'],
            "timestamp": datetime.now().isoformat(),
        }
        
        try:
            inicio = time.time()
            
            # Executa query
            resposta, posts = self.agent.query(
                cenario['pergunta'],
                profile_filter=cenario['perfil_filtro'],
                stream=False
            )
            
            tempo_execucao = time.time() - inicio
            
            resultado.update({
                "status": "executado",
                "resposta": resposta,
                "num_posts": len(posts),
                "tempo_execucao": round(tempo_execucao, 2),
                "erro": None
            })
            
            # Mostra resultado resumido
            print(f"\n✅ Executado em {tempo_execucao:.2f}s")
            print(f"📊 Posts recuperados: {len(posts)}")
            print(f"📝 Resposta (primeiras linhas):")
            print("-" * 80)
            linhas_resposta = resposta.split('\n')[:5]
            print('\n'.join(linhas_resposta))
            if len(resposta.split('\n')) > 5:
                print("...")
            
        except Exception as e:
            resultado.update({
                "status": "erro",
                "resposta": None,
                "num_posts": 0,
                "tempo_execucao": 0,
                "erro": str(e)
            })
            
            print(f"\n❌ ERRO: {e}")
        
        return resultado
    
    def avaliar_resultado(self, resultado: Dict[str, Any]) -> Dict[str, Any]:
        """
        Avalia se o resultado está conforme esperado.
        
        Args:
            resultado: Resultado do teste
            
        Returns:
            Avaliação do resultado
        """
        avaliacao = {
            "passou": False,
            "observacoes": []
        }
        
        # Se era esperado sucesso
        if resultado['sucesso_esperado']:
            if resultado['status'] == 'executado' and resultado['num_posts'] > 0:
                avaliacao['passou'] = True
                avaliacao['observacoes'].append("✅ Retornou resultados conforme esperado")
            elif resultado['status'] == 'executado' and resultado['num_posts'] == 0:
                avaliacao['observacoes'].append("⚠️ Executou mas não retornou posts")
            else:
                avaliacao['observacoes'].append("❌ Falhou quando deveria funcionar")
        
        # Se era esperado falha/limitação
        else:
            if resultado['status'] == 'erro':
                avaliacao['passou'] = True
                avaliacao['observacoes'].append("✅ Falhou conforme esperado (limitação conhecida)")
            elif resultado['status'] == 'executado':
                # Verifica se a resposta indica limitação
                resposta_lower = resultado['resposta'].lower() if resultado['resposta'] else ""
                indicadores_limitacao = [
                    'não encontr',
                    'não há',
                    'não tenho',
                    'não posso',
                    'fora do escopo',
                    'não disponível',
                    'dados insuficientes'
                ]
                
                if any(ind in resposta_lower for ind in indicadores_limitacao):
                    avaliacao['passou'] = True
                    avaliacao['observacoes'].append("✅ Reconheceu limitação adequadamente")
                else:
                    avaliacao['observacoes'].append("⚠️ Tentou responder algo que não deveria")
        
        # Avaliações gerais
        if resultado['status'] == 'executado':
            if resultado['tempo_execucao'] > 30:
                avaliacao['observacoes'].append(f"⚠️ Tempo alto: {resultado['tempo_execucao']}s")
            
            if resultado['resposta'] and len(resultado['resposta']) < 50:
                avaliacao['observacoes'].append("⚠️ Resposta muito curta")
        
        return avaliacao
    
    def executar_homologacao(self, salvar_relatorio: bool = True):
        """
        Executa bateria completa de testes.
        
        Args:
            salvar_relatorio: Se deve salvar relatório em JSON
        """
        print("\n" + "="*80)
        print("🧪 INICIANDO HOMOLOGAÇÃO DO SISTEMA RAG")
        print("="*80)
        
        cenarios = self.cenarios_teste()
        print(f"\n📋 Total de cenários de teste: {len(cenarios)}")
        
        # Agrupa por categoria
        categorias = {}
        for c in cenarios:
            cat = c['categoria'].split(' - ')[0]
            categorias[cat] = categorias.get(cat, 0) + 1
        
        print("\n📊 Testes por categoria:")
        for cat, count in sorted(categorias.items()):
            print(f"   • {cat}: {count} teste(s)")
        
        input("\n⏸️  Pressione ENTER para iniciar os testes...")
        
        # Executa testes
        for i, cenario in enumerate(cenarios, 1):
            print(f"\n\n{'#'*80}")
            print(f"# TESTE {i}/{len(cenarios)}")
            print(f"{'#'*80}")
            
            resultado = self.executar_teste(cenario)
            avaliacao = self.avaliar_resultado(resultado)
            
            resultado['avaliacao'] = avaliacao
            self.resultados.append(resultado)
            
            print(f"\n🎯 Avaliação: {'✅ PASSOU' if avaliacao['passou'] else '❌ FALHOU'}")
            for obs in avaliacao['observacoes']:
                print(f"   {obs}")
            
            # Pequena pausa entre testes
            if i < len(cenarios):
                time.sleep(2)
        
        # Gera relatório
        self.gerar_relatorio(salvar_relatorio)
    
    def gerar_relatorio(self, salvar: bool = True):
        """
        Gera relatório final da homologação.
        
        Args:
            salvar: Se deve salvar em arquivo
        """
        print("\n\n" + "="*80)
        print("📊 RELATÓRIO FINAL DE HOMOLOGAÇÃO")
        print("="*80)
        
        total = len(self.resultados)
        executados = sum(1 for r in self.resultados if r['status'] == 'executado')
        erros = sum(1 for r in self.resultados if r['status'] == 'erro')
        passou = sum(1 for r in self.resultados if r['avaliacao']['passou'])
        
        print(f"\n📈 Resumo Geral:")
        print(f"   • Total de testes: {total}")
        print(f"   • Executados: {executados} ({executados/total*100:.1f}%)")
        print(f"   • Erros: {erros} ({erros/total*100:.1f}%)")
        print(f"   • Passou na avaliação: {passou} ({passou/total*100:.1f}%)")
        
        # Agrupa por categoria
        print(f"\n📊 Resultados por Categoria:")
        categorias = {}
        for r in self.resultados:
            cat = r['categoria'].split(' - ')[0]
            if cat not in categorias:
                categorias[cat] = {'total': 0, 'passou': 0}
            categorias[cat]['total'] += 1
            if r['avaliacao']['passou']:
                categorias[cat]['passou'] += 1
        
        for cat in sorted(categorias.keys()):
            stats = categorias[cat]
            pct = stats['passou'] / stats['total'] * 100
            status = "✅" if pct >= 70 else "⚠️" if pct >= 50 else "❌"
            print(f"   {status} {cat}: {stats['passou']}/{stats['total']} ({pct:.1f}%)")
        
        # Casos problemáticos
        problemas = [r for r in self.resultados if not r['avaliacao']['passou']]
        if problemas:
            print(f"\n⚠️ Casos que Precisam de Atenção ({len(problemas)}):")
            for p in problemas[:10]:  # Mostra até 10
                print(f"\n   • {p['categoria']}")
                print(f"     Pergunta: {p['pergunta'][:80]}...")
                print(f"     Motivo: {', '.join(p['avaliacao']['observacoes'])}")
        
        # Performance
        tempos = [r['tempo_execucao'] for r in self.resultados if r['status'] == 'executado']
        if tempos:
            print(f"\n⏱️ Performance:")
            print(f"   • Tempo médio: {sum(tempos)/len(tempos):.2f}s")
            print(f"   • Tempo mínimo: {min(tempos):.2f}s")
            print(f"   • Tempo máximo: {max(tempos):.2f}s")
        
        # Salva relatório
        if salvar:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"homologacao_relatorio_{timestamp}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump({
                    'timestamp': timestamp,
                    'resumo': {
                        'total': total,
                        'executados': executados,
                        'erros': erros,
                        'passou': passou,
                        'taxa_sucesso': round(passou/total*100, 2)
                    },
                    'por_categoria': categorias,
                    'resultados_detalhados': self.resultados
                }, f, indent=2, ensure_ascii=False)
            
            print(f"\n💾 Relatório detalhado salvo em: {filename}")
        
        print("\n" + "="*80)
        print("✅ HOMOLOGAÇÃO CONCLUÍDA!")
        print("="*80)


def main():
    """Função principal."""
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║                  SISTEMA DE HOMOLOGAÇÃO - RAG AGENT UFF                      ║
║                                                                              ║
║  Este script testa o sistema com diversos cenários incluindo:               ║
║  • Perguntas bem formadas                                                    ║
║  • Perguntas ambíguas                                                        ║
║  • Informações incorretas                                                    ║
║  • Edge cases                                                                ║
║  • Perguntas fora do escopo                                                  ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)
    
    homologacao = HomologacaoRAG()
    homologacao.executar_homologacao(salvar_relatorio=True)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Homologação interrompida pelo usuário.")
    except Exception as e:
        print(f"\n\n❌ Erro durante homologação: {e}")
        import traceback
        traceback.print_exc()
