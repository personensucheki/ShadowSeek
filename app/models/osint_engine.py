from __future__ import annotations

from datetime import datetime

from app.extensions.main import db


class ExternalProfile(db.Model):
    __tablename__ = "external_profiles"

    id = db.Column(db.Integer, primary_key=True)
    platform = db.Column(db.String(32), nullable=False, index=True)
    normalized_username = db.Column(db.String(128), nullable=False, index=True)
    username = db.Column(db.String(128), nullable=False)
    display_name = db.Column(db.String(255), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    profile_url = db.Column(db.String(512), nullable=True)
    avatar_url = db.Column(db.String(512), nullable=True)
    links = db.Column(db.JSON, nullable=True)
    evidence = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class IdentityMatch(db.Model):
    __tablename__ = "identity_matches"

    id = db.Column(db.Integer, primary_key=True)
    query_signature = db.Column(db.String(255), nullable=False, index=True)
    platform = db.Column(db.String(32), nullable=False, index=True)
    normalized_username = db.Column(db.String(128), nullable=False, index=True)
    matched_profile_id = db.Column(db.Integer, db.ForeignKey("external_profiles.id"), nullable=True, index=True)
    score = db.Column(db.Integer, nullable=False, default=0)
    confidence = db.Column(db.String(16), nullable=False, default="low", index=True)
    match_reasons = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class ImageHash(db.Model):
    __tablename__ = "image_hashes"

    id = db.Column(db.Integer, primary_key=True)
    source_platform = db.Column(db.String(32), nullable=False, index=True)
    source_profile = db.Column(db.String(255), nullable=False, index=True)
    hash_type = db.Column(db.String(16), nullable=False)
    hash_value = db.Column(db.String(64), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class ProfileAnalysis(db.Model):
    __tablename__ = "profile_analysis"

    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(db.Integer, db.ForeignKey("external_profiles.id"), nullable=True, index=True)
    fake_score = db.Column(db.Integer, nullable=False, default=0)
    bot_score = db.Column(db.Integer, nullable=False, default=0)
    scam_score = db.Column(db.Integer, nullable=False, default=0)
    risk_level = db.Column(db.String(16), nullable=False, default="low", index=True)
    indicators = db.Column(db.JSON, nullable=True)
    explanation = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class GraphNode(db.Model):
    __tablename__ = "graph_nodes"

    id = db.Column(db.Integer, primary_key=True)
    node_type = db.Column(db.String(32), nullable=False, index=True)
    node_key = db.Column(db.String(255), nullable=False, index=True)
    payload = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class GraphEdge(db.Model):
    __tablename__ = "graph_edges"

    id = db.Column(db.Integer, primary_key=True)
    source_node_id = db.Column(db.Integer, db.ForeignKey("graph_nodes.id"), nullable=False, index=True)
    target_node_id = db.Column(db.Integer, db.ForeignKey("graph_nodes.id"), nullable=False, index=True)
    edge_type = db.Column(db.String(32), nullable=False, index=True)
    confidence = db.Column(db.Float, nullable=False, default=0.0, index=True)
    payload = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class Watchlist(db.Model):
    __tablename__ = "watchlist"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    platform = db.Column(db.String(32), nullable=False, index=True)
    normalized_username = db.Column(db.String(128), nullable=False, index=True)
    last_seen_bio = db.Column(db.Text, nullable=True)
    last_seen_avatar_hash = db.Column(db.String(64), nullable=True, index=True)
    last_seen_links = db.Column(db.JSON, nullable=True)
    last_checked_at = db.Column(db.DateTime, nullable=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
