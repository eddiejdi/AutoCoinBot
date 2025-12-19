#!/usr/bin/env python3
"""
manage_bot_service.py (corrigido)

Script para automatizar configuração do ambiente do bot e gerenciamento:
- cria venv em ~/Downloads/kucoin_app/venv (se necessário)
- instala requirements.txt (se existir)
- cria logs dir
- cria user systemd unit em ~/.config/systemd/user/kucoin-bot@.service
- habilita/ativa/desativa/desinstala o serviço (por símbolo)
- fallback para nohup se systemd --user não disponível

Use por exemplo:
  python scripts/manage_bot_service.py install --symbol BTC-USDT --entry 88000 --no-dry
  python scripts/manage_bot_service.py stop --symbol BTC-USDT
"""

import os
import sys
import argparse
import subprocess
import shutil
import time
import json
from pathlib import Path
import stat

HOME = Path.home()
PROJECT = HOME / "Downloads" / "kucoin_app"
VENV = PROJECT / "venv"
PY_BIN = VENV / "bin" / "python"
PIP_BIN = VENV / "bin" / "pip"
LOGS_DIR = PROJECT / "logs"
SYSTEMD_USER_DIR = HOME / ".config" / "systemd" / "user"
UNIT_NAME_TEMPLATE = "kucoin-bot@.service"
UNIT_PATH = SYSTEMD_USER_DIR / UNIT_NAME_TEMPLATE

# NOTE: Use .format() to fill placeholders and keep literal %i for systemd.
UNIT_BODY = """[Unit]
Description=KuCoin Bot %i
After=network.target

[Service]
Type=simple
User={user}
WorkingDirectory={workdir}
Environment=PATH={venv_bin}:{system_path}
ExecStart={pyexe} -m kucoin_app.bot_worker --symbol %i --entry {entry} --mode {mode} --targets "{targets}" --trailing {trailing} --stoploss {stoploss} --stoploss_type {stoploss_type} --size {size} --interval {interval} {dryflag}
Restart=always
RestartSec=10
StandardOutput=append:{logs_dir}/kucoin-bot-%i.out
StandardError=append:{logs_dir}/kucoin-bot-%i.err

[Install]
WantedBy=default.target
"""

def cmd_exists(cmd):
    return shutil.which(cmd) is not None

def ensure_project_exists():
    if not PROJECT.exists():
        raise SystemExit(f"Project directory not found: {PROJECT}")

def create_venv_and_install(recreate=False):
    ensure_project_exists()
    if VENV.exists() and not recreate:
        print(f"venv already exists at {VENV}")
    else:
        if VENV.exists():
            print("Removing existing venv...")
            shutil.rmtree(VENV)
        print("Creating venv...")
        subprocess.check_call([sys.executable, "-m", "venv", str(VENV)])
    # install requirements if file present
    req = PROJECT / "requirements.txt"
    if req.exists():
        print("Installing requirements...")
        subprocess.check_call([str(PIP_BIN), "install", "-U", "pip"])
        subprocess.check_call([str(PIP_BIN), "install", "-r", str(req)])
        print("Installed requirements.")
    else:
        print("No requirements.txt found; skipping pip install.")

def ensure_logs_dir():
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.chmod(0o755)

def write_systemd_unit(params):
    SYSTEMD_USER_DIR.mkdir(parents=True, exist_ok=True)
    user = os.getenv("USER") or os.getenv("LOGNAME") or "user"
    pyexe = str(PY_BIN)
    system_path = os.getenv("PATH", "")
    dryflag = "--no-dry" if params.get("no_dry") else "--dry"

    content = UNIT_BODY.format(
        user=user,
        workdir=str(PROJECT),
        venv_bin=str(VENV / "bin"),
        system_path=system_path,
        pyexe=pyexe,
        entry=str(params.get("entry", "88000")),
        mode=str(params.get("mode", "both")),
        targets=str(params.get("targets", "1:0.3,3:0.5,5:0.2")),
        trailing=str(params.get("trailing", "1.0")),
        stoploss=str(params.get("stoploss", "-2.0")),
        stoploss_type=str(params.get("stoploss_type", "fixed")),
        size=str(params.get("size", "0.001")),
        interval=str(params.get("interval", "5")),
        dryflag=dryflag,
        logs_dir=str(LOGS_DIR)
    )

    UNIT_PATH.write_text(content)
    UNIT_PATH.chmod(0o644)
    print(f"Wrote systemd user unit at {UNIT_PATH}")

