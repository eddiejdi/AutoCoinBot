# kucoin_app/bot_session.py
from pathlib import Path
import streamlit as st


class BotSession:
    """
    Classe de compatibilidade.
    Mantém a API original esperada pelo projeto.
    """

    ROOT = Path(__file__).resolve().parent
    BOT_LOG_DIR = ROOT / "bot_logs"

    @staticmethod
    def get_active_bot_id():
        """
        Retorna o bot_id ativo a partir da query string (?bot=...)
        """
        params = st.query_params
        bot_id = params.get("bot") or params.get("bot_id")

        if not bot_id:
            return None

        try:
            if isinstance(bot_id, (list, tuple)):
                bot_id = bot_id[0] if bot_id else None
        except Exception:
            pass

        if not bot_id:
            return None

        if not str(bot_id).startswith("bot_"):
            bot_id = f"bot_{bot_id}"

        return str(bot_id)

    @staticmethod
    def get_bot_log_file(bot_id: str) -> Path:
        """
        Retorna o caminho correto do arquivo de log
        """
        return BotSession.BOT_LOG_DIR / f"{bot_id}.log"

