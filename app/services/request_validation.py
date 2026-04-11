from __future__ import annotations

from datetime import datetime


class ValidationError(Exception):
    def __init__(self, errors: dict):
        self.errors = errors
        super().__init__("Validation failed")


def parse_date(date_raw: str, field: str) -> datetime:
    try:
        return datetime.strptime(date_raw, "%Y-%m-%d")
    except ValueError as exc:
        raise ValidationError({field: "Expected format YYYY-MM-DD."}) from exc


def parse_float(value_raw: str, field: str, minimum: float | None = None, maximum: float | None = None) -> float:
    try:
        value = float(value_raw)
    except (TypeError, ValueError) as exc:
        raise ValidationError({field: "Expected numeric value."}) from exc

    if minimum is not None and value < minimum:
        raise ValidationError({field: f"Must be >= {minimum}."})
    if maximum is not None and value > maximum:
        raise ValidationError({field: f"Must be <= {maximum}."})
    return value


def parse_pagination(args, default_limit: int = 50, max_limit: int = 200) -> tuple[int, int]:
    page_raw = args.get("page")
    offset_raw = args.get("offset")
    limit_raw = args.get("limit")

    limit = default_limit
    if limit_raw is not None:
        limit = int(parse_float(limit_raw, "limit", minimum=1, maximum=max_limit))

    if offset_raw is not None:
        offset = int(parse_float(offset_raw, "offset", minimum=0))
        return limit, offset

    page = 1
    if page_raw is not None:
        page = int(parse_float(page_raw, "page", minimum=1))

    return limit, (page - 1) * limit
