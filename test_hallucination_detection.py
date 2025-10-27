#!/usr/bin/env python3
"""
Teste para verificar se alucinações são detectadas
"""
import sys
sys.path.insert(0, '/home/marcus/projects/ping')

from agent_system import RAGAgent

print("=" * 70)
print("TESTE: Detecção de Alucinações - Fabio Passos vs Roberto Salles")
print("=" * 70)

agent = RAGAgent()

# Teste: Pergunta que deve detectar alucinação
print("\n❓ Query: 'Que estratégia o Fabio Passos poderia adotar para enfrentar")
print("           o Roberto Salles numa eleição para reitoria em debates?'")
print("-" * 70)

response, posts = agent.query(
    "Que estratégia o Fabio Passos poderia adotar para enfrentar o Roberto Salles numa eleição para reitoria em debates?"
)

print("\n✅ RESPOSTA DO SISTEMA:")
print(response)

# Verificações
has_warning = "Aviso importante" in response or "⚠️" in response
is_fabricated = "Fabio Passos pode:" in response.lower()

print(f"\n\n🔍 ANÁLISE:")
print(f"  ✅ Detectou alucinação (aviso)? {has_warning}")
print(f"  ❌ Fabricou resposta? {is_fabricated}")

if has_warning and not is_fabricated:
    print("\n✅ TESTE PASSOU! Sistema alertou sobre dados insuficientes.")
else:
    print("\n⚠️ TESTE FALHOU! Sistema ainda está alucinando.")

print("\n" + "=" * 70)
