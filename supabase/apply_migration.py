"""
Aplica as migrations do Supabase via DATABASE_URL.

Uso:
  python supabase/apply_migration.py postgresql://postgres:SENHA@db.REF.supabase.co:5432/postgres

Ou com variável de ambiente:
  DATABASE_URL=... python supabase/apply_migration.py
"""
import sys
import os
from pathlib import Path

def main():
    url = (
        sys.argv[1] if len(sys.argv) > 1
        else os.getenv("DATABASE_URL")
    )
    if not url:
        print("Informe a DATABASE_URL como argumento ou variável de ambiente.")
        print("Formato: postgresql://postgres:SENHA@db.REF.supabase.co:5432/postgres")
        sys.exit(1)

    try:
        import psycopg2
    except ImportError:
        print("Instale psycopg2: pip install psycopg2-binary")
        sys.exit(1)

    migrations_dir = Path(__file__).parent / "migrations"
    sql_files = sorted(migrations_dir.glob("*.sql"))

    conn = psycopg2.connect(url)
    conn.autocommit = True
    cur = conn.cursor()

    for f in sql_files:
        print(f"Aplicando {f.name}...")
        cur.execute(f.read_text(encoding="utf-8"))
        print(f"  OK")

    cur.close()
    conn.close()
    print("\nMigrations aplicadas com sucesso!")

if __name__ == "__main__":
    main()
