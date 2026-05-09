import httpx
from ..fetcher import Fetcher


def make_httpx_fetch(client: httpx.AsyncClient) -> Fetcher:
    async def httpx_fetch(
        url: str, params: dict | None = None
    ) -> tuple[list[dict], bool]:
        r = await client.get(url, params=params)
        r.raise_for_status()
        body = r.json()
        return body["data"], "next" in body.get("links", {})

    return httpx_fetch
