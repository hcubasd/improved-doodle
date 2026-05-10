import asyncio

from .fetcher import Fetcher
from .fetch_deals_by_product_maker import make_fetch_deals_by_product

BASE = "https://api.rd.services/crm/v2"


def make_fetch_products(fetcher: Fetcher, cutoff: str):
    fetch_deals_by_product = make_fetch_deals_by_product(fetcher, cutoff)

    async def fetch_products() -> tuple[list, list, dict]:
        page = 1
        all_products = []
        deal_tasks: list[tuple[str, asyncio.Task]] = []
        while True:
            batch, has_next = await fetcher(
                f"{BASE}/products", {"page[number]": page, "page[size]": 200}
            )
            all_products.extend(batch)
            for p in batch:
                pid = str(p["id"])
                deal_tasks.append(
                    (pid, asyncio.create_task(fetch_deals_by_product(pid)))
                )
            if not has_next:
                break
            page += 1
        deal_results = await asyncio.gather(*[t for _, t in deal_tasks])
        deals_by_id: dict[str, dict] = {}
        deal_products: dict[str, list[str]] = {}
        for (pid, _), (ongoing, won) in zip(deal_tasks, deal_results):
            for deal in [*ongoing, *won]:
                did = deal["id"]
                deals_by_id[did] = deal
                deal_products.setdefault(did, []).append(pid)
        deal_products = {
            did: list(dict.fromkeys(product_ids))
            for did, product_ids in deal_products.items()
        }
        return all_products, list(deals_by_id.values()), deal_products

    return fetch_products
