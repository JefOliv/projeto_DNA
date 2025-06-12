import psycopg2
from datetime import datetime
import sys

try:
    conn = psycopg2.connect(
        host="127.0.0.1",
        port="5432",
        dbname="dnaman_db",
        user="postgres",
        password="admin123",
        client_encoding="UTF8" # Tente explicitamente
    )
    cur = conn.cursor()
    cur.execute("SELECT version();")
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Conexão bem-sucedida ao PostgreSQL!")
    print(cur.fetchone())
    cur.close()
    conn.close()
except Exception as e:
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Erro ao conectar ao PostgreSQL: {e}", file=sys.stderr)
    sys.exit(1) # Sai com código de erro se houver falha na conexão