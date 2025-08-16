from __future__ import annotations
import os, re, time
from typing import List
from urllib.parse import urlparse
import requests

USER_AGENT = os.getenv("USER_AGENT", "ShopifyInsightsFetcher/1.0")
HEADERS = {"User-Agent": USER_AGENT}
SERPAPI_KEY = os.getenv("SERPAPI_KEY")

def _domain(url: str) -> str:
    try:
        netloc = urlparse(url).netloc.lower()
        if netloc.startswith("www."):
            netloc = netloc[4:]
        return netloc
    except Exception:
        return ""

def _is_shop(url: str) -> bool:
    host = _domain(url)
    bad = ("facebook.com","instagram.com","twitter.com","x.com","youtube.com","linkedin.com",
           "pinterest.com","wikipedia.org","medium.com","crunchbase.com","reddit.com",
           "apps.shopify.com","github.com","docs.google.com")
    if any(host.endswith(b) for b in bad):
        return False
    return host and "." in host

def via_serpapi(query: str, num: int = 10) -> List[str]:
    if not SERPAPI_KEY:
        return []
    try:
        params = {"engine":"google","q":query,"num":num,"api_key":SERPAPI_KEY}
        r = requests.get("https://serpapi.com/search", params=params, headers=HEADERS, timeout=25)
        data = r.json()
        links = []
        for res in (data.get("organic_results") or []):
            url = res.get("link")
            if url and _is_shop(url):
                links.append(url)
        return links
    except Exception:
        return []

def via_duckduckgo(query: str, num: int = 20) -> List[str]:
    try:
        # lite HTML endpoint avoids JS
        r = requests.get("https://duckduckgo.com/html/", params={"q": query}, headers=HEADERS, timeout=20)
        html = r.text
        urls = re.findall(r'href="(https?://[^"]+)"', html)
        dedup = []
        seen = set()
        for u in urls:
            d = _domain(u)
            if not _is_shop(u): 
                continue
            if d not in seen:
                seen.add(d); dedup.append(u)
            if len(dedup) >= num: break
        return dedup
    except Exception:
        return []

def guess_competitors(brand_name: str, base_url: str, max_results: int = 5) -> List[str]:
    queries = [
        f"{brand_name} competitors",
        f"sites like {brand_name}",
        f"alternatives to {brand_name}",
        f"{brand_name} similar brands",
    ]
    found: List[str] = []
    seen_domains = set([_domain(base_url)])
    for q in queries:
        links = via_serpapi(q, num=10) or via_duckduckgo(q, num=20)
        for u in links:
            d = _domain(u)
            if not d or d in seen_domains:
                continue
            seen_domains.add(d)
            found.append(f"https://{d}")
            if len(found) >= max_results:
                return found
        time.sleep(0.5)
    return found[:max_results]
