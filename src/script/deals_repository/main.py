import psycopg
from psycopg.rows import dict_row

from fluffy_waddle.sales import CRMDeal

from .deleter import delete
from .inserters import (
    insert_industries,
    insert_products,
    insert_loss_reasons,
    insert_sources,
    insert_campaigns,
    insert_users,
    insert_teams,
    insert_teams_users,
    insert_pipelines,
    insert_pipeline_stages,
    insert_organizations,
    insert_organizations_industries,
    insert_organizations_users,
    insert_contacts,
    insert_deals,
    insert_deals_products,
    insert_deals_contacts,
    insert_tasks,
    insert_tasks_users,
)
from .selected_deals_assembler import assemble_selected_deals


class DealsRepository:
    def __init__(self, conn: psycopg.Connection):
        self._conn = conn

    def update(self, deals: list[CRMDeal]) -> None:
        with self._conn.transaction():
            with self._conn.cursor() as cur:
                delete(cur)

                insert_industries(cur, deals)
                insert_products(cur, deals)
                insert_loss_reasons(cur, deals)
                insert_sources(cur, deals)
                insert_campaigns(cur, deals)
                insert_users(cur, deals)
                insert_teams(cur, deals)
                insert_teams_users(cur, deals)
                insert_pipelines(cur, deals)
                insert_pipeline_stages(cur, deals)
                insert_organizations(cur, deals)
                insert_organizations_industries(cur, deals)
                insert_organizations_users(cur, deals)
                insert_contacts(cur, deals)
                insert_deals(cur, deals)
                insert_deals_products(cur, deals)
                insert_deals_contacts(cur, deals)
                insert_tasks(cur, deals)
                insert_tasks_users(cur, deals)

    def get(self) -> list[CRMDeal]:
        with self._conn.cursor(row_factory=dict_row) as cur:
            return assemble_selected_deals(cur)
