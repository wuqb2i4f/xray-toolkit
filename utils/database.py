import sqlite3
import os


def get_db_connection(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def create_table(db_path, table_name, columns):
    column_defs = [f"{name} {data_type}" for name, data_type in columns.items()]
    sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(column_defs)})"
    with get_db_connection(db_path) as conn:
        conn.execute(sql)
        conn.commit()


def ensure_table(db_path, table_name, columns):
    column_defs = [f"{name} {data_type}" for name, data_type in columns.items()]
    sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(column_defs)})"
    with get_db_connection(db_path) as conn:
        conn.execute(sql)
        conn.commit()


def insert_record(db_path, table_name, data):
    columns = ", ".join(data.keys())
    placeholders = ", ".join("?" * len(data))
    sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
    try:
        with get_db_connection(db_path) as conn:
            cur = conn.cursor()
            cur.execute(sql, list(data.values()))
            conn.commit()
            return cur.lastrowid
    except sqlite3.Error:
        return None


def insert_or_ignore(db_path, table_name, data):
    columns = ", ".join(data.keys())
    placeholders = ", ".join("?" * len(data))
    sql = f"INSERT OR IGNORE INTO {table_name} ({columns}) VALUES ({placeholders})"
    try:
        with get_db_connection(db_path) as conn:
            cur = conn.cursor()
            cur.execute(sql, list(data.values()))
            conn.commit()
            return cur.lastrowid
    except sqlite3.Error:
        return None


def bulk_import_from_file(db_path, file_path, table_name, temp_table_name="temp_bulk"):
    if not os.path.exists(file_path):
        return 0
    added = 0
    conn = None
    try:
        conn = get_db_connection(db_path)
        cur = conn.cursor()
        cur.executescript(
            """
            PRAGMA journal_mode = OFF;
            PRAGMA synchronous = OFF;
            PRAGMA cache_size = 1000000;
            PRAGMA locking_mode = EXCLUSIVE;
            PRAGMA temp_store = MEMORY;
            """
        )
        with open(file_path, "r", encoding="utf-8") as f:
            batch = []
            batch_size = 10000
            for line in f:
                uri = line.strip()
                if uri:
                    batch.append((uri,))
                    if len(batch) >= batch_size:
                        cur.executemany(
                            f"INSERT OR IGNORE INTO {table_name} (uri) VALUES (?)",
                            batch,
                        )
                        added += cur.rowcount
                        batch.clear()
            if batch:
                cur.executemany(
                    f"INSERT OR IGNORE INTO {table_name} (uri) VALUES (?)", batch
                )
                added += cur.rowcount
        conn.commit()
        return added
    except Exception as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        if conn:
            conn.close()


def count_records(db_path, table_name):
    with get_db_connection(db_path) as conn:
        row = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()
        return row[0] if row else 0


def select_all(db_path, table_name, where_clause="", params=()):
    sql = f"SELECT * FROM {table_name}"
    if where_clause:
        sql += f" WHERE {where_clause}"
    with get_db_connection(db_path) as conn:
        cur = conn.cursor()
        cur.execute(sql, params)
        rows = cur.fetchall()
        return [dict(row) for row in rows]


def select_one(db_path, table_name, where_clause, params=()):
    sql = f"SELECT * FROM {table_name} WHERE {where_clause}"
    with get_db_connection(db_path) as conn:
        cur = conn.cursor()
        cur.execute(sql, params)
        row = cur.fetchone()
        return dict(row) if row else None


def update_record(db_path, table_name, data, where_clause, params=()):
    set_clause = ", ".join([f"{k} = ?" for k in data.keys()])
    sql = f"UPDATE {table_name} SET {set_clause} WHERE {where_clause}"
    values = list(data.values()) + list(params)
    with get_db_connection(db_path) as conn:
        cur = conn.cursor()
        cur.execute(sql, values)
        conn.commit()
        return cur.rowcount > 0


def delete_record(db_path, table_name, where_clause, params=()):
    sql = f"DELETE FROM {table_name} WHERE {where_clause}"
    with get_db_connection(db_path) as conn:
        cur = conn.cursor()
        cur.execute(sql, params)
        conn.commit()
        return True


database_map = {
    "get_db_connection": get_db_connection,
    "create_table": create_table,
    "ensure_table": ensure_table,
    "insert_record": insert_record,
    "insert_or_ignore": insert_or_ignore,
    "bulk_import_from_file": bulk_import_from_file,
    "count_records": count_records,
    "select_all": select_all,
    "select_one": select_one,
    "update_record": update_record,
    "delete_record": delete_record,
}
