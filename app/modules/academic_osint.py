"""
academic_osint.py

Modul für die Suche nach wissenschaftlichen Publikationen zu Namen oder Alias.
APIs: Crossref, Semantic Scholar, ORCID, PubMed (optional)

Output:
{
    "papers": [],
    "authors": [],
    "institutions": [],
    "doi_links": []
}

Hinweis: Dieses Modul ist vorbereitet, aber noch nicht im Frontend aktiv.
"""

import requests
from typing import List, Dict, Any

class AcademicOSINT:
    def __init__(self):
        pass

    def search_crossref(self, query: str) -> List[Dict[str, Any]]:
        """Suche Publikationen über Crossref API."""
        url = f"https://api.crossref.org/works?query={query}&rows=10"
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            return data.get('message', {}).get('items', [])
        except Exception as e:
            return []

    def search_semantic_scholar(self, query: str) -> List[Dict[str, Any]]:
        """Suche Publikationen über Semantic Scholar API."""
        url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={query}&limit=10"
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            return data.get('data', [])
        except Exception as e:
            return []

    def search_orcid(self, query: str) -> List[Dict[str, Any]]:
        """Suche Autoren über ORCID API."""
        url = f"https://pub.orcid.org/v3.0/search/?q={query}"
        headers = {'Accept': 'application/json'}
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            return data.get('result', [])
        except Exception as e:
            return []

    def search_pubmed(self, query: str) -> List[Dict[str, Any]]:
        """Optional: Suche Publikationen über PubMed API."""
        url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term={query}&retmode=json&retmax=10"
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            ids = data.get('esearchresult', {}).get('idlist', [])
            return ids
        except Exception as e:
            return []

    def aggregate_results(self, query: str) -> Dict[str, List[Any]]:
        """Aggregiert Ergebnisse aus allen APIs im gewünschten Output-Format."""
        papers = []
        authors = []
        institutions = []
        doi_links = []

        # Crossref
        crossref_items = self.search_crossref(query)
        for item in crossref_items:
            papers.append(item.get('title', [''])[0])
            doi = item.get('DOI')
            if doi:
                doi_links.append(f"https://doi.org/{doi}")
            author_list = item.get('author', [])
            for author in author_list:
                authors.append(author.get('family', ''))
                if 'affiliation' in author and author['affiliation']:
                    institutions.extend([aff['name'] for aff in author['affiliation'] if 'name' in aff])

        # Semantic Scholar
        sem_items = self.search_semantic_scholar(query)
        for item in sem_items:
            papers.append(item.get('title', ''))
            if 'doi' in item and item['doi']:
                doi_links.append(f"https://doi.org/{item['doi']}")
            if 'authors' in item:
                authors.extend([a.get('name', '') for a in item['authors']])
            if 'venue' in item and item['venue']:
                institutions.append(item['venue'])

        # ORCID
        orcid_items = self.search_orcid(query)
        for item in orcid_items:
            if 'orcid-identifier' in item:
                authors.append(item['orcid-identifier'].get('path', ''))

        # PubMed (optional, nur IDs)
        pubmed_ids = self.search_pubmed(query)
        for pmid in pubmed_ids:
            doi_links.append(f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/")

        # Duplikate entfernen
        papers = list(dict.fromkeys(papers))
        authors = list(dict.fromkeys(authors))
        institutions = list(dict.fromkeys(institutions))
        doi_links = list(dict.fromkeys(doi_links))

        return {
            "papers": papers,
            "authors": authors,
            "institutions": institutions,
            "doi_links": doi_links
        }

# Beispiel-Nutzung (noch nicht im Frontend aktiv)
if __name__ == "__main__":
    aosint = AcademicOSINT()
    result = aosint.aggregate_results("John Doe")
    print(result)
