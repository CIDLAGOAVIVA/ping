#!/bin/bash

# Script de inicialização do sistema RAG Instagram
# Verifica dependências e inicia a aplicação

set -e

echo "========================================="
echo "  Instagram RAG - Setup e Inicialização"
echo "========================================="
echo ""

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função para verificar se comando existe
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Função para imprimir status
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[AVISO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERRO]${NC} $1"
}

# 1. Verificar Python
print_status "Verificando instalação do Python..."
if ! command_exists python3; then
    print_error "Python 3 não encontrado. Por favor, instale Python 3.12+"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
print_success "Python $PYTHON_VERSION encontrado"

# 2. Verificar uv
print_status "Verificando uv..."
if ! command_exists uv; then
    print_warning "uv não encontrado. Instalando..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
    
    if ! command_exists uv; then
        print_error "Falha ao instalar uv. Instale manualmente: https://docs.astral.sh/uv/"
        exit 1
    fi
fi
print_success "uv encontrado"

# 3. Verificar Ollama
print_status "Verificando Ollama..."
if ! command_exists ollama; then
    print_error "Ollama não encontrado!"
    echo ""
    echo "Por favor, instale o Ollama primeiro:"
    echo ""
    echo "  Linux/macOS:"
    echo "    curl -fsSL https://ollama.com/install.sh | sh"
    echo ""
    echo "  macOS (Homebrew):"
    echo "    brew install ollama"
    echo ""
    echo "  Windows:"
    echo "    Baixe de https://ollama.com/download"
    echo ""
    exit 1
fi
print_success "Ollama encontrado"

# 4. Verificar se Ollama está rodando
print_status "Verificando serviço Ollama..."
if ! curl -s http://localhost:11434/api/version >/dev/null 2>&1; then
    print_warning "Ollama não está rodando. Iniciando..."
    
    # Tenta iniciar em background
    if command_exists systemctl; then
        sudo systemctl start ollama 2>/dev/null || ollama serve >/dev/null 2>&1 &
    else
        ollama serve >/dev/null 2>&1 &
    fi
    
    sleep 3
    
    if ! curl -s http://localhost:11434/api/version >/dev/null 2>&1; then
        print_error "Não foi possível iniciar Ollama. Inicie manualmente: ollama serve"
        exit 1
    fi
fi
print_success "Ollama está rodando"

# 5. Sincronizar dependências
print_status "Sincronizando dependências Python..."
uv sync
print_success "Dependências instaladas"

# 6. Verificar/instalar modelos Ollama
print_status "Verificando modelos Ollama..."

EMBEDDING_MODEL="mxbai-embed-large"
GENERATION_MODEL="qwen3:30b"

# Verifica modelo de embedding
if ! ollama list | grep -q "$EMBEDDING_MODEL"; then
    print_warning "Modelo de embedding não encontrado: $EMBEDDING_MODEL"
    print_status "Baixando $EMBEDDING_MODEL (~700MB)..."
    ollama pull "$EMBEDDING_MODEL"
    print_success "Modelo de embedding instalado"
else
    print_success "Modelo de embedding já instalado: $EMBEDDING_MODEL"
fi

# Verifica modelo de geração
if ! ollama list | grep -q "qwen3"; then
    print_warning "Modelo de geração não encontrado"
    print_status "Baixando $GENERATION_MODEL (~18GB)..."
    echo ""
    echo "Nota: Este é um modelo grande. Para alternativas mais leves:"
    echo "  - qwen2.5:3b  (~2GB) - Leve"
    echo "  - qwen2.5:7b  (~4GB) - Médio"
    echo "  - qwen2.5:14b (~8GB) - Pesado"
    echo ""
    ollama pull "$GENERATION_MODEL"
    print_success "Modelo de geração instalado"
else
    print_success "Modelo de geração já instalado"
fi

# 7. Verificar arquivos de dados
print_status "Verificando arquivos de dados..."
if [ ! -d "data" ]; then
    print_error "Pasta 'data/' não encontrada!"
    exit 1
