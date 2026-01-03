#!/usr/bin/env python3
"""
Script para monitorar consumo de Copilot Pro em tempo real.

Uso:
    python monitor_copilot_usage.py              # Status atual
    python monitor_copilot_usage.py --watch      # Monitorar a cada 60s
    python monitor_copilot_usage.py --json       # Saída JSON

Requisitos:
    - Autenticação GitHub válida (via gh CLI ou token)
    - Conexão com internet
"""

import sys
import json
import time
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, Any
import argparse

# Verificar se requests está instalado
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    print("⚠️ Módulo 'requests' não instalado. Execute: pip install requests", file=sys.stderr)

# Cores para output no terminal
class Colors:
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    RESET = "\033[0m"
    BOLD = "\033[1m"


def get_github_token() -> Optional[str]:
    """Tenta obter token GitHub de várias fontes."""
    # 1. Tentar gh CLI
    try:
        result = subprocess.run(
            ["gh", "auth", "token"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    
    # 2. Tentar variável de ambiente
    import os
    if os.getenv("GITHUB_TOKEN"):
        return os.getenv("GITHUB_TOKEN")
    
    return None


def fetch_copilot_usage(token: str) -> Dict[str, Any]:
    """
    Busca dados de uso do Copilot Pro via GraphQL ou REST API.
    
    Return:
        Dict com informações de uso
    """
    if not HAS_REQUESTS:
        return {
            "status": "error",
            "message": "requests not installed. Run: pip install requests"
        }
    
    # Tentar GraphQL API (mais preciso)
    query = """
    {
      viewer {
        login
        copilotPro {
          enabled
          requestsUsedThisMonth
          requestsLimitPerMonth
        }
      }
    }
    """
    
    headers = {
        "Authorization": f"bearer {token}",
        "Content-Type": "application/json",
    }
    
    try:
        response = requests.post(
            "https://api.github.com/graphql",
            json={"query": query},
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if "errors" in data:
                # Fallback: tentar REST API
                return fetch_copilot_usage_rest(token)
            
            viewer = data.get("data", {}).get("viewer", {})
            copilot = viewer.get("copilotPro", {})
            
            return {
                "status": "success",
                "user": viewer.get("login", "Unknown"),
                "plan": "Copilot Pro",
                "enabled": copilot.get("enabled", False),
                "requests_used": copilot.get("requestsUsedThisMonth", 0),
                "requests_limit": copilot.get("requestsLimitPerMonth", 0),
                "period": "monthly",
                "fetched_at": datetime.now().isoformat()
            }
        else:
            return {
                "status": "error",
                "message": f"HTTP {response.status_code}: {response.text[:200]}"
            }
    
    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "message": f"Network error: {str(e)}"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Unexpected error: {str(e)}"
        }


def fetch_copilot_usage_rest(token: str) -> Dict[str, Any]:
    """Fallback: usar REST API do GitHub."""
    if not HAS_REQUESTS:
        return {"status": "error", "message": "requests not installed"}
    
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
    }
    
    try:
        response = requests.get(
            "https://api.github.com/user",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            user = response.json()
            return {
                "status": "success",
                "user": user.get("login", "Unknown"),
                "plan": "Unknown (check github.com/copilot/usage manually)",
                "fetched_at": datetime.now().isoformat()
            }
        else:
            return {
                "status": "error",
                "message": f"HTTP {response.status_code}"
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"REST API error: {str(e)}"
        }


def format_usage_report(usage: Dict[str, Any]) -> str:
    """Formata relatório de uso de forma legível."""
    if usage["status"] == "error":
        return f"{Colors.RED}❌ Erro: {usage['message']}{Colors.RESET}"
    
    user = usage.get("user", "Unknown")
    plan = usage.get("plan", "Unknown")
    enabled = usage.get("enabled", "N/A")
    
    report = [
        f"\n{Colors.BOLD}📊 Copilot Usage Report{Colors.RESET}",
        f"{'=' * 50}",
        f"👤 User: {Colors.CYAN}{user}{Colors.RESET}",
        f"📦 Plan: {Colors.BLUE}{plan}{Colors.RESET}",
        f"✅ Enabled: {enabled}",
        f"⏰ Fetched: {usage.get('fetched_at', 'N/A')}",
    ]
    
    if "requests_used" in usage and "requests_limit" in usage:
        used = usage["requests_used"]
        limit = usage["requests_limit"]
        period = usage.get("period", "unknown")
        
        # Calcular percentual
        if limit > 0:
            pct = (used / limit) * 100
            remaining = limit - used
            
            # Determinar cor baseado em percentual
            if pct < 50:
                color = Colors.GREEN
                emoji = "✅"
            elif pct < 80:
                color = Colors.YELLOW
                emoji = "⚠️"
            else:
                color = Colors.RED
                emoji = "🔴"
            
            report.extend([
                f"",
                f"Period: {period.capitalize()}",
                f"Requests Used: {color}{used}/{limit}{Colors.RESET} ({pct:.1f}%)",
                f"Remaining: {color}{remaining}{Colors.RESET}",
                f"{emoji} Status: {_get_status_text(pct)}",
            ])
    
    report.append(f"{'=' * 50}\n")
    return "\n".join(report)


def _get_status_text(percentage: float) -> str:
    """Retorna texto de status baseado em percentual de uso."""
    if percentage < 50:
        return f"{Colors.GREEN}Ótimo (< 50%){Colors.RESET}"
    elif percentage < 80:
        return f"{Colors.YELLOW}Atenção (50-80%){Colors.RESET}"
    else:
        return f"{Colors.RED}Limite próximo (> 80%){Colors.RESET}"


def save_usage_json(usage: Dict[str, Any], filepath: str = ".copilot_usage.json"):
    """Salva último relatório em JSON para referência."""
    try:
        with open(filepath, "w") as f:
            json.dump(usage, f, indent=2)
        return filepath
    except Exception as e:
        print(f"⚠️ Não foi possível salvar JSON: {e}", file=sys.stderr)
        return None


def main():
    parser = argparse.ArgumentParser(
        description="Monitor Copilot Pro usage",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python monitor_copilot_usage.py              # Mostrar status
  python monitor_copilot_usage.py --watch      # Atualizar a cada 60s
  python monitor_copilot_usage.py --json       # Saída JSON pura
  python monitor_copilot_usage.py --save       # Salvar em .copilot_usage.json
        """
    )
    parser.add_argument("--watch", action="store_true", 
                        help="Monitorar continuamente (atualiza a cada 60s)")
    parser.add_argument("--json", action="store_true",
                        help="Saída em formato JSON (sem formatação)")
    parser.add_argument("--save", action="store_true",
                        help="Salvar último resultado em .copilot_usage.json")
    parser.add_argument("--interval", type=int, default=60,
                        help="Intervalo entre atualizações em --watch (padrão: 60s)")
    
    args = parser.parse_args()
    
    # Verificar token
    token = get_github_token()
    if not token:
        print(
            f"{Colors.RED}❌ Erro: Token GitHub não encontrado!{Colors.RESET}\n"
            f"Certifique-se de que:\n"
            f"  1. GitHub CLI ('gh') está instalado e autenticado: gh auth login\n"
            f"  2. OU defina GITHUB_TOKEN: export GITHUB_TOKEN='your_token'\n"
            f"\nPara obter um token:\n"
            f"  https://github.com/settings/tokens (escopo: read:user)\n",
            file=sys.stderr
        )
        sys.exit(1)
    
    # Executar loop de monitoramento
    try:
        iteration = 0
        while True:
            iteration += 1
            
            if args.watch and iteration > 1:
                print(f"\n{Colors.CYAN}[{datetime.now().strftime('%H:%M:%S')}] Atualizando...{Colors.RESET}")
            
            # Fetch dados
            usage = fetch_copilot_usage(token)
            
            # Output
            if args.json:
                print(json.dumps(usage, indent=2))
            else:
                print(format_usage_report(usage))
            
            # Salvar se solicitado
            if args.save:
                filepath = save_usage_json(usage)
                if filepath:
                    print(f"💾 Salvo em: {filepath}")
            
            # Se não está em watch mode, sair
            if not args.watch:
                break
            
            # Aguardar antes de próxima iteração
            time.sleep(args.interval)
    
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⏹️ Monitoramento interrompido{Colors.RESET}")
        sys.exit(0)
    except Exception as e:
        print(f"{Colors.RED}❌ Erro inesperado: {e}{Colors.RESET}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
