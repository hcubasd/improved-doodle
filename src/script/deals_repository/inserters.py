import psycopg
from datetime import datetime
from psycopg import sql
from psycopg.types.json import Jsonb

from fluffy_waddle.sales import CRMDeal, CRMUser


def all_users(deals: list[CRMDeal]):
    for d in deals:
        if d.owner:
            yield d.owner
        if d.organization:
            if d.organization.owner:
                yield d.organization.owner
            yield from d.organization.followers
        for t in d.tasks:
            yield t.created_by
            if t.completed_by:
                yield t.completed_by
            yield from t.assignees


def insert_titled(
    cur: psycopg.Cursor, table: str, rows: list[dict], synced_at: datetime
) -> None:
    cur.executemany(
        sql.SQL(
            "INSERT INTO sales.{} (id, title, created_at, updated_at, synced_at)"
            " VALUES (%(id)s, %(title)s, %(created_at)s, %(updated_at)s, %(synced_at)s)"
            " ON CONFLICT (id) DO UPDATE SET"
            "  title = EXCLUDED.title,"
            "  updated_at = EXCLUDED.updated_at,"
            "  synced_at = EXCLUDED.synced_at"
        ).format(sql.Identifier(table)),
        [{**r, "synced_at": synced_at} for r in rows],
    )


def insert_titled_described(
    cur: psycopg.Cursor, table: str, rows: list[dict], synced_at: datetime
) -> None:
    cur.executemany(
        sql.SQL(
            "INSERT INTO sales.{} (id, title, description, created_at, updated_at, synced_at)"
            " VALUES (%(id)s, %(title)s, %(description)s, %(created_at)s, %(updated_at)s, %(synced_at)s)"
            " ON CONFLICT (id) DO UPDATE SET"
            "  title = EXCLUDED.title,"
            "  description = EXCLUDED.description,"
            "  updated_at = EXCLUDED.updated_at,"
            "  synced_at = EXCLUDED.synced_at"
        ).format(sql.Identifier(table)),
        [{**r, "synced_at": synced_at} for r in rows],
    )


def insert_loss_reasons(
    cur: psycopg.Cursor, rows: list[dict], synced_at: datetime
) -> None:
    cur.executemany(
        "INSERT INTO sales.crm_loss_reasons (id, reason, created_at, updated_at, synced_at)"
        " VALUES (%(id)s, %(reason)s, %(created_at)s, %(updated_at)s, %(synced_at)s)"
        " ON CONFLICT (id) DO UPDATE SET"
        "  reason = EXCLUDED.reason,"
        "  updated_at = EXCLUDED.updated_at,"
        "  synced_at = EXCLUDED.synced_at",
        [{**r, "synced_at": synced_at} for r in rows],
    )


def insert_join(
    cur: psycopg.Cursor, table: str, col1: str, col2: str, rows: list[tuple]
) -> None:
    cur.executemany(
        sql.SQL(
            "INSERT INTO sales.{} ({}, {}) VALUES (%s, %s) ON CONFLICT DO NOTHING"
        ).format(sql.Identifier(table), sql.Identifier(col1), sql.Identifier(col2)),
        rows,
    )


def insert_users(
    cur: psycopg.Cursor, users: list[CRMUser], synced_at: datetime
) -> None:
    cur.executemany(
        "INSERT INTO sales.crm_users"
        " (id, full_name, email, phone, created_at, updated_at, synced_at)"
        " VALUES (%(id)s, %(full_name)s, %(email)s, %(phone)s, %(created_at)s, %(updated_at)s, %(synced_at)s)"
        " ON CONFLICT (id) DO UPDATE SET"
        "  full_name = EXCLUDED.full_name,"
        "  email = EXCLUDED.email,"
        "  phone = EXCLUDED.phone,"
        "  updated_at = EXCLUDED.updated_at,"
        "  synced_at = EXCLUDED.synced_at",
        [{**u.model_dump(), "synced_at": synced_at} for u in users],
    )


def insert_pipelines(
    cur: psycopg.Cursor, deals: list[CRMDeal], synced_at: datetime
) -> None:
    cur.executemany(
        "INSERT INTO sales.crm_pipelines"
        " (id, title, display_order, created_at, updated_at, synced_at)"
        " VALUES (%(id)s, %(title)s, %(display_order)s, %(created_at)s, %(updated_at)s, %(synced_at)s)"
        " ON CONFLICT (id) DO UPDATE SET"
        "  title = EXCLUDED.title,"
        "  display_order = EXCLUDED.display_order,"
        "  updated_at = EXCLUDED.updated_at,"
        "  synced_at = EXCLUDED.synced_at",
        [{**d.stage.pipeline.model_dump(), "synced_at": synced_at} for d in deals],
    )


