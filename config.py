"""
Configurações de modelos de IA - DeepSeek e Ollama
"""

import os
from typing import Optional

# ============================================
# CONFIGURAÇÃO: Qual modelo usar?
# ============================================

# Define o modelo padrão: 'deepseek' ou 'ollama'
DEFAULT_PROVIDER = os.getenv('AI_PROVIDER', 'deepseek')

# DeepSeek API
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY', 'sk-70edfcda9e0e49e3829e2acb3b9f5bd6')
DEEPSEEK_API_BASE = os.getenv('DEEPSEEK_API_BASE', 'https://api.deepseek.com/v1')
DEEPSEEK_MODEL = os.getenv('DEEPSEEK_MODEL', 'deepseek-chat')

# Ollama (local)
OLLAMA_API_BASE = os.getenv('OLLAMA_API_BASE', 'http://localhost:11434')
OLLAMA_EMBEDDING_MODEL = os.getenv('OLLAMA_EMBEDDING_MODEL', 'mxbai-embed-large')
OLLAMA_GENERATION_MODEL = os.getenv('OLLAMA_GENERATION_MODEL', 'qwen3:30b')

print(f"✓ AI Provider: {DEFAULT_PROVIDER.upper()}")
if DEFAULT_PROVIDER == 'deepseek':
    print(f"  - API Base: {DEEPSEEK_API_BASE}")
    print(f"  - Model: {DEEPSEEK_MODEL}")
else:
    print(f"  - API Base: {OLLAMA_API_BASE}")
    print(f"  - Generation Model: {OLLAMA_GENERATION_MODEL}")
