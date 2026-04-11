import re


YEAR_PATTERN = re.compile(r"(19|20)\d{2}$")


def analyze_username_patterns(username):
    value = str(username or "").strip()
    lower_value = value.lower()
    tags = []

    if "_" in value:
        tags.append("underscore")
    if "-" in value:
        tags.append("hyphen")
    if "." in value:
        tags.append("dot")
    if any(char.isdigit() for char in value):
        tags.append("numeric")
    if value.islower():
        tags.append("lowercase")
    if value.isupper():
        tags.append("uppercase")
    if len(value) >= 12:
        tags.append("long")

    possible_year = None
    year_match = YEAR_PATTERN.search(value)
    if year_match:
        possible_year = int(year_match.group(0))

    if any(separator in value for separator in ("_", "-", ".")):
        style = "segmented"
    elif value.isalpha():
        style = "alphabetic"
    elif value.isalnum():
        style = "alphanumeric"
    else:
        style = "mixed"

    if possible_year:
        pattern_family = "alias_year"
    elif any(separator in value for separator in ("_", "-", ".")):
        pattern_family = "segmented_alias"
    elif lower_value.isalpha():
        pattern_family = "plain_alias"
    else:
        pattern_family = "mixed_alias"

    return {
        "style": style,
        "tags": tags,
        "possible_year": possible_year,
        "pattern_family": pattern_family,
    }
