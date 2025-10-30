"""
Sistema de cache para análises de sentimento.
Evita recálculo quando os dados não mudarem.
"""

import json
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime


class SentimentCache:
    """Gerenciador de cache para análises de sentimento."""
    
    def __init__(self, cache_dir: str = "./cache"):
        """
        Inicializa o cache.
        
        Args:
            cache_dir: Diretório para armazenar cache
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.cache_file = self.cache_dir / "sentiment_cache.json"
        self.metadata_file = self.cache_dir / "cache_metadata.json"
        
        self.cache = self._load_cache()
        self.metadata = self._load_metadata()
    
    def _load_cache(self) -> Dict[str, Any]:
        """Carrega cache do disco."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ Erro ao carregar cache: {e}")
                return {}
        return {}
    
    def _load_metadata(self) -> Dict[str, Any]:
        """Carrega metadados do cache."""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ Erro ao carregar metadata: {e}")
                return {}
        return {}
    
    def _save_cache(self):
        """Salva cache no disco."""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Erro ao salvar cache: {e}")
    
    def _save_metadata(self):
        """Salva metadados no disco."""
        try:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Erro ao salvar metadata: {e}")
    
    def _generate_key(
        self,
        profile: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        total_docs: int = 0,
        content_filter: str = "both"  # 🆕 Filtro de conteúdo
    ) -> str:
        """
        Gera chave única para a análise baseada nos parâmetros.
        
        Args:
            profile: Perfil filtrado
            start_date: Data inicial
            end_date: Data final
            total_docs: Total de documentos analisados
            content_filter: Tipo de conteúdo ("caption", "comments", "both")
            
        Returns:
            Hash MD5 como chave
        """
        key_parts = [
            profile or "all",
            start_date or "none",
            end_date or "none",
            str(total_docs),
            content_filter  # 🆕 Inclui no hash
        ]
        key_string = "|".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def get(
        self,
        profile: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        total_docs: int = 0,
        content_filter: str = "both"  # 🆕 Filtro de conteúdo
    ) -> Optional[Dict[str, Any]]:
        """
        Busca análise no cache.
        
        Args:
            profile: Perfil filtrado
            start_date: Data inicial
            end_date: Data final
            total_docs: Total de documentos na análise
            content_filter: Tipo de conteúdo ("caption", "comments", "both")
            
        Returns:
            Resultado do cache ou None se não encontrado/inválido
        """
        key = self._generate_key(profile, start_date, end_date, total_docs, content_filter)
        
        if key not in self.cache:
            return None
        
        cached_entry = self.cache[key]
        
        # Verifica se o total de documentos mudou (novos posts adicionados)
        if cached_entry.get('total_docs') != total_docs:
            print(f"🔄 Cache inválido: total de docs mudou ({cached_entry.get('total_docs')} → {total_docs})")
            self.invalidate(profile, start_date, end_date, content_filter)
            return None
        
        # Cache válido
        print(f"✅ Cache hit! Usando análise de {cached_entry.get('cached_at', 'N/A')}")
        return cached_entry['result']
    
    def set(
        self,
        result: Dict[str, Any],
        profile: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        total_docs: int = 0,
        content_filter: str = "both"  # 🆕 Filtro de conteúdo
    ):
        """
        Armazena análise no cache.
        
        Args:
            result: Resultado da análise
            profile: Perfil filtrado
            start_date: Data inicial
            end_date: Data final
            total_docs: Total de documentos analisados
            content_filter: Tipo de conteúdo ("caption", "comments", "both")
        """
        key = self._generate_key(profile, start_date, end_date, total_docs, content_filter)
        
        self.cache[key] = {
            'result': result,
            'profile': profile,
            'start_date': start_date,
            'end_date': end_date,
            'total_docs': total_docs,
            'content_filter': content_filter,  # 🆕 Armazena filtro
            'cached_at': datetime.now().isoformat()
        }
        
        # Atualiza metadata
        self.metadata[key] = {
            'profile': profile or 'all',
            'total_docs': total_docs,
            'content_filter': content_filter,
            'cached_at': datetime.now().isoformat()
        }
        
        self._save_cache()
        self._save_metadata()
        
        print(f"💾 Cache salvo para: perfil={profile or 'todos'}, docs={total_docs}, conteúdo={content_filter}")
    
    def invalidate(
        self,
        profile: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        content_filter: Optional[str] = None  # 🆕 Filtro de conteúdo
    ):
        """
        Invalida entrada específica do cache.
        
        Args:
            profile: Perfil a invalidar
            start_date: Data inicial
            end_date: Data final
            content_filter: Tipo de conteúdo (None = invalida todos)
        """
        # Invalida todas as entradas com os mesmos parâmetros (diferentes total_docs)
        keys_to_remove = []
        
        for key, entry in self.cache.items():
            match = (
                entry.get('profile') == profile and
                entry.get('start_date') == start_date and
                entry.get('end_date') == end_date
            )
            
            # Se content_filter especificado, filtra por ele também
            if content_filter:
                match = match and entry.get('content_filter') == content_filter
            
            if match:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.cache[key]
            if key in self.metadata:
                del self.metadata[key]
        
        if keys_to_remove:
            self._save_cache()
            self._save_metadata()
            print(f"🗑️ {len(keys_to_remove)} entrada(s) invalidada(s)")
    
    def clear_all(self):
        """Limpa todo o cache."""
        self.cache = {}
        self.metadata = {}
        self._save_cache()
        self._save_metadata()
        print("🗑️ Cache completamente limpo")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas do cache.
        
        Returns:
            Dict com estatísticas
        """
        total_entries = len(self.cache)
        
        # Agrupa por perfil
        by_profile = {}
        for entry in self.cache.values():
            prof = entry.get('profile') or 'all'
            by_profile[prof] = by_profile.get(prof, 0) + 1
        
        # Tamanho em disco
        cache_size = 0
        if self.cache_file.exists():
            cache_size += self.cache_file.stat().st_size
        if self.metadata_file.exists():
            cache_size += self.metadata_file.stat().st_size
        
        return {
            'total_entries': total_entries,
            'by_profile': by_profile,
            'cache_size_kb': round(cache_size / 1024, 2),
            'cache_dir': str(self.cache_dir)
        }


def main():
    """Função de teste."""
    print("=== Testando Sistema de Cache ===\n")
    
    cache = SentimentCache()
    
    # Teste 1: Salvar no cache
    print("1. Salvando análise no cache...")
    result = {
        'total_analyzed': 100,
        'positive': 30,
        'negative': 50,
        'neutral': 20,
        'trend': 'negative'
    }
    cache.set(result, profile="dceuff", total_docs=100)
    
    # Teste 2: Recuperar do cache
    print("\n2. Recuperando do cache...")
    cached = cache.get(profile="dceuff", total_docs=100)
    print(f"Resultado: {cached}")
    
    # Teste 3: Cache miss (total_docs diferente)
    print("\n3. Testando cache miss (novos posts)...")
    cached = cache.get(profile="dceuff", total_docs=150)
    print(f"Resultado: {cached}")
    
    # Teste 4: Estatísticas
    print("\n4. Estatísticas do cache:")
    stats = cache.get_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")


if __name__ == '__main__':
    main()