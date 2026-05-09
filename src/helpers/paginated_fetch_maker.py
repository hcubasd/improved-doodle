from ..fetcher import Fetcher

BASE_URL = "https://api.rd.services/crm/v2"


def make_paginated_fetch(fetcher: Fetcher):
    async def paginated_fetch(
        relative_url: str, params: dict | None = None
    ) -> list[dict]:
        results = []
        page = 1
        while True:
            batch, has_next = await fetcher(
                f"{BASE_URL}{relative_url}",
                {"page[number]": page, "page[size]": 200, **(params or {})},
            )

            results.extend(batch)
            if not has_next:
                break
            page += 1
        return results

    return paginated_fetch
