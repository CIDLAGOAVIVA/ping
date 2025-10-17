#!/usr/bin/env python3
from embedding_manager import EmbeddingManager

em = EmbeddingManager()
stats = em.get_stats()
print('Perfis encontrados:', stats.get('profiles', []))
print('Total de documentos:', stats.get('total_documents', 0))
