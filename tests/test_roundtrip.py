import asyncio
from pathlib import Path

import psycopg
import pytest

from src.script.deals_fetcher.main import _fetch_all
from src.script.deals_fetcher.fetched_deals_assembler import assemble_fetched_deals
from src.script.deals_repository import DealsRepository
from tests.fetch_json_maker import make_fetch_json

DATA_DIR = Path(__file__).parent / "data"


def _sort_key(value):
    if isinstance(value, dict):
        return (value.get("id") is None, value.get("id"), repr(value))
    return (False, None, repr(value))


def _normalize(value):
    if isinstance(value, dict):
        return {key: _normalize(inner) for key, inner in value.items()}
    if isinstance(value, list):
        return sorted((_normalize(inner) for inner in value), key=_sort_key)
    return value


def _normalize_deals(deals):
    return sorted((_normalize(deal.model_dump()) for deal in deals), key=_sort_key)


@pytest.fixture(scope="session")
def deals():
    fetcher = make_fetch_json(DATA_DIR)
    raw = asyncio.run(_fetch_all(fetcher))
    return assemble_fetched_deals(raw)


def test_roundtrip(deals):
    with psycopg.connect() as conn:
        repo = DealsRepository(conn)
        repo.update(deals)
        result = repo.get()

    assert _normalize_deals(result) == _normalize_deals(deals)
