import asyncio
import os
from datetime import date, timedelta

import httpx
import psycopg

from .fetcher import Fetcher
from .helpers.httpx_fetch_maker import make_httpx_fetch
from .helpers.paginated_fetch_maker import make_paginated_fetch
from .fetch_pipelines_maker import make_fetch_pipelines
from .fetch_products_maker import make_fetch_products
from .tokens_repository import Token, TokensRepository
from .tokens_rotator import rotate_tokens


async def _fetch_all(fetcher: Fetcher) -> dict:
    cutoff = (date.today() - timedelta(days=365)).strftime("%Y-%m-%d")
    paginated_fetch = make_paginated_fetch(fetcher)
    fetch_pipelines = make_fetch_pipelines(fetcher)
    fetch_products = make_fetch_products(fetcher, cutoff)

    (
        (pipelines, pipeline_stages),
        (products, deals, deal_products),
        users,
        teams,
        campaigns,
        loss_reasons,
        sources,
        segments,
        organizations,
        contacts,
        tasks,
    ) = await asyncio.gather(
        fetch_pipelines(),
        fetch_products(),
        paginated_fetch("/users"),
        paginated_fetch("/teams"),
        paginated_fetch("/campaigns"),
        paginated_fetch("/lost_reasons"),
        paginated_fetch("/sources"),
        paginated_fetch("/segments"),
        paginated_fetch("/organizations"),
        paginated_fetch("/contacts"),
        paginated_fetch("/tasks"),
    )

    return {
        "users": users,
        "teams": teams,
        "pipelines": pipelines,
        "pipeline_stages": pipeline_stages,
        "campaigns": campaigns,
        "loss_reasons": loss_reasons,
        "industries": segments,
        "products": products,
        "organizations": organizations,
        "contacts": contacts,
        "tasks": tasks,
        "deals": deals,
        "deal_products": deal_products,
    }


def fetch() -> dict:
    with psycopg.connect() as conn:
        tokens_repository = TokensRepository(conn)
        token: Token = tokens_repository.get("rd_station")
        token = rotate_tokens(os.getenv("CRM_CLIENT_ID"), os.getenv("CRM_CLIENT_SECRET"), token)

        tokens_repository.update("rd_station", token)
        conn.commit()

    async def _run() -> dict:
        async with httpx.AsyncClient(
            headers={"Authorization": f"Bearer {token.access_token}"},
            timeout=30.0,
        ) as client:
            return await _fetch_all(make_httpx_fetch(client))

    return asyncio.run(_run())
