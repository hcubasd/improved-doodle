import asyncio
from pathlib import Path

import pytest

from src.deals_fetcher import _fetch_all
from tests.fetch_json_maker import make_fetch_json

DATA_DIR = Path(__file__).parent / "data"


@pytest.fixture(scope="session")
def data():
    fetcher = make_fetch_json(DATA_DIR)
    return asyncio.run(_fetch_all(fetcher))


def test_all_resources_present(data):
    for key in (
        "users",
        "teams",
        "pipelines",
        "pipeline_stages",
        "campaigns",
        "loss_reasons",
        "industries",
        "products",
        "organizations",
        "contacts",
        "tasks",
        "deals",
    ):
        assert data[key], f"expected non-empty {key}"


def test_pipeline_stages_have_pipeline_id(data):
    for stage in data["pipeline_stages"]:
        assert "pipeline_id" in stage


def test_deal_products_built(data):
    assert data["deal_products"]
    deal_ids = {d["id"] for d in data["deals"]}
    for deal_id, product_ids in data["deal_products"].items():
        assert deal_id in deal_ids
        assert product_ids
