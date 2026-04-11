from urllib.parse import urlparse

from .email_osint import analyze_email


def _normalize_domain_from_url(value):
    raw = str(value or "").strip().lower()
    if not raw:
        return None

    parsed = urlparse(raw if "://" in raw else f"https://{raw}")
    hostname = parsed.hostname
    return hostname.lower() if hostname else None


def _split_domain(domain):
    if not domain:
        return {"domain": None, "root_domain": None, "tld": None}

    parts = domain.split(".")
    root_domain = ".".join(parts[-2:]) if len(parts) >= 2 else domain
    tld = parts[-1] if len(parts) >= 2 else None
    return {
        "domain": domain,
        "root_domain": root_domain,
        "tld": tld,
    }


def analyze_domain_osint(website=None, email=None):
    website_domain = _normalize_domain_from_url(website)
    email_info = analyze_email(email)
    email_domain = email_info.get("domain")

    domains = []
    for domain in (website_domain, email_domain):
        if domain and domain not in domains:
            domains.append(domain)

    return {
        "domains": [_split_domain(domain) for domain in domains],
        "emails": [email_info] if email_info.get("email") else [],
    }
