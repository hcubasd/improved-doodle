from .fetcher import Fetcher
from .helpers.paginated_fetch_maker import make_paginated_fetch


def make_fetch_deals_by_product(fetcher: Fetcher, cutoff: str):
    paginated_fetch = make_paginated_fetch(fetcher)

    async def fetch(product_id: str) -> tuple[list[dict], list[dict]]:
        ongoing = await paginated_fetch(
            "/deals", {"filter": f"product_ids:({product_id}) status:ongoing"}
        )
        won = await paginated_fetch(
            "/deals",
            {"filter": f'product_ids:({product_id}) status:won closed_at:>"{cutoff}"'},
        )
        return ongoing, won

    return fetch
