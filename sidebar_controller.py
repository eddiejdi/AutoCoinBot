import streamlit as st
from pathlib import Path
import time
import requests
import os
import sys

# Ensure current directory is in sys.path for imports
sys.path.insert(0, os.path.dirname(__file__))

try:
    import importlib.util
    spec = importlib.util.spec_from_file_location("api", os.path.join(os.path.dirname(__file__), "api.py"))
    api = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api)
    from database import DatabaseManager
except Exception:
    import importlib.util
    spec = importlib.util.spec_from_file_location("api", os.path.join(os.path.dirname(__file__), "api.py"))
    api = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api)
    from database import DatabaseManager


class SidebarController:
    def __init__(self):
        self.db = DatabaseManager()
        self._usd_brl_rate = None
        self._usd_brl_cache_time = 0
    
    # --------------------------------------------------
    # COTAÇÃO USD/BRL
    # --------------------------------------------------
    def get_usd_brl_rate(self) -> float:
        """Obtém cotação USD/BRL (com cache de 5 minutos)"""
        now = time.time()
        
        # Cache válido por 5 minutos
        if self._usd_brl_rate and (now - self._usd_brl_cache_time) < 300:
            return self._usd_brl_rate
        
        try:
            # Usar API pública gratuita
            response = requests.get(
                "https://economia.awesomeapi.com.br/json/last/USD-BRL",
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                rate = float(data.get("USDBRL", {}).get("bid", 6.0))
                self._usd_brl_rate = rate
                self._usd_brl_cache_time = now
                return rate
        except Exception:
            pass
        
        # Fallback: valor aproximado
        return self._usd_brl_rate or 6.0
    
    # --------------------------------------------------
    # PARSE TARGETS STRING
    # --------------------------------------------------
    @staticmethod
    def parse_targets(targets_str: str):
        """Parse '2:0.3,5:0.5' -> [(2.0, 0.3), (5.0, 0.5)]"""
        out = []
        if not targets_str:
            return out
        for part in targets_str.split(","):
            if ":" not in part:
                continue
            try:
                pct, portion = part.split(":", 1)
                out.append((float(pct), float(portion)))
            except ValueError:
                continue
        return out
    
    @staticmethod
    def check_recent_trade() -> bool:
        """
        Verifica se houve um trade executado recentemente (últimos 3 segundos)
        Retorna True se houver sinal de trade, False caso contrário
        """
        try:
            signal_file = Path(__file__).parent / ".trade_signal"
            if signal_file.exists():
                # Verificar se o arquivo é recente (menos de 3 segundos)
                mtime = signal_file.stat().st_mtime
                if time.time() - mtime < 3:
                    return True
                else:
                    # Deletar arquivo antigo
                    signal_file.unlink()
            return False
        except Exception:
            return False

    # --------------------------------------------------
    # CÁLCULO DE CUSTO MÉDIO E P&L
    # --------------------------------------------------
    def get_average_cost_by_currency(self, currency: str) -> dict:
        """
        Calcula custo médio de compra por moeda baseado em histórico de trades
        Retorna: {avg_cost, total_bought, total_sold, qty_held}
        """
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            symbol = f"{currency}-USDT"
            
            # Busca todos os trades (compras e vendas)
            cursor.execute('''
                SELECT side, price, size, funds 
                FROM trades 
                WHERE symbol = ? AND dry_run = 0
                ORDER BY timestamp ASC
            ''', (symbol,))
            
            trades = cursor.fetchall()
            conn.close()
            
            total_cost = 0.0
            total_qty = 0.0
            
            for trade in trades:
                side = trade[0]  # "buy" ou "sell"
                price = float(trade[1])
                size = float(trade[2]) if trade[2] else 0.0
                
                if side == "buy":
                    total_cost += price * size
                    total_qty += size
                elif side == "sell":
                    total_qty -= size
            
            avg_cost = (total_cost / total_qty) if total_qty > 0 else 0.0
            
            return {
                "avg_cost": avg_cost,
                "qty_held": total_qty,
                "total_invested": total_cost
            }
        except Exception as e:
            return {
                "avg_cost": 0.0,
                "qty_held": 0.0,
                "total_invested": 0.0
            }

    @staticmethod
    def calculate_portfolio_value(balances: list) -> dict:
        """
        Calcula valor total da carteira em USDT
        Retorna: {total_usdt, moedas_com_valor}
        """
        total_usdt = 0.0
        assets_value = []
        
        for b in balances:
            cur = b["currency"]
            avail = b.get("available", 0.0)
            
            # Se for USDT, valor é o saldo direto
            if cur == "USDT":
                value_usdt = float(avail) if avail else 0.0
                assets_value.append({
                    "currency": cur,
                    "amount": value_usdt,
                    "value_usdt": value_usdt,
                    "is_usdt": True
                })
                total_usdt += value_usdt
            else:
                # Para outras moedas, tenta pegar preço atual
                try:
                    symbol = f"{cur}-USDT"
                    price = api.get_price(symbol)
                    if price and avail and avail > 0:
                        avail_float = float(avail)
                        price_float = float(price)
                        value_usdt = avail_float * price_float
                        if value_usdt > 0:  # Só adiciona se tiver valor
                            assets_value.append({
                                "currency": cur,
                                "amount": avail_float,
                                "price": price_float,
                                "value_usdt": value_usdt,
                                "is_usdt": False
                            })
                            total_usdt += value_usdt
                except Exception as e:
                    pass  # Silenciosamente ignora moedas sem preço
        
        return {
            "total_usdt": total_usdt,
            "assets": assets_value
        }

    # --------------------------------------------------
    # SALDOS COLORIDOS COM P&L REAL
    # --------------------------------------------------
    @staticmethod
    def render_targets_horizontal():
        """Renderiza targets configurados de forma horizontal"""
        try:
            if "targets" in st.session_state and st.session_state.targets:
                targets = st.session_state.targets
                if isinstance(targets, str):
                    # Parse string format: "1:0.3,3:0.5,5:0.2"
                    target_list = []
                    for part in targets.split(','):
                        if ':' in part:
                            tier, portion = part.split(':')
                            target_list.append(f"Tier {tier}: {float(portion)*100:.0f}%")
                    
                    if target_list:
                        st.markdown("**📊 Targets:** " + " | ".join(target_list))
        except Exception:
            pass

    def render_balances(self, container=None):
        """Render balances section"""
        sidebar = container if container is not None else st.sidebar

        try:
            # Check if API credentials are configured
            if not hasattr(api, '_has_keys') or not api._has_keys():
                sidebar.warning("⚠️ API credentials not configured")
                sidebar.info("💡 Configure KUCOIN_API_KEY, KUCOIN_API_SECRET, and KUCOIN_API_PASSPHRASE in .env file")
                return

            balances = api.get_balances()
            if not balances or len(balances) == 0:
                sidebar.info("📭 Nenhum saldo disponível")
                return

            # Calcular valor total da carteira
            portfolio = self.calculate_portfolio_value(balances)
            total_usdt = portfolio["total_usdt"]
            assets = portfolio["assets"]
            
            if total_usdt == 0:
                sidebar.warning("⚠️ Saldo total é zero")
                return
            
            # 📊 Mostra saldo total de investimento
            sidebar.markdown(f"### 📊 **${total_usdt:,.2f}**")
            
            sidebar.markdown("<hr style='margin: 0.5rem 0'>", unsafe_allow_html=True)
            
            # Listar cada ativo com P&L real
            if len(assets) == 0:
                sidebar.info("Sem ativos com valor")
                return
            
            # Separa USDT das outras moedas
            usdt_assets = [a for a in assets if a["currency"] == "USDT"]
            crypto_assets = [a for a in assets if a["currency"] != "USDT"]
            
            # Mostra USDT
            if usdt_assets:
                for asset in usdt_assets:
                    value = asset["value_usdt"]
                    pct = (value / total_usdt) * 100 if total_usdt > 0 else 0
                    
                    col1, col2, col3 = sidebar.columns([2, 2, 2])
                    with col1:
                        st.write("💵 **USDT**")
                    with col2:
                        st.write(f"`${value:,.0f}`")
                    with col3:
                        st.markdown(f"<span style='color:#c9d1d9'>{pct:.1f}%</span>", 
                                    unsafe_allow_html=True)
            
            # Mostra cryptos com P&L
            if crypto_assets:
                sidebar.markdown("<hr style='margin: 0.5rem 0'>", unsafe_allow_html=True)
                
                for asset in crypto_assets:
                    try:
                        cur = asset["currency"]
                        amount = asset["amount"]
                        price_current = asset["price"]
                        value_current = asset["value_usdt"]
                        pct_portfólio = (value_current / total_usdt) * 100 if total_usdt > 0 else 0
                        
                        # Obtém custo médio do histórico
                        cost_info = self.get_average_cost_by_currency(cur)
                        cost_avg = cost_info["avg_cost"]
                        
                        # Calcula P&L
                        if cost_avg > 0 and amount > 0:
                            value_invested = cost_avg * amount
                            pl_value = value_current - value_invested
                            pl_pct = ((price_current - cost_avg) / cost_avg) * 100
                            
                            # Determina cor e emoji
                            if pl_pct > 0:
                                color_pl = "#22c55e"  # Verde
                                emoji_pl = "📈"
                            elif pl_pct < 0:
                                color_pl = "#ef4444"  # Vermelho
                                emoji_pl = "📉"
                            else:
                                color_pl = "#c9d1d9"  # Cinza
                                emoji_pl = "➡️"
                        else:
                            pl_value = 0
                            pl_pct = 0
                            color_pl = "#c9d1d9"
                            emoji_pl = "➡️"
                        
                        # Calcular preço target de venda
                        target_profit_pct = st.session_state.get("target_profit_pct", 2.0)
                        target_price = cost_avg * (1 + target_profit_pct / 100) if cost_avg > 0 else 0
                        distance_to_target = ((target_price - price_current) / price_current * 100) if price_current > 0 else 0
                        
                        # Cor para distância ao target
                        if distance_to_target <= 0:
                            color_target = "#22c55e"  # Verde - já atingiu
                            emoji_target = "✅"
                        elif distance_to_target <= 2:
                            color_target = "#fbbf24"  # Amarelo - perto
                            emoji_target = "⚡"
                        else:
                            color_target = "#60a5fa"  # Azul - longe
                            emoji_target = "📍"
                        
                        # Layout melhorado
                        col1, col2 = sidebar.columns([3, 3])
                        
                        with col1:
                            st.write(f"💎 **{cur}**")
                            st.caption(f"{amount:.6f}")
                        
                        with col2:
                            # Preço e P&L %
                            st.write(f"`${price_current:,.2f}`")
                            st.markdown(
                                f"<span style='color:{color_pl};font-weight:bold;font-size:0.9em'>"
                                f"{emoji_pl} {pl_pct:+.2f}%</span>",
                                unsafe_allow_html=True
                            )
                        
                        # Linha de detalhe - Valor, Custo e % carteira
                        col1, col2, col3 = sidebar.columns([2, 2, 2])
                        with col1:
                            st.caption(f"Valor: ${value_current:,.2f}")
                        with col2:
                            if cost_avg > 0:
                                st.caption(f"Custo: ${cost_avg:,.2f}")
                            else:
                                st.caption("Custo: -")
                        with col3:
                            st.caption(f"{pct_portfólio:.1f}% carteira")
                        
                        # Linha de target - Preço Alvo, Distância e Meta
                        col1, col2, col3 = sidebar.columns([2, 2, 2])
                        with col1:
                            if target_price > 0:
                                st.caption(f"🎯 Alvo: ${target_price:,.2f}")
                            else:
                                st.caption("🎯 Alvo: -")
                        with col2:
                            st.markdown(
                                f"<span style='color:{color_target};font-weight:bold;font-size:0.85em'>"
                                f"{emoji_target} {distance_to_target:+.2f}%</span>",
                                unsafe_allow_html=True
                            )
                        with col3:
                            st.caption(f"Meta: +{target_profit_pct:.1f}%")
                        
                        # Linha resumida - Valor que precisa alcançar
                        # if target_price > 0:
                        #     sidebar.markdown(f"💰 {cur} precisa alcançar **${target_price:,.2f}** para +{target_profit_pct:.1f}%")
                        
                        st.markdown("<hr style='margin: 0.3rem 0'>", unsafe_allow_html=True)
                        
                    except Exception as item_error:
                        sidebar.warning(f"⚠️ Erro: {cur}")
                        continue
                    
        except Exception as e:
            sidebar.error(f"❌ Erro ao carregar saldos")
            sidebar.info("💡 Verifique API")

    # --------------------------------------------------
    # INPUTS DO BOT
    # --------------------------------------------------
    def render_inputs(self, container=None):
        """Render inputs section"""
        sidebar = container if container is not None else st.sidebar
        sidebar.header("Controls")

        symbol = st.text_input("Symbol", "BTC-USDT", key="symbol")
        
        # Busca o preço atual do símbolo como valor padrão para Entry
        try:
            current_price = api.get_price(symbol)
            default_entry = float(current_price) if current_price else 0.0
        except:
            default_entry = 0.0
        
        st.number_input("Entry", value=default_entry, key="entry")

        st.selectbox(
            "Mode",
            ["sell", "buy", "mixed", "flow"],
            key="mode",
        )

        st.text_input(
            "Targets",
            "1:0.3,3:0.5,5:0.2",
            key="targets",
        )

        st.number_input("Interval", value=5.0, key="interval")
        st.number_input("Size", value=0.0006, format="%.6f", key="size")
        st.number_input("Funds", value=20.0, key="funds")
        
        # ===== NOVOS PARÂMETROS: RESERVA E LUCRO =====
        st.divider()
        st.markdown("**💰 Gestão de Fundos**")
        st.number_input(
            "Reserve % do Saldo",
            min_value=1.0,
            max_value=100.0,
            value=50.0,
            step=5.0,
            help="% do saldo USDT disponível a reservar para o bot",
            key="reserve_pct",
        )
        
        st.number_input(
            "Lucro Alvo (%)",
            min_value=0.1,
            max_value=100.0,
            value=2.0,
            step=0.5,
            help="% de lucro esperado antes de vender",
            key="target_profit_pct",
        )
        
        # ===== CÁLCULO DE TARGETS E LUCRO PREVISTO =====
        self._render_target_preview()
        
        # ===== START N BOTS =====
        st.divider()
        st.markdown("**🤖 Multi-Bot Launch**")
        st.number_input(
            "Start N Bots",
            min_value=1,
            max_value=10,
            value=1,
            step=1,
            help="Número de bots idênticos a iniciar simultaneamente",
            key="num_bots",
        )
        
        # ===== ETERNAL RUNNING MODE =====
        st.divider()
        st.markdown("**🔄 Eternal Running**")
        st.checkbox(
            "Ativar Eternal Mode",
            value=False,
            help="Quando ativado, o bot reinicia automaticamente após atingir todos os targets",
            key="eternal_mode",
        )
        
        if st.session_state.get("eternal_mode", False):
            st.caption("🔁 Bot reiniciará automaticamente após cada ciclo completo")

    # --------------------------------------------------
    # PREVIEW DE TARGETS E LUCRO
    # --------------------------------------------------
    def _render_target_preview(self):
        """Exibe preview dos targets em $ e lucro previsto"""
        st.divider()
        st.markdown("**🎯 Preview de Targets**")
        
        try:
            entry = float(st.session_state.get("entry", 0))
            targets_str = st.session_state.get("targets", "")
            funds = float(st.session_state.get("funds", 0))
            size = float(st.session_state.get("size", 0))
            mode = st.session_state.get("mode", "sell")
            
            if entry <= 0:
                st.caption("⚠️ Defina o Entry Price")
                return
            
            targets = self.parse_targets(targets_str)
            if not targets:
                st.caption("⚠️ Configure os targets (ex: 2:0.3,5:0.5)")
                return
            
            # Calcular tamanho total da posição
            if size > 0:
                position_size = size
                position_value = size * entry
            elif funds > 0:
                position_size = funds / entry
                position_value = funds
            else:
                st.caption("⚠️ Defina Size ou Funds")
                return
            
            # Obter cotação USD/BRL
            usd_brl = self.get_usd_brl_rate()
            
            total_profit = 0.0
            
            # Exibir cada target
            for i, (pct, portion) in enumerate(targets, 1):
                if mode == "sell":
                    target_price = entry * (1 + pct / 100)
                else:  # buy
                    target_price = entry * (1 - pct / 100)
                
                # Lucro para esta porção
                portion_size = position_size * portion
                if mode == "sell":
                    profit_usdt = portion_size * (target_price - entry)
                else:
                    profit_usdt = portion_size * (entry - target_price)
                
                profit_brl = profit_usdt * usd_brl
                total_profit += profit_usdt
                
                # Cor baseada no lucro
                color = "#4ade80" if profit_usdt > 0 else "#ff6b6b"
                
                st.markdown(f'''
                <div style="background: #0a0a0a; border: 1px solid #333; border-radius: 4px; 
                            padding: 8px; margin: 4px 0; font-family: monospace; font-size: 12px;">
                    <div style="display: flex; justify-content: space-between;">
                        <span style="color: #888;">T{i} ({pct:+.1f}%)</span>
                        <span style="color: #fbbf24; font-weight: bold;">${target_price:,.2f}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-top: 4px;">
                        <span style="color: #888;">Porção: {portion*100:.0f}%</span>
                        <span style="color: {color}; font-weight: bold;">
                            ${profit_usdt:+.2f} <span style="color: #22d3ee;">R${profit_brl:+.2f}</span>
                        </span>
                    </div>
                </div>
                ''', unsafe_allow_html=True)
            
            # Total em USD e BRL
            total_profit_brl = total_profit * usd_brl
            total_color = "#4ade80" if total_profit > 0 else "#ff6b6b"
            total_pct = (total_profit / position_value * 100) if position_value > 0 else 0
            
            st.markdown(f'''
            <div style="background: #111; border: 2px solid {total_color}; border-radius: 6px; 
                        padding: 10px; margin-top: 8px; font-family: monospace;">
                <div style="text-align: center;">
                    <div style="color: #888; font-size: 11px;">💵 LUCRO TOTAL PREVISTO (RETIRADA)</div>
                    <div style="color: {total_color}; font-size: 20px; font-weight: bold;">
                        ${total_profit:+.2f}
                    </div>
                    <div style="color: #22d3ee; font-size: 18px; font-weight: bold;">
                        🇧🇷 R${total_profit_brl:+.2f}
                    </div>
                    <div style="color: #888; font-size: 11px; margin-top: 4px;">
                        ({total_pct:+.2f}% do investimento)
                    </div>
                    <div style="color: #666; font-size: 10px; margin-top: 6px; border-top: 1px solid #333; padding-top: 6px;">
                        Cotação: $1 = R${usd_brl:.2f}
                    </div>
                </div>
            </div>
            ''', unsafe_allow_html=True)
            
        except Exception as e:
            st.caption(f"⚠️ Erro ao calcular: {e}")

    # --------------------------------------------------
    # AÇÕES (SEM LÓGICA)
    # --------------------------------------------------
    def render_actions(self, container=None):
        """Render actions section"""
        sidebar = container if container is not None else st.sidebar
        sidebar.divider()
        sidebar.subheader("🚀 Bot Control")

        col1, col2 = sidebar.columns(2)
        
        with col1:
            start_real = st.button("▶️ START (REAL)", type="primary", key="start_real")
        
        with col2:
            kill_bot = st.button("🛑 KILL BOT", type="secondary", key="kill_bot")

        start_dry = sidebar.button("🧪 START (DRY-RUN)", key="start_dry")

        num_bots = st.session_state.get("num_bots", 1)
        return start_real, start_dry, kill_bot, num_bots

    # --------------------------------------------------
    # STATUS DO BOT
    # --------------------------------------------------
    def get_bot_status(self) -> dict:
        """
        Retorna status atual do bot (running/stopped)
        """
        is_running = st.session_state.get("bot_running", False)
        target = st.session_state.get("target_profit_pct", 2.0)
        entry = st.session_state.get("entry", 0.0)
        symbol = st.session_state.get("symbol", "BTC-USDT")
        
        return {
            "is_running": is_running,
            "target": target,
            "entry": entry,
            "symbol": symbol
        }

    # --------------------------------------------------
    # SIDEBAR COMPLETO
    # --------------------------------------------------
    def render(self):
        with st.sidebar:
            # Obter status do bot
            status = self.get_bot_status()

            # Mostrar título com status e alvo
            if status["is_running"]:
                st.sidebar.markdown(
                    f"### 🤖 **BOT RODANDO** | 🎯 Alvo: +{status['target']:.1f}%"
                )
            else:
                st.sidebar.markdown(
                    f"### 🤖 **BOT PARADO** | 🎯 Alvo: +{status['target']:.1f}%"
                )

            st.sidebar.markdown("<hr style='margin: 0.3rem 0'>", unsafe_allow_html=True)

            self.render_balances()
            st.divider()
            self.render_inputs()
            return self.render_actions()

    def render_in(self, container):
        """Render sidebar controls dentro de um container específico"""
        with container:
            # Obter status do bot
            status = self.get_bot_status()

            # Mostrar título com status e alvo
            if status["is_running"]:
                st.markdown(
                    f"### 🤖 **BOT RODANDO** | 🎯 Alvo: +{status['target']:.1f}%"
                )
            else:
                st.markdown(
                    f"### 🤖 **BOT PARADO** | 🎯 Alvo: +{status['target']:.1f}%"
                )

            st.markdown("<hr style='margin: 0.3rem 0'>", unsafe_allow_html=True)

            self.render_balances()
            st.divider()
            self.render_inputs()
            return self.render_actions()

