from typing import List, Dict, Any

class RankingService:
    @staticmethod
    def score_result(result: Dict[str, Any], query_variants: List[str], selected_platforms: List[str]) -> Dict[str, Any]:
        score = 0.0
        match_reasons = []
        quality_flags = []
        username = result.get('username', '').lower()
        platform = result.get('platform', '').lower()
        evidence_count = result.get('evidence_count', 1)
        confidence_hint = result.get('raw_confidence_hint', 0.0)
        # 1. Exact username match
        if username in [v.lower() for v in query_variants]:
            score += 2.0
            match_reasons.append('exact username match')
        # 2. Normalized/variant match
        elif any(username in v.lower() or v.lower() in username for v in query_variants):
            score += 1.0
            match_reasons.append('variant/normalized match')
        # 3. Plattform gewählt
        if platform in [p.lower() for p in selected_platforms]:
            score += 0.7
            match_reasons.append('selected platform match')
        # 4. Evidence count
        if evidence_count > 1:
            score += min(0.5, 0.1 * (evidence_count-1))
            match_reasons.append('corroborated by multiple sources')
        # 5. Confidence hint
        score += min(1.0, confidence_hint)
        # 6. Profile URL vorhanden
        if result.get('profile_url'):
            score += 0.3
            match_reasons.append('direct profile endpoint reachable')
        # 7. Snippet/Titel-Plausibilität
        if result.get('title') and result.get('snippet'):
            score += 0.2
        # 8. Quality flags
        if evidence_count > 2:
            quality_flags.append('strong evidence')
        if confidence_hint < 0.3:
            quality_flags.append('weak confidence')
        # Confidence Level
        if score >= 2.5:
            confidence = 'high'
        elif score >= 1.5:
            confidence = 'medium'
        else:
            confidence = 'low'
        return {
            **result,
            'score': round(score, 3),
            'confidence': confidence,
            'match_reasons': match_reasons,
            'quality_flags': quality_flags
        }

    @staticmethod
    def rank_results(results: List[Dict[str, Any]], query_variants: List[str], selected_platforms: List[str]) -> List[Dict[str, Any]]:
        scored = [RankingService.score_result(r, query_variants, selected_platforms) for r in results]
        return sorted(scored, key=lambda x: x['score'], reverse=True)

# Beispiel-Nutzung:
# ranked = RankingService.rank_results(deduped_results, [v['value'] for v in variants], ['github', 'twitter'])
# print(ranked)
