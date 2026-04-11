import unittest
from app.services.query_normalizer import QueryNormalizer
from app.services.provider_router import ProviderRouter, GithubProvider
from app.services.evidence_fusion import EvidenceFusion
from app.services.ranking_service import RankingService
from app.services.search_assistant import RuleBasedSearchAssistant

class TestQueryNormalizer(unittest.TestCase):
    def test_generate_variants(self):
        norm = QueryNormalizer()
        variants = norm.generate_variants('ShadowSeek.Exe', real_name='Florian', clan='Cyber', year='2024')
        values = [v.value for v in variants]
        self.assertIn('shadowseek.exe', values)
        self.assertIn('shadowseekexe', values)
        self.assertIn('cybershadowseekexe', values)
        self.assertLessEqual(len(variants), 10)

class TestProviderRouter(unittest.TestCase):
    def test_github_provider(self):
        router = ProviderRouter([GithubProvider()])
        results = router.search_all('shadowseek')
        self.assertTrue(any('github.com' in r['profile_url'] for r in results))

class TestEvidenceFusion(unittest.TestCase):
    def test_deduplication(self):
        results = [
            {'platform': 'GitHub', 'username': 'shadowseek', 'profile_url': 'https://github.com/shadowseek', 'provider': 'github', 'evidence_signals': ['profile_exists'], 'raw_confidence_hint': 0.8},
            {'platform': 'GitHub', 'username': 'shadowseek', 'profile_url': 'https://github.com/shadowseek', 'provider': 'github', 'evidence_signals': ['profile_exists'], 'raw_confidence_hint': 0.7},
        ]
        deduped = EvidenceFusion.deduplicate(results)
        self.assertEqual(len(deduped), 1)
        self.assertGreaterEqual(deduped[0]['evidence_count'], 2)

class TestRankingService(unittest.TestCase):
    def test_ranking(self):
        results = [
            {'platform': 'GitHub', 'username': 'shadowseek', 'profile_url': 'https://github.com/shadowseek', 'provider': 'github', 'evidence_signals': ['profile_exists'], 'raw_confidence_hint': 0.8, 'evidence_count': 2},
            {'platform': 'GitHub', 'username': 'shadowseek2', 'profile_url': 'https://github.com/shadowseek2', 'provider': 'github', 'evidence_signals': ['profile_exists'], 'raw_confidence_hint': 0.2, 'evidence_count': 1},
        ]
        ranked = RankingService.rank_results(results, ['shadowseek'], ['github'])
        self.assertGreater(ranked[0]['score'], ranked[1]['score'])
        self.assertIn(ranked[0]['confidence'], ['high', 'medium', 'low'])

class TestSearchAssistant(unittest.TestCase):
    def test_no_results(self):
        assistant = RuleBasedSearchAssistant({'results': []}, {'confidence_distribution': {'high': 0, 'medium': 0, 'low': 0}})
        resp = assistant.get_response()
        self.assertIn('Keine Treffer', resp)

if __name__ == '__main__':
    unittest.main()
