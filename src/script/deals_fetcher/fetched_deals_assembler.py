from fluffy_waddle.sales import (
    CRMCampaign,
    CRMContact,
    CRMDeal,
    CRMIndustry,
    CRMLossReason,
    CRMOrganization,
    CRMPipeline,
    CRMPipelineStage,
    CRMProduct,
    CRMSource,
    CRMTask,
    CRMTeam,
    CRMUser,
)


def _make_leaf_map(Model, items: list[dict], name_field: str = "title") -> dict:
    return {
        item["id"]: Model.model_validate({**item, name_field: item["name"]})
        for item in items
    }


def _make_team_map(teams: list[dict]) -> dict:
    result = {}
    for raw in teams:
        team = CRMTeam.model_validate({**raw, "title": raw["name"]})
        result[team.id] = team
    return result


def _make_pipeline_map(pipelines: list[dict]) -> dict:
    result = {}
    for raw in pipelines:
        pipeline = CRMPipeline.model_validate(
            {**raw, "title": raw["name"], "display_order": raw["order"]}
        )
        result[pipeline.id] = pipeline
    return result


def _make_pipeline_stage_map(stages: list[dict], pipeline_map: dict) -> dict:
    result = {}
    for raw in stages:
        stage = CRMPipelineStage.model_validate(
            {
                **raw,
                "title": raw["name"],
                "display_order": raw["order"],
                "pipeline": pipeline_map[raw["pipeline_id"]],
            }
        )
        result[stage.id] = stage
    return result


def _make_user_map(users: list[dict], teams: list[dict], team_map: dict) -> dict:
    user_team_map = {
        user_id: team_map[raw["id"]]
        for raw in teams
        if raw["id"] in team_map
        for user_id in raw.get("user_ids", [])
    }
    return {
        user["id"]: CRMUser.model_validate(
            {**user, "full_name": user["name"], "team": user_team_map.get(user["id"])}
        )
        for user in users
    }


def _make_organization_map(
    organizations: list[dict],
    user_map: dict,
    industry_map: dict,
    contacts: list[dict],
    contact_map: dict,
) -> dict:
    org_contacts_map: dict[str, list] = {}
    for raw in contacts:
        org_id = raw.get("organization_id")
        if org_id and raw["id"] in contact_map:
            org_contacts_map.setdefault(org_id, []).append(contact_map[raw["id"]])

    result = {}
    for raw in organizations:
        org = CRMOrganization.model_validate(
            {
                **raw,
                "title": raw["name"],
                "website": raw.get("url"),
                "owner": user_map.get(raw.get("owner_id")),
                "industries": [
                    industry_map[i]
                    for i in raw.get("segment_ids", [])
                    if i in industry_map
                ],
                "followers": [
                    user_map[i] for i in raw.get("follower_ids", []) if i in user_map
                ],
                "contacts": org_contacts_map.get(raw["id"], []),
            }
        )
        result[org.id] = org
    return result


def _make_tasks_by_deal_map(tasks: list[dict], user_map: dict) -> dict[str, list]:
    result: dict[str, list] = {}
    for raw in tasks:
        task = CRMTask.model_validate(
            {
                **raw,
                "title": raw["name"],
                "task_type": raw["type"],
                "created_by": user_map[raw["created_by_id"]],
                "completed_by": user_map.get(raw.get("completed_by_id")),
                "assignees": [
                    user_map[i] for i in raw.get("owner_ids", []) if i in user_map
                ],
            }
        )
        if raw.get("deal_id"):
            result.setdefault(raw["deal_id"], []).append(task)
    return result


def _make_deal_products_map(
    deal_products: dict[str, list[str]], product_map: dict
) -> dict[str, list]:
    return {
        deal_id: [product_map[pid] for pid in product_ids if pid in product_map]
        for deal_id, product_ids in deal_products.items()
    }


def _make_deals(
    deals: list[dict],
    pipeline_stage_map: dict,
    user_map: dict,
    source_map: dict,
    campaign_map: dict,
    loss_reason_map: dict,
    organization_map: dict,
    contact_map: dict,
    deal_products_map: dict,
    tasks_by_deal_map: dict,
) -> list[CRMDeal]:
    return [
        CRMDeal.model_validate(
            {
                **deal,
                "title": deal["name"],
                "amount": deal.get("total_price"),
                "stage": pipeline_stage_map[deal["stage_id"]],
                "owner": user_map.get(deal.get("owner_id")),
                "source": source_map.get(deal.get("source_id")),
                "campaign": campaign_map.get(deal.get("campaign_id")),
                "loss_reason": loss_reason_map.get(deal.get("lost_reason_id")),
                "organization": organization_map.get(deal.get("organization_id")),
                "contacts": [
                    contact_map[i]
                    for i in deal.get("contact_ids", [])
                    if i in contact_map
                ],
                "products": deal_products_map.get(deal["id"], []),
                "tasks": tasks_by_deal_map.get(deal["id"], []),
            }
        )
        for deal in deals
    ]


def assemble_fetched_deals(raw: dict) -> list[CRMDeal]:
    industry_map = _make_leaf_map(CRMIndustry, raw["industries"])
    product_map = _make_leaf_map(CRMProduct, raw["products"])
    loss_reason_map = _make_leaf_map(
        CRMLossReason, raw["loss_reasons"], name_field="reason"
    )
    source_map = _make_leaf_map(CRMSource, raw["sources"])
    campaign_map = _make_leaf_map(CRMCampaign, raw["campaigns"])

    team_map = _make_team_map(raw["teams"])
    user_map = _make_user_map(raw["users"], raw["teams"], team_map)

    pipeline_map = _make_pipeline_map(raw["pipelines"])
    pipeline_stage_map = _make_pipeline_stage_map(raw["pipeline_stages"], pipeline_map)

    contact_map = _make_leaf_map(CRMContact, raw["contacts"], name_field="full_name")
    organization_map = _make_organization_map(
        raw["organizations"], user_map, industry_map, raw["contacts"], contact_map
    )

    deal_products_map = _make_deal_products_map(raw["deal_products"], product_map)
    tasks_by_deal_map = _make_tasks_by_deal_map(raw["tasks"], user_map)

    return _make_deals(
        raw["deals"],
        pipeline_stage_map,
        user_map,
        source_map,
        campaign_map,
        loss_reason_map,
        organization_map,
        contact_map,
        deal_products_map,
        tasks_by_deal_map,
    )
