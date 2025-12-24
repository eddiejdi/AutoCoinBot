# bot_core.py
import sys
import time
import os

# ======================================================
# IMPORT DO BOT — NÃO INVENTA MÓDULO
# ======================================================
try:
    from .bot import EnhancedTradeBot
except ImportError:
    try:
        from bot import EnhancedTradeBot
    except ImportError:
        EnhancedTradeBot = None


#from .utils import parse_targets 


def parse_targets(s: str):
    """
    Converte '2:0.3,5:0.4' em [(2.0, 0.3), (5.0, 0.4)]
    Mantido aqui para evitar dependências inexistentes.
    """
    out = []
    if not s:
        return out

    for part in s.split(","):
        if ":" not in part:
            continue
        a, b = part.split(":", 1)
        try:
            out.append((float(a), float(b)))
        except ValueError:
            continue

    return out


# ======================================================
# LOG SETUP — GRAVA EM SQLITE VIA DATABASE.PY
# ======================================================
class DatabaseLogger:
    """Wrapper que permite usar DatabaseManager como um logger Python"""
    def __init__(self, db_manager, bot_id: str):
        self.db = db_manager
        self.bot_id = bot_id
        self.handlers = []  # Fake handlers para compatibilidade
        self.propagate = False
    
    def setLevel(self, level):
        """Noop para compatibilidade"""
        pass
    
    def addHandler(self, handler):
        """Noop para compatibilidade"""
        self.handlers.append(handler)
    
    def info(self, message: str):
        """Grava INFO log"""
        try:
            self.db.add_bot_log(self.bot_id, "INFO", message, {"message": message})
        except Exception as e:
            print(f"[LOG ERROR] {e}", file=sys.stderr)
    
    def error(self, message: str):
        """Grava ERROR log"""
        try:
            self.db.add_bot_log(self.bot_id, "ERROR", message, {"message": message})
        except Exception as e:
            print(f"[LOG ERROR] {e}", file=sys.stderr)
    
    def warning(self, message: str):
        """Grava WARNING log"""
        try:
            self.db.add_bot_log(self.bot_id, "WARNING", message, {"message": message})
        except Exception as e:
            print(f"[LOG ERROR] {e}", file=sys.stderr)
    
    def debug(self, message: str):
        """Grava DEBUG log"""
        try:
            self.db.add_bot_log(self.bot_id, "DEBUG", message, {"message": message})
        except Exception as e:
            print(f"[LOG ERROR] {e}", file=sys.stderr)


def init_log(bot_id: str):
    """Inicializa o gerenciador de logs para o bot (usa SQLite)"""
    try:
        from .database import DatabaseManager
    except ImportError:
        from database import DatabaseManager
    db = DatabaseManager()
    return DatabaseLogger(db, bot_id)


def log(db_logger, bot_id: str, event: dict):
    """Grava evento de log em SQLite"""
    event["timestamp"] = time.time()
    event["bot_id"] = bot_id
    
    # Extrai o tipo de evento para usar como nível de log
    level = str(event.pop("event", "INFO")).upper()
    if level not in ("DEBUG", "INFO", "WARNING", "ERROR"):
        level = "INFO"
    
    # Message é uma concatenação legível do evento
    message = str(event)
    
    # Grava usando o método apropriado
    getattr(db_logger, level.lower(), db_logger.info)(message)


