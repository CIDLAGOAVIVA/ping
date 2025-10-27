#!/bin/bash

# Script para reiniciar a aplicação RAG Instagram

set -e

echo "========================================="
echo "  Instagram RAG - Restart"
echo "========================================="
echo ""

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${YELLOW}⏳${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# 1. Parar aplicação se estiver rodando
print_status "Verificando se há processos rodando..."

PIDS=$(pgrep -f "python.*app.py" || true)

if [ -n "$PIDS" ]; then
    print_info "Processos encontrados, parando..."
    
    for PID in $PIDS; do
        print_status "Parando processo $PID..."
        kill $PID 2>/dev/null || kill -9 $PID 2>/dev/null
        
        # Aguarda processo terminar
        COUNTER=0
        while [ $COUNTER -lt 5 ]; do
            if ! ps -p $PID > /dev/null 2>&1; then
                print_success "Processo $PID parado"
                break
            fi
            sleep 1
            COUNTER=$((COUNTER + 1))
        done
        
        # Força se necessário
        if ps -p $PID > /dev/null 2>&1; then
            kill -9 $PID 2>/dev/null || true
            print_success "Processo $PID forçadamente parado"
        fi
    done
else
    print_info "Nenhum processo rodando"
fi

echo ""

# 2. Aguardar um pouco
print_status "Aguardando 2 segundos..."
sleep 2

# 3. Iniciar novamente
print_status "Iniciando aplicação..."
echo ""

# Detecta modelos disponíveis
if ! command -v ollama &> /dev/null; then
    print_error "Ollama não encontrado. Instale o Ollama primeiro."
    exit 1
fi

# Verifica se Ollama está rodando
if ! curl -s http://localhost:11434/api/version >/dev/null 2>&1; then
    print_error "Ollama não está rodando. Execute: ollama serve"
    exit 1
fi

# Modelo padrão
GENERATION_MODEL="qwen3:30b"

# Verifica se modelo existe
if ! ollama list | grep -q "qwen3:30b"; then
    print_info "Modelo qwen3:30b não encontrado, usando qwen2.5:7b"
    GENERATION_MODEL="qwen2.5:7b"
fi

# Porta
PORT="${PORT:-7860}"

# Opções
EMBEDDING_MODEL="mxbai-embed-large"
SHARE="${SHARE:-}"

print_info "Configuração:"
echo "  - Modelo de geração: $GENERATION_MODEL"
echo "  - Modelo de embedding: $EMBEDDING_MODEL"
echo "  - Porta: $PORT"
echo ""

# Cria comando
CMD="uv run app.py --embedding-model $EMBEDDING_MODEL --generation-model $GENERATION_MODEL --port $PORT"

if [ -n "$SHARE" ]; then
    CMD="$CMD --share"
fi

# Inicia com nohup
print_status "Executando: $CMD"
nohup $CMD > nohup.out 2>&1 &

NEW_PID=$!
print_success "Aplicação iniciada com PID: $NEW_PID"

echo ""
print_status "Aguardando inicialização (5 segundos)..."
sleep 5

# Verifica se ainda está rodando
if ps -p $NEW_PID > /dev/null 2>&1; then
    print_success "Aplicação rodando com sucesso!"
    echo ""
    print_info "Acesse: http://localhost:$PORT"
    print_info "Logs: tail -f nohup.out"
    print_info "Parar: ./stop.sh"
else
    print_error "Aplicação falhou ao iniciar. Verifique nohup.out"
    echo ""
    echo "Últimas linhas do log:"
    tail -20 nohup.out
    exit 1
fi

echo ""
echo "========================================="
echo "  Aplicação reiniciada com sucesso!"
echo "========================================="
