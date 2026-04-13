from __future__ import annotations

from collections import Counter


def build_social_graph(profiles: list[dict]) -> dict:
    nodes = []
    edges = []
    clusters = []

    node_index = {}

    def add_node(node_type: str, key: str, payload: dict):
        identity = f"{node_type}:{key}"
        if identity in node_index:
            return node_index[identity]
        node_id = len(nodes) + 1
        node = {"id": node_id, "type": node_type, "key": key, **payload}
        nodes.append(node)
        node_index[identity] = node_id
        return node_id

    link_to_profiles = {}
    username_to_profiles = {}

    for profile in profiles or []:
        username = str(profile.get("username") or "").lower()
        platform = str(profile.get("platform") or "unknown").lower()
        profile_key = f"{platform}:{username}"
        profile_node = add_node("profile", profile_key, {"platform": platform, "username": username})

        person_node = add_node("person", username or profile_key, {"label": profile.get("display_name") or username})
        edges.append({"source": person_node, "target": profile_node, "type": "same_username", "confidence": 0.9})

        username_to_profiles.setdefault(username, []).append(profile_node)

        for link in profile.get("links") or []:
            url = link.get("url") if isinstance(link, dict) else str(link)
            if not url:
                continue
            link_node = add_node("link", url, {"url": url})
            edges.append({"source": profile_node, "target": link_node, "type": "shared_link", "confidence": 0.75})
            link_to_profiles.setdefault(url, []).append(profile_node)

        avatar_hash = profile.get("avatar_hash")
        if avatar_hash:
            image_node = add_node("image_hash", avatar_hash, {"hash": avatar_hash})
            edges.append({"source": profile_node, "target": image_node, "type": "shared_avatar", "confidence": 0.88})

    for nodes_for_username in username_to_profiles.values():
        if len(nodes_for_username) < 2:
            continue
        for idx, src in enumerate(nodes_for_username):
            for dst in nodes_for_username[idx + 1 :]:
                edges.append({"source": src, "target": dst, "type": "same_username", "confidence": 0.86})

    for url, linked_profiles in link_to_profiles.items():
        if len(linked_profiles) < 2:
            continue
        clusters.append({"reason": "shared_link", "value": url, "node_ids": linked_profiles})

    edge_counter = Counter(edge["type"] for edge in edges)
    confidence_summary = {
        "edge_counts": dict(edge_counter),
        "cluster_count": len(clusters),
        "node_count": len(nodes),
    }

    return {
        "nodes": nodes,
        "edges": edges,
        "clusters": clusters,
        "confidence_summary": confidence_summary,
    }
