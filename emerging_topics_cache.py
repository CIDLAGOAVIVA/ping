"""
Sistema de cache para análise de tópicos emergentes.
Evita reprocessamento quando os dados não mudarem.
"""

import json
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime


class EmergingTopicsCache:
    """Gerenciador de cache para tópicos emergentes."""
    
    def __init__(self, cache_dir: str = "./cache"):
        """
        Inicializa o cache.
        
        Args:
            cache_dir: Diretório para armazenar cache
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.cache_file = self.cache_dir / "emerging_topics_cache.json"
        self.metadata_file = self.cache_dir / "topics_cache_metadata.json"
        
        self.cache = self._load_cache()
        self.metadata = self._load_metadata()
        
        # 🆕 Log de inicialização
        print(f"📦 Cache de tópicos inicializado: {len(self.cache)} entrada(s) em {self.cache_file}")
    
    def _load_cache(self) -> Dict[str, Any]:
        """Carrega cache do disco."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                    print(f"   ✅ Cache carregado: {len(cache_data)} entrada(s)")
                    return cache_data
            except Exception as e:
                print(f"   ⚠️ Erro ao carregar cache de tópicos: {e}")
                return {}
        else:
            print(f"   ℹ️ Arquivo de cache não existe ainda: {self.cache_file}")
        return {}
    
    def _load_metadata(self) -> Dict[str, Any]:
        """Carrega metadados do cache."""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"   ⚠️ Erro ao carregar metadata de tópicos: {e}")
                return {}
        return {}
    
    def _save_cache(self):
        """Salva cache no disco."""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, indent=2, ensure_ascii=False)
            print(f"   💾 Cache salvo: {self.cache_file} ({len(self.cache)} entrada(s))")
        except Exception as e:
            print(f"   ⚠️ Erro ao salvar cache de tópicos: {e}")
    
    def _save_metadata(self):
        """Salva metadados no disco."""
        try:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"   ⚠️ Erro ao salvar metadata de tópicos: {e}")
    
    def _generate_key(
        self,
        profiles: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        total_posts: int = 0,
        total_texts: int = 0
    ) -> str:
        """
        Gera chave única para a análise baseada nos parâmetros.
        
        Args:
            profiles: Lista de perfis filtrados
            start_date: Data inicial
            end_date: Data final
            total_posts: Total de posts analisados
            total_texts: Total de textos (legendas + comentários)
            
        Returns:
            Hash MD5 como chave
        """
        profiles_str = ",".join(sorted(profiles)) if profiles else "all"
        key_parts = [
            profiles_str,
            start_date or "none",
            end_date or "none",
            str(total_posts),
            str(total_texts)
        ]
        key_string = "|".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def get(
        self,
        profiles: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        total_posts: int = 0,
        total_texts: int = 0
    ) -> Optional[Dict[str, Any]]:
        """
        Busca análise no cache.
        
        Args:
            profiles: Lista de perfis filtrados
            start_date: Data inicial
            end_date: Data final
            total_posts: Total de posts
            total_texts: Total de textos analisados
            
        Returns:
            Resultado do cache ou None se não encontrado/inválido
        """
        key = self._generate_key(profiles, start_date, end_date, total_posts, total_texts)
        
        # 🆕 Logs de debug detalhados
        print(f"\n🔍 Buscando cache de tópicos:")
        print(f"   - Chave gerada: {key}")
        print(f"   - Perfis: {profiles or 'all'}")
        print(f"   - Datas: {start_date or 'none'} → {end_date or 'none'}")
        print(f"   - Posts: {total_posts}, Textos: {total_texts}")
        print(f"   - Cache possui: {len(self.cache)} entrada(s)")
        
        if key not in self.cache:
            print(f"   ❌ CACHE MISS - chave '{key}' não encontrada")
            if len(self.cache) > 0:
                print(f"   📋 Chaves disponíveis no cache:")
                for cached_key in list(self.cache.keys())[:3]:  # Mostra até 3
                    entry = self.cache[cached_key]
                    print(f"      - {cached_key}: posts={entry.get('total_posts')}, textos={entry.get('total_texts')}")
            return None
        
        cached_entry = self.cache[key]
        
        print(f"   ✅ Chave encontrada no cache!")
        print(f"      - Cache salvo em: {cached_entry.get('cached_at', 'N/A')}")
        print(f"      - Cache tem: {cached_entry.get('total_posts')} posts, {cached_entry.get('total_texts')} textos")
        print(f"      - Solicitado: {total_posts} posts, {total_texts} textos")
        
        # Verifica se o total de posts ou textos mudou
        if (cached_entry.get('total_posts') != total_posts or 
            cached_entry.get('total_texts') != total_texts):
            print(f"   🔄 CACHE INVÁLIDO - dados mudaram!")
            self.invalidate(profiles, start_date, end_date)
            return None
        
        # Cache válido
        print(f"   ✅✅ CACHE HIT VÁLIDO!")
        return cached_entry['result']
    
    def set(
        self,
        result: Dict[str, Any],
        profiles: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        total_posts: int = 0,
        total_texts: int = 0
    ):
        """
        Armazena análise no cache.
        
        Args:
            result: Resultado da análise
            profiles: Lista de perfis filtrados
            start_date: Data inicial
            end_date: Data final
            total_posts: Total de posts analisados
            total_texts: Total de textos analisados
        """
        key = self._generate_key(profiles, start_date, end_date, total_posts, total_texts)
        
        self.cache[key] = {
            'result': result,
            'profiles': profiles or [],
            'start_date': start_date,
            'end_date': end_date,
            'total_posts': total_posts,
            'total_texts': total_texts,
            'cached_at': datetime.now().isoformat()
        }
        
        # Atualiza metadata
        profiles_str = ",".join(sorted(profiles)) if profiles else "all"
        self.metadata[key] = {
            'profiles': profiles_str,
            'total_posts': total_posts,
            'total_texts': total_texts,
            'cached_at': datetime.now().isoformat()
        }
        
        self._save_cache()
        self._save_metadata()
        
        print(f"\n💾 Cache de tópicos salvo!")
        print(f"   - Chave: {key}")
        print(f"   - Perfis: {profiles_str}")
        print(f"   - Posts: {total_posts}, Textos: {total_texts}")
        print(f"   - Total entradas: {len(self.cache)}")
    
    def invalidate(
        self,
        profiles: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ):
        """
        Invalida entradas específicas do cache.
        
        Args:
            profiles: Lista de perfis
            start_date: Data inicial
            end_date: Data final
        """
        keys_to_remove = []
        
        profiles_str = ",".join(sorted(profiles)) if profiles else "all"
        
        for key, entry in self.cache.items():
            entry_profiles = ",".join(sorted(entry.get('profiles', []))) if entry.get('profiles') else "all"
            match = (
                entry_profiles == profiles_str and
                entry.get('start_date') == start_date and
                entry.get('end_date') == end_date
            )
            
            if match:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.cache[key]
            if key in self.metadata:
                del self.metadata[key]
        
        if keys_to_remove:
            self._save_cache()
            self._save_metadata()
            print(f"🗑️ {len(keys_to_remove)} entrada(s) de tópicos invalidada(s)")
    
    def clear_all(self):
        """Limpa todo o cache."""
        self.cache = {}
        self.metadata = {}
        self._save_cache()
        self._save_metadata()
        print("🗑️ Cache de tópicos completamente limpo")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas do cache.
        
        Returns:
            Dict com estatísticas
        """
        total_entries = len(self.cache)
        
        # Agrupa por perfis
        by_profiles = {}
        for entry in self.cache.values():
            profiles_str = ",".join(sorted(entry.get('profiles', []))) if entry.get('profiles') else "all"
            by_profiles[profiles_str] = by_profiles.get(profiles_str, 0) + 1
        
        # Tamanho em disco
        cache_size = 0
        if self.cache_file.exists():
            cache_size += self.cache_file.stat().st_size
        if self.metadata_file.exists():
            cache_size += self.metadata_file.stat().st_size
        
        return {
            'total_entries': total_entries,
            'by_profiles': by_profiles,
            'cache_size_kb': round(cache_size / 1024, 2),
            'cache_dir': str(self.cache_dir)
        }


def main():
    """Função de teste."""
    print("=== Testando Cache de Tópicos Emergentes ===\n")
    
    cache = EmergingTopicsCache()
    
    # Teste 1: Salvar no cache
    print("1. Salvando análise no cache...")
    result = {
        'total_topics': 5,
        'total_posts_analyzed': 100,
        'topics': [
            {'term': 'Greve', 'count': 45, 'percentage': 15.0},
            {'term': 'HUAP', 'count': 30, 'percentage': 10.0}
        ]
    }
    cache.set(result, profiles=['dceuff'], total_posts=100, total_texts=300)
    
    # Teste 2: Recuperar do cache
    print("\n2. Recuperando do cache...")
    cached = cache.get(profiles=['dceuff'], total_posts=100, total_texts=300)
    print(f"Resultado: {cached is not None}")
    
    # Teste 3: Cache miss (novos posts)
    print("\n3. Testando cache miss (novos posts)...")
    cached = cache.get(profiles=['dceuff'], total_posts=150, total_texts=400)
    print(f"Resultado: {cached}")
    
    # Teste 4: Estatísticas
    print("\n4. Estatísticas do cache:")
    stats = cache.get_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")


if __name__ == '__main__':
    main()