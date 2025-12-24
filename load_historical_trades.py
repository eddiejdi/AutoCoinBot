#!/usr/bin/env python3
"""
Script para carregar histórico de trades do KuCoin na base de dados.
Executa uma vez para popular a base com dados históricos.
"""

import sys
import os
import time
import threading

# Adicionar o diretório do projeto ao path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

from kucoin_app import api as kucoin_api
from kucoin_app.database import DatabaseManager

def load_historical_trades():
    """Carrega trades históricos (últimos 365 dias) na base de dados."""
    print("🔄 Iniciando carga de histórico de trades...")

    # Período: últimos 365 dias
    now_ms = int(time.time() * 1000)
    start_ms = now_ms - (365 * 24 * 3600 * 1000)

    print(f"📅 Período: {time.strftime('%Y-%m-%d', time.localtime(start_ms / 1000))} até {time.strftime('%Y-%m-%d', time.localtime(now_ms / 1000))}")

    fills = []
    try:
        print("📡 Buscando fills da API KuCoin...")
        fills = kucoin_api.get_all_fills(start_at=start_ms, end_at=now_ms, page_size=200, max_pages=100)  # Até 20.000 trades
        print(f"✅ Encontrados {len(fills)} fills")
    except Exception as e:
        print(f"❌ Erro ao buscar fills: {e}")
        return

    if not fills:
        print("⚠️ Nenhum fill encontrado.")
        return

    db = DatabaseManager()
    inserted = 0
    skipped = 0

    for f in fills:
        if not isinstance(f, dict):
            continue

        trade_id = f.get("tradeId") or f.get("id")
        order_id = f.get("orderId")
        created_at = f.get("createdAt")

        if not trade_id:
            continue

        # Verificar se já existe
        try:
            existing = db.get_trade_by_id(trade_id)
            if existing:
                skipped += 1
                continue
        except Exception:
            pass

        # Timestamp em segundos
        ts_s = None
        try:
            if created_at is not None:
                ca = float(created_at)
                ts_s = ca / 1000.0 if ca > 1e12 else ca
        except Exception:
            ts_s = time.time()

        symbol = f.get("symbol")
        side = f.get("side")
        price = f.get("price")
        size = f.get("size")
        funds = f.get("funds")
        fee = f.get("fee")

        try:
            price = float(price) if price is not None else None
        except Exception:
            price = None

        try:
            size = float(size) if size is not None else None
        except Exception:
            size = None

        try:
            funds = float(funds) if funds is not None else None
        except Exception:
            funds = None

        try:
            fee = float(fee) if fee is not None else None
        except Exception:
            fee = None

        trade_data = {
            "id": str(trade_id),
            "timestamp": ts_s or time.time(),
            "symbol": symbol or "",
            "side": (side or "").lower(),
            "price": price or 0.0,
            "size": size,
            "funds": funds,
            "profit": None,
            "commission": fee,
            "order_id": str(order_id) if order_id is not None else None,
            "bot_id": "KUCOIN",
            "strategy": "kucoin_fill",
            "dry_run": False,
            "metadata": {"source": "kucoin", "fill": f},
        }

        try:
            db.insert_trade_ignore(trade_data)
            inserted += 1
        except Exception as e:
            print(f"❌ Erro ao inserir trade {trade_id}: {e}")
            continue

    print(f"✅ Inseridos: {inserted} | Pulados (duplicados): {skipped}")
    print("🎉 Carga de histórico concluída!")

if __name__ == "__main__":
    load_historical_trades()