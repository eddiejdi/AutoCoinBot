#!/bin/bash
# Plano de Testes: Validação pós-correção 404
# Data: 2026-01-04

set -e

echo "🧪 INICIANDO TESTES PÓS-CORREÇÃO 404"
echo "===================================="

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

test_count=0
pass_count=0
fail_count=0

# Função para testar
test_endpoint() {
    local name=$1
    local url=$2
    local expected_code=$3
    
    ((test_count++))
    echo ""
    echo -n "🔍 Teste $test_count: $name... "
    
    response=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo "000")
    
    if [ "$response" = "$expected_code" ]; then
        echo -e "${GREEN}✅ PASS${NC} (HTTP $response)"
        ((pass_count++))
    else
        echo -e "${RED}❌ FAIL${NC} (HTTP $response, esperado $expected_code)"
        ((fail_count++))
    fi
}

# Testes HTTP
echo -e "\n${YELLOW}📡 TESTES DE CONECTIVIDADE HTTP${NC}"
test_endpoint "Streamlit Health" "http://localhost:8506/_stcore/health" "200"
test_endpoint "API HTTP /monitor" "http://127.0.0.1:8765/monitor" "200"
test_endpoint "API HTTP /report" "http://127.0.0.1:8765/report" "200"
test_endpoint "API /api/logs" "http://127.0.0.1:8765/api/logs?limit=1" "200"
test_endpoint "API /api/trades" "http://127.0.0.1:8765/api/trades?limit=1" "200"

# Verificações de Arquivo
echo -e "\n${YELLOW}📁 VERIFICAÇÕES DE ARQUIVO${NC}"
for file in "autocoinbot/monitor_window.html" "autocoinbot/report_window.html"; do
    ((test_count++))
    echo -n "🔍 Teste $test_count: Arquivo $file existe... "
    if [ -f "$file" ]; then
        echo -e "${GREEN}✅ PASS${NC}"
        ((pass_count++))
    else
        echo -e "${RED}❌ FAIL${NC}"
        ((fail_count++))
    fi
done

# Verificações de Docker
echo -e "\n${YELLOW}🐳 VERIFICAÇÕES DE DOCKER${NC}"
((test_count++))
echo -n "🔍 Teste $test_count: Container deploy-streamlit-1 não existe... "
if ! docker ps -a | grep -q "deploy-streamlit-1"; then
    echo -e "${GREEN}✅ PASS${NC} (Container removido corretamente)"
    ((pass_count++))
else
    echo -e "${RED}❌ FAIL${NC} (Container ainda existe)"
    ((fail_count++))
fi

# Verificações de Portas
echo -e "\n${YELLOW}🔌 VERIFICAÇÕES DE PORTAS${NC}"
for port in 8506 8765; do
    ((test_count++))
    echo -n "🔍 Teste $test_count: Porta $port está aberta... "
    if ss -tuln 2>/dev/null | grep -q ":$port"; then
        echo -e "${GREEN}✅ PASS${NC}"
        ((pass_count++))
    else
        echo -e "${RED}❌ FAIL${NC} (Porta $port não encontrada)"
        ((fail_count++))
    fi
done

# Verificações de Processos
echo -e "\n${YELLOW}⚙️ VERIFICAÇÕES DE PROCESSOS${NC}"
((test_count++))
echo -n "🔍 Teste $test_count: Streamlit processo ativo... "
if pgrep -f "streamlit run" > /dev/null; then
    echo -e "${GREEN}✅ PASS${NC}"
    ((pass_count++))
else
    echo -e "${RED}❌ FAIL${NC} (Streamlit não está rodando)"
    ((fail_count++))
fi

# Resumo
echo ""
echo "===================================="
echo -e "${YELLOW}📊 RESUMO DE TESTES${NC}"
echo "===================================="
echo "Total de testes: $test_count"
echo -e "Passou: ${GREEN}$pass_count${NC}"
echo -e "Falhou: ${RED}$fail_count${NC}"

if [ $fail_count -eq 0 ]; then
    echo -e "\n${GREEN}✅ TODOS OS TESTES PASSARAM!${NC}"
    exit 0
else
    echo -e "\n${RED}❌ ALGUNS TESTES FALHARAM${NC}"
    exit 1
fi
