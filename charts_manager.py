import pandas as pd
import numpy as np
import streamlit as st

from database import db


class ChartsManager:
    def __init__(self, days: int = 30):
        self.days = days

    # ======================================================
    # EQUITY HISTORY
    # ======================================================
    def load_equity_history(self, bot_id: str = None):
        """
        Carrega histórico de equity a partir do database.
        """
        rows = db.get_equity_history(days=self.days)

        if not rows:
            return pd.DataFrame()

        df = pd.DataFrame(rows)

        # Colunas obrigatórias
        required = {"timestamp", "balance_usdt"}
        if not required.issubset(df.columns):
            return pd.DataFrame()

        if bot_id:
            df = df[df["bot_id"] == bot_id]

        df = df.sort_values("timestamp")
        df["time"] = pd.to_datetime(df["timestamp"], unit="s")

        return df

    # ======================================================
    # PNL HISTORY
    # ======================================================
    def load_pnl_history(self, bot_id: str = None):
        """
        Histórico de PnL acumulado (tabela trades).
        """
        rows = db.get_trades(bot_id=bot_id)

        if not rows:
            return pd.DataFrame()

        df = pd.DataFrame(rows)

        if "timestamp" not in df.columns or "profit" not in df.columns:
            return pd.DataFrame()

        df = df.sort_values("timestamp")
        df["time"] = pd.to_datetime(df["timestamp"], unit="s")
        df["pnl_usdt"] = df["profit"].cumsum()

        return df[["time", "pnl_usdt"]]

    # ======================================================
    # METRICS
    # ======================================================
    def calculate_cumulative_pnl(self, bot_id: str = None) -> float:
        pnl_df = self.load_pnl_history(bot_id)
        if pnl_df.empty:
            return 0.0
        return round(pnl_df["pnl_usdt"].iloc[-1], 2)

    def calculate_max_drawdown(self, bot_id: str = None) -> float:
        df = self.load_equity_history(bot_id)

        if df.empty:
            return 0.0

        equity = df["balance_usdt"]
        peak = equity.cummax()
        drawdown = (equity - peak) / peak

        return round(drawdown.min() * 100, 2)

    def calculate_sharpe_ratio(self, bot_id: str = None) -> float:
        df = self.load_equity_history(bot_id)

        if len(df) < 2:
            return 0.0

        equity = df["balance_usdt"]
        returns = equity.pct_change().dropna()

        if returns.std() == 0:
            return 0.0

        sharpe = (returns.mean() / returns.std()) * np.sqrt(len(returns))
        return round(sharpe, 2)

    # ======================================================
    # RENDER GRÁFICOS
    # ======================================================
    def render_equity_vs_btc(self, bot_id: str = None):
        df = self.load_equity_history(bot_id)

        if df.empty or "btc_price" not in df.columns:
            st.info("Sem dados suficientes para Equity vs BTC.")
            return

        plot_df = df.set_index("time")[["balance_usdt", "btc_price"]].dropna()
        st.line_chart(plot_df, use_container_width=True)

    def render_equity_comparison(self):
        df = self.load_equity_history()

        if df.empty:
            st.info("Sem dados para comparação.")
            return

        pivot = (
            df.pivot_table(
                index="time",
                columns="bot_id",
                values="balance_usdt",
                aggfunc="last",
            )
            .sort_index()
        )

        st.line_chart(pivot, use_container_width=True)

    def render_consolidated_equity(self):
        df = self.load_equity_history()

        if df.empty:
            st.info("Sem dados consolidados.")
            return

        grouped = (
            df.groupby("time")["balance_usdt"]
            .sum()
            .to_frame("Equity Total")
        )

        st.line_chart(grouped, use_container_width=True)

    def render_normalized_equity_vs_btc(self, bot_id: str = None):
        df = self.load_equity_history(bot_id)

        if df.empty or "btc_price" not in df.columns:
            st.info("Sem dados para normalização.")
            return

        base_equity = df["balance_usdt"].iloc[0]
        base_btc = df["btc_price"].iloc[0]

        df_norm = pd.DataFrame({
            "Equity (Base 100)": (df["balance_usdt"] / base_equity) * 100,
            "BTC Hold (Base 100)": (df["btc_price"] / base_btc) * 100,
        }, index=df["time"])

        st.line_chart(df_norm, use_container_width=True)

