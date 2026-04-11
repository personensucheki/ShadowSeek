import json
import os
from datetime import datetime
from typing import Dict, Any

SEARCH_CONTEXT_FILE = 'instance/search_context.json'
SEARCH_LOG_FILE = 'instance/search_log.jsonl'

class SearchContextStorage:
    @staticmethod
    def save_context(context: Dict[str, Any]):
        context = dict(context)
        context['timestamp'] = datetime.utcnow().isoformat()
        os.makedirs(os.path.dirname(SEARCH_CONTEXT_FILE), exist_ok=True)
        with open(SEARCH_CONTEXT_FILE, 'w', encoding='utf-8') as f:
            json.dump(context, f, ensure_ascii=False, indent=2)

    @staticmethod
    def load_context() -> Dict[str, Any]:
        if not os.path.exists(SEARCH_CONTEXT_FILE):
            return {}
        with open(SEARCH_CONTEXT_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)

class SearchLogger:
    @staticmethod
    def log(event: Dict[str, Any]):
        event = dict(event)
        event['timestamp'] = datetime.utcnow().isoformat()
        os.makedirs(os.path.dirname(SEARCH_LOG_FILE), exist_ok=True)
        with open(SEARCH_LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(json.dumps(event, ensure_ascii=False) + '\n')

# Beispiel-Nutzung:
# SearchContextStorage.save_context({'query': 'shadowseek', 'results': [...]})
# ctx = SearchContextStorage.load_context()
# SearchLogger.log({'event': 'search_started', 'query': 'shadowseek'})
