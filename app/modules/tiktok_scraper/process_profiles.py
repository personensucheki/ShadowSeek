import csv
import os
import re
from collections import Counter

INPUT_FILES = [
    "TikTok - Profiles.csv",
    "profiles_detailed.csv",
    "profiles.csv",
]

OUTPUT_FILE = "scored_profiles.csv"
TOP_LEADS_FILE = "top_leads.csv"
OUTREACH_FILE = "outreach_leads.csv"
MIN_FOLLOWERS = 500
TARGET_LANGUAGE = "de"

CATEGORY_KEYWORDS = {
    "beauty": [
        "beauty",
        "makeup",
        "skincare",
        "kosmetik",
        "lashes",
        "brows",
        "hair",
        "nails",
    ],
    "fitness": [
        "fitness",
        "gym",
        "workout",
        "personal trainer",
        "nutrition",
        "health",
    ],
    "coach": [
        "coach",
        "coaching",
        "mentor",
        "beratung",
        "consulting",
        "trainer",
    ],
    "business": [
        "business",
        "agentur",
        "agency",
        "entrepreneur",
        "founder",
        "ceo",
        "brand",
        "shop",
        "service",
    ],
    "podcast": [
        "podcast",
        "host",
        "show",
    ],
    "talk": [
        "talk",
        "interview",
        "speaker",
        "speaking",
    ],
    "creator": [
        "creator",
        "content creator",
        "ugc",
        "influencer",
    ],
    "booking": [
        "booking",
        "book",
        "kontakt",
        "contact",
        "email",
        "e-mail",
        "dm",
        "collab",
        "collaboration",
        "management",
    ],
    "live": [
        "live",
        "stream",
        "streamer",
    ],
}

CATEGORY_PRIORITY = [
    "beauty",
    "fitness",
    "coach",
    "business",
    "podcast",
    "talk",
    "creator",
    "booking",
    "live",
]

BUSINESS_SIGNAL_KEYWORDS = {
    "coach",
    "coaching",
    "mentor",
    "business",
    "agentur",
    "agency",
    "entrepreneur",
    "founder",
    "ceo",
    "brand",
    "service",
    "booking",
    "kontakt",
    "contact",
    "email",
    "e-mail",
    "dm",
    "collab",
    "collaboration",
    "management",
    "book",
}

FIELDNAMES = [
    "profile_url",
    "username",
    "bio",
    "followers",
    "likes",
    "videos",
    "bio_link",
    "email",
    "category",
    "reach_score",
    "business_score",
    "contact_score",
    "monet_score",
    "total_score",
    "priority_tier",
    "is_private",
    "predicted_lang",
]

OUTREACH_FIELDNAMES = [
    "profile_url",
    "username",
    "bio",
    "followers",
    "likes",
    "videos",
    "email",
    "bio_link",
    "category",
    "total_score",
    "priority_tier",
    "contact_channel",
    "contact_value",
    "outreach_status",
    "notes",
]


def parse_int(value):
    if value in (None, ""):
        return 0

    cleaned = re.sub(r"[^\d]", "", str(value))
    return int(cleaned) if cleaned else 0


def parse_bool(value):
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def normalize_text(*parts):
    return " ".join(str(part).strip().lower() for part in parts if part)


def extract_email(text):
    if not text:
        return ""

    match = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
    return match.group(0) if match else ""


def keyword_in_text(text, keyword):
    pattern = r"(?<!\w)" + re.escape(keyword.lower()) + r"(?!\w)"
    return re.search(pattern, text) is not None


def collect_keyword_hits(text):
    hits = {}
    for category, keywords in CATEGORY_KEYWORDS.items():
        matched = [keyword for keyword in keywords if keyword_in_text(text, keyword)]
        if matched:
            hits[category] = matched
    return hits


def guess_category(keyword_hits):
    if not keyword_hits:
        return "general"

    for category in CATEGORY_PRIORITY:
        if category in keyword_hits:
            return category

    return "general"