fi

JSON_COUNT=$(find data -name "*.json" | wc -l)
if [ "$JSON_COUNT" -eq 0 ]; then
    print_warning "Nenhum arquivo JSON encontrado em data/"
else
    print_success "Encontrados $JSON_COUNT arquivo(s) JSON"
fi

# 8. Perguntar sobre indexação
echo ""
echo "========================================="
echo "  Pronto para iniciar!"
echo "========================================="
echo ""

if [ -d "chroma_db" ] && [ "$(ls -A chroma_db 2>/dev/null)" ]; then
    print_warning "Índice existente detectado em chroma_db/"
    echo ""
    read -p "Deseja reindexar os posts? (s/N): " REINDEX
    if [[ "$REINDEX" =~ ^[Ss]$ ]]; then
        print_status "Limpando índice antigo..."
        rm -rf chroma_db/
        print_success "Índice removido. Será recriado na inicialização."
    fi
else
    print_status "Primeira execução: índice será criado automaticamente"
fi

# 9. Opções de inicialização
echo ""
echo "Escolha o modelo de geração:"
echo "  1) qwen3:30b   (Melhor - 18GB RAM)"
echo "  2) qwen2.5:7b  (Médio - 8GB RAM)"
echo "  3) qwen2.5:14b (Pesado - 16GB RAM)"
echo "  4) qwen2.5:3b  (Leve - 2GB RAM)"
echo "  5) Personalizado"
echo ""
read -p "Opção [1]: " MODEL_CHOICE

case "$MODEL_CHOICE" in
    2)
        GENERATION_MODEL="qwen2.5:7b"
        if ! ollama list | grep -q "$GENERATION_MODEL"; then
            print_status "Baixando $GENERATION_MODEL..."
            ollama pull "$GENERATION_MODEL"
        fi
        ;;
    3)
        GENERATION_MODEL="qwen2.5:14b"
        if ! ollama list | grep -q "$GENERATION_MODEL"; then
            print_status "Baixando $GENERATION_MODEL..."
            ollama pull "$GENERATION_MODEL"
        fi
        ;;
    4)
        GENERATION_MODEL="qwen2.5:3b"
        if ! ollama list | grep -q "$GENERATION_MODEL"; then
            print_status "Baixando $GENERATION_MODEL..."
            ollama pull "$GENERATION_MODEL"
        fi
        ;;
    5)
        read -p "Nome do modelo: " GENERATION_MODEL
        if ! ollama list | grep -q "$GENERATION_MODEL"; then
            print_status "Baixando $GENERATION_MODEL..."
            ollama pull "$GENERATION_MODEL"
        fi
        ;;
    *)
        GENERATION_MODEL="qwen3:30b"
        if ! ollama list | grep -q "qwen3"; then
            print_status "Baixando $GENERATION_MODEL..."
            ollama pull "$GENERATION_MODEL"
        fi
        ;;
esac

# 10. Opções adicionais
echo ""
read -p "Porta da aplicação [7860]: " PORT
PORT=${PORT:-7860}

read -p "Criar link público? (s/N): " SHARE
SHARE_FLAG=""
if [[ "$SHARE" =~ ^[Ss]$ ]]; then
    SHARE_FLAG="--share"
fi

# 11. Iniciar aplicação
echo ""
print_success "Configuração concluída!"
echo ""
echo "========================================="
echo "  Iniciando Instagram RAG Chat"
echo "========================================="
echo ""
echo "Modelo de geração: $GENERATION_MODEL"
echo "Porta: $PORT"
echo ""
print_status "Iniciando aplicação..."
echo ""

# Executa a aplicação
uv run python app.py \
    --generation-model "$GENERATION_MODEL" \
    --port "$PORT" \
    $SHARE_FLAG

# Se chegou aqui, a aplicação foi encerrada
echo ""
print_status "Aplicação encerrada."
