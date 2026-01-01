#!/usr/bin/env python3
"""Script para consultar o retrofit das operações do bot via API KuCoin"""

from api import get_all_fills, get_recent_orders, _has_keys
import json
from datetime import datetime

# Constantes de taxas (mesmas do bot.py)
BUY_FEE_PCT = 0.10
SELL_FEE_PCT = 0.10
SLIPPAGE_PCT = 0.05
TOTAL_TRADING_COST_PCT = BUY_FEE_PCT + SELL_FEE_PCT + SLIPPAGE_PCT

def main():
    print('='*60)
    print('RETROFIT DAS OPERAÇÕES DO BOT - KuCoin API')
    print('='*60)
    print(f'\n💰 CUSTOS DE TRADING CONFIGURADOS:')
    print(f'   Taxa de compra:  {BUY_FEE_PCT:.2f}%')
    print(f'   Taxa de venda:   {SELL_FEE_PCT:.2f}%')
    print(f'   Slippage:        {SLIPPAGE_PCT:.2f}%')
    print(f'   CUSTO TOTAL:     {TOTAL_TRADING_COST_PCT:.2f}%')

    if not _has_keys():
        print('❌ Credenciais da API não configuradas!')
        print('Por favor, configure API_KEY, API_SECRET e API_PASSPHRASE')
        return

    print('\n📊 Buscando execuções (fills) dos últimos 7 dias...\n')

    try:
        fills = get_all_fills(page_size=100, max_pages=5)
        
        if not fills:
            print('Nenhuma execução encontrada nos últimos 7 dias.')
        else:
            print(f'Total de execuções encontradas: {len(fills)}')
            print('-'*60)
            
            # Agrupar por símbolo
            by_symbol = {}
            for f in fills:
                sym = f.get('symbol', 'UNKNOWN')
                if sym not in by_symbol:
                    by_symbol[sym] = []
                by_symbol[sym].append(f)
            
            grand_total_buy = 0
            grand_total_sell = 0
            grand_total_fee = 0
            
            for symbol, trades in by_symbol.items():
                print(f'\n🔹 {symbol} ({len(trades)} trades)')
                print('-'*40)
                
                total_buy = 0
                total_sell = 0
                total_fee = 0
                
                for t in sorted(trades, key=lambda x: x.get('createdAt', 0), reverse=True)[:10]:
                    side = t.get('side', '?')
                    price = float(t.get('price', 0))
                    size = float(t.get('size', 0))
                    fee = float(t.get('fee', 0))
                    fee_currency = t.get('feeCurrency', '')
                    created_at = t.get('createdAt', 0)
                    
                    if created_at:
                        dt = datetime.fromtimestamp(created_at/1000)
                        dt_str = dt.strftime('%Y-%m-%d %H:%M')
                    else:
                        dt_str = 'N/A'
                    
                    value = price * size
                    emoji = '🟢' if side == 'buy' else '🔴'
                    
                    print(f'  {emoji} {side.upper():4} | {size:.6f} @ {price:.4f} = ${value:.2f} | Fee: {fee:.6f} {fee_currency} | {dt_str}')
                    
                    if side == 'buy':
                        total_buy += value
                    else:
                        total_sell += value
                    total_fee += fee
                
                pnl = total_sell - total_buy
                pnl_emoji = '✅' if pnl >= 0 else '❌'
                print(f'\n  Resumo {symbol}:')
                print(f'    Compras: ${total_buy:.2f}')
                print(f'    Vendas:  ${total_sell:.2f}')
                print(f'    {pnl_emoji} PnL Realizado: ${pnl:.2f}')
                print(f'    Taxas: {total_fee:.6f}')
                
                grand_total_buy += total_buy
                grand_total_sell += total_sell
                grand_total_fee += total_fee
            
            # Resumo geral
            print('\n' + '='*60)
            print('📊 RESUMO GERAL')
            print('='*60)
            grand_pnl = grand_total_sell - grand_total_buy
            grand_pnl_emoji = '✅' if grand_pnl >= 0 else '❌'
            print(f'  Total Compras: ${grand_total_buy:.2f}')
            print(f'  Total Vendas:  ${grand_total_sell:.2f}')
            print(f'  {grand_pnl_emoji} PnL Bruto: ${grand_pnl:.2f}')
            print(f'  Total Taxas: {grand_total_fee:.6f} USDT')
            
            # Calcular PnL líquido (após taxas)
            net_pnl = grand_pnl - grand_total_fee
            net_pnl_emoji = '✅' if net_pnl >= 0 else '❌'
            print(f'  {net_pnl_emoji} PnL LÍQUIDO (após taxas): ${net_pnl:.2f}')
            
            # Calcular ROI
            if grand_total_buy > 0:
                roi_bruto = (grand_pnl / grand_total_buy) * 100
                roi_liquido = (net_pnl / grand_total_buy) * 100
                print(f'\n  📈 ROI Bruto:   {roi_bruto:+.2f}%')
                print(f'  📈 ROI Líquido: {roi_liquido:+.2f}%')
                print(f'  📉 Custo médio de trading: {(grand_total_fee / grand_total_buy) * 100:.2f}%')
            
    except Exception as e:
        print(f'❌ Erro ao buscar fills: {e}')
        import traceback
        traceback.print_exc()

    print('\n' + '='*60)
    print('📋 Buscando ordens recentes...')
    print('='*60)

    try:
        orders = get_recent_orders(status='done', limit=50)
        
        if not orders:
            print('Nenhuma ordem finalizada encontrada.')
        else:
            print(f'\nOrdens finalizadas: {len(orders)}')
            for o in orders[:15]:
                symbol = o.get('symbol', '?')
                side = o.get('side', '?')
                type_ = o.get('type', '?')
                price = float(o.get('price', 0) or o.get('dealFunds', 0))
                size = float(o.get('size', 0) or o.get('dealSize', 0))
                created = o.get('createdAt', 0)
                
                if created:
                    dt = datetime.fromtimestamp(created/1000)
                    dt_str = dt.strftime('%Y-%m-%d %H:%M')
                else:
                    dt_str = 'N/A'
                
                emoji = '🟢' if side == 'buy' else '🔴'
                print(f'{emoji} {symbol:12} | {side:4} {type_:8} | Size: {size:.6f} | {dt_str}')

    except Exception as e:
        print(f'❌ Erro ao buscar ordens: {e}')
        import traceback
        traceback.print_exc()

    print('\n' + '='*60)
    print('✅ Consulta finalizada')
    print('='*60)

if __name__ == '__main__':
    main()
