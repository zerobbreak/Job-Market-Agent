"""typed tables: profiles, jobs, matches, applications

Splits the four collections with real filter/sort/join needs out of the
generic ``documents`` blob table into dedicated typed tables (see
``app.core.database`` and ``app.repositories.postgres_base.TypedRepository``
for the rationale). ``documents`` keeps backing ``analytics`` and any future
ad-hoc collection.

Existing rows for the four migrated collections are copied into their new
tables (matches are unpacked from one blob-per-user into one row per
matched job) and then removed from ``documents``.

Revision ID: 0003
Revises: 0002
Create Date: 2026-09-11

"""
from __future__ import annotations

import json
import uuid

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def _load(value):
    """Best-effort JSON decode for the double-serialized string fields the
    Appwrite-era repositories wrote (e.g. a list stored as a JSON string
    inside the JSON `data` column)."""
    if isinstance(value, str):
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value
    return value


def _documents(bind, collection):
    return bind.execute(
        sa.text("SELECT id, user_id, data, created_at, updated_at FROM documents WHERE collection = :c"),
        {"c": collection},
    ).mappings().all()


def upgrade() -> None:
    bind = op.get_bind()

    # ── schema ────────────────────────────────────────────────────────────

    op.create_table(
        "profiles",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("email", sa.String(length=320), nullable=True),
        sa.Column("phone", sa.String(length=64), nullable=True),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("experience_level", sa.String(length=100), nullable=True),
        sa.Column("education", sa.String(length=500), nullable=True),
        sa.Column("career_goals", sa.Text(), nullable=True),
        sa.Column("cv_filename", sa.String(length=500), nullable=True),
        sa.Column("cv_file_id", sa.String(length=64), sa.ForeignKey("files.id", ondelete="SET NULL"), nullable=True),
        sa.Column("cv_hash", sa.String(length=128), nullable=True),
        sa.Column("has_cv", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("notification_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("notification_threshold", sa.Integer(), nullable=False, server_default="70"),
        sa.Column("attrs", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_profiles_user_id", "profiles", ["user_id"])
    op.create_index("ix_profiles_is_active", "profiles", ["is_active"])

    op.create_table(
        "jobs",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("company", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="initializing"),
        sa.Column("progress", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("phase", sa.String(length=255), nullable=True),
        sa.Column("template_type", sa.String(length=50), nullable=False, server_default="modern"),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("attrs", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_jobs_user_id", "jobs", ["user_id"])
    op.create_index("ix_jobs_status", "jobs", ["status"])

    op.create_table(
        "matches",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("job_hash", sa.String(length=500), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("company", sa.String(length=255), nullable=True),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("match_score", sa.Float(), nullable=True),
        sa.Column("semantic_score", sa.Float(), nullable=True),
        sa.Column("keyword_score", sa.Float(), nullable=True),
        sa.Column("score_breakdown", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("match_reasons", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("last_seen", sa.DateTime(timezone=True), nullable=True),
        sa.Column("attrs", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("user_id", "job_hash", name="uq_matches_user_job"),
    )
    op.create_index("ix_matches_user_id", "matches", ["user_id"])
    op.create_index("ix_matches_job_hash", "matches", ["job_hash"])
    op.create_index("ix_matches_match_score", "matches", ["match_score"])

    op.create_table(
        "applications",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("company", sa.String(length=255), nullable=True),
        sa.Column("role", sa.String(length=255), nullable=True),
        sa.Column("job_url", sa.Text(), nullable=True),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="generated"),
        sa.Column("match_score", sa.Float(), nullable=True),
        sa.Column("ats_score", sa.Float(), nullable=True),
        sa.Column("cv_storage_id", sa.String(length=64), sa.ForeignKey("files.id", ondelete="SET NULL"), nullable=True),
        sa.Column("cover_letter_storage_id", sa.String(length=64), sa.ForeignKey("files.id", ondelete="SET NULL"), nullable=True),
        sa.Column("job_description", sa.Text(), nullable=True),
        sa.Column("views", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("date_created", sa.String(length=64), nullable=True),
        sa.Column("date_updated", sa.String(length=64), nullable=True),
        sa.Column("attrs", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_applications_user_id", "applications", ["user_id"])
    op.create_index("ix_applications_status", "applications", ["status"])
    op.create_index("ix_applications_date_created", "applications", ["date_created"])

    # ── data backfill ─────────────────────────────────────────────────────

    for row in _documents(bind, "profiles"):
        data = dict(row["data"] or {})
        is_active = bool(data.pop("isActive", None) or data.pop("is_active", None) or False)
        user_id = row["user_id"] or data.pop("user_id", None) or data.pop("userId", None)
        data.pop("user_id", None)
        data.pop("userId", None)
        params = {
            "id": row["id"],
            "user_id": user_id,
            "name": data.pop("name", None),
            "email": data.pop("email", None),
            "phone": data.pop("phone", None),
            "location": data.pop("location", None),
            "title": data.pop("title", None),
            "experience_level": data.pop("experience_level", None),
            "education": data.pop("education", None),
            "career_goals": data.pop("career_goals", None),
            "cv_filename": data.pop("cv_filename", None),
            "cv_file_id": data.pop("cv_file_id", None),
            "cv_hash": data.pop("cv_hash", None),
            "has_cv": bool(data.pop("has_cv", False)),
            "is_active": is_active,
            "notification_enabled": bool(data.pop("notification_enabled", False)),
            "notification_threshold": int(data.pop("notification_threshold", 70) or 70),
            "attrs": json.dumps(data),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }
        bind.execute(sa.text("""
            INSERT INTO profiles (id, user_id, name, email, phone, location, title,
                experience_level, education, career_goals, cv_filename, cv_file_id, cv_hash,
                has_cv, is_active, notification_enabled, notification_threshold, attrs,
                created_at, updated_at)
            VALUES (:id, :user_id, :name, :email, :phone, :location, :title,
                :experience_level, :education, :career_goals, :cv_filename, :cv_file_id, :cv_hash,
                :has_cv, :is_active, :notification_enabled, :notification_threshold, :attrs::jsonb,
                :created_at, :updated_at)
            ON CONFLICT (id) DO NOTHING
        """), params)

    for row in _documents(bind, "jobs"):
        data = dict(row["data"] or {})
        user_id = row["user_id"] or data.pop("user_id", None)
        data.pop("user_id", None)
        params = {
            "id": row["id"],
            "user_id": user_id,
            "title": data.pop("title", None),
            "company": data.pop("company", None),
            "status": data.pop("status", None) or "initializing",
            "progress": int(data.pop("progress", 0) or 0),
            "phase": data.pop("phase", None),
            "template_type": data.pop("template_type", None) or "modern",
            "error": data.pop("error", None),
            "attrs": json.dumps(data),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }
        bind.execute(sa.text("""
            INSERT INTO jobs (id, user_id, title, company, status, progress, phase,
                template_type, error, attrs, created_at, updated_at)
            VALUES (:id, :user_id, :title, :company, :status, :progress, :phase,
                :template_type, :error, :attrs::jsonb, :created_at, :updated_at)
            ON CONFLICT (id) DO NOTHING
        """), params)

    for row in _documents(bind, "applications"):
        data = dict(row["data"] or {})
        user_id = row["user_id"] or data.pop("user_id", None)
        data.pop("user_id", None)
        params = {
            "id": row["id"],
            "user_id": user_id,
            "company": data.pop("company", None),
            "role": data.pop("role", None),
            "job_url": data.pop("job_url", None),
            "location": data.pop("location", None),
            "status": data.pop("status", None) or "generated",
            "match_score": data.pop("match_score", None),
            "ats_score": data.pop("ats_score", None),
            "cv_storage_id": data.pop("cv_storage_id", None),
            "cover_letter_storage_id": data.pop("cover_letter_storage_id", None),
            "job_description": data.pop("job_description", None),
            "views": int(data.pop("views", 0) or 0),
            "date_created": data.pop("date_created", None),
            "date_updated": data.pop("date_updated", None),
            "attrs": json.dumps(data),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }
        if user_id is None:
            continue  # applications.user_id is NOT NULL; skip unattributable legacy rows
        bind.execute(sa.text("""
            INSERT INTO applications (id, user_id, company, role, job_url, location, status,
                match_score, ats_score, cv_storage_id, cover_letter_storage_id, job_description,
                views, date_created, date_updated, attrs, created_at, updated_at)
            VALUES (:id, :user_id, :company, :role, :job_url, :location, :status,
                :match_score, :ats_score, :cv_storage_id, :cover_letter_storage_id, :job_description,
                :views, :date_created, :date_updated, :attrs::jsonb, :created_at, :updated_at)
            ON CONFLICT (id) DO NOTHING
        """), params)

    for row in _documents(bind, "matches"):
        data = dict(row["data"] or {})
        user_id = row["user_id"] or data.get("user_id") or data.get("userId")
        if user_id is None:
            continue
        location = data.get("location") or ""
        last_seen = data.get("last_seen")
        matches = _load(data.get("matches", "[]")) or []
        seen_hashes: set[str] = set()

        for match in matches:
            job = (match or {}).get("job", {}) or {}
            job_hash = str(job.get("id") or job.get("url") or uuid.uuid4().hex)[:500]
            if job_hash in seen_hashes:
                continue
            seen_hashes.add(job_hash)

            score_breakdown = match.get("score_breakdown") or {}
            params = {
                "id": uuid.uuid4().hex,
                "user_id": user_id,
                "job_hash": job_hash,
                "title": job.get("title", ""),
                "company": job.get("company", ""),
                "location": job.get("location") or location,
                "url": job.get("url", ""),
                "description": job.get("description", ""),
                "match_score": match.get("match_score"),
                "semantic_score": match.get("semantic_score"),
                "keyword_score": score_breakdown.get("keyword"),
                "score_breakdown": json.dumps(score_breakdown),
                "match_reasons": json.dumps(match.get("match_reasons") or []),
                "last_seen": last_seen,
                "attrs": "{}",
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }
            bind.execute(sa.text("""
                INSERT INTO matches (id, user_id, job_hash, title, company, location, url,
                    description, match_score, semantic_score, keyword_score, score_breakdown,
                    match_reasons, last_seen, attrs, created_at, updated_at)
                VALUES (:id, :user_id, :job_hash, :title, :company, :location, :url,
                    :description, :match_score, :semantic_score, :keyword_score, :score_breakdown::jsonb,
                    :match_reasons::jsonb, :last_seen, :attrs::jsonb, :created_at, :updated_at)
                ON CONFLICT (user_id, job_hash) DO NOTHING
            """), params)

    bind.execute(sa.text(
        "DELETE FROM documents WHERE collection IN ('jobs', 'profiles', 'matches', 'applications')"
    ))


def downgrade() -> None:
    bind = op.get_bind()
    now = sa.text("now()")

    def _insert_document(collection, doc_id, user_id, data, created_at, updated_at):
        bind.execute(sa.text("""
            INSERT INTO documents (collection, id, user_id, data, created_at, updated_at)
            VALUES (:collection, :id, :user_id, :data::jsonb, :created_at, :updated_at)
            ON CONFLICT (collection, id) DO NOTHING
        """), {
            "collection": collection, "id": doc_id, "user_id": str(user_id) if user_id else None,
            "data": json.dumps(data), "created_at": created_at, "updated_at": updated_at,
        })

    for row in bind.execute(sa.text("SELECT * FROM profiles")).mappings().all():
        data = dict(row["attrs"] or {})
        data.update({
            "name": row["name"], "email": row["email"], "phone": row["phone"],
            "location": row["location"], "title": row["title"],
            "experience_level": row["experience_level"], "education": row["education"],
            "career_goals": row["career_goals"], "cv_filename": row["cv_filename"],
            "cv_file_id": row["cv_file_id"], "cv_hash": row["cv_hash"],
            "has_cv": row["has_cv"], "isActive": row["is_active"],
            "notification_enabled": row["notification_enabled"],
            "notification_threshold": row["notification_threshold"],
            "user_id": str(row["user_id"]) if row["user_id"] else None,
        })
        _insert_document("profiles", row["id"], row["user_id"], data, row["created_at"], row["updated_at"])

    for row in bind.execute(sa.text("SELECT * FROM jobs")).mappings().all():
        data = dict(row["attrs"] or {})
        data.update({
            "title": row["title"], "company": row["company"], "status": row["status"],
            "progress": row["progress"], "phase": row["phase"], "template_type": row["template_type"],
            "error": row["error"], "user_id": str(row["user_id"]) if row["user_id"] else None,
        })
        _insert_document("jobs", row["id"], row["user_id"], data, row["created_at"], row["updated_at"])

    for row in bind.execute(sa.text("SELECT * FROM applications")).mappings().all():
        data = dict(row["attrs"] or {})
        data.update({
            "company": row["company"], "role": row["role"], "job_url": row["job_url"],
            "location": row["location"], "status": row["status"], "match_score": row["match_score"],
            "ats_score": row["ats_score"], "cv_storage_id": row["cv_storage_id"],
            "cover_letter_storage_id": row["cover_letter_storage_id"],
            "job_description": row["job_description"], "views": row["views"],
            "date_created": row["date_created"], "date_updated": row["date_updated"],
            "user_id": str(row["user_id"]),
        })
        _insert_document("applications", row["id"], row["user_id"], data, row["created_at"], row["updated_at"])

    for user_id, in bind.execute(sa.text("SELECT DISTINCT user_id FROM matches")).all():
        rows = bind.execute(
            sa.text("SELECT * FROM matches WHERE user_id = :u ORDER BY match_score DESC"), {"u": user_id}
        ).mappings().all()
        matches_list = [{
            "job": {
                "id": r["job_hash"], "title": r["title"], "company": r["company"],
                "location": r["location"], "description": r["description"], "url": r["url"],
            },
            "match_score": r["match_score"],
            "match_reasons": r["match_reasons"] or [],
            "score_breakdown": r["score_breakdown"] or {},
            "semantic_score": r["semantic_score"],
        } for r in rows]
        last_seen = next((r["last_seen"] for r in rows if r["last_seen"]), None)
        data = {
            "user_id": str(user_id), "userId": str(user_id),
            "location": rows[0]["location"] if rows else "",
            "matches": json.dumps(matches_list),
            "last_seen": last_seen.isoformat() if last_seen else None,
        }
        _insert_document(
            "matches", f"match_{user_id}", user_id, data,
            rows[0]["created_at"] if rows else None, rows[0]["updated_at"] if rows else None,
        )

    op.drop_table("applications")
    op.drop_table("matches")
    op.drop_table("jobs")
    op.drop_table("profiles")
