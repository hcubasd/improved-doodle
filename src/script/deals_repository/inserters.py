import psycopg
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
    cur: psycopg.Cursor, table: str, rows: list[dict]
) -> None:
    cur.executemany(
        sql.SQL(
            "INSERT INTO sales.{} (id, title, created_at, updated_at)"
            " VALUES (%(id)s, %(title)s, %(created_at)s, %(updated_at)s)"
            " ON CONFLICT (id) DO NOTHING"
        ).format(sql.Identifier(table)),
        rows,
    )


def insert_titled_described(
    cur: psycopg.Cursor, table: str, rows: list[dict]
) -> None:
    cur.executemany(
        sql.SQL(
            "INSERT INTO sales.{} (id, title, description, created_at, updated_at)"
            " VALUES (%(id)s, %(title)s, %(description)s, %(created_at)s, %(updated_at)s)"
            " ON CONFLICT (id) DO NOTHING"
        ).format(sql.Identifier(table)),
        rows,
    )


def insert_loss_reasons(
    cur: psycopg.Cursor, rows: list[dict]
) -> None:
    cur.executemany(
        "INSERT INTO sales.crm_loss_reasons (id, reason, created_at, updated_at)"
        " VALUES (%(id)s, %(reason)s, %(created_at)s, %(updated_at)s)"
        " ON CONFLICT (id) DO NOTHING",
        rows,
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
    cur: psycopg.Cursor, users: list[CRMUser]
) -> None:
    cur.executemany(
        "INSERT INTO sales.crm_users"
        " (id, full_name, email, phone, created_at, updated_at)"
        " VALUES (%(id)s, %(full_name)s, %(email)s, %(phone)s, %(created_at)s, %(updated_at)s)"
        " ON CONFLICT (id) DO NOTHING",
        [u.model_dump() for u in users],
    )


def insert_pipelines(
    cur: psycopg.Cursor, deals: list[CRMDeal]
) -> None:
    cur.executemany(
        "INSERT INTO sales.crm_pipelines"
        " (id, title, display_order, created_at, updated_at)"
        " VALUES (%(id)s, %(title)s, %(display_order)s, %(created_at)s, %(updated_at)s)"
        " ON CONFLICT (id) DO NOTHING",
        [d.stage.pipeline.model_dump() for d in deals],
    )


def insert_pipeline_stages(
    cur: psycopg.Cursor, deals: list[CRMDeal]
) -> None:
    cur.executemany(
        "INSERT INTO sales.crm_pipeline_stages"
        " (id, pipeline_id, title, description, objective, display_order, created_at, updated_at)"
        " VALUES"
        " (%(id)s, %(pipeline_id)s, %(title)s, %(description)s, %(objective)s,"
        "  %(display_order)s, %(created_at)s, %(updated_at)s)"
        " ON CONFLICT (id) DO NOTHING",
        [
            {**d.stage.model_dump(), "pipeline_id": d.stage.pipeline.id}
            for d in deals
        ],
    )


def insert_organizations(
    cur: psycopg.Cursor, deals: list[CRMDeal]
) -> None:
    cur.executemany(
        "INSERT INTO sales.crm_organizations"
        " (id, owner_id, title, description, website, address, created_at, updated_at)"
        " VALUES"
        " (%(id)s, %(owner_id)s, %(title)s, %(description)s, %(website)s,"
        "  %(address)s, %(created_at)s, %(updated_at)s)"
        " ON CONFLICT (id) DO NOTHING",
        [
            {
                **d.organization.model_dump(),
                "owner_id": d.organization.owner.id if d.organization.owner else None,
                "address": Jsonb(d.organization.address) if d.organization.address else None,
            }
            for d in deals
            if d.organization
        ],
    )


def insert_contacts(
    cur: psycopg.Cursor, deals: list[CRMDeal]
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
                }
            )
    cur.executemany(
        "INSERT INTO sales.crm_contacts"
        " (id, organization_id, full_name, job_title, emails, phones, social_profiles,"
        "  created_at, updated_at)"
        " VALUES"
        " (%(id)s, %(organization_id)s, %(full_name)s, %(job_title)s, %(emails)s,"
        "  %(phones)s, %(social_profiles)s, %(created_at)s, %(updated_at)s)"
        " ON CONFLICT (id) DO NOTHING",
        rows,
    )


def insert_products(
    cur: psycopg.Cursor, deals: list[CRMDeal]
) -> None:
    cur.executemany(
        "INSERT INTO sales.crm_products"
        " (id, title, description, price, created_at, updated_at)"
        " VALUES (%(id)s, %(title)s, %(description)s, %(price)s, %(created_at)s, %(updated_at)s)"
        " ON CONFLICT (id) DO NOTHING",
        [p.model_dump() for d in deals for p in d.products],
    )


def insert_deals(
    cur: psycopg.Cursor, deals: list[CRMDeal]
) -> None:
    cur.executemany(
        "INSERT INTO sales.crm_deals"
        " (id, stage_id, owner_id, source_id, campaign_id, loss_reason_id, organization_id,"
        "  title, amount, expected_close_date, rating, status, closed_at, created_at, updated_at)"
        " VALUES"
        " (%(id)s, %(stage_id)s, %(owner_id)s, %(source_id)s, %(campaign_id)s,"
        "  %(loss_reason_id)s, %(organization_id)s, %(title)s, %(amount)s,"
        "  %(expected_close_date)s, %(rating)s, %(status)s, %(closed_at)s,"
        "  %(created_at)s, %(updated_at)s)"
        " ON CONFLICT (id) DO NOTHING",
        [
            {
                **d.model_dump(),
                "stage_id": d.stage.id,
                "owner_id": d.owner.id if d.owner else None,
                "source_id": d.source.id if d.source else None,
                "campaign_id": d.campaign.id if d.campaign else None,
                "loss_reason_id": d.loss_reason.id if d.loss_reason else None,
                "organization_id": d.organization.id if d.organization else None,
            }
            for d in deals
        ],
    )


def insert_tasks(
    cur: psycopg.Cursor, deals: list[CRMDeal]
) -> None:
    cur.executemany(
        "INSERT INTO sales.crm_tasks"
        " (id, created_by_id, completed_by_id, deal_id, title, description, task_type,"
        "  status, due_date, completed_at, created_at, updated_at)"
        " VALUES"
        " (%(id)s, %(created_by_id)s, %(completed_by_id)s, %(deal_id)s, %(title)s,"
        "  %(description)s, %(task_type)s, %(status)s, %(due_date)s, %(completed_at)s,"
        "  %(created_at)s, %(updated_at)s)"
        " ON CONFLICT (id) DO NOTHING",
        [
            {
                **t.model_dump(),
                "created_by_id": t.created_by.id,
                "completed_by_id": t.completed_by.id if t.completed_by else None,
                "deal_id": d.id,
            }
            for d in deals
            for t in d.tasks
        ],
    )
