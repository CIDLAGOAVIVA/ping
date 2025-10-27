#!/usr/bin/env python3
"""
Teste para verificar rejeição de candidatos fictícios
"""
import sys
sys.path.insert(0, '/home/marcus/projects/ping')

from agent_system import RAGAgent

print("=" * 70)
print("TESTE: Rejeição de Candidato Fictício")
print("=" * 70)

agent = RAGAgent()

# Teste: Pergunta com candidato fictício
print("\n❓ Query: 'Que estratégia o Fabio Passos poderia adotar...")
print("          para enfrentar o Roberto Salles numa eleição?'")
print("-" * 70)

response, posts = agent.query(
    "Que estratégia o Fabio Passos poderia adotar para enfrentar o Roberto Salles numa eleição para reitoria em debates?"
)

print("\n✅ RESPOSTA DO SISTEMA:")
print(response)

# Verificações
has_rejection = "Não posso responder" in response or "Não é um candidato" in response
has_fabio_analysis = "Fabio Passos pode:" in response.lower() or "estratégia para fabio" in response.lower()

print(f"\n\n🔍 ANÁLISE:")
print(f"  ✅ Sistema rejeitou candidato fictício? {has_rejection}")
print(f"  ❌ Sistema fabricou análise de Fabio? {has_fabio_analysis}")

if has_rejection and not has_fabio_analysis:
    print("\n✅ TESTE PASSOU! Sistema corretamente rejeita candidatos fictícios.")
else:
    print("\n⚠️ TESTE FALHOU!")

print("\n" + "=" * 70)
