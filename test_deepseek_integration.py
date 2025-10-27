#!/usr/bin/env python3
"""
Script de teste para validar integração com DeepSeek.
"""

import sys
sys.path.insert(0, '/home/marcus/projects/ping')

from config import DEFAULT_PROVIDER, DEEPSEEK_MODEL, OLLAMA_GENERATION_MODEL
import llm_chat

print("=" * 60)
print("🧪 TESTE DE INTEGRAÇÃO DEEPSEEK")
print("=" * 60)

# 1. Verificar configuração
print(f"\n📋 Configuração:")
print(f"  Provider padrão: {DEFAULT_PROVIDER}")
print(f"  Modelo DeepSeek: {DEEPSEEK_MODEL}")
print(f"  Modelo Ollama: {OLLAMA_GENERATION_MODEL}")

# 2. Testar chamada simples com DeepSeek
print(f"\n🔄 Testando chamada ao DeepSeek...")
try:
    response = llm_chat.chat(
        model=DEEPSEEK_MODEL,
        messages=[{
            'role': 'user',
            'content': 'Quem foi Roberto de Souza Salles? Responda em poucas linhas.'
        }]
    )
    
    print(f"✅ Resposta do DeepSeek:")
    print(f"  {response['message']['content'][:200]}...")
    
except Exception as e:
    print(f"❌ Erro ao chamar DeepSeek: {e}")
    sys.exit(1)

# 3. Testar com agent_system
print(f"\n🔄 Testando agent_system com query simples...")
try:
    from agent_system import InstagramRAGApp
    
    app = InstagramRAGApp(
        embedding_model="mxbai-embed-large",
        generation_model=OLLAMA_GENERATION_MODEL,
        use_agent=True
    )
    
    print(f"✅ InstagramRAGApp inicializado com provider: {DEFAULT_PROVIDER}")
    
    # Query simples
    print(f"\n🔄 Executando query: 'Quem é o reitor atual?'")
    response, sources = app.query("Quem é o reitor atual?")
    
    print(f"✅ Resposta recebida ({len(response)} caracteres)")
    print(f"   {response[:150]}...")
    print(f"\n📊 Fontes usadas: {len(sources)}")
    
except Exception as e:
    print(f"❌ Erro ao testar agent_system: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("✅ TODOS OS TESTES PASSARAM!")
print("=" * 60)
