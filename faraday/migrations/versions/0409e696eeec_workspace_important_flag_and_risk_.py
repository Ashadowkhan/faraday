"""workspace important flag and risk constraint

Revision ID: 0409e696eeec
Revises: f6edb9a16479
Create Date: 2022-09-01 17:05:05.344298+00:00

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = '0409e696eeec'
down_revision = 'f6edb9a16479'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.execute("ALTER TABLE vulnerability DROP CONSTRAINT check_vulnerability_risk")
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    ...
    # ### end Alembic commands ###
