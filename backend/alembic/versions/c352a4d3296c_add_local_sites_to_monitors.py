"""Add local sites to monitors

Revision ID: c352a4d3296c
Revises: 5c1f2342c3ae
Create Date: 2026-06-20 11:17:42.248919

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c352a4d3296c'
down_revision: Union[str, Sequence[str], None] = '5c1f2342c3ae'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


import uuid
from sqlalchemy.sql import table, column
from sqlalchemy import String, Integer

def upgrade() -> None:
    """Upgrade schema."""
    monitors_table = table(
        'monitors',
        column('id', String),
        column('name', String),
        column('url', String),
        column('check_interval_seconds', Integer)
    )

    INITIAL_URLS = [
        "https://promptwars-week-3.vercel.app/",
        "https://cluster-adaptive-blood-report-analy.vercel.app/",
        "https://web-prog-project-weld.vercel.app/",
        "https://sreeansh-dash.netlify.app/",
        "https://enchanting-banoffee-6c5cf4.netlify.app/",
        "https://cs-sandbox.netlify.app/",
        "https://indianedgeanpr.netlify.app/"
    ]

    def extract_name(url: str) -> str:
        name = url.replace("https://", "").replace("http://", "").split(".")[0]
        return name.title().replace("-", " ")

    rows = [
        {
            "id": str(uuid.uuid4()),
            "name": extract_name(url),
            "url": url,
            "check_interval_seconds": 120
        }
        for url in INITIAL_URLS
    ]

    op.bulk_insert(monitors_table, rows)


def downgrade() -> None:
    """Downgrade schema."""
    pass
