"""initial schema

Revision ID: 20260328_0001
Revises:
Create Date: 2026-03-28 15:20:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260328_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tickers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("symbol", sa.String(length=16), nullable=False),
        sa.Column("exchange", sa.String(length=32), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("sector", sa.String(length=128), nullable=True),
        sa.Column("industry", sa.String(length=128), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_tickers_symbol"), "tickers", ["symbol"], unique=True)

    op.create_table(
        "scan_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("tickers_scanned", sa.Integer(), nullable=False),
        sa.Column("candidates_found", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "daily_bars",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("ticker_id", sa.Integer(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("open", sa.Float(), nullable=False),
        sa.Column("high", sa.Float(), nullable=False),
        sa.Column("low", sa.Float(), nullable=False),
        sa.Column("close", sa.Float(), nullable=False),
        sa.Column("volume", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(["ticker_id"], ["tickers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("ticker_id", "date", name="uq_daily_bars_ticker_date"),
    )
    op.create_index("ix_daily_bars_ticker_date", "daily_bars", ["ticker_id", "date"], unique=False)
    op.create_index(op.f("ix_daily_bars_ticker_id"), "daily_bars", ["ticker_id"], unique=False)

    op.create_table(
        "pump_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("ticker_id", sa.Integer(), nullable=False),
        sa.Column("base_date", sa.Date(), nullable=False),
        sa.Column("trigger_date", sa.Date(), nullable=False),
        sa.Column("peak_date", sa.Date(), nullable=False),
        sa.Column("base_price", sa.Float(), nullable=False),
        sa.Column("peak_price", sa.Float(), nullable=False),
        sa.Column("return_pct", sa.Float(), nullable=False),
        sa.Column("duration_days", sa.Integer(), nullable=False),
        sa.Column("event_quality_score", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(["ticker_id"], ["tickers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_pump_events_ticker_trigger", "pump_events", ["ticker_id", "trigger_date"], unique=False)
    op.create_index(op.f("ix_pump_events_ticker_id"), "pump_events", ["ticker_id"], unique=False)

    op.create_table(
        "feature_snapshots",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("ticker_id", sa.Integer(), nullable=False),
        sa.Column("event_id", sa.Integer(), nullable=True),
        sa.Column("reference_date", sa.Date(), nullable=False),
        sa.Column("is_positive_case", sa.Boolean(), nullable=False),
        sa.Column("ret_5d", sa.Float(), nullable=False),
        sa.Column("ret_10d", sa.Float(), nullable=False),
        sa.Column("ret_20d", sa.Float(), nullable=False),
        sa.Column("ret_30d", sa.Float(), nullable=False),
        sa.Column("rv_ratio", sa.Float(), nullable=False),
        sa.Column("atr_pct", sa.Float(), nullable=False),
        sa.Column("volatility_10d", sa.Float(), nullable=False),
        sa.Column("range_compression_score", sa.Float(), nullable=False),
        sa.Column("breakout_distance", sa.Float(), nullable=False),
        sa.Column("rsi_14", sa.Float(), nullable=False),
        sa.Column("sma20_distance", sa.Float(), nullable=False),
        sa.Column("sma50_distance", sa.Float(), nullable=False),
        sa.Column("avg_dollar_volume_20d", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(["event_id"], ["pump_events.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["ticker_id"], ["tickers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_feature_snapshots_ref_positive",
        "feature_snapshots",
        ["reference_date", "is_positive_case"],
        unique=False,
    )
    op.create_index(op.f("ix_feature_snapshots_event_id"), "feature_snapshots", ["event_id"], unique=False)
    op.create_index(
        op.f("ix_feature_snapshots_reference_date"),
        "feature_snapshots",
        ["reference_date"],
        unique=False,
    )
    op.create_index(op.f("ix_feature_snapshots_ticker_id"), "feature_snapshots", ["ticker_id"], unique=False)

    op.create_table(
        "scan_results",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("run_id", sa.Integer(), nullable=False),
        sa.Column("ticker_id", sa.Integer(), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("similarity_score", sa.Float(), nullable=False),
        sa.Column("matched_pattern_count", sa.Integer(), nullable=False),
        sa.Column("explanation_json", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["scan_runs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["ticker_id"], ["tickers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_scan_results_run_id"), "scan_results", ["run_id"], unique=False)
    op.create_index(op.f("ix_scan_results_ticker_id"), "scan_results", ["ticker_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_scan_results_ticker_id"), table_name="scan_results")
    op.drop_index(op.f("ix_scan_results_run_id"), table_name="scan_results")
    op.drop_table("scan_results")
    op.drop_index(op.f("ix_feature_snapshots_ticker_id"), table_name="feature_snapshots")
    op.drop_index(op.f("ix_feature_snapshots_reference_date"), table_name="feature_snapshots")
    op.drop_index(op.f("ix_feature_snapshots_event_id"), table_name="feature_snapshots")
    op.drop_index("ix_feature_snapshots_ref_positive", table_name="feature_snapshots")
    op.drop_table("feature_snapshots")
    op.drop_index(op.f("ix_pump_events_ticker_id"), table_name="pump_events")
    op.drop_index("ix_pump_events_ticker_trigger", table_name="pump_events")
    op.drop_table("pump_events")
    op.drop_index(op.f("ix_daily_bars_ticker_id"), table_name="daily_bars")
    op.drop_index("ix_daily_bars_ticker_date", table_name="daily_bars")
    op.drop_table("daily_bars")
    op.drop_table("scan_runs")
    op.drop_index(op.f("ix_tickers_symbol"), table_name="tickers")
    op.drop_table("tickers")

