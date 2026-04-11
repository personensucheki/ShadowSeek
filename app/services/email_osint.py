def analyze_email(email):
    value = str(email or "").strip().lower()
    if "@" not in value:
        return {"email": None, "domain": None, "local_part": None}

    local_part, domain = value.split("@", 1)
    if not local_part or not domain:
        return {"email": None, "domain": None, "local_part": None}

    return {
        "email": value,
        "domain": domain,
        "local_part": local_part,
    }