# ======================================================
# MAIN
# ======================================================
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="KuCoin Trading Bot")

    parser.add_argument("--bot-id", required=True)
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--entry", type=float, required=True)
    # Keep in sync with EnhancedTradeBot supported modes
    parser.add_argument("--mode", default="mixed", choices=["sell", "buy", "mixed", "flow"])
    parser.add_argument("--targets", required=True)
    parser.add_argument("--interval", type=float, default=5.0)
    parser.add_argument("--size", type=float, default=0.0)
    parser.add_argument("--funds", type=float, default=0.0)
    parser.add_argument("--dry", action="store_true", default=False)
    parser.add_argument("--reserve-pct", type=float, default=50.0, help="% do saldo a reservar")
    parser.add_argument("--target-profit-pct", type=float, default=2.0, help="% de lucro alvo")
    parser.add_argument("--eternal", action="store_true", default=False, help="Eternal mode - reinicia após targets")

    args = parser.parse_args()

    if EnhancedTradeBot is None:
        print("Erro crítico: EnhancedTradeBot não encontrado", file=sys.stderr)
        sys.exit(1)

    logger = init_log(args.bot_id)

    # ========== LOG INICIAL COM BOT_ID E PID ==========
    current_pid = os.getpid()
    logger.info(f"Bot iniciado: ID={args.bot_id}, PID={current_pid}")
    
    targets = parse_targets(args.targets)
    if not targets:
        log(logger, args.bot_id, {
            "event": "error",
            "message": "Nenhum target configurado"
        })
        sys.exit(1)

    log(logger, args.bot_id, {
        "event": "bot_started",
        "symbol": args.symbol,
        "mode": args.mode,
        "dry_run": args.dry,
        "bot_id": args.bot_id,
        "pid": current_pid,
        "reserve_pct": args.reserve_pct,
        "target_profit_pct": args.target_profit_pct,
        "eternal_mode": args.eternal
    })

    # ======================================================
    # AUTO: usar posição real já comprada (cota por bot) OU SIMULAR EM DRY
    # Regras:
    # - Apenas em modo sell
    # - Dispara quando entry <= 0 OU size <= 0
    # - Em real: aloca cota baseada em saldo livre
    # - Em dry: simula saldo e reserva %
    # ======================================================
    try:
        from .database import DatabaseManager
    except ImportError:
        from database import DatabaseManager

    db = DatabaseManager()

    def _as_none_if_zero(x):
        try:
            v = float(x)
        except Exception:
            return None
        return v if v > 0 else None

    size_arg = _as_none_if_zero(args.size)
    funds_arg = _as_none_if_zero(args.funds)
    entry_arg = _as_none_if_zero(args.entry)

    allocated_qty = None
    computed_entry = None

    if str(args.mode).lower() == "sell" and (entry_arg is None or size_arg is None):
        symbol_u = str(args.symbol).upper().strip()
        asset = symbol_u.split("-")[0] if "-" in symbol_u else symbol_u

        if not args.dry:
            # Modo real: consulta saldo e aloca
            try:
                from . import api as kucoin_api
            except Exception:
                import api as kucoin_api  # type: ignore

            # 1) Atualiza fills reais (fonte de verdade) antes de calcular custo médio.
            #    Isso evita usar trades internos do bot (que podem ter size impreciso).
            try:
                fills = kucoin_api.get_all_fills(symbol=symbol_u, page_size=200, max_pages=3)
                for f in fills or []:
                    if not isinstance(f, dict):
                        continue
                    trade_id = f.get("tradeId") or f.get("id")
                    order_id = f.get("orderId")
                    created_at = f.get("createdAt")  # ms

                    if not trade_id:
                        trade_id = f"kucoin_{order_id or 'no_order'}_{created_at or int(time.time()*1000)}"

                    ts_s = None
                    try:
                        if created_at is not None:
                            ca = float(created_at)
                            ts_s = ca / 1000.0 if ca > 1e12 else ca
                    except Exception:
                        ts_s = None

                    try:
                        price_f = float(f.get("price")) if f.get("price") is not None else 0.0
                    except Exception:
                        price_f = 0.0
                    try:
                        size_f = float(f.get("size")) if f.get("size") is not None else None
                    except Exception:
                        size_f = None
                    try:
                        funds_f = float(f.get("funds")) if f.get("funds") is not None else None
                    except Exception:
                        funds_f = None
                    try:
                        fee_f = float(f.get("fee")) if f.get("fee") is not None else None
                    except Exception:
                        fee_f = None

                    db.insert_trade_ignore({
                        "id": str(trade_id),
                        "timestamp": ts_s or time.time(),
                        "symbol": symbol_u,
                        "side": (str(f.get("side") or "").lower()),
                        "price": price_f,
                        "size": size_f,
                        "funds": funds_f,
                        "profit": None,
                        "commission": fee_f,
                        "order_id": str(order_id) if order_id is not None else None,
                        "bot_id": "KUCOIN",
                        "strategy": "kucoin_fill",
                        "dry_run": False,
                        "metadata": {"source": "kucoin", "fill": f},
                    })
            except Exception:
                pass

            # 2) Entry = menor BUY e quantidade = total comprado nesse menor BUY (apenas fills da KuCoin)
            lowest_buy = {"price": 0.0, "qty": 0.0}
            try:
                lowest_buy = db.get_lowest_buy_fill(symbol_u, only_kucoin=True)
            except Exception:
                lowest_buy = {"price": 0.0, "qty": 0.0}

            lowest_price = 0.0
            lowest_qty = 0.0
            try:
                lowest_price = float(lowest_buy.get("price") or 0.0)
            except Exception:
                lowest_price = 0.0
            try:
                lowest_qty = float(lowest_buy.get("qty") or 0.0)
            except Exception:
                lowest_qty = 0.0

            # Se entry do usuário foi informado e é >0, usa; senão usa menor BUY; senão usa preço atual
            computed_entry = entry_arg if entry_arg and entry_arg > 0 else (lowest_price if lowest_price > 0 else None)

            # Cota/size: se usuário informou size>0, essa é a cota desejada;
            # senão, usa a quantidade comprada no menor BUY.
            desired_qty = size_arg if size_arg is not None else (lowest_qty if lowest_qty > 0 else None)

            # Loop de espera por saldo disponível (desconta o que já está alocado por outros bots)
            while True:
                try:
                    # api pode falhar / credenciais inválidas; se falhar, espera
                    try:
                        from . import api as kucoin_api
                    except Exception:
                        import api as kucoin_api  # type: ignore
                    balances = kucoin_api.get_balances(account_type="trade")
                    avail_qty = 0.0
                    for b in balances or []:
                        if (b.get("currency") or "").upper() == asset:
                            try:
                                avail_qty = float(b.get("available") or 0.0)
                            except Exception:
                                avail_qty = 0.0
                            break
                except Exception:
                    avail_qty = 0.0

                allocated_total = 0.0
                try:
                    allocated_total = float(db.get_allocated_qty(asset) or 0.0)
                except Exception:
                    allocated_total = 0.0

                free_qty = max(0.0, avail_qty - allocated_total)

                if desired_qty is None:
                    # sem cota definida: pega tudo que está livre
                    if free_qty > 0:
                        allocated_qty = free_qty
                        break
                else:
                    # com cota definida: aloca no máximo o que está livre
                    if free_qty > 0:
                        allocated_qty = min(free_qty, float(desired_qty))
                        break

                log(logger, args.bot_id, {
                    "event": "waiting_balance",
                    "message": "Aguardando saldo livre para cota do bot",
                    "asset": asset,
                    "available": avail_qty,
                    "allocated_other_bots": allocated_total,
                    "free": free_qty,
                    "desired": desired_qty or 0.0,
                })
                time.sleep(5)

        else:
            # Modo dry-run: simula saldo e reserva %
            # Assume saldo simulado de 1000 USDT para base de cálculo
            simulated_balance_usdt = 1000.0
            reserved_usdt = simulated_balance_usdt * (args.reserve_pct / 100.0)
            
            # Calcula entry simulado se necessário
            if entry_arg is None or entry_arg <= 0:
                # Busca preço atual para simulação
                try:
                    try:
                        from . import api as kucoin_api
                    except Exception:
                        import api as kucoin_api  # type: ignore
                    p = kucoin_api.get_price(symbol_u)
                    computed_entry = float(p) if p else 1.0
                except Exception:
                    computed_entry = 1.0  # Fallback
            
            # Calcula quantidade baseada em reserva
            if size_arg is None or size_arg <= 0:
                # Simula compra com fundos reservados
                allocated_qty = reserved_usdt / computed_entry
            else:
                allocated_qty = size_arg
            
            log(logger, args.bot_id, {
                "event": "dry_allocation",
                "message": "Simulação de alocação em dry-run",
                "simulated_balance_usdt": simulated_balance_usdt,
                "reserved_usdt": reserved_usdt,
                "computed_entry": computed_entry,
                "allocated_qty": allocated_qty,
            })

        # Código comum para ambos os modos: finaliza entry/size se necessário
        # Se ainda não temos entry, usa preço atual
        if computed_entry is None:
            try:
                try:
                    from . import api as kucoin_api
                except Exception:
                    import api as kucoin_api  # type: ignore
                p = kucoin_api.get_price(symbol_u)
                computed_entry = float(p) if p else None
            except Exception:
                computed_entry = None

        if computed_entry is None or computed_entry <= 0 or (not args.dry and (allocated_qty is None or allocated_qty <= 0)):
            log(logger, args.bot_id, {
                "event": "error",
                "message": "Não foi possível determinar entry/size automaticamente",
                "computed_entry": computed_entry,
                "allocated_qty": allocated_qty,
            })
            sys.exit(1)

        # Grava cota no DB apenas em modo real (bloqueia outros bots)
        if not args.dry:
            try:
                db.upsert_bot_quota(args.bot_id, symbol_u, asset, float(allocated_qty), float(computed_entry))
            except Exception:
                pass

        # Sobrescreve args efetivos
        size_arg = float(allocated_qty)
        funds_arg = None
        entry_arg = float(computed_entry)

        log(logger, args.bot_id, {
            "event": "quota_allocated",
            "symbol": symbol_u,
            "asset": asset,
            "qty": float(allocated_qty),
            "entry_price": float(entry_arg),
            "note": "Bot iniciado usando posição real previamente comprada" if not args.dry else "Bot iniciado com simulação de reserva em dry-run",
        })

        lowest_price = 0.0
        lowest_qty = 0.0
        try:
            lowest_price = float(lowest_buy.get("price") or 0.0)
        except Exception:
            lowest_price = 0.0
        try:
            lowest_qty = float(lowest_buy.get("qty") or 0.0)
        except Exception:
            lowest_qty = 0.0

        # Se entry do usuário foi informado e é >0, usa; senão usa menor BUY; senão usa preço atual
        computed_entry = entry_arg if entry_arg and entry_arg > 0 else (lowest_price if lowest_price > 0 else None)

        # Cota/size: se usuário informou size>0, essa é a cota desejada;
        # senão, usa a quantidade comprada no menor BUY.
        desired_qty = size_arg if size_arg is not None else (lowest_qty if lowest_qty > 0 else None)

        # Loop de espera por saldo disponível (desconta o que já está alocado por outros bots)
        while True:
            try:
                # api pode falhar / credenciais inválidas; se falhar, espera
                try:
                    from . import api as kucoin_api
                except Exception:
                    import api as kucoin_api  # type: ignore

                balances = kucoin_api.get_balances(account_type="trade")
                avail_qty = 0.0
                for b in balances or []:
                    if (b.get("currency") or "").upper() == asset:
                        try:
                            avail_qty = float(b.get("available") or 0.0)
                        except Exception:
                            avail_qty = 0.0
                        break
            except Exception:
                avail_qty = 0.0

            allocated_total = 0.0
            try:
                allocated_total = float(db.get_allocated_qty(asset) or 0.0)
            except Exception:
                allocated_total = 0.0

            free_qty = max(0.0, avail_qty - allocated_total)

            if desired_qty is None:
                # sem cota definida: pega tudo que está livre
                if free_qty > 0:
                    allocated_qty = free_qty
                    break
            else:
                # com cota definida: aloca no máximo o que está livre
                if free_qty > 0:
                    allocated_qty = min(free_qty, float(desired_qty))
                    break

            log(logger, args.bot_id, {
                "event": "waiting_balance",
                "message": "Aguardando saldo livre para cota do bot",
                "asset": asset,
                "available": avail_qty,
                "allocated_other_bots": allocated_total,
                "free": free_qty,
                "desired": desired_qty or 0.0,
            })
            time.sleep(5)

        # Se ainda não temos entry, usa preço atual
        if computed_entry is None:
            try:
                try:
                    from . import api as kucoin_api
                except Exception:
                    import api as kucoin_api  # type: ignore
                p = kucoin_api.get_price(symbol_u)
                computed_entry = float(p) if p else None
            except Exception:
                computed_entry = None

        if computed_entry is None or computed_entry <= 0 or (not args.dry and (allocated_qty is None or allocated_qty <= 0)):
            log(logger, args.bot_id, {
                "event": "error",
                "message": "Não foi possível determinar entry/size automaticamente",
                "computed_entry": computed_entry,
                "allocated_qty": allocated_qty,
            })
            sys.exit(1)

        # Grava cota no DB apenas em modo real (bloqueia outros bots)
        if not args.dry:
            try:
                db.upsert_bot_quota(args.bot_id, symbol_u, asset, float(allocated_qty), float(computed_entry))
            except Exception:
                pass

        # Sobrescreve args efetivos
        size_arg = float(allocated_qty)
        funds_arg = None
        entry_arg = float(computed_entry)

        log(logger, args.bot_id, {
            "event": "quota_allocated",
            "symbol": symbol_u,
            "asset": asset,
            "qty": float(allocated_qty),
            "entry_price": float(entry_arg),
            "note": "Bot iniciado usando posição real previamente comprada" if not args.dry else "Bot iniciado com simulação de reserva em dry-run",
        })

    # ======================================================
    # Garantia: entry_price precisa ser > 0
    # - Em DRY, a UI costuma iniciar com entry=0 (auto). Isso quebrava o simulador
    #   (`ZeroDivisionError` ao calcular change_pct) e o bot encerrava imediatamente.
    # - Em REAL, entry<=0 é inválido (a menos que o bloco de auto-entry acima tenha
    #   preenchido entry_arg).
    # ======================================================
    if entry_arg is None or float(entry_arg) <= 0:
        symbol_u = str(args.symbol).upper().strip()
        fetched = None
        try:
            try:
                from . import api as kucoin_api
            except Exception:
                import api as kucoin_api  # type: ignore
            p = kucoin_api.get_price(symbol_u)
            if p is not None:
                try:
                    fetched = float(p)
                except Exception:
                    fetched = None
        except Exception:
            fetched = None

        if fetched is not None and fetched > 0:
            entry_arg = float(fetched)
            log(logger, args.bot_id, {
                "event": "entry_auto_price",
                "symbol": symbol_u,
                "entry_price": float(entry_arg),
                "note": "Entry preenchido automaticamente para evitar entry=0",
            })
        else:
            if args.dry:
                # Fallback seguro para não crashar o simulador mesmo sem rede.
                entry_arg = 1.0
                log(logger, args.bot_id, {
                    "event": "entry_fallback",
                    "symbol": symbol_u,
                    "entry_price": float(entry_arg),
                    "note": "Fallback de entry em DRY (falha ao buscar preço)",
                })
            else:
                log(logger, args.bot_id, {
                    "event": "error",
                    "message": "Entry inválido (<=0) e não foi possível buscar preço atual",
                    "symbol": symbol_u,
                })
                sys.exit(1)

    bot = EnhancedTradeBot(
        symbol=args.symbol,
        entry_price=float(entry_arg) if entry_arg is not None else float(args.entry),
        mode=args.mode,
        targets=targets,
        interval=args.interval,
        size=size_arg,
        funds=funds_arg,
        dry_run=args.dry,
        bot_id=args.bot_id,
        logger=logger,
        target_profit_pct=args.target_profit_pct,
        # Eternal mode interno NÃO é usado para o modo contínuo desejado.
        eternal_mode=False,
    )

    try:
        bot.run()
    finally:
        # Libera a cota do bot ao sair
        try:
            db.release_bot_quota(args.bot_id)
        except Exception:
            pass
        # Best-effort: marcar sessão como stopped
        try:
            db.update_bot_session(args.bot_id, {"status": "stopped", "end_ts": time.time()})
        except Exception:
            pass

