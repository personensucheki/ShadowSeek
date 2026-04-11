import re
import unicodedata
from typing import List, Dict, Any, Optional

class QueryVariant:
    def __init__(self, value: str, strength: str, origin: str, vtype: str, priority: int, reason: str):
        self.value = value
        self.strength = strength  # 'strong', 'medium', 'weak'
        self.origin = origin      # e.g. 'input', 'normalized', 'alias', ...
        self.vtype = vtype        # e.g. 'exact', 'normalized', 'alias', ...
        self.priority = priority
        self.reason = reason

    def as_dict(self):
        return {
            'value': self.value,
            'strength': self.strength,
            'origin': self.origin,
            'type': self.vtype,
            'priority': self.priority,
            'reason': self.reason
        }

class QueryNormalizer:
    @staticmethod
    def normalize(text: str) -> str:
        # Unicode-Normalisierung, Trimmen, Lowercase
        text = unicodedata.normalize('NFKC', text)
        text = text.strip().lower()
        return text

    @staticmethod
    def clean(text: str) -> str:
        # Entferne Sonderzeichen außer _ . -
        return re.sub(r'[^\w\d_.-]', '', text)

    @staticmethod
    def tokenize(text: str) -> List[str]:
        # Split on common separators
        return re.split(r'[\s_.-]+', text)

    def generate_variants(self, username: str, real_name: Optional[str]=None, clan: Optional[str]=None, year: Optional[str]=None) -> List[QueryVariant]:
        variants = []
        base = username.strip()
        norm = self.normalize(base)
        clean = self.clean(norm)
        tokens = self.tokenize(norm)
        # 1. Original
        variants.append(QueryVariant(base, 'strong', 'input', 'exact', 1, 'Original input'))
        # 2. Normalized
        if norm != base:
            variants.append(QueryVariant(norm, 'strong', 'normalized', 'normalized', 2, 'Unicode-normalized, lowercased'))
        # 3. Cleaned
        if clean != norm:
            variants.append(QueryVariant(clean, 'medium', 'cleaned', 'normalized', 3, 'Sonderzeichen entfernt'))
        # 4. Token-Join-Varianten
        if len(tokens) > 1:
            for sep in ['_', '.', '-']:
                joined = sep.join(tokens)
                variants.append(QueryVariant(joined, 'medium', 'token_join', f'joined_{sep}', 4, f'Tokens mit {sep} verbunden'))
        # 5. Name+Username
        if real_name:
            rn = self.normalize(real_name)
            variants.append(QueryVariant(f"{rn}{clean}", 'weak', 'contextual', 'name_username', 5, 'Realname+Username'))
        # 6. Clan+Username
        if clan:
            cn = self.normalize(clan)
            variants.append(QueryVariant(f"{cn}{clean}", 'weak', 'contextual', 'clan_username', 6, 'Clan+Username'))
        # 7. Username+Jahr
        if year and year.isdigit():
            variants.append(QueryVariant(f"{clean}{year}", 'weak', 'contextual', 'username_year', 7, 'Username+Jahr'))
        # 8. Kürzungen
        if len(clean) > 4:
            variants.append(QueryVariant(clean[:4], 'weak', 'short', 'short', 8, 'Kürzung auf 4 Zeichen'))
        # 9. Alias-Variante (z.B. nur erster Token)
        if len(tokens) > 1:
            variants.append(QueryVariant(tokens[0], 'weak', 'alias', 'alias', 9, 'Erster Token als Alias'))
        # Dubletten filtern
        seen = set()
        filtered = []
        for v in variants:
            if v.value not in seen and len(v.value) > 1:
                filtered.append(v)
                seen.add(v.value)
        # Priorisieren (max. 10 Varianten)
        filtered = sorted(filtered, key=lambda v: v.priority)[:10]
        return filtered
