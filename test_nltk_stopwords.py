"""
Teste para verificar a integração com NLTK stopwords.
"""

import nltk
from nltk.corpus import stopwords

# Download stopwords (se necessário)
try:
    stopwords.words('portuguese')
    print("✅ Stopwords já disponíveis")
except LookupError:
    print("⬇️ Baixando stopwords do NLTK...")
    nltk.download('stopwords', quiet=True)
    print("✅ Stopwords baixadas com sucesso!")

# Teste básico
print("\n📊 Estatísticas de Stopwords:")
print(f"   - Total de stopwords (português): {len(stopwords.words('portuguese'))}")
print(f"   - Exemplos: {stopwords.words('portuguese')[:15]}")

# Teste com stopwords customizadas
nltk_stopwords = set(stopwords.words('portuguese'))
technical_terms = {'https', 'http', 'www', 'com', 'br', 'instagram', 'post', 'foto'}
stopwords_combined = nltk_stopwords.union(technical_terms)

print(f"\n✨ Stopwords combinadas (NLTK + termos técnicos):")
print(f"   - Total: {len(stopwords_combined)} palavras")
print(f"   - Termos técnicos adicionados: {technical_terms}")

# Teste de filtragem
test_text = "A UFF é uma universidade federal do Brasil que está no Instagram com fotos e posts"
words = test_text.lower().split()
filtered_words = [w for w in words if w not in stopwords_combined and len(w) >= 4]

print(f"\n🧪 Teste de filtragem:")
print(f"   - Texto original: {test_text}")
print(f"   - Palavras originais: {words}")
print(f"   - Palavras filtradas: {filtered_words}")
print(f"   - Removidas: {len(words) - len(filtered_words)} palavras")

print("\n✅ Teste concluído com sucesso!")
