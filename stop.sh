#!/bin/bash

# Script para parar a aplicação RAG Instagram rodando com nohup

set -e

echo "========================================="
echo "  Instagram RAG - Stop"
echo "========================================="
echo ""

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

# Procura processo do app.py
print_status "Procurando processos do app.py..."

# Busca PID do processo
PIDS=$(pgrep -f "python.*app.py" || true)

if [ -z "$PIDS" ]; then
    print_error "Nenhum processo do app.py encontrado"
    exit 1
fi

echo "Processos encontrados:"
ps aux | grep "[p]ython.*app.py"
echo ""

# Conta quantos processos
COUNT=$(echo "$PIDS" | wc -w)
print_status "Encontrados $COUNT processo(s)"

# Pergunta confirmação
read -p "Deseja parar estes processos? (s/N): " CONFIRM

if [[ ! "$CONFIRM" =~ ^[Ss]$ ]]; then
    print_error "Operação cancelada"
    exit 0
fi

# Para cada PID
for PID in $PIDS; do
    print_status "Parando processo $PID..."
    kill $PID 2>/dev/null || kill -9 $PID 2>/dev/null
    
    # Aguarda até 5 segundos para o processo terminar
    COUNTER=0
    while [ $COUNTER -lt 5 ]; do
        if ! ps -p $PID > /dev/null 2>&1; then
            print_success "Processo $PID parado"
            break
        fi
        sleep 1
        COUNTER=$((COUNTER + 1))
    done
    
    # Se ainda estiver rodando, força
    if ps -p $PID > /dev/null 2>&1; then
        print_status "Forçando parada do processo $PID..."
        kill -9 $PID 2>/dev/null || true
        print_success "Processo $PID forçadamente parado"
    fi
done

echo ""
print_success "Todos os processos foram parados"

# Remove arquivo nohup.out se existir
if [ -f "nohup.out" ]; then
    SIZE=$(du -h nohup.out | cut -f1)
    print_status "Arquivo nohup.out ($SIZE) encontrado"
    read -p "Deseja apagar nohup.out? (s/N): " DEL_LOG
    
    if [[ "$DEL_LOG" =~ ^[Ss]$ ]]; then
        rm nohup.out
        print_success "nohup.out apagado"
    fi
fi

echo ""
echo "========================================="
echo "  Aplicação parada com sucesso!"
echo "========================================="
