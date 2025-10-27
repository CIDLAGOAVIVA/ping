#!/usr/bin/env python3
"""
Teste para verificar se o LLM não confunde notícias com perfil
"""
import sys
sys.path.insert(0, '/home/marcus/projects/ping')

from agent_system import RAGAgent

print("=" * 60)
print("TESTE: Notícias NÃO é um perfil")
print("=" * 60)

agent = RAGAgent()

# Teste: Comparar perfis - não deve mencionar notícias como perfil
print("\n\n❓ Query: 'Comparar perfis'")
print("-" * 60)

response, posts = agent.query("Comparar perfis")

print("\n✅ RESPOSTA (primeiras 500 chars):")
print(response[:500])

# Verificações
has_noticias_profile = "@noticias" in response or "noticias (Notícias" in response
has_unwanted_aviso = "⚠️ Importante sobre Roberto Salles" in response

print(f"\n\n🔍 VERIFICAÇÕES:")
print(f"  ❌ '@noticias' mencionado como perfil? {has_noticias_profile}")
print(f"  ❌ Aviso sobre Roberto Salles na resposta? {has_unwanted_aviso}")

if not has_noticias_profile and not has_unwanted_aviso:
    print("\n✅ TESTE PASSOU! Notícias não é confundido com perfil.")
else:
    print("\n⚠️ TESTE FALHOU! Ainda há problemas.")

print("\n" + "=" * 60)
