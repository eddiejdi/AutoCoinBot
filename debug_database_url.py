#!/usr/bin/env python3
"""Script de diagnóstico para verificar DATABASE_URL no ambiente."""
import os
import sys

def diagnose_database_url():
    """Diagnóstica a configuração da DATABASE_URL."""
    print("=== DIAGNÓSTICO DATABASE_URL ===\n")
    
    # Carregar .env
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ .env carregado")
    except Exception as e:
        print(f"⚠️ Erro ao carregar .env: {e}")
    
    # Verificar variáveis de ambiente
    database_url = os.environ.get("DATABASE_URL")
    trades_db = os.environ.get("TRADES_DB")
    
    print(f"\n📊 Variáveis de ambiente:")
    print(f"DATABASE_URL: {'✅ definida' if database_url else '❌ não definida'}")
    if database_url:
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
        print(f"  Valor: {safe_url}")
        
        # Validar formato
        errors = []
        if not database_url.startswith(('postgresql://', 'postgres://')):
            errors.append("❌ Deve começar com 'postgresql://' ou 'postgres://'")
        if '@' not in database_url:
            errors.append("❌ Falta '@' (separador host)")
        if database_url.count(':') < 2:
            errors.append("❌ Falta ':' (separadores de senha e porta)")
        if '/' not in database_url.split('@')[-1] if '@' in database_url else True:
            errors.append("❌ Falta '/' (separador de database name)")
        
        # Verificar se há espaço onde deveria haver '='
        if ' ' in database_url and '=' not in database_url.split('?')[-1] if '?' in database_url else True:
            errors.append("❌ ERRO CRÍTICO: Espaço detectado onde deveria ter '=' ou '/'")
            # Tentar identificar a posição
            if 'trades.db' in database_url:
                idx = database_url.index('trades.db')
                context = database_url[max(0, idx-20):idx+20]
                errors.append(f"   Contexto: ...{context}...")
        
        if errors:
            print("\n⚠️ ERROS DE FORMATO:")
            for err in errors:
                print(f"  {err}")
        else:
            print("  ✅ Formato válido")
    
    print(f"\nTRADES_DB: {'✅ definida' if trades_db else '❌ não definida'}")
    if trades_db and trades_db != database_url:
        print(f"  ⚠️ Difere de DATABASE_URL")
    
    # Tentar conectar
    print(f"\n🔌 Teste de conexão:")
    try:
        import psycopg
        from psycopg.rows import dict_row
        
        dsn = database_url or trades_db
        if not dsn:
            print("  ❌ Nenhuma DSN disponível")
            return False
        
        conn = psycopg.connect(dsn, row_factory=dict_row)
        cursor = conn.cursor()
        cursor.execute("SELECT version()")
        version = cursor.fetchone()
        conn.close()
        
        print(f"  ✅ Conexão bem-sucedida")
        print(f"  PostgreSQL: {version['version'][:50]}...")
        return True
        
    except Exception as e:
        print(f"  ❌ Erro ao conectar: {e}")
        print(f"  Tipo: {type(e).__name__}")
        
        # Análise específica do erro
        err_str = str(e)
        if "missing" in err_str.lower() and "=" in err_str:
            print("\n🔍 ANÁLISE DO ERRO:")
            print("  Este erro ocorre quando a connection string tem formato inválido.")
            print("  Formato correto: postgresql://user:password@host:port/database")
            print("  Formato incorreto: postgresql://user:password@host:port database")
            print("                                                          ↑ falta '/'")
        
        return False

if __name__ == "__main__":
    success = diagnose_database_url()
    sys.exit(0 if success else 1)
