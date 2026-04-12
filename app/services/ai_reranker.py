import os
import logging

try:
    import openai
except ImportError:
    openai = None

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")


def rerank_results(results):
    """
    Rerank a list of result dicts using OpenAI API.
    Returns the reranked list or the original list on error/fallback.
    """
    if not openai or not OPENAI_API_KEY:
        logging.warning("OpenAI not available or API key missing. Returning original results.")
        return results
    try:
        openai.api_key = OPENAI_API_KEY
        # Example: Use GPT-3.5/4 to rerank results based on a prompt
        prompt = f"Rerank the following results by relevance: {results}"
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=256,
            temperature=0.2,
        )
        # Parse response (assume response.choices[0].message['content'] is a JSON list)
        import json

        reranked = json.loads(response.choices[0].message['content'])
        return reranked
    except Exception as e:
        logging.exception(f"OpenAI rerank failed: {e}")
        return results