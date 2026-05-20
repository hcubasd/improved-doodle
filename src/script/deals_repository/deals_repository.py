import psycopg
from psycopg.rows import dict_row

from fluffy_waddle.sales import CRMDeal

from .deleter import delete
from .inserters import (
    all_users,
    insert_contacts,
    insert_deals,
    insert_join,
    insert_loss_reasons,
    insert_organizations,
    insert_pipeline_stages,
    insert_pipelines,
    insert_products,
    insert_tasks,
    insert_titled,
    insert_titled_described,
    insert_users,
)
from .selected_deals_assembler import assemble_selected_deals


class DealsRepository:
    def __init__(self, conn: psycopg.Connection):
        self._conn = conn

    def update(self, deals: list[CRMDeal]) -> None:
        with self._conn.transaction():
            with self._conn.cursor() as cur:
                delete(cur)

                users = list(all_users(deals))

                insert_titled(
                    cur,
                    "crm_industries",
                    [
                        i.model_dump()
                        for d in deals
                        if d.organization
                        for i in d.organization.industries
                    ],
                )
                insert_products(cur, deals)
                insert_loss_reasons(
                    cur,
                    [d.loss_reason.model_dump() for d in deals if d.loss_reason],
                )
                insert_titled_described(
                    cur,
                    "crm_sources",
                    [d.source.model_dump() for d in deals if d.source],
                )
                insert_titled_described(
                    cur,
                    "crm_campaigns",
                    [d.campaign.model_dump() for d in deals if d.campaign],
                )
                insert_users(cur, users)
                insert_titled(
                    cur, "crm_teams", [u.team.model_dump() for u in users if u.team]
                )
                insert_join(
                    cur,
                    "crm_teams_users",
                    "team_id",
                    "user_id",
                    [(u.team.id, u.id) for u in users if u.team],
                )
                insert_pipelines(cur, deals)
                insert_pipeline_stages(cur, deals)
                insert_organizations(cur, deals)
                insert_join(
                    cur,
                    "crm_organizations_industries",
                    "organization_id",
                    "industry_id",
                    [
                        (d.organization.id, i.id)
                        for d in deals
                        if d.organization
                        for i in d.organization.industries
                    ],
                )
                insert_join(
                    cur,
                    "crm_organizations_users",
                    "organization_id",
                    "user_id",
                    [
                        (d.organization.id, u.id)
                        for d in deals
                        if d.organization
                        for u in d.organization.followers
                    ],
                )
                insert_contacts(cur, deals)
                insert_deals(cur, deals)
                insert_join(
                    cur,
                    "crm_deals_products",
                    "deal_id",
                    "product_id",
                    [(d.id, p.id) for d in deals for p in d.products],
                )
                insert_join(
                    cur,
                    "crm_deals_contacts",
                    "deal_id",
                    "contact_id",
                    [(d.id, c.id) for d in deals for c in d.contacts],
                )
                insert_tasks(cur, deals)
                insert_join(
                    cur,
                    "crm_tasks_users",
                    "task_id",
                    "user_id",
                    [(t.id, u.id) for d in deals for t in d.tasks for u in t.assignees],
                )

    def get(self) -> list[CRMDeal]:
        with self._conn.cursor(row_factory=dict_row) as cur:
            return assemble_selected_deals(cur)
