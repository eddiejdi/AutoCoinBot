import types
import time
import pytest

import ui


def test_confirm_pid_dead_all_dead(monkeypatch):
    # Simulate _pid_alive always False
    monkeypatch.setattr(ui, "_pid_alive", lambda pid: False)
    # Use zero delay to speed test
    assert ui._confirm_pid_dead(12345, checks=3, delay_s=0) is True


def test_confirm_pid_dead_alive_once(monkeypatch):
    # Simulate _pid_alive returns True first then False
    calls = {"n": 0}

    def _fake(pid):
        calls["n"] += 1
        return calls["n"] == 1

    monkeypatch.setattr(ui, "_pid_alive", _fake)
    # If _pid_alive returns True on first check, confirmation should fail
    assert ui._confirm_pid_dead(12345, checks=3, delay_s=0) is False


class DummyDB:
    def __init__(self):
        self.updated = []

    def get_active_bots(self):
        # Return one active session with pid
        return [{"id": "bot_test", "pid": 99999}]

    def update_bot_session(self, bot_id, updates):
        self.updated.append((bot_id, updates))

    def release_bot_quota(self, bot_id):
        pass


def test_kill_active_bot_sessions_marks_stopped(monkeypatch):
    # Replace DatabaseManager with a shared DummyDB instance
    db_instance = DummyDB()
    monkeypatch.setattr(ui, "DatabaseManager", lambda: db_instance)

    # Ensure kill-on-start guard uses session fallback
    monkeypatch.setattr(ui, "_KILL_ON_START_GUARD_RESOURCE", None)
    ui._KILL_ON_START_DONE = False

    # Monkeypatch BotController.stop_all_continuous to no-op
    class DummyBC:
        @staticmethod
        def stop_all_continuous():
            return None

    monkeypatch.setattr(ui, "BotController", DummyBC)

    # Monkeypatch _confirm_pid_dead to return True (PID considered dead)
    monkeypatch.setattr(ui, "_confirm_pid_dead", lambda pid: True)

    # Provide a lightweight st.session_state to avoid streamlit dependency
    monkeypatch.setattr(ui, "st", types.SimpleNamespace(session_state={}))

    # Run cleanup
    ui._kill_active_bot_sessions_on_start(controller=None)

    # Verify DB update called marking bot stopped
    db = db_instance
    assert len(db.updated) == 1
    bot_id, updates = db.updated[0]
    assert bot_id == "bot_test"
    assert updates.get("status") == "stopped"
    assert "end_ts" in updates
