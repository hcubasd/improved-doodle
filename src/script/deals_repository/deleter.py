import psycopg
from datetime import datetime
from psycopg import sql

_JOIN_TABLES = (
    "sales.crm_tasks_users",
    "sales.crm_deals_contacts",
    "sales.crm_deals_products",
    "sales.crm_organizations_industries",
    "sales.crm_organizations_users",
    "sales.crm_teams_users",
)

_ENTITY_TABLES = (
    "sales.crm_tasks",
    "sales.crm_deals",
    "sales.crm_contacts",
    "sales.crm_organizations",
    "sales.crm_pipeline_stages",
    "sales.crm_users",
    "sales.crm_teams",
    "sales.crm_pipelines",
    "sales.crm_campaigns",
    "sales.crm_sources",
    "sales.crm_loss_reasons",
    "sales.crm_industries",
    "sales.crm_products",
)


def delete_join_tables(cur: psycopg.Cursor) -> None:
    for table in _JOIN_TABLES:
        cur.execute(sql.SQL("DELETE FROM {}").format(sql.Identifier(*table.split("."))))


def delete_orphans(cur: psycopg.Cursor, synced_at: datetime) -> None:
    for table in _ENTITY_TABLES:
        cur.execute(
            sql.SQL("DELETE FROM {} WHERE synced_at < %s").format(
                sql.Identifier(*table.split("."))
            ),
            (synced_at,),
        )
