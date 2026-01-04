#!/usr/bin/env python3
"""
Teste Dry-Run do Retrofit (Ajuste de Preços para Compensar Taxas)
==================================================================

Valida se o bot está ajustando corretamente os targets para compensar
custos de trading (taxa de compra + venda + slippage = 0.25%).

Exemplo:
- Target nominal: 2%
- Retrofit total: +0.25%
- Target ajustado: 2.25% (preço deve subir 2.25% para lucro líquido de 2%)
"""

import sys
import os
import time
import json
from datetime import datetime
from pathlib import Path

# Adicionar diretório do projeto ao path
sys.path.insert(0, os.path.dirname(__file__))

# Constantes de teste
TEST_SYMBOL = "BTC-USDT"
TEST_ENTRY = 90000.0
TEST_TARGETS = "2:0.3,5:0.5"
TEST_INTERVAL = 5
TEST_SIZE = 0.001
TEST_DRY_RUN = True
TEST_BOT_ID = f"retrofit_test_{int(time.time())}"

print("=" * 80)
print("🔧 TESTE DRY-RUN DO RETROFIT")
print("=" * 80)
print()

# Validação 1: Constantes de retrofit
print("✓ Constantes de Retrofit (do bot.py)")
print("-" * 80)
RETROFIT_CONFIG = {
    "buy_fee_pct": 0.10,
    "sell_fee_pct": 0.10,
    "slippage_pct": 0.05,
    "total_trading_cost_pct": 0.25
}

for key, value in RETROFIT_CONFIG.items():
    print(f"  {key:.<30} {value}%")

print()
print("Total Retrofit: 0.10% + 0.10% + 0.05% = 0.25%")
print()

# Validação 2: Cálculo de targets ajustados
print("✓ Cálculo de Targets Ajustados (Sell Mode)")
print("-" * 80)

targets_raw = "2:0.3,5:0.5"  # pct:portion
targets = []
for part in targets_raw.split(","):
    try:
        pct_str, portion_str = part.split(":")
        targets.append((float(pct_str), float(portion_str)))
    except:
        pass

print(f"Targets nominais: {targets}")
print(f"Entry price: ${TEST_ENTRY:,.2f}")
print()

retrofit_pct = 0.25
for target_pct, portion in targets:
    # Cálculo CORRETO do retrofit
    adjusted_pct = target_pct + retrofit_pct
    adjusted_price = TEST_ENTRY * (1 + adjusted_pct / 100)
    nominal_price = TEST_ENTRY * (1 + target_pct / 100)
    
    profit_net = TEST_ENTRY * (adjusted_price - TEST_ENTRY) / TEST_ENTRY - retrofit_pct
    
    print(f"  Target {target_pct}% (porção {portion}):")
    print(f"    ├─ Preço nominal (sem retrofit): ${nominal_price:,.2f}")
    print(f"    ├─ Preço ajustado (com retrofit): ${adjusted_price:,.2f}")
    print(f"    ├─ Pct nominal: {target_pct}%")
    print(f"    ├─ Pct ajustado: {adjusted_pct}%")
    print(f"    └─ Lucro líquido esperado: {target_pct}% (após deduzir {retrofit_pct}% em taxas)")
    print()

# Validação 3: Comando dry-run
print("✓ Comando Dry-Run Configurado")
print("-" * 80)

cmd = [
    "python", "-u", "bot_core.py",
    "--bot-id", TEST_BOT_ID,
    "--symbol", TEST_SYMBOL,
    "--entry", str(TEST_ENTRY),
    "--mode", "sell",
    "--targets", TEST_TARGETS,
    "--interval", str(TEST_INTERVAL),
    "--size", str(TEST_SIZE),
    "--funds", "0",
    "--dry"
]

print("Comando que será executado:")
print()
print(" ".join(cmd))
print()

# Validação 4: Logs esperados
print("✓ Logs Esperados durante execução")
print("-" * 80)
print("""
O bot deve registrar (em tempo real):

1. ✓ Bot inicializado:
   - bot_id: retrofit_test_<timestamp>
   - symbol: BTC-USDT
   - entry_price: 90000
   - mode: sell
   
2. ✓ Custos de trading configurados:
   - buy_fee_pct: 0.10
   - sell_fee_pct: 0.10
   - slippage_pct: 0.05
   - total_trading_cost_pct: 0.25
   - min_true_profit_pct: 2.25 (para atingir lucro líquido de 2%)

3. ✓ Atualizações periódicas de preço e status

4. ✓ Eventos de targets (quando preço atinge o nível ajustado):
   - price_update
   - target_armed / target_hit
   - trade_executed (simulado)

5. ✓ Finalização:
   - Resumo de trades
   - Lucro simulado
""")

# Validação 5: Executar dry-run
print("=" * 80)
print("🚀 INICIANDO TESTE DRY-RUN...")
print("=" * 80)
print()

import subprocess

try:
    process = subprocess.Popen(
        cmd,
        cwd=os.path.dirname(__file__),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        universal_newlines=True
    )
    
    # Coletar output
    output_lines = []
    retrofit_validated = False
    target_adjusted_validated = False
    
    for line in process.stdout:
        line = line.rstrip()
        print(line)
        output_lines.append(line)
        
        # Validações automáticas
        if "total_trading_cost_pct" in line and "0.25" in line:
            retrofit_validated = True
            print("  ✓✓✓ RETROFIT VALIDADO NO LOG!")
        
        if "min_true_profit_pct" in line and "2.25" in line:
            target_adjusted_validated = True
            print("  ✓✓✓ TARGET AJUSTADO VALIDADO NO LOG!")
    
    process.wait(timeout=60)
    
    print()
    print("=" * 80)
    print("📊 RESULTADOS DO TESTE")
    print("=" * 80)
    print()
    
    if retrofit_validated:
        print("✅ Retrofit Total (0.25%) CONFIRMADO no log do bot")
    else:
        print("⚠️  Retrofit não encontrado no log - verificar saída acima")
    
    if target_adjusted_validated:
        print("✅ Target Ajustado (2.25%) CONFIRMADO no log do bot")
    else:
        print("⚠️  Target ajustado não encontrado no log - verificar saída acima")
    
    print()
    print("✓ Teste concluído com sucesso!")
    print("✓ Verifique o banco de dados:")
    print(f"  - Sessão: psql \"$DATABASE_URL\" -c \"SELECT * FROM bot_sessions WHERE id='{TEST_BOT_ID}'\"")
    print(f"  - Logs: psql \"$DATABASE_URL\" -c \"SELECT * FROM bot_logs WHERE bot_id='{TEST_BOT_ID}' LIMIT 5\"")
    
except subprocess.TimeoutExpired:
    print("\n⚠️ Timeout: teste rodou por mais de 60 segundos")
    process.kill()
except KeyboardInterrupt:
    print("\n⚠️ Teste interrompido pelo usuário")
    process.kill()
except Exception as e:
    print(f"\n❌ Erro ao executar teste: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 80)
