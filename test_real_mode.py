#!/usr/bin/env python3
"""
Script de teste para verificar se o modo real está funcionando
"""
import sys
import os

# Adiciona o diretório atual ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("TESTE DE MODO REAL - DIAGNÓSTICO")
print("=" * 60)

# 1. Teste de import da API
print("\n[1/5] Testando import da API...")
try:
    import api
    print("✅ API importada com sucesso")
    print(f"   - API_KEY presente: {bool(api.API_KEY)}")
    print(f"   - API_SECRET presente: {bool(api.API_SECRET)}")
    print(f"   - API_PASSPHRASE presente: {bool(api.API_PASSPHRASE)}")
    print(f"   - KUCOIN_BASE: {api.KUCOIN_BASE}")
    HAS_API = bool(api.API_KEY and api.API_SECRET and api.API_PASSPHRASE)
    print(f"   - Credenciais válidas: {HAS_API}")
except Exception as e:
    print(f"❌ Erro ao importar API: {e}")
    HAS_API = False

# 2. Teste da função place_market_order
print("\n[2/5] Testando função place_market_order...")
try:
    from bot_core import place_market_order, HAS_REAL_API
    print(f"✅ Função importada com sucesso")
    print(f"   - HAS_REAL_API: {HAS_REAL_API}")
except Exception as e:
    print(f"❌ Erro ao importar place_market_order: {e}")

# 3. Teste de ordem simulada
print("\n[3/5] Testando ordem SIMULADA (dry_run=True)...")
try:
    result = place_market_order(
        symbol="BTC-USDT",
        side="sell",
        size=0.00001,
        dry_run=True,
        logger=None
    )
    print(f"✅ Ordem simulada executada")
    print(f"   - Resultado: {result}")
    print(f"   - É simulação: {result.get('simulated', False)}")
except Exception as e:
    print(f"❌ Erro na ordem simulada: {e}")

# 4. Teste de ordem real (SEM EXECUTAR)
print("\n[4/5] Testando parâmetros para ordem REAL (dry_run=False)...")
print("   ATENÇÃO: NÃO vamos executar, apenas verificar parâmetros")
if HAS_API:
    print("✅ API disponível - ordem real SERIA executada")
    print("   Parâmetros que seriam usados:")
    print("   - symbol: BTC-USDT")
    print("   - side: sell")
    print("   - size: 0.00001")
    print("   - dry_run: False")
else:
    print("❌ API não disponível - ordem seria simulada mesmo com dry_run=False")

# 5. Teste do EnhancedTradeBot
print("\n[5/5] Testando classe EnhancedTradeBot...")
try:
    from bot_core import EnhancedTradeBot
    
    # Teste com dry_run=True
    print("   Testando com dry_run=True...")
    bot1 = EnhancedTradeBot(
        symbol="BTC-USDT",
        entry_price=90000,
        targets=[(0.5, 0.5), (1.0, 0.5)],
        size=0.00001,
        dry_run=True
    )
    print(f"   ✅ Bot criado: dry_run={bot1.dry_run}")
    
    # Teste com dry_run=False
    print("   Testando com dry_run=False...")
    bot2 = EnhancedTradeBot(
        symbol="BTC-USDT",
        entry_price=90000,
        targets=[(0.5, 0.5), (1.0, 0.5)],
        size=0.00001,
        dry_run=False
    )
    print(f"   ✅ Bot criado: dry_run={bot2.dry_run}")
    
    if bot2.dry_run and HAS_API:
        print("   ⚠️ PROBLEMA DETECTADO!")
        print("   Bot está forçando dry_run=True mesmo com API disponível")
    elif not bot2.dry_run and HAS_API:
        print("   ✅ Bot está em MODO REAL (como esperado)")
    elif bot2.dry_run and not HAS_API:
        print("   ✅ Bot está em modo simulação (sem API, correto)")
    
except Exception as e:
    print(f"❌ Erro ao criar bot: {e}")
    import traceback
    traceback.print_exc()

# Resumo
print("\n" + "=" * 60)
print("RESUMO DO DIAGNÓSTICO")
print("=" * 60)
print(f"API disponível: {HAS_API}")
if HAS_API:
    print("✅ Modo REAL está disponível")
    print("   Para usar:")
    print("   1. Na UI: Desmarque 'Dry Run' E marque a confirmação")
    print("   2. CLI: Use --no-dry")
    print("\n   Comando de teste seguro:")
    print("   python bot_core.py --symbol BTC-USDT --entry 90000 \\")
    print("      --targets '0.5:1.0' --interval 30 --no-dry --size 0.00001")
else:
    print("❌ Modo REAL não disponível (sem credenciais)")
    print("   Configure o arquivo .env com suas credenciais da KuCoin")

print("\n" + "=" * 60)
