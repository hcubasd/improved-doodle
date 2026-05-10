import psycopg
from psycopg import sql


def select_all(cur: psycopg.Cursor, table: str):
    query = sql.SQL("SELECT * FROM {}").format(sql.Identifier(*table.split(".")))
    cur.execute(query)
    return cur.fetchall()


def select_columns(cur: psycopg.Cursor, table: str, columns: tuple[str, ...]):
    query = sql.SQL("SELECT {} FROM {}").format(
        sql.SQL(", ").join(sql.Identifier(column) for column in columns),
        sql.Identifier(*table.split(".")),
    )
    cur.execute(query)
    return cur.fetchall()
