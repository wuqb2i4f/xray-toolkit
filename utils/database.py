import sqlite3


def get_db_connection(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_table(db_path, table_name, columns):
    column_defs = [f"{name} {data_type}" for name, data_type in columns.items()]
    sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(column_defs)})"
    with get_db_connection(db_path) as conn:
        conn.execute(sql)
        conn.commit()


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


def bulk_upsert(db_path, table_name, records, key_columns, batch_size=10_000):
    if not records:
        return 0
    iterator = records() if callable(records) else iter(records)
    try:
        first = next(iterator)
    except StopIteration:
        return 0
    if not isinstance(first, dict):
        raise TypeError("Records must be dictionaries mapping column names to values.")
    all_columns = list(first.keys())
    if isinstance(key_columns, str):
        key_columns = [key_columns]
    update_columns = [col for col in all_columns if col not in key_columns]
    placeholders = ", ".join(["?"] * len(all_columns))
    column_list = ", ".join(all_columns)
    if update_columns:
        update_set = ", ".join([f"{col} = excluded.{col}" for col in update_columns])
        on_conflict_clause = (
            f"ON CONFLICT({', '.join(key_columns)}) DO UPDATE SET {update_set}"
        )
    else:
        on_conflict_clause = f"ON CONFLICT({', '.join(key_columns)}) DO NOTHING"
    sql = f"""
        INSERT INTO {table_name} ({column_list})
        VALUES ({placeholders})
        {on_conflict_clause}
    """.strip()
    batch = [tuple(first.values())]
    upserted = 0
    with get_db_connection(db_path) as conn:
        cur = conn.cursor()
        for record in iterator:
            batch.append(tuple(record[col] for col in all_columns))
            if len(batch) >= batch_size:
                cur.executemany(sql, batch)
                upserted += cur.rowcount
                batch.clear()
        if batch:
            cur.executemany(sql, batch)
            upserted += cur.rowcount
        conn.commit()
    return upserted


def optimize_database(db_path):
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode = DELETE")
    conn.execute("PRAGMA page_size = 4096")
    conn.execute("PRAGMA synchronous = NORMAL")
    conn.execute("PRAGMA cache_size = -64000")
    conn.execute("PRAGMA temp_store = MEMORY")
    conn.execute("PRAGMA mmap_size = 268435456")
    conn.execute("PRAGMA optimize")
    conn.execute("VACUUM")
    conn.close()


database_map = {
    "get_db_connection": get_db_connection,
    "ensure_table": ensure_table,
    "count_records": count_records,
    "select_all": select_all,
    "bulk_upsert": bulk_upsert,
    "optimize_database": optimize_database,
}
