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


def bulk_insert_from_iterable(
    db_path, table_name, records, conflict_strategy="IGNORE", batch_size=10_000
):
    if not records:
        return 0
    if callable(records):
        iterator = records()
    else:
        iterator = iter(records)
    try:
        first_record = next(iterator)
    except StopIteration:
        return 0
    if isinstance(first_record, dict):
        columns = list(first_record.keys())
        column_list = ",".join(columns)
        placeholders = ",".join("?" for _ in columns)
        use_dict = True
    else:
        column_count = len(first_record)
        column_list = ",".join(f"col{i+1}" for i in range(column_count))
        placeholders = ",".join("?" for _ in range(column_count))
        use_dict = False
    conflict_clause = "OR IGNORE" if conflict_strategy == "IGNORE" else "OR REPLACE"
    sql = f"INSERT {conflict_clause} INTO {table_name} ({column_list}) VALUES ({placeholders})"
    if use_dict:
        batch = [tuple(first_record.get(c) for c in columns)]
    else:
        batch = [tuple(first_record)]
    inserted = 0
    try:
        with get_db_connection(db_path) as conn:
            cur = conn.cursor()
            for record in iterator:
                if use_dict:
                    row = tuple(record.get(c) for c in columns)
                else:
                    row = tuple(record)
                batch.append(row)
                if len(batch) >= batch_size:
                    cur.executemany(sql, batch)
                    inserted += cur.rowcount
                    batch.clear()
            if batch:
                cur.executemany(sql, batch)
                inserted += cur.rowcount
            conn.commit()
        return inserted
    except Exception as e:
        print(f"[DB ERROR] bulk_insert_from_iterable failed: {e}")
        raise


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


def bulk_update_multi_columns(
    db_path, table_name, updates, key_column, extra_sets=None
):
    if not updates:
        return 0
    keys = list(updates.keys())
    all_columns = set()
    for vals in updates.values():
        all_columns.update(vals.keys())
    all_columns = list(all_columns)
    if not all_columns:
        return 0
    case_sql_parts = []
    params = []
    for col in all_columns:
        case_clauses = []
        for key in keys:
            value = updates[key].get(col)
            if value is not None:
                case_clauses.append("WHEN ? THEN ?")
                params.extend([key, value])
            else:
                case_clauses.append("WHEN ? THEN NULL")
                params.append(key)

        case_sql = f"CASE {key_column} {' '.join(case_clauses)} END"
        case_sql_parts.append(f"{col} = {case_sql}")
    if extra_sets:
        for col, val in extra_sets.items():
            if val == "CURRENT_TIMESTAMP":
                case_sql_parts.append(f"{col} = CURRENT_TIMESTAMP")
            else:
                case_sql_parts.append(f"{col} = ?")
                params.append(val)
    set_clause = ", ".join(case_sql_parts)
    placeholders = ", ".join("?" for _ in keys)
    sql = f"""
        UPDATE {table_name}
        SET {set_clause}
        WHERE {key_column} IN ({placeholders})
    """
    final_params = params + keys
    try:
        with get_db_connection(db_path) as conn:
            cursor = conn.execute(sql, final_params)
            conn.commit()
        return cursor.rowcount
    except Exception as e:
        print(f"[DB ERROR] bulk_update_multi_columns failed: {e}")
        return 0


database_map = {
    "get_db_connection": get_db_connection,
    "ensure_table": ensure_table,
    "bulk_insert_from_iterable": bulk_insert_from_iterable,
    "count_records": count_records,
    "select_all": select_all,
    "bulk_update_multi_columns": bulk_update_multi_columns,
}