def systemctl_user_available():
    if not cmd_exists("systemctl"):
        return False
    try:
        # returns 0/1/3... but presence is enough
        subprocess.check_call(["systemctl", "--user", "status"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError:
        # systemctl exists but user session may not be available; still treat as available and try later.
        return True
    except Exception:
        return False

def systemd_daemon_reload():
    subprocess.check_call(["systemctl", "--user", "daemon-reload"])

def enable_start_service(symbol):
    unit_instance = f"kucoin-bot@{symbol}.service"
    subprocess.check_call(["systemctl", "--user", "enable", "--now", unit_instance])
    print(f"Enabled & started {unit_instance}")

def stop_disable_service(symbol):
    unit_instance = f"kucoin-bot@{symbol}.service"
    subprocess.check_call(["systemctl", "--user", "disable", "--now", unit_instance])
    print(f"Disabled & stopped {unit_instance}")

def uninstall_service(symbol, yes=False):
    if not yes:
        print("Refusing to uninstall without --yes")
        return
    try:
        stop_disable_service(symbol)
    except Exception:
        pass
    if UNIT_PATH.exists():
        UNIT_PATH.unlink()
        print("Removed unit file.")
    try:
        systemd_daemon_reload()
    except Exception:
        pass

# Fallback nohup runner (start/stop) — start writes pidfile
PID_DIR = PROJECT / "pids"
PID_DIR.mkdir(parents=True, exist_ok=True)

def start_nohup(symbol, params):
    venv_py = str(PY_BIN)
    cmd = [
        venv_py, "-m", "kucoin_app.bot_worker",
        "--symbol", str(symbol),
        "--entry", str(params.get("entry","88000")),
        "--mode", str(params.get("mode","both")),
        "--targets", str(params.get("targets","1:0.3,3:0.5,5:0.2")),
        "--trailing", str(params.get("trailing","1.0")),
        "--stoploss", str(params.get("stoploss","-2.0")),
        "--stoploss_type", str(params.get("stoploss_type","fixed")),
        "--size", str(params.get("size","0.001")),
        "--interval", str(params.get("interval","5"))
    ]
    if params.get("no_dry"):
        cmd.append("--no-dry")
    else:
        cmd.append("--dry")
    log_out = LOGS_DIR / f"kucoin-bot-{symbol}.out"
    log_err = LOGS_DIR / f"kucoin-bot-{symbol}.err"
    # start process in background, group created
    with open(log_out, "a") as o, open(log_err, "a") as e:
        p = subprocess.Popen(cmd, stdout=o, stderr=e, preexec_fn=os.setsid)
    pidfile = PID_DIR / f"{symbol}.pid"
    pidfile.write_text(str(p.pid))
    print(f"Started nohup process pid={p.pid}")

def stop_nohup(symbol):
    pidfile = PID_DIR / f"{symbol}.pid"
    if pidfile.exists():
        pid = int(pidfile.read_text().strip())
        try:
            os.killpg(os.getpgid(pid), 15)
        except Exception:
            try:
                os.kill(pid, 15)
            except Exception:
                pass
        pidfile.unlink()
        print(f"Stopped pid {pid}")
    else:
        print("No pidfile found for", symbol)

# CLI interface
def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_install = sub.add_parser("install")
    p_install.add_argument("--symbol", required=True)
    p_install.add_argument("--entry", default="88000")
    p_install.add_argument("--mode", default="both")
    p_install.add_argument("--targets", default="1:0.3,3:0.5,5:0.2")
    p_install.add_argument("--trailing", default="1.0")
    p_install.add_argument("--stoploss", default="-2.0")
    p_install.add_argument("--stoploss_type", default="fixed")
    p_install.add_argument("--size", default="0.001")
    p_install.add_argument("--interval", default="5")
    p_install.add_argument("--no-dry", action="store_true", dest="no_dry")
    p_install.add_argument("--recreate-venv", action="store_true")

    p_start = sub.add_parser("start")
    p_start.add_argument("--symbol", required=True)

    p_stop = sub.add_parser("stop")
    p_stop.add_argument("--symbol", required=True)

    p_uninstall = sub.add_parser("uninstall")
    p_uninstall.add_argument("--symbol", required=True)
    p_uninstall.add_argument("--yes", action="store_true")

    args = parser.parse_args()

    if args.cmd == "install":
        ensure_project_exists()
        create_venv_and_install(recreate=args.recreate_venv)
        ensure_logs_dir()
        params = {
            "entry": args.entry,
            "mode": args.mode,
            "targets": args.targets,
            "trailing": args.trailing,
            "stoploss": args.stoploss,
            "stoploss_type": args.stoploss_type,
            "size": args.size,
            "interval": args.interval,
            "no_dry": args.no_dry
        }
        write_systemd_unit(params)
        if systemctl_user_available():
            try:
                systemd_daemon_reload()
                print("systemd --user daemon-reload executed.")
                try:
                    enable_start_service(args.symbol)
                except Exception as e:
                    print("Failed to enable/start via systemd --user:", e)
                    print("Falling back to nohup start.")
                    start_nohup(args.symbol, params)
            except Exception as e:
                print("systemd available but daemon-reload failed:", e)
                print("Falling back to nohup")
                start_nohup(args.symbol, params)
        else:
            print("systemd --user not available; starting via nohup")
            start_nohup(args.symbol, params)

    elif args.cmd == "start":
        ensure_project_exists()
        symbol = args.symbol
        if systemctl_user_available():
            enable_start_service(symbol)
        else:
            params = {"entry":"88000","mode":"both","targets":"1:0.3,3:0.5,5:0.2","trailing":"1.0","stoploss":"-2.0","stoploss_type":"fixed","size":"0.001","interval":"5","no_dry":False}
            start_nohup(symbol, params)

    elif args.cmd == "stop":
        ensure_project_exists()
        symbol = args.symbol
        if systemctl_user_available():
            try:
                stop_disable_service(symbol)
            except Exception as e:
                print("systemctl stop failed:", e)
                print("Trying nohup stop fallback.")
                stop_nohup(symbol)
        else:
            stop_nohup(symbol)

    elif args.cmd == "uninstall":
        ensure_project_exists()
        uninstall_service(args.symbol, yes=args.yes)

if __name__ == "__main__":
    main()

