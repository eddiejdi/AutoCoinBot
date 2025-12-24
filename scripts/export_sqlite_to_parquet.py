#!/usr/bin/env python3
"""Exporta tabelas do SQLite para arquivos Parquet (pandas + pyarrow).

Usage:
    python3 scripts/export_sqlite_to_parquet.py /path/to/db.sqlite out_dir

If pandas/pyarrow are not installed the script prints install instructions.
"""
import sys
from pathlib import Path

def main():
    if len(sys.argv) < 3:
        print('Usage: export_sqlite_to_parquet.py <db_path> <out_dir>')
        return 2
    db_path = Path(sys.argv[1])
    out_dir = Path(sys.argv[2])
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        import pandas as pd
        import sqlite3
    except Exception as e:
        print('Missing dependencies: please install pandas and pyarrow (or pandas[parquet])')
        print('pip install pandas pyarrow')
        return 3

    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()
    # list tables
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cur.fetchall()]
    for t in tables:
        try:
            print(f'Exporting {t}...')
            df = pd.read_sql_query(f'SELECT * FROM "{t}"', conn)
            out_file = out_dir / f'{t}.parquet'
            df.to_parquet(out_file, index=False)
            print(f'Wrote {out_file}')
        except Exception as e:
            print(f'Failed to export {t}: {e}')

    conn.close()
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
