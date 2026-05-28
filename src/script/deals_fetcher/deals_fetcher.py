import asyncio
import os
from datetime import date

import httpx
import psycopg
from fluffy_waddle.sales import CRMDeal

from .fetcher import Fetcher
from .helpers.httpx_fetch_maker import make_httpx_fetch
from .helpers.paginated_fetch_maker import make_paginated_fetch
from .fetch_pipelines_maker import make_fetch_pipelines
from .fetch_products_maker import make_fetch_products
from .tokens_repository import Token, TokensRepository
from .tokens_rotator import rotate_tokens
from .fetched_deals_assembler import assemble_fetched_deals


def _won_deals_cutoff(today: date | None = None) -> str:
    today = today or date.today()
    return today.replace(year=today.year - 1, day=1).strftime("%Y-%m-%d 00:00:00")


async def _fetch_all(fetcher: Fetcher) -> dict:
    cutoff = _won_deals_cutoff()
    paginated_fetch = make_paginated_fetch(fetcher)
    fetch_pipelines = make_fetch_pipelines(fetcher)
    fetch_products = make_fetch_products(fetcher, cutoff)

    (
        (pipelines, pipeline_stages),
        (products, deals, deal_products),
        productless_ongoing,
        productless_won,
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
        paginated_fetch("/deals", {"filter": "status:ongoing -has:product"}),
        paginated_fetch("/deals", {"filter": f'status:won -has:product closed_at:>"{cutoff}"'}),
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

    deals_by_id = {d["id"]: d for d in deals}
    for d in [*productless_ongoing, *productless_won]:
        deals_by_id.setdefault(d["id"], d)

    return {
        "users": users,
        "teams": teams,
        "pipelines": pipelines,
        "pipeline_stages": pipeline_stages,
        "campaigns": campaigns,
        "loss_reasons": loss_reasons,
        "sources": sources,
        "industries": segments,
        "products": products,
        "organizations": organizations,
        "contacts": contacts,
        "tasks": tasks,
        "deals": list(deals_by_id.values()),
        "deal_products": deal_products,
    }


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if value is None:
        raise ValueError(f"Missing required environment variable {name}")
    return value


def fetch_deals() -> list[CRMDeal]:
    with psycopg.connect() as conn:
        tokens_repository = TokensRepository(conn)
        token: Token = tokens_repository.get("rd_station")
        token = rotate_tokens(
            _require_env("CRM_CLIENT_ID"),
            _require_env("CRM_CLIENT_SECRET"),
            token,
        )

        tokens_repository.update("rd_station", token)
        conn.commit()

    async def _run():
        async with httpx.AsyncClient(
            headers={"Authorization": f"Bearer {token.access_token}"},
            timeout=30.0,
        ) as client:
            return await _fetch_all(make_httpx_fetch(client))

    return assemble_fetched_deals(asyncio.run(_run()))
