import re
import unicodedata
from typing import List, Optional


class QueryVariant:
    def __init__(
        self,
        value: str,
        strength: str,
        origin: str,
        vtype: str,
        priority: int,
        reason: str,
    ):
        self.value = value
        self.strength = strength
        self.origin = origin
        self.vtype = vtype
        self.priority = priority
        self.reason = reason

    def as_dict(self):
        return {
            "value": self.value,
            "strength": self.strength,
            "origin": self.origin,
            "type": self.vtype,
            "priority": self.priority,
            "reason": self.reason,
        }


class QueryNormalizer:
    @staticmethod
    def normalize(text: str) -> str:
        text = unicodedata.normalize("NFKC", text)
        return text.strip().lower()

    @staticmethod
    def clean(text: str) -> str:
        return re.sub(r"[^\w\d_.-]", "", text)

    @staticmethod
    def compact(text: str) -> str:
        return re.sub(r"[._-]+", "", text)

    @staticmethod
    def tokenize(text: str) -> List[str]:
        return re.split(r"[\s_.-]+", text)

    def generate_variants(
        self,
        username: str,
        real_name: Optional[str] = None,
        clan: Optional[str] = None,
        year: Optional[str] = None,
    ) -> List[QueryVariant]:
        variants = []
        base = username.strip()
        norm = self.normalize(base)
        clean = self.clean(norm)
        compact = self.compact(clean)
        tokens = [token for token in self.tokenize(norm) if token]
        contextual_base = compact or clean

        variants.append(QueryVariant(base, "strong", "input", "exact", 1, "Original input"))

        if norm != base:
            variants.append(
                QueryVariant(
                    norm,
                    "strong",
                    "normalized",
                    "normalized",
                    2,
                    "Unicode-normalized, lowercased",
                )
            )

        if compact and compact != norm:
            variants.append(
                QueryVariant(compact, "strong", "compact", "compact", 3, "Trenner entfernt")
            )

        if clean != norm:
            variants.append(
                QueryVariant(
                    clean,
                    "medium",
                    "cleaned",
                    "normalized",
                    4,
                    "Sonderzeichen entfernt",
                )
            )

        if len(tokens) > 1:
            for sep in ("_", "-", "."):
                joined = sep.join(tokens)
                variants.append(
                    QueryVariant(
                        joined,
                        "medium",
                        "token_join",
                        f"joined_{sep}",
                        5,
                        f"Tokens mit {sep} verbunden",
                    )
                )

        if real_name:
            rn = self.normalize(real_name)
            variants.append(
                QueryVariant(
                    f"{rn}{contextual_base}",
                    "weak",
                    "contextual",
                    "name_username",
                    6,
                    "Realname+Username",
                )
            )

        if clan:
            cn = self.normalize(clan)
            variants.append(
                QueryVariant(
                    f"{cn}{contextual_base}",
                    "weak",
                    "contextual",
                    "clan_username",
                    7,
                    "Clan+Username",
                )
            )

        if year and year.isdigit():
            variants.append(
                QueryVariant(
                    f"{contextual_base}{year}",
                    "weak",
                    "contextual",
                    "username_year",
                    8,
                    "Username+Jahr",
                )
            )

        if len(contextual_base) > 4:
            variants.append(
                QueryVariant(
                    contextual_base[:4],
                    "weak",
                    "short",
                    "short",
                    9,
                    "Kuerzung auf 4 Zeichen",
                )
            )

        if len(tokens) > 1:
            variants.append(
                QueryVariant(tokens[0], "weak", "alias", "alias", 10, "Erster Token als Alias")
            )

        seen = set()
        filtered = []
        for variant in sorted(variants, key=lambda item: item.priority):
            if len(variant.value) <= 1 or variant.value in seen:
                continue
            filtered.append(variant)
            seen.add(variant.value)
            if len(filtered) >= 10:
                break

        return filtered
