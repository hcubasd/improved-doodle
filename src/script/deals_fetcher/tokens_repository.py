import psycopg
from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class Token:
    provider: str
    access_token: str
    refresh_token: str | None
    updated_at: datetime


class TokensRepository:
    def __init__(self, conn: psycopg.Connection):
        self._conn = conn

    def get(self, provider: str) -> Token:
        row = self._conn.execute(
            """
            SELECT provider, access_token, refresh_token, updated_at
                FROM tokens WHERE provider = %s
            """,
            (provider,),
        ).fetchone()

        if row is None:
            raise ValueError(f"No token found for provider {provider}")
        return Token(*row)

    def update(self, provider: str, token: Token) -> None:
        self._conn.execute(
            """
            UPDATE tokens
                SET access_token = %s, refresh_token = %s, updated_at = %s
                    WHERE provider = %s
            """,
            (token.access_token, token.refresh_token, token.updated_at, provider),
        )
