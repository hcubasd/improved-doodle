from typing import TypeVar

import psycopg
from psycopg import sql

_Row = TypeVar("_Row")


def select_all(cur: psycopg.Cursor[_Row], table: str) -> list[_Row]:
    query = sql.SQL("SELECT * FROM {}").format(sql.Identifier(*table.split(".")))
    cur.execute(query)
    return cur.fetchall()


def select_columns(
    cur: psycopg.Cursor[_Row], table: str, columns: tuple[str, ...]
) -> list[_Row]:
    query = sql.SQL("SELECT {} FROM {}").format(
        sql.SQL(", ").join(sql.Identifier(column) for column in columns),
        sql.Identifier(*table.split(".")),
    )
    cur.execute(query)
    return cur.fetchall()
