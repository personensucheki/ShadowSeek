from __future__ import annotations

from collections import Counter


def analyze_content_patterns(payload: dict) -> dict:
    posts = payload.get("posts") or []
    hashtags = []
    captions = []
    bio_patterns = []
    image_hashes = []

    for post in posts:
        if not isinstance(post, dict):
            continue
        hashtags.extend([str(tag).lower() for tag in (post.get("hashtags") or []) if str(tag).strip()])
        caption = str(post.get("caption") or "").strip().lower()
        if caption:
            captions.append(" ".join(caption.split()[:6]))
        if post.get("image_hash"):
            image_hashes.append(str(post.get("image_hash")))

    profiles = payload.get("profiles") or []
    for profile in profiles:
        if not isinstance(profile, dict):
            continue
        bio = str(profile.get("bio") or "").strip().lower()
        if bio:
            bio_patterns.append(" ".join(bio.split()[:8]))

    repeated_hashtags = [{"tag": k, "count": v} for k, v in Counter(hashtags).items() if v > 2]
    repeated_caption_structures = [{"pattern": k, "count": v} for k, v in Counter(captions).items() if v > 2]
    repeated_bio_patterns = [{"pattern": k, "count": v} for k, v in Counter(bio_patterns).items() if v > 1]
    repeated_image_hashes = [{"hash": k, "count": v} for k, v in Counter(image_hashes).items() if v > 1]

    spam_cluster_detected = bool(repeated_hashtags or repeated_caption_structures or repeated_bio_patterns)

    return {
        "repeated_hashtags": repeated_hashtags,
        "repeated_caption_structures": repeated_caption_structures,
        "similar_image_hashes": repeated_image_hashes,
        "repeated_bio_patterns": repeated_bio_patterns,
        "spam_cluster_detected": spam_cluster_detected,
        "template_reuse_detected": bool(repeated_caption_structures or repeated_bio_patterns),
        "multi_account_pattern_detected": bool(repeated_image_hashes or repeated_bio_patterns),
    }
