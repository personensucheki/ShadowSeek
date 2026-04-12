"""
Feed-Service: Verwaltung und Auslieferung von Feed-Posts
Unterstützt Discovery, Following, Local
"""


from datetime import datetime

class FeedService:
    def get_feed(self, user_id, feed_type="discovery", location=None, dev_fallback=False):
        """Holt Feed-Posts nach Feed-Typ (discovery|following|local)"""
        from app.models.media_post import MediaPost
        from app.models import User
        from app.services.media import resolve_user_avatar_url
        from flask import url_for

        # Nur wirklich feedfähige, veröffentlichte, öffentliche Posts
        query = MediaPost.query.filter(
            MediaPost.is_public.is_(True),
            MediaPost.media_type.in_(["video", "photo"]),
            MediaPost.file_path != None,
        ).order_by(MediaPost.created_at.desc())
        posts = query.limit(20).all()
        user_ids = {post.user_id for post in posts}
        users = {user.id: user for user in User.query.filter(User.id.in_(user_ids)).all()} if user_ids else {}

        items = []
        for post in posts:
            user = users.get(post.user_id)
            items.append({
                **post.to_dict(),
                "username": user.username if user else "user",
                "display_name": (user.display_name or user.username) if user else "User",
                "avatar_url": resolve_user_avatar_url(user) if user else url_for("static", filename="images/default-avatar.png"),
                "media_url": url_for("profile.uploaded_file", filename=post.file_path),
                "profile_url": url_for("feed.public_profile", username=user.username) if user else None,
            })

        # Fallback: Demo-Seed nur, wenn keine echten Posts oder Dev-Fallback
        if (not items or dev_fallback):
            items = get_demo_seed_posts()
        return items


def get_demo_seed_posts():
    # Themen: Deep Search, Cyberpunk, Dark OSINT, Analyse/Tracking
    demo_posts = [
        {
            "id": 10001,
            "username": "deepsearch_ai",
            "display_name": "DeepSearch AI",
            "caption": "Realtime Investigation: Dark Web Monitoring & Threat Analysis.",
            "hashtags": "#deepsearch #osint #cyberpunk",
            "media_url": "/static/demo/demo1.mp4",
            "media_type": "video",
            "likes": 420,
            "views": 9001,
            "comments": 12,
            "location": "Darknet",
            "created_at": datetime(2026, 4, 1, 12, 0, 0).isoformat(),
            "category": "Investigation",
        },
        {
            "id": 10002,
            "username": "cyberpunk_ops",
            "display_name": "Cyberpunk Ops",
            "caption": "Tracking digital footprints in the neon city.",
            "hashtags": "#cyberpunk #osint #tracking",
            "media_url": "/static/demo/demo2.mp4",
            "media_type": "video",
            "likes": 1337,
            "views": 2048,
            "comments": 7,
            "location": "Neo-Tokyo",
            "created_at": datetime(2026, 4, 2, 18, 30, 0).isoformat(),
            "category": "Tracking",
        },
        {
            "id": 10003,
            "username": "osint_dark",
            "display_name": "OSINT Dark",
            "caption": "Analyse von anonymen Datenströmen. #analysis #osint",
            "hashtags": "#analysis #osint #darkweb",
            "media_url": "/static/demo/demo3.mp4",
            "media_type": "video",
            "likes": 256,
            "views": 512,
            "comments": 2,
            "location": "Matrix",
            "created_at": datetime(2026, 4, 3, 9, 15, 0).isoformat(),
            "category": "Analysis",
        },
        {
            "id": 10004,
            "username": "investigator_x",
            "display_name": "Investigator X",
            "caption": "Live Tracking: Social Graphs & Threat Actors.",
            "hashtags": "#investigation #osint #live",
            "media_url": "/static/demo/demo4.mp4",
            "media_type": "video",
            "likes": 99,
            "views": 333,
            "comments": 1,
            "location": "Cyberspace",
            "created_at": datetime(2026, 4, 4, 21, 0, 0).isoformat(),
            "category": "Live",
        },
    ]
    for post in demo_posts:
        post.setdefault("avatar_url", "/static/images/default-avatar.png")
    return demo_posts

feed_service = FeedService()
