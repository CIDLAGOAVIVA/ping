"""
Wrapper para chamar LLMs - suporta DeepSeek e Ollama
"""

from typing import Optional, List, Dict, Any, Union, Generator
import os
from config import DEFAULT_PROVIDER, DEEPSEEK_API_KEY, DEEPSEEK_API_BASE, DEEPSEEK_MODEL, OLLAMA_API_BASE, OLLAMA_GENERATION_MODEL

class LLMClient:
    """
    Cliente unificado para chamar LLMs (DeepSeek ou Ollama)
    """
    
    def __init__(self, provider: Optional[str] = None):
        """
        Inicializa o cliente LLM
        
        Args:
            provider: 'deepseek' ou 'ollama' (usa DEFAULT_PROVIDER se None)
        """
        self.provider = provider or DEFAULT_PROVIDER
        
        if self.provider == 'deepseek':
            try:
                from openai import OpenAI
                self.client = OpenAI(
                    api_key=DEEPSEEK_API_KEY,
                    base_url=DEEPSEEK_API_BASE
                )
                print(f"✓ DeepSeek Chat inicializado")
            except ImportError:
                print("❌ Erro: 'openai' package não instalado. Execute: pip install openai")
                raise
        else:
            try:
                import ollama
                self.client = ollama
                print(f"✓ Ollama inicializado")
            except ImportError:
                print("❌ Erro: 'ollama' package não instalado. Execute: pip install ollama")
                raise
    
    def chat(
        self,
        model: Optional[str] = None,
        messages: List[Dict[str, str]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        format: Optional[str] = None,
        **kwargs
    ) -> Union[Dict[str, Any], Generator]:
        """
        Chama um modelo de chat
        
        Args:
            model: Nome do modelo (usa padrão se None)
            messages: Lista de mensagens no formato OpenAI
            temperature: Temperatura de resposta
            max_tokens: Máximo de tokens
            stream: Se True, retorna streaming
            format: Formato da resposta ('json' para JSON forçado)
            **kwargs: Argumentos adicionais específicos do provider
            
        Returns:
            Resposta do modelo (Dict ou Generator se streaming)
        """
        if self.provider == 'deepseek':
            return self._deepseek_chat(
                model=model or DEEPSEEK_MODEL,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=stream,
                **kwargs
            )
        else:
            return self._ollama_chat(
                model=model or OLLAMA_GENERATION_MODEL,
                messages=messages,
                temperature=temperature,
                stream=stream,
                format=format,
                **kwargs
            )
    
    def _deepseek_chat(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs
    ) -> Union[Dict[str, Any], Generator]:
        """Chama DeepSeek Chat via OpenAI SDK"""
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=stream,
                **kwargs
            )
            
            if stream:
                # Retorna generator para streaming
                def stream_generator():
                    for chunk in response:
                        if chunk.choices[0].delta.content:
                            yield {'message': {'content': chunk.choices[0].delta.content}}
                return stream_generator()
            else:
                # Retorna resposta no formato compatível com Ollama
                return {
                    'message': {
                        'content': response.choices[0].message.content,
                        'role': response.choices[0].message.role
                    }
                }
        except Exception as e:
            print(f"❌ Erro ao chamar DeepSeek: {e}")
            raise
    
    def _ollama_chat(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        stream: bool = False,
        format: Optional[str] = None,
        **kwargs
    ) -> Union[Dict[str, Any], Generator]:
        """Chama Ollama localmente"""
        try:
            response = self.client.chat(
                model=model,
                messages=messages,
                stream=stream,
                format=format,
                options={'temperature': temperature},
                **kwargs
            )
            
            return response
        except Exception as e:
            print(f"❌ Erro ao chamar Ollama: {e}")
            raise


# Cliente global (lazy initialization)
_llm_client: Optional[LLMClient] = None

def get_llm_client(provider: Optional[str] = None) -> LLMClient:
    """
    Retorna cliente LLM global (singleton)
    
    Args:
        provider: Força um provider específico
        
    Returns:
        Instância de LLMClient
    """
    global _llm_client
    
    if provider:
        # Se especificou provider, cria novo cliente
        return LLMClient(provider=provider)
    
    if _llm_client is None:
        _llm_client = LLMClient()
    
    return _llm_client


# ============================================
# FUNÇÕES DE COMPATIBILIDADE COM OLLAMA
# ============================================

def chat(
    model: Optional[str] = None,
    messages: List[Dict[str, str]] = None,
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    stream: bool = False,
    format: Optional[str] = None,
    **kwargs
) -> Union[Dict[str, Any], Generator]:
    """
    Wrapper direto - compatível com ollama.chat()
    
    Uso:
        response = llm_chat.chat(
            model='deepseek-chat',
            messages=[{'role': 'user', 'content': 'Olá'}]
        )
    """
    client = get_llm_client()
    return client.chat(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        stream=stream,
        format=format,
        **kwargs
    )