def insert_pipeline_stages(
    cur: psycopg.Cursor, deals: list[CRMDeal], synced_at: datetime
) -> None:
    cur.executemany(
        "INSERT INTO sales.crm_pipeline_stages"
        " (id, pipeline_id, title, description, objective, display_order, created_at, updated_at, synced_at)"
        " VALUES"
        " (%(id)s, %(pipeline_id)s, %(title)s, %(description)s, %(objective)s,"
        "  %(display_order)s, %(created_at)s, %(updated_at)s, %(synced_at)s)"
        " ON CONFLICT (id) DO UPDATE SET"
        "  pipeline_id = EXCLUDED.pipeline_id,"
        "  title = EXCLUDED.title,"
        "  description = EXCLUDED.description,"
        "  objective = EXCLUDED.objective,"
        "  display_order = EXCLUDED.display_order,"
        "  updated_at = EXCLUDED.updated_at,"
        "  synced_at = EXCLUDED.synced_at",
        [
            {**d.stage.model_dump(), "pipeline_id": d.stage.pipeline.id, "synced_at": synced_at}
            for d in deals
        ],
    )


def insert_organizations(
    cur: psycopg.Cursor, deals: list[CRMDeal], synced_at: datetime
) -> None:
    cur.executemany(
        "INSERT INTO sales.crm_organizations"
        " (id, owner_id, title, description, website, address, created_at, updated_at, synced_at)"
        " VALUES"
        " (%(id)s, %(owner_id)s, %(title)s, %(description)s, %(website)s,"
        "  %(address)s, %(created_at)s, %(updated_at)s, %(synced_at)s)"
        " ON CONFLICT (id) DO UPDATE SET"
        "  owner_id = EXCLUDED.owner_id,"
        "  title = EXCLUDED.title,"
        "  description = EXCLUDED.description,"
        "  website = EXCLUDED.website,"
        "  address = EXCLUDED.address,"
        "  updated_at = EXCLUDED.updated_at,"
        "  synced_at = EXCLUDED.synced_at",
        [
            {
                **d.organization.model_dump(),
                "owner_id": d.organization.owner.id if d.organization.owner else None,
                "address": Jsonb(d.organization.address) if d.organization.address else None,
                "synced_at": synced_at,
            }
            for d in deals
            if d.organization
        ],
    )


def insert_contacts(
    cur: psycopg.Cursor, deals: list[CRMDeal], synced_at: datetime
) -> None:
    rows = []
    for d in deals:
        if d.organization:
            for c in d.organization.contacts:
                rows.append(
                    {
                        **c.model_dump(),
                        "organization_id": d.organization.id,
                        "emails": Jsonb(c.emails),
                        "phones": Jsonb(c.phones),
                        "social_profiles": Jsonb(c.social_profiles),
                        "synced_at": synced_at,
                    }
                )
        for c in d.contacts:
            rows.append(
                {
                    **c.model_dump(),
                    "organization_id": None,
                    "emails": Jsonb(c.emails),
                    "phones": Jsonb(c.phones),
                    "social_profiles": Jsonb(c.social_profiles),
                    "synced_at": synced_at,
                }
            )
    cur.executemany(
        "INSERT INTO sales.crm_contacts"
        " (id, organization_id, full_name, job_title, emails, phones, social_profiles,"
        "  created_at, updated_at, synced_at)"
        " VALUES"
        " (%(id)s, %(organization_id)s, %(full_name)s, %(job_title)s, %(emails)s,"
        "  %(phones)s, %(social_profiles)s, %(created_at)s, %(updated_at)s, %(synced_at)s)"
        " ON CONFLICT (id) DO UPDATE SET"
        "  organization_id = COALESCE(EXCLUDED.organization_id, sales.crm_contacts.organization_id),"
        "  full_name = EXCLUDED.full_name,"
        "  job_title = EXCLUDED.job_title,"
        "  emails = EXCLUDED.emails,"
        "  phones = EXCLUDED.phones,"
        "  social_profiles = EXCLUDED.social_profiles,"
        "  updated_at = EXCLUDED.updated_at,"
        "  synced_at = EXCLUDED.synced_at",
        rows,
    )