def has_business_keywords(text):
    return any(keyword_in_text(text, keyword) for keyword in BUSINESS_SIGNAL_KEYWORDS)


def score_reach(followers, likes, videos):
    score = 0

    if followers >= 100000:
        score += 7
    elif followers >= 50000:
        score += 6
    elif followers >= 20000:
        score += 5
    elif followers >= 10000:
        score += 4
    elif followers >= 5000:
        score += 3
    elif followers >= 1000:
        score += 2
    elif followers > 0:
        score += 1

    if likes >= 250000:
        score += 3
    elif likes >= 75000:
        score += 2
    elif likes >= 10000:
        score += 1

    if videos >= 200:
        score += 2
    elif videos >= 50:
        score += 1

    return score


def score_business(text, category, keyword_hits, bio_link, email):
    score = 0

    if category in {"coach", "business"}:
        score += 5
    elif category in {"podcast", "talk"}:
        score += 3
    elif category == "creator":
        score += 2

    if "coach" in keyword_hits:
        score += 2
    if "business" in keyword_hits:
        score += 2
    if "podcast" in keyword_hits or "talk" in keyword_hits:
        score += 2
    if "creator" in keyword_hits:
        score += 1
    if "booking" in keyword_hits:
        score += 3
    if has_business_keywords(text):
        score += 2
    if bio_link:
        score += 2
    if email:
        score += 3

    return min(score, 14)


def score_contact(text, category, email, bio_link):
    score = 0

    if email:
        score += 5
    if bio_link:
        score += 3
    if any(keyword_in_text(text, keyword) for keyword in CATEGORY_KEYWORDS["booking"]):
        score += 2
    if category == "booking":
        score += 2

    return min(score, 10)


def score_monetization(category, keyword_hits, bio_link):
    score = 0

    if category in {"beauty", "fitness"}:
        score += 5
    elif category in {"coach", "business"}:
        score += 4
    elif category in {"podcast", "talk", "creator"}:
        score += 3
    elif category == "booking":
        score += 2

    if "beauty" in keyword_hits and "fitness" in keyword_hits:
        score += 1
    if "coach" in keyword_hits and "business" in keyword_hits:
        score += 1
    if bio_link:
        score += 2

    return min(score, 8)


def get_tier(total_score):
    if total_score >= 16:
        return "A"
    if total_score >= 11:
        return "B"
    if total_score >= 7:
        return "C"
    return "D"


def passes_tier_a_gate(email, bio_link, followers):
    return bool(email or bio_link or followers >= 2000)


def apply_tier_gate(total_score, email, bio_link, followers):
    tier = get_tier(total_score)
    if tier == "A" and not passes_tier_a_gate(email, bio_link, followers):
        return "B"
    return tier


def find_input_file():
    for filename in INPUT_FILES:
        if os.path.exists(filename):
            return filename
    return None


def load_rows(input_file):
    for encoding in ("utf-8", "utf-8-sig", "cp1252"):
        try:
            with open(input_file, encoding=encoding, newline="") as handle:
                return list(csv.DictReader(handle))
        except UnicodeDecodeError:
            continue

    with open(input_file, encoding="utf-8", errors="ignore", newline="") as handle:
        return list(csv.DictReader(handle))


def get_field(row, *names, default=""):
    for name in names:
        value = row.get(name)
        if value not in (None, ""):
            return value
    return default


