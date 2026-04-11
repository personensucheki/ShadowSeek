import requests
import os

def convert_eur(amount, to_currency="USD"):
    url = f"https://api.exchangerate.host/convert?from=EUR&to={to_currency}&amount={amount}"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        return data.get("result", None)
    except Exception:
        return None
