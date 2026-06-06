import psycopg

_ALL_TABLES = (
    "sales.crm_tasks_users, sales.crm_deals_contacts, sales.crm_deals_products,"
    " sales.crm_organizations_industries, sales.crm_organizations_users, sales.crm_teams_users,"
    " sales.crm_tasks, sales.crm_deals, sales.crm_contacts, sales.crm_organizations,"
    " sales.crm_pipeline_stages, sales.crm_users, sales.crm_teams, sales.crm_pipelines,"
    " sales.crm_campaigns, sales.crm_sources, sales.crm_loss_reasons,"
    " sales.crm_industries, sales.crm_products"
)


def truncate_all(cur: psycopg.Cursor) -> None:
    cur.execute(f"TRUNCATE {_ALL_TABLES} CASCADE")
