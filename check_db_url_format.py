#!/usr/bin/env python3
"""
Script para adicionar endpoint de diagnóstico temporário no terminal_component.py
Este endpoint mostrará a DATABASE_URL mascarada para debug.
"""
import os
import json

def get_safe_database_url():
    """Retorna DATABASE_URL mascarada para debug."""
    database_url = os.environ.get("DATABASE_URL") or os.environ.get("TRADES_DB")
    
    if not database_url:
        return "❌ DATABASE_URL não definida"
    
    # Mascarar senha
    safe_url = database_url
    if '@' in safe_url and ':' in safe_url:
        parts = safe_url.split('@')
        if len(parts) == 2:
            before_at = parts[0]
            if '://' in before_at:
                protocol, user_pass = before_at.split('://', 1)
                if ':' in user_pass:
                    user, _ = user_pass.split(':', 1)
                    safe_url = f"{protocol}://{user}:***@{parts[1]}"
    
    # Analisar erros
    errors = []
    if not database_url.startswith(('postgresql://', 'postgres://')):
        errors.append("Deve começar com 'postgresql://' ou 'postgres://'")
    if '@' not in database_url:
        errors.append("Falta '@' (separador host)")
    if database_url.count(':') < 2:
        errors.append("Falta ':' (separadores)")
    
    # Verificar pattern suspeito: "host:port database" em vez de "host:port/database"
    if '@' in database_url:
        after_at = database_url.split('@')[1]
        # Verificar se tem espaço antes do nome do banco
        if ' ' in after_at and '/' not in after_at.split(' ')[0]:
            errors.append("ERRO CRÍTICO: Espaço em vez de '/' antes do database name")
            idx = after_at.index(' ')
            errors.append(f"Encontrado: '{after_at[max(0,idx-10):idx+20]}'")
            errors.append(f"Esperado formato: 'host:port/database' não 'host:port database'")
    
    return {
        "url_safe": safe_url,
        "length": len(database_url),
        "has_space": ' ' in database_url,
        "has_equals": '=' in database_url,
        "format_errors": errors
    }

if __name__ == "__main__":
    result = get_safe_database_url()
    print(json.dumps(result, indent=2))
