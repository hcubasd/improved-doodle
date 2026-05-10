from .fetcher import Fetcher
from .helpers.paginated_fetch_maker import make_paginated_fetch


def make_fetch_pipeline_stages_by_pipeline(fetcher: Fetcher):
    paginated_fetch = make_paginated_fetch(fetcher)

    async def fetch_pipeline_stages_by_pipeline(pipeline_id: str) -> list[dict]:
        stages = await paginated_fetch(f"/pipelines/{pipeline_id}/stages")
        return [{**stage, "pipeline_id": pipeline_id} for stage in stages]

    return fetch_pipeline_stages_by_pipeline
