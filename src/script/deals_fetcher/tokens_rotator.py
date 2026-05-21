import httpx
from datetime import UTC, datetime
from .tokens_repository import Token


def rotate_tokens(
    client_id: str,
    client_secret: str,
    token: Token,
) -> Token:
    r = httpx.post(
        "https://api.rd.services/oauth2/token",
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": token.refresh_token,
            "grant_type": "refresh_token",
        },
    )

    r.raise_for_status()
    body = r.json()

    return Token(
        provider_name="rd_station",
        access_token=body["access_token"],
        refresh_token=body["refresh_token"],
        updated_at=datetime.now(UTC),
    )
