"""add osint engine tables

Revision ID: 20260413_0200
Revises: 20260412_9998
Create Date: 2026-04-13
"""

from alembic import op
import sqlalchemy as sa


revision = "20260413_0200"
down_revision = "20260412_9998"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    if "external_profiles" not in existing_tables:
        op.create_table(
        "external_profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("platform", sa.String(length=32), nullable=False),
        sa.Column("normalized_username", sa.String(length=128), nullable=False),
        sa.Column("username", sa.String(length=128), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("profile_url", sa.String(length=512), nullable=True),
        sa.Column("avatar_url", sa.String(length=512), nullable=True),
        sa.Column("links", sa.JSON(), nullable=True),
        sa.Column("evidence", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        )
    _create_index_if_missing("external_profiles", "ix_external_profiles_platform", ["platform"])
    _create_index_if_missing("external_profiles", "ix_external_profiles_normalized_username", ["normalized_username"])

    if "identity_matches" not in existing_tables:
        op.create_table(
        "identity_matches",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("query_signature", sa.String(length=255), nullable=False),
        sa.Column("platform", sa.String(length=32), nullable=False),
        sa.Column("normalized_username", sa.String(length=128), nullable=False),
        sa.Column("matched_profile_id", sa.Integer(), sa.ForeignKey("external_profiles.id"), nullable=True),
        sa.Column("score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("confidence", sa.String(length=16), nullable=False, server_default="low"),
        sa.Column("match_reasons", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        )
    _create_index_if_missing("identity_matches", "ix_identity_matches_query_signature", ["query_signature"])
    _create_index_if_missing("identity_matches", "ix_identity_matches_platform", ["platform"])
    _create_index_if_missing("identity_matches", "ix_identity_matches_normalized_username", ["normalized_username"])
    _create_index_if_missing("identity_matches", "ix_identity_matches_confidence", ["confidence"])

    if "image_hashes" not in existing_tables:
        op.create_table(
        "image_hashes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_platform", sa.String(length=32), nullable=False),
        sa.Column("source_profile", sa.String(length=255), nullable=False),
        sa.Column("hash_type", sa.String(length=16), nullable=False),
        sa.Column("hash_value", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        )
    _create_index_if_missing("image_hashes", "ix_image_hashes_source_platform", ["source_platform"])
    _create_index_if_missing("image_hashes", "ix_image_hashes_source_profile", ["source_profile"])
    _create_index_if_missing("image_hashes", "ix_image_hashes_hash_value", ["hash_value"])

    if "profile_analysis" not in existing_tables:
        op.create_table(
        "profile_analysis",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("profile_id", sa.Integer(), sa.ForeignKey("external_profiles.id"), nullable=True),
        sa.Column("fake_score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("bot_score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("scam_score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("risk_level", sa.String(length=16), nullable=False, server_default="low"),
        sa.Column("indicators", sa.JSON(), nullable=True),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        )
    _create_index_if_missing("profile_analysis", "ix_profile_analysis_profile_id", ["profile_id"])
    _create_index_if_missing("profile_analysis", "ix_profile_analysis_risk_level", ["risk_level"])

    if "graph_nodes" not in existing_tables:
        op.create_table(
        "graph_nodes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("node_type", sa.String(length=32), nullable=False),
        sa.Column("node_key", sa.String(length=255), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        )
    _create_index_if_missing("graph_nodes", "ix_graph_nodes_node_type", ["node_type"])
    _create_index_if_missing("graph_nodes", "ix_graph_nodes_node_key", ["node_key"])

    if "graph_edges" not in existing_tables:
        op.create_table(
        "graph_edges",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_node_id", sa.Integer(), sa.ForeignKey("graph_nodes.id"), nullable=False),
        sa.Column("target_node_id", sa.Integer(), sa.ForeignKey("graph_nodes.id"), nullable=False),
        sa.Column("edge_type", sa.String(length=32), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        )
    _create_index_if_missing("graph_edges", "ix_graph_edges_source_node_id", ["source_node_id"])
    _create_index_if_missing("graph_edges", "ix_graph_edges_target_node_id", ["target_node_id"])
    _create_index_if_missing("graph_edges", "ix_graph_edges_edge_type", ["edge_type"])
    _create_index_if_missing("graph_edges", "ix_graph_edges_confidence", ["confidence"])

    if "watchlist" not in existing_tables:
        op.create_table(
        "watchlist",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("platform", sa.String(length=32), nullable=False),
        sa.Column("normalized_username", sa.String(length=128), nullable=False),
        sa.Column("last_seen_bio", sa.Text(), nullable=True),
        sa.Column("last_seen_avatar_hash", sa.String(length=64), nullable=True),
        sa.Column("last_seen_links", sa.JSON(), nullable=True),
        sa.Column("last_checked_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        )
    _create_index_if_missing("watchlist", "ix_watchlist_user_id", ["user_id"])
    _create_index_if_missing("watchlist", "ix_watchlist_platform", ["platform"])
    _create_index_if_missing("watchlist", "ix_watchlist_normalized_username", ["normalized_username"])
    _create_index_if_missing("watchlist", "ix_watchlist_last_seen_avatar_hash", ["last_seen_avatar_hash"])
    _create_index_if_missing("watchlist", "ix_watchlist_last_checked_at", ["last_checked_at"])


def downgrade():
    op.drop_index("ix_watchlist_last_checked_at", table_name="watchlist")
    op.drop_index("ix_watchlist_last_seen_avatar_hash", table_name="watchlist")
    op.drop_index("ix_watchlist_normalized_username", table_name="watchlist")
    op.drop_index("ix_watchlist_platform", table_name="watchlist")
    op.drop_index("ix_watchlist_user_id", table_name="watchlist")
    op.drop_table("watchlist")

    op.drop_index("ix_graph_edges_confidence", table_name="graph_edges")
    op.drop_index("ix_graph_edges_edge_type", table_name="graph_edges")
    op.drop_index("ix_graph_edges_target_node_id", table_name="graph_edges")
    op.drop_index("ix_graph_edges_source_node_id", table_name="graph_edges")
    op.drop_table("graph_edges")

    op.drop_index("ix_graph_nodes_node_key", table_name="graph_nodes")
    op.drop_index("ix_graph_nodes_node_type", table_name="graph_nodes")
    op.drop_table("graph_nodes")

    op.drop_index("ix_profile_analysis_risk_level", table_name="profile_analysis")
    op.drop_index("ix_profile_analysis_profile_id", table_name="profile_analysis")
    op.drop_table("profile_analysis")

    op.drop_index("ix_image_hashes_hash_value", table_name="image_hashes")
    op.drop_index("ix_image_hashes_source_profile", table_name="image_hashes")
    op.drop_index("ix_image_hashes_source_platform", table_name="image_hashes")
    op.drop_table("image_hashes")

    op.drop_index("ix_identity_matches_confidence", table_name="identity_matches")
    op.drop_index("ix_identity_matches_normalized_username", table_name="identity_matches")
    op.drop_index("ix_identity_matches_platform", table_name="identity_matches")
    op.drop_index("ix_identity_matches_query_signature", table_name="identity_matches")
    op.drop_table("identity_matches")

    op.drop_index("ix_external_profiles_normalized_username", table_name="external_profiles")
    op.drop_index("ix_external_profiles_platform", table_name="external_profiles")
    op.drop_table("external_profiles")


def _create_index_if_missing(table_name: str, index_name: str, columns: list[str]):
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing = {row["name"] for row in inspector.get_indexes(table_name)}
    if index_name not in existing:
        op.create_index(index_name, table_name, columns)
