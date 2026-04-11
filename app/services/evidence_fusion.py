from typing import List, Dict, Any
import hashlib

def cluster_key(result: Dict[str, Any]) -> str:
    # Cluster nach (plattform, normalized_username, ggf. profile_url)
    base = f"{result.get('platform','')}|{result.get('username','').lower()}"
    if result.get('profile_url'):
        base += f"|{result['profile_url'].lower()}"
    return hashlib.md5(base.encode('utf-8')).hexdigest()

class EvidenceFusion:
    @staticmethod
    def deduplicate(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        clusters = {}
        for res in results:
            key = cluster_key(res)
            if key not in clusters:
                clusters[key] = {
                    'dedup_cluster_id': key,
                    'evidence_count': 0,
                    'sources': set(),
                    'providers': set(),
                    'evidence_signals': set(),
                    'raw_confidence_hints': [],
                    'results': [],
                    # Felder für Ausgabe
                    'platform': res.get('platform'),
                    'username': res.get('username'),
                    'profile_url': res.get('profile_url'),
                    'title': res.get('title'),
                    'snippet': res.get('snippet'),
                }
            clusters[key]['evidence_count'] += 1
            clusters[key]['sources'].add(res.get('source'))
            clusters[key]['providers'].add(res.get('provider'))
            clusters[key]['evidence_signals'].update(res.get('evidence_signals', []))
            clusters[key]['raw_confidence_hints'].append(res.get('raw_confidence_hint', 0.0))
            clusters[key]['results'].append(res)
        # Aggregation
        fused = []
        for c in clusters.values():
            agg_conf = sum(c['raw_confidence_hints']) / max(1, len(c['raw_confidence_hints']))
            fused.append({
                'dedup_cluster_id': c['dedup_cluster_id'],
                'evidence_count': c['evidence_count'],
                'platform': c['platform'],
                'username': c['username'],
                'profile_url': c['profile_url'],
                'title': c['title'],
                'snippet': c['snippet'],
                'sources': list(c['sources']),
                'providers': list(c['providers']),
                'evidence_signals': list(c['evidence_signals']),
                'raw_confidence_hint': agg_conf,
                'results': c['results'],
            })
        return fused

# Beispiel-Nutzung:
# fusion = EvidenceFusion()
# deduped = fusion.deduplicate(provider_results)
# print(deduped)
