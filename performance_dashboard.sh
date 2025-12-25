#!/bin/bash
echo "=== DASHBOARD DE PERFORMANCE DO AGENTE ==="
echo "Período: Últimos 30 dias"
echo "Data: $(date)"
echo ""

# Verificar se arquivo de log existe
if [ ! -f logs/agent_training.log ]; then
    echo "📝 Nenhum histórico de treinamento encontrado ainda."
    echo "   O agente começará a registrar performance após os primeiros ajustes."
    echo ""
    echo "💡 Para começar:"
    echo "   1. Faça um ajuste na aplicação"
    echo "   2. Registre o resultado no log"
    echo "   3. Execute este dashboard novamente"
    exit 0
fi

# Calcular métricas
TOTAL_TASKS=$(grep -c "timestamp" logs/agent_training.log)
if [ $TOTAL_TASKS -eq 0 ]; then
    echo "📝 Nenhum registro de tarefa encontrado."
    exit 0
fi

SUCCESS_TASKS=$(grep "success_rate.*1\.0" logs/agent_training.log | wc -l)
SUCCESS_RATE=$(( SUCCESS_TASKS * 100 / TOTAL_TASKS ))

AVG_TIME=$(grep "time_spent" logs/agent_training.log | jq -r '.time_spent' 2>/dev/null | awk '{sum+=$1; count++} END {print int(sum/count)}' || echo "0")

ERROR_COUNT=$(grep "error_type.*[^n][^o][^n][^e]" logs/agent_training.log | wc -l)

echo "📊 MÉTRICAS PRINCIPAIS:"
echo "   Total de Tarefas: $TOTAL_TASKS"
echo "   Taxa de Sucesso: ${SUCCESS_RATE}%"
echo "   Tempo Médio: ${AVG_TIME}min"
echo "   Total de Erros: $ERROR_COUNT"
echo ""

echo "🎯 STATUS ATUAL:"
if [ $SUCCESS_RATE -ge 90 ]; then
    echo "   ✅ Excelente performance!"
elif [ $SUCCESS_RATE -ge 80 ]; then
    echo "   ⚠️  Performance boa, pode melhorar"
else
    echo "   ❌ Performance precisa de atenção"
fi

echo ""
echo "📈 TENDÊNCIAS RECENTES:"
echo "   Últimas 5 tarefas:"
tail -5 logs/agent_training.log | jq -r '"   \(.timestamp[:10]): \(.task) - Sucesso: \(.success_rate)"' 2>/dev/null || echo "   (Formato de log precisa ser JSON)"

echo ""
echo "🔧 AÇÃO RECOMENDADA:"
if [ $SUCCESS_RATE -lt 80 ]; then
    echo "   📚 Revisar manual de treinamento"
    echo "   🧪 Praticar com ajustes simples"
elif [ $SUCCESS_RATE -lt 90 ]; then
    echo "   🎯 Focar em reduzir tempo de execução"
    echo "   🔍 Identificar padrões de erro"
else
    echo "   🚀 Pronto para ajustes complexos!"
    echo "   📊 Considere automatizar processos"
fi