def insert_products(
    cur: psycopg.Cursor, deals: list[CRMDeal], synced_at: datetime
) -> None:
    cur.executemany(
        "INSERT INTO sales.crm_products"
        " (id, title, description, price, created_at, updated_at, synced_at)"
        " VALUES (%(id)s, %(title)s, %(description)s, %(price)s, %(created_at)s, %(updated_at)s, %(synced_at)s)"
        " ON CONFLICT (id) DO UPDATE SET"
        "  title = EXCLUDED.title,"
        "  description = EXCLUDED.description,"
        "  price = EXCLUDED.price,"
        "  updated_at = EXCLUDED.updated_at,"
        "  synced_at = EXCLUDED.synced_at",
        [{**p.model_dump(), "synced_at": synced_at} for d in deals for p in d.products],
    )


def insert_deals(
    cur: psycopg.Cursor, deals: list[CRMDeal], synced_at: datetime
) -> None:
    cur.executemany(
        "INSERT INTO sales.crm_deals"
        " (id, stage_id, owner_id, source_id, campaign_id, loss_reason_id, organization_id,"
        "  title, amount, expected_close_date, rating, status, closed_at, created_at, updated_at, synced_at)"
        " VALUES"
        " (%(id)s, %(stage_id)s, %(owner_id)s, %(source_id)s, %(campaign_id)s,"
        "  %(loss_reason_id)s, %(organization_id)s, %(title)s, %(amount)s,"
        "  %(expected_close_date)s, %(rating)s, %(status)s, %(closed_at)s,"
        "  %(created_at)s, %(updated_at)s, %(synced_at)s)"
        " ON CONFLICT (id) DO UPDATE SET"
        "  stage_id = EXCLUDED.stage_id,"
        "  owner_id = EXCLUDED.owner_id,"
        "  source_id = EXCLUDED.source_id,"
        "  campaign_id = EXCLUDED.campaign_id,"
        "  loss_reason_id = EXCLUDED.loss_reason_id,"
        "  organization_id = EXCLUDED.organization_id,"
        "  title = EXCLUDED.title,"
        "  amount = EXCLUDED.amount,"
        "  expected_close_date = EXCLUDED.expected_close_date,"
        "  rating = EXCLUDED.rating,"
        "  status = EXCLUDED.status,"
        "  closed_at = EXCLUDED.closed_at,"
        "  updated_at = EXCLUDED.updated_at,"
        "  synced_at = EXCLUDED.synced_at",
        [
            {
                **d.model_dump(),
                "stage_id": d.stage.id,
                "owner_id": d.owner.id if d.owner else None,
                "source_id": d.source.id if d.source else None,
                "campaign_id": d.campaign.id if d.campaign else None,
                "loss_reason_id": d.loss_reason.id if d.loss_reason else None,
                "organization_id": d.organization.id if d.organization else None,
                "synced_at": synced_at,
            }
            for d in deals
        ],
    )


def insert_tasks(
    cur: psycopg.Cursor, deals: list[CRMDeal], synced_at: datetime
) -> None:
    cur.executemany(
        "INSERT INTO sales.crm_tasks"
        " (id, created_by_id, completed_by_id, deal_id, title, description, task_type,"
        "  status, due_date, completed_at, created_at, updated_at, synced_at)"
        " VALUES"
        " (%(id)s, %(created_by_id)s, %(completed_by_id)s, %(deal_id)s, %(title)s,"
        "  %(description)s, %(task_type)s, %(status)s, %(due_date)s, %(completed_at)s,"
        "  %(created_at)s, %(updated_at)s, %(synced_at)s)"
        " ON CONFLICT (id) DO UPDATE SET"
        "  created_by_id = EXCLUDED.created_by_id,"
        "  completed_by_id = EXCLUDED.completed_by_id,"
        "  deal_id = EXCLUDED.deal_id,"
        "  title = EXCLUDED.title,"
        "  description = EXCLUDED.description,"
        "  task_type = EXCLUDED.task_type,"
        "  status = EXCLUDED.status,"
        "  due_date = EXCLUDED.due_date,"
        "  completed_at = EXCLUDED.completed_at,"
        "  updated_at = EXCLUDED.updated_at,"
        "  synced_at = EXCLUDED.synced_at",
        [
            {
                **t.model_dump(),
                "created_by_id": t.created_by.id,
                "completed_by_id": t.completed_by.id if t.completed_by else None,
                "deal_id": d.id,
                "synced_at": synced_at,
            }
            for d in deals
            for t in d.tasks
        ],
    )
