from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "products", sa.Column("stock_count", sa.Integer(), nullable=True),
    )
    products = sa.table("products", sa.column("stock_count", sa.Integer()))
    op.get_bind().execute(
        products.update()
        .where(products.c.stock_count.is_(None))
        .values(stock_count=0)
    )
    with op.batch_alter_table("products") as batch:
        batch.alter_column(
            "stock_count", existing_type=sa.Integer(), nullable=False,
        )


def downgrade() -> None:
    with op.batch_alter_table("products") as batch:
        batch.drop_column("stock_count")
