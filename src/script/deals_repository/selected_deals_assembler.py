import psycopg

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

from .selectors import select_all, select_columns


def _leaf_map(Model, rows):
    return {r["id"]: Model.model_validate(r) for r in rows}


def _user_map(users_rows, teams_rows, teams_users_rows):
    teams = {r["id"]: CRMTeam.model_validate(r) for r in teams_rows}
    user_team = {
        r["user_id"]: teams[r["team_id"]]
        for r in teams_users_rows
        if r["team_id"] in teams
    }
    return {
        r["id"]: CRMUser.model_validate({**r, "team": user_team.get(r["id"])})
        for r in users_rows
    }


def _pipeline_stage_map(rows, pipeline_map):
    return {
        r["id"]: CRMPipelineStage.model_validate(
            {**r, "pipeline": pipeline_map[r["pipeline_id"]]}
        )
        for r in rows
    }


def _organization_map(
    orgs_rows,
    user_map,
    industry_map,
    org_industries_rows,
    org_followers_rows,
    contact_map,
    contact_rows,
):
    org_industries: dict[str, list] = {}
    for r in org_industries_rows:
        if r["industry_id"] in industry_map:
            org_industries.setdefault(r["organization_id"], []).append(
                industry_map[r["industry_id"]]
            )

    org_followers: dict[str, list] = {}
    for r in org_followers_rows:
        if r["user_id"] in user_map:
            org_followers.setdefault(r["organization_id"], []).append(
                user_map[r["user_id"]]
            )

    org_contacts: dict[str, list] = {}
    for r in contact_rows:
        if r.get("organization_id") and r["id"] in contact_map:
            org_contacts.setdefault(r["organization_id"], []).append(
                contact_map[r["id"]]
            )

    return {
        r["id"]: CRMOrganization.model_validate(
            {
                **r,
                "owner": user_map.get(r["owner_id"]) if r["owner_id"] else None,
                "industries": org_industries.get(r["id"], []),
                "followers": org_followers.get(r["id"], []),
                "contacts": org_contacts.get(r["id"], []),
            }
        )
        for r in orgs_rows
    }


def _deal_contacts_map(rows, contact_map):
    result: dict[str, list] = {}
    for r in rows:
        if r["contact_id"] in contact_map:
            result.setdefault(r["deal_id"], []).append(contact_map[r["contact_id"]])
    return result


def _deal_products_map(rows, product_map):
    result: dict[str, list] = {}
    for r in rows:
        if r["product_id"] in product_map:
            result.setdefault(r["deal_id"], []).append(product_map[r["product_id"]])
    return result


def _tasks_by_deal_map(tasks_rows, user_map, tasks_users_rows):
    task_assignees: dict[str, list] = {}
    for r in tasks_users_rows:
        if r["user_id"] in user_map:
            task_assignees.setdefault(r["task_id"], []).append(user_map[r["user_id"]])

    result: dict[str, list] = {}
    for r in tasks_rows:
        task = CRMTask.model_validate(
            {
                **r,
                "created_by": user_map[r["created_by_id"]],
                "completed_by": user_map.get(r["completed_by_id"])
                if r["completed_by_id"]
                else None,
                "assignees": task_assignees.get(r["id"], []),
            }
        )
        if r["deal_id"]:
            result.setdefault(r["deal_id"], []).append(task)
    return result


def assemble_selected_deals(cur: psycopg.Cursor) -> list[CRMDeal]:
    industry_map = _leaf_map(CRMIndustry, select_all(cur, "sales.crm_industries"))
    product_map = _leaf_map(CRMProduct, select_all(cur, "sales.crm_products"))
    loss_reason_map = _leaf_map(
        CRMLossReason, select_all(cur, "sales.crm_loss_reasons")
    )
    source_map = _leaf_map(CRMSource, select_all(cur, "sales.crm_sources"))
    campaign_map = _leaf_map(CRMCampaign, select_all(cur, "sales.crm_campaigns"))

    user_map = _user_map(
        select_all(cur, "sales.crm_users"),
        select_all(cur, "sales.crm_teams"),
        select_columns(cur, "sales.crm_teams_users", ("team_id", "user_id")),
    )

    pipeline_map = _leaf_map(CRMPipeline, select_all(cur, "sales.crm_pipelines"))
    pipeline_stage_map = _pipeline_stage_map(
        select_all(cur, "sales.crm_pipeline_stages"), pipeline_map
    )

    contact_rows = select_all(cur, "sales.crm_contacts")
    contact_map = _leaf_map(CRMContact, contact_rows)

    organization_map = _organization_map(
        select_all(cur, "sales.crm_organizations"),
        user_map,
        industry_map,
        select_columns(
            cur,
            "sales.crm_organizations_industries",
            ("organization_id", "industry_id"),
        ),
        select_columns(
            cur, "sales.crm_organizations_users", ("organization_id", "user_id")
        ),
        contact_map,
        contact_rows,
    )

    deal_contacts_map = _deal_contacts_map(
        select_columns(cur, "sales.crm_deals_contacts", ("deal_id", "contact_id")),
        contact_map,
    )
    deal_products_map = _deal_products_map(
        select_columns(cur, "sales.crm_deals_products", ("deal_id", "product_id")),
        product_map,
    )
    tasks_by_deal_map = _tasks_by_deal_map(
        select_all(cur, "sales.crm_tasks"),
        user_map,
        select_columns(cur, "sales.crm_tasks_users", ("task_id", "user_id")),
    )

    return [
        CRMDeal.model_validate(
            {
                **r,
                "stage": pipeline_stage_map[r["stage_id"]],
                "owner": user_map.get(r["owner_id"]) if r["owner_id"] else None,
                "source": source_map.get(r["source_id"]) if r["source_id"] else None,
                "campaign": campaign_map.get(r["campaign_id"])
                if r["campaign_id"]
                else None,
                "loss_reason": loss_reason_map.get(r["loss_reason_id"])
                if r["loss_reason_id"]
                else None,
                "organization": organization_map.get(r["organization_id"])
                if r["organization_id"]
                else None,
                "contacts": deal_contacts_map.get(r["id"], []),
                "products": deal_products_map.get(r["id"], []),
                "tasks": tasks_by_deal_map.get(r["id"], []),
            }
        )
        for r in select_all(cur, "sales.crm_deals")
    ]
