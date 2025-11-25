import sqlite3


def get_db_connection(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def create_table(db_path, table_name, columns):
    column_defs = [f"{name} {data_type}" for name, data_type in columns.items()]
    sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(column_defs)})"
    try:
        with get_db_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(sql)
            conn.commit()
    except sqlite3.Error as e:
        print(f"Error creating table: {e}")


def insert_record(db_path, table_name, data):
    columns = ", ".join(data.keys())
    placeholders = ", ".join("?" * len(data))
    sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
    try:
        with get_db_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(sql, list(data.values()))
            conn.commit()
            return cursor.lastrowid
    except sqlite3.Error as e:
        print(f"Error inserting record: {e}")
        return None


def select_all(db_path, table_name, where_clause="", params=()):
    sql = f"SELECT * FROM {table_name}"
    if where_clause:
        sql += f" WHERE {where_clause}"
    try:
        with get_db_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    except sqlite3.Error as e:
        print(f"Error selecting records: {e}")
        return []


def select_one(db_path, table_name, where_clause, params=()):
    sql = f"SELECT * FROM {table_name} WHERE {where_clause}"
    try:
        with get_db_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            row = cursor.fetchone()
            return dict(row) if row else None
    except sqlite3.Error as e:
        print(f"Error selecting record: {e}")
        return None


def update_record(db_path, table_name, data, where_clause, params=()):
    set_clause = ", ".join([f"{key} = ?" for key in data.keys()])
    sql = f"UPDATE {table_name} SET {set_clause} WHERE {where_clause}"
    values = list(data.values()) + list(params)
    try:
        with get_db_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(sql, values)
            conn.commit()
            return True
    except sqlite3.Error as e:
        print(f"Error updating record: {e}")
        return False


def delete_record(db_path, table_name, where_clause, params=()):
    sql = f"DELETE FROM {table_name} WHERE {where_clause}"
    try:
        with get_db_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            conn.commit()
            return True
    except sqlite3.Error as e:
        print(f"Error deleting record: {e}")
        return False


database_maps = {
    "get_db_connection": get_db_connection,
    "create_table": create_table,
    "insert_record": insert_record,
    "select_all": select_all,
    "select_one": select_one,
    "update_record": update_record,
    "delete_record": delete_record,
}
