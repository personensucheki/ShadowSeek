import re

def load_urls(file_path):
    if not file_path:
        return []
    with open(file_path, "r") as f:
        return [line.strip() for line in f if line.strip()]

def classify_url(url):
    if "tiktok.com" not in url:
        return "unsupported"
    if re.search(r"/video/\d+", url):
        return "video"
    if re.search(r"tiktok.com/@", url):
        return "profile"
    return "unsupported"
