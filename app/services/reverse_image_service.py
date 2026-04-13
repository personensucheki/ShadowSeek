from __future__ import annotations

import hashlib
from datetime import datetime
from io import BytesIO

import imagehash
from PIL import Image

from app.extensions.main import db
from app.models.osint_engine import ImageHash
from .upload_security import validate_image_upload


def analyze_reverse_image(file_obj, *, max_size_bytes: int = 5 * 1024 * 1024, similarity_threshold: int = 10):
    _, raw = validate_image_upload(file_obj, max_size_bytes=max_size_bytes)
    with Image.open(BytesIO(raw)) as image:
        phash = str(imagehash.phash(image))
        dhash = str(imagehash.dhash(image))

    possible_matches = []
    stored_hashes = ImageHash.query.filter(ImageHash.hash_type.in_(["phash", "dhash"]))\
        .order_by(ImageHash.created_at.desc())\
        .limit(3000)\
        .all()

    for row in stored_hashes:
        probe = phash if row.hash_type == "phash" else dhash
        try:
            distance = imagehash.hex_to_hash(probe) - imagehash.hex_to_hash(row.hash_value)
        except Exception:
            continue
        if distance <= similarity_threshold:
            similarity = max(0.0, 1.0 - (distance / max(1, similarity_threshold)))
            possible_matches.append(
                {
                    "similarity": round(similarity, 3),
                    "distance": int(distance),
                    "source_profile": row.source_profile,
                    "source_platform": row.source_platform,
                    "hash_type": row.hash_type,
                }
            )

    possible_matches.sort(key=lambda item: item["similarity"], reverse=True)
    return {
        "possible_matches": possible_matches[:50],
        "hashes": {"phash": phash, "dhash": dhash},
    }


def persist_image_hashes(*, source_platform: str, source_profile: str, phash: str, dhash: str):
    now = datetime.utcnow()
    rows = [
        ImageHash(source_platform=source_platform, source_profile=source_profile, hash_type="phash", hash_value=phash, created_at=now),
        ImageHash(source_platform=source_platform, source_profile=source_profile, hash_type="dhash", hash_value=dhash, created_at=now),
    ]
    db.session.add_all(rows)
    db.session.commit()
    return rows


def stable_image_fingerprint(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()
