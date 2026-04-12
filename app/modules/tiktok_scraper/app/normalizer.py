from datetime import datetime

def normalize(data):
    return {
        "video_id": data.get("video_id"),
        "author_username": data.get("author_username"),
        "description": data.get("description"),
        "views": to_int(data.get("views")),
        "likes": to_int(data.get("likes")),
        "comments_count": to_int(data.get("comments_count")),
        "shares": to_int(data.get("shares")),
        "scraped_at": datetime.utcnow().isoformat()
    }

def to_int(value):
    try:
        return int(value)
    except:
        return None
