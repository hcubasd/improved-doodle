import asyncio

from .fetcher import Fetcher
from .fetch_pipeline_stages_by_pipeline_maker import (
    make_fetch_pipeline_stages_by_pipeline,
)

BASE = "https://api.rd.services/crm/v2"


def make_fetch_pipelines(fetcher: Fetcher):
    fetch_pipeline_stages_by_pipeline = make_fetch_pipeline_stages_by_pipeline(fetcher)

    async def fetch_pipelines() -> tuple[list, list]:
        pipelines = []
        page = 1
        tasks: list[tuple[str, asyncio.Task]] = []
        while True:
            batch, has_next = await fetcher(
                f"{BASE}/pipelines", {"page[number]": page, "page[size]": 200}
            )
            pipelines.extend(batch)
            for pipeline in batch:
                tasks.append(
                    (
                        pipeline["id"],
                        asyncio.create_task(
                            fetch_pipeline_stages_by_pipeline(pipeline["id"])
                        ),
                    )
                )
            if not has_next:
                break
            page += 1
        stage_results = await asyncio.gather(*[task for _, task in tasks])

        pipeline_stages = [stage for stages in stage_results for stage in stages]
        return pipelines, pipeline_stages

    return fetch_pipelines
