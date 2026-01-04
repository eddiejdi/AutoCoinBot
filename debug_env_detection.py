#!/usr/bin/env python3
"""
Script de debug para verificar detecção de ambiente
"""
import os
import socket

print("=" * 60)
print("🔍 DEBUG: Detecção de Ambiente")
print("=" * 60)

# Variáveis de ambiente
env_vars = [
    "FLY_APP_NAME",
    "FLY_ALLOC_ID",
    "DYNO",
    "RENDER",
    "APP_ENV",
    "PORT",
    "DATABASE_URL",
]

print("\n📦 Variáveis de Ambiente:")
for var in env_vars:
    value = os.environ.get(var)
    status = "✅" if value else "❌"
    print(f"  {status} {var:20} = {value or '(não definida)'}")

# Hostname
print("\n🌐 Hostname:")
try:
    hostname = socket.gethostname()
    print(f"  Hostname: {hostname}")
    print(f"  É localhost? {hostname.startswith('localhost') or hostname.startswith('127.')}")
except Exception as e:
    print(f"  ❌ Erro ao obter hostname: {e}")

# Detecção de produção (mesma lógica do ui.py)
is_production = bool(
    os.environ.get("FLY_APP_NAME") or
    os.environ.get("FLY_ALLOC_ID") or
    os.environ.get("DYNO") or
    os.environ.get("RENDER") or
    os.environ.get("APP_ENV") in ("prod", "production", "hom", "homologation")
)

if not is_production:
    try:
        hostname = socket.gethostname()
        if hostname and not hostname.startswith("localhost") and not hostname.startswith("127."):
            is_production = True
            print(f"  ℹ️ Detecção via hostname: {hostname}")
    except Exception:
        pass

print("\n🎯 Resultado:")
print(f"  is_production = {is_production}")
print(f"  Ambiente: {'PRODUÇÃO' if is_production else 'LOCAL/DEV'}")

if is_production:
    print("\n✅ URLs devem ser RELATIVAS:")
    print("  base = ''")
    print("  log_url = '/monitor?...'")
else:
    print("\n⚠️ URLs devem ser ABSOLUTAS:")
    print("  base = 'http://127.0.0.1:8765'")
    print("  log_url = 'http://127.0.0.1:8765/monitor?...'")

print("=" * 60)