def write_csv(path, rows, fieldnames):
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def build_result_row(row):
    bio = get_field(row, "biography", "signature", "bio")
    bio_link = get_field(row, "bio_link", "external_link", "website", "site")
    url = get_field(row, "url", "profile_url")
    username = get_field(row, "nickname", "username", "display_name")
    lang = get_field(row, "predicted_lang", "lang")

    followers = parse_int(get_field(row, "followers", "follower_count"))
    likes = parse_int(get_field(row, "likes", "heart_count", "hearts"))
    videos = parse_int(get_field(row, "videos_count", "video_count", "videos"))
    is_private = parse_bool(get_field(row, "is_private", "private", default="false"))

    if is_private:
        return None

    if followers < MIN_FOLLOWERS:
        return None

    if lang and lang.lower() != TARGET_LANGUAGE:
        return None

    combined_text = normalize_text(bio, username)
    keyword_hits = collect_keyword_hits(combined_text)
    category = guess_category(keyword_hits)
    email = extract_email(bio)

    reach_score = score_reach(followers, likes, videos)
    business_score = score_business(combined_text, category, keyword_hits, bio_link, email)
    contact_score = score_contact(combined_text, category, email, bio_link)
    monet_score = score_monetization(category, keyword_hits, bio_link)
    total_score = reach_score + business_score + contact_score + monet_score
    priority_tier = apply_tier_gate(total_score, email, bio_link, followers)

    return {
        "profile_url": url,
        "username": username,
        "bio": bio,
        "followers": followers,
        "likes": likes,
        "videos": videos,
        "bio_link": bio_link,
        "email": email,
        "category": category,
        "reach_score": reach_score,
        "business_score": business_score,
        "contact_score": contact_score,
        "monet_score": monet_score,
        "total_score": total_score,
        "priority_tier": priority_tier,
        "is_private": str(is_private).lower(),
        "predicted_lang": lang,
    }


def build_outreach_row(row):
    if row["email"]:
        contact_channel = "email"
        contact_value = row["email"]
    elif row["bio_link"]:
        contact_channel = "website"
        contact_value = row["bio_link"]
    else:
        contact_channel = "manual_review"
        contact_value = ""

    return {
        "profile_url": row["profile_url"],
        "username": row["username"],
        "bio": row["bio"],
        "followers": row["followers"],
        "likes": row["likes"],
        "videos": row["videos"],
        "email": row["email"],
        "bio_link": row["bio_link"],
        "category": row["category"],
        "total_score": row["total_score"],
        "priority_tier": row["priority_tier"],
        "contact_channel": contact_channel,
        "contact_value": contact_value,
        "outreach_status": "new",
        "notes": "",
    }


def main():
    input_file = find_input_file()
    if not input_file:
        print("Keine Input-Datei gefunden.")
        return

    rows = load_rows(input_file)
    results = []
    seen_profiles = set()

    for row in rows:
        result = build_result_row(row)
        if not result:
            continue

        dedupe_key = (result["profile_url"] or result["username"]).strip().lower()
        if dedupe_key and dedupe_key in seen_profiles:
            continue

        if dedupe_key:
            seen_profiles.add(dedupe_key)

        results.append(result)

    if not results:
        print("Keine passenden Datensaetze gefunden.")
        return

    results.sort(
        key=lambda item: (
            item["total_score"],
            item["business_score"],
            item["contact_score"],
            item["reach_score"],
            item["followers"],
            item["likes"],
        ),
        reverse=True,
    )

    top_leads = [row for row in results if row["priority_tier"] in {"A", "B"}]
    outreach_leads = [build_outreach_row(row) for row in top_leads]
    tier_counts = Counter(row["priority_tier"] for row in results)

    write_csv(OUTPUT_FILE, results, FIELDNAMES)
    write_csv(TOP_LEADS_FILE, top_leads, FIELDNAMES)
    write_csv(OUTREACH_FILE, outreach_leads, OUTREACH_FIELDNAMES)

    print(f"Verwendete Input-Datei: {input_file}")
    print(f"Geladene Zeilen: {len(rows)}")
    print(f"Exportierte Leads: {len(results)}")
    print("Tier-Verteilung:")
    for tier in ("A", "B", "C", "D"):
        print(f"  Tier {tier}: {tier_counts.get(tier, 0)}")
    print(f"Anzahl Top-Leads: {len(top_leads)}")
    print(f"Anzahl Outreach-Leads: {len(outreach_leads)}")
    print(f"Erzeugte Exporte: {OUTPUT_FILE}, {TOP_LEADS_FILE}, {OUTREACH_FILE}")


if __name__ == "__main__":
    main()
