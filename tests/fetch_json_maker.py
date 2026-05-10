import json
from pathlib import Path

_FIXTURE_MAP = {
    "users": "users.json",
    "teams": "teams.json",
    "pipelines": "pipelines.json",
    "stages": "pipeline_stages.json",
    "campaigns": "campaigns.json",
    "lost_reasons": "loss_reasons.json",
    "sources": "sources.json",
    "segments": "industries.json",
    "products": "products.json",
    "organizations": "organizations.json",
    "contacts": "contacts.json",
    "tasks": "tasks.json",
    "deals": "deals.json",
}


def make_fetch_json(data_dir: Path):
    async def fetch_json(url: str, _: dict | None = None) -> tuple[list[dict], bool]:
        key = url.rstrip("/").split("/")[-1]
        data = json.loads((data_dir / _FIXTURE_MAP[key]).read_text())
        return data["data"], False

    return fetch_json
