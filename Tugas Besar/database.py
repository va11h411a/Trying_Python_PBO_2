# database.py
import sqlite3
import pandas as pd
from konfigurasi import DB_PATH

def get_db_connection() -> sqlite3.Connection | None:
    """Membuka dan mengembalikan koneksi baru ke database SQLite."""
    try:
        conn = sqlite3.connect(DB_PATH, timeout=10, detect_types=sqlite3.PARSE_DECLTYPES)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        print(f"ERROR [database.py] Koneksi DB gagal: {e}")
        return None

def execute_query(query: str, params: tuple | None = None) -> bool:
    conn = get_db_connection()
    if not conn: return False # Koneksi gagal
    try:
        cursor = conn.cursor()
        cursor.execute(query, params) if params else cursor.execute(query)
        conn.commit()
        print(f"DEBUG [execute_query] Query '{query[:50]}...' berhasil dieksekusi. Affected rows: {cursor.rowcount}") # Tambah affected_rows
        return True # Berhasil
    except sqlite3.Error as e:
        print(f"ERROR [database.py] Query gagal: {e} | Query: {query[:100]}...")
        conn.rollback()
        return False # Gagal
    finally:
        if conn: conn.close()

def fetch_query(query: str, params: tuple | None = None, fetch_all: bool = True) -> list | tuple | None:
    """Menjalankan query SELECT dan mengembalikan hasilnya."""
    conn = get_db_connection()
    if not conn:
        return None

    try:
        cursor = conn.cursor()
        cursor.execute(query, params) if params else cursor.execute(query)
        return cursor.fetchall() if fetch_all else cursor.fetchone()
    except sqlite3.Error as e:
        print(f"ERROR [database.py] Fetch gagal: {e} | Query: {query[:100]}...")
        return None
    finally:
        conn.close()

def get_dataframe(query: str, params: tuple | None = None) -> pd.DataFrame:
    """Menjalankan query SELECT dan mengembalikan hasilnya dalam bentuk DataFrame."""
    conn = get_db_connection()
    if not conn:
        return pd.DataFrame()

    try:
        return pd.read_sql_query(query, conn, params=params)
    except Exception as e:
        print(f"ERROR [database.py] Gagal baca ke DataFrame: {e} | Query: {query[:100]}...")
        return pd.DataFrame()
    finally:
        conn.close()

def setup_database_initial() -> bool:
    """Membuat tabel 'problems' jika belum ada di dalam database."""
    print(f"Memeriksa/membuat tabel di database (via database.py): {DB_PATH}")
    conn = get_db_connection()
    if not conn:
        return False

    try:
        cursor = conn.cursor()
        sql_create_table = """
        CREATE TABLE IF NOT EXISTS problems (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nama_problem TEXT NOT NULL,
            deskripsi_problem TEXT,
            kategori_problem TEXT,
            penyebab TEXT NOT NULL,
            solusi TEXT NOT NULL,
            tanggal_masuk DATE NOT NULL
        );
        """
        cursor.execute(sql_create_table)
        conn.commit()
        print(" -> Tabel 'problems' siap (dari database.py).")
        return True
    except sqlite3.Error as e:
        print(f"Error SQLite saat setup tabel (dari database.py): {e}")
        return False
    finally:
        conn.close()
