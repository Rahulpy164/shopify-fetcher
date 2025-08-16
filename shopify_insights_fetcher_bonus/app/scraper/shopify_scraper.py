from __future__ import annotations
import re, json, time
from typing import Optional, List
from urllib.parse import urljoin, urlparse
import tldextract
import requests
from bs4 import BeautifulSoup
from ..config import settings
from ..models import Product, FAQ, PolicyLinks, SocialHandles, Contact, ImportantLinks, BrandContext
from ..utils.text import clean_text, extract_emails, extract_phones, find_faq_pairs

HEADERS = {
    'User-Agent': settings.USER_AGENT,
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}

SOCIAL_DOMAINS = {
    'instagram.com': 'instagram',
    'facebook.com': 'facebook',
    'fb.com': 'facebook',
    'tiktok.com': 'tiktok',
    'twitter.com': 'twitter',
    'x.com': 'twitter',
    'youtube.com': 'youtube',
    'youtu.be': 'youtube',
    'pinterest.com': 'pinterest',
    'linkedin.com': 'linkedin',
}

def _get(url: str, **kwargs) -> requests.Response:
    timeout = kwargs.pop('timeout', settings.REQUEST_TIMEOUT)
    return requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True, **kwargs)

def normalize_base(url: str) -> str:
    if not url.startswith('http'):
        url = 'https://' + url
    parts = urlparse(url)
    return f"{parts.scheme}://{parts.netloc}"

def is_shopify_store(html: str) -> bool:
    hints = ['cdn.shopify.com','Shopify.theme','ShopifyAnalytics','shopify-section']
    tl = html.lower()
    return any(h.lower() in tl for h in hints)

def paginate_products_json(base: str, limit: int = 250, max_pages: int = 50) -> List[dict]:
    products = []
    page = 1
    while page <= max_pages:
        url = f"{base}/products.json?limit={limit}&page={page}"
        r = _get(url)
        if r.status_code != 200:
            break
        try:
            data = r.json()
        except Exception:
            break
        batch = data.get('products') or []
        if not batch:
            break
        products.extend(batch)
        if len(batch) < limit:
            break
        page += 1
        time.sleep(0.3)
    return products

def parse_product_json(pj: dict, base: str) -> Product:
    handle = pj.get('handle')
    url = f"{base}/products/{handle}" if handle else None
    images = pj.get('images') or []
    image = images[0]['src'] if images else None
    prices = [v.get('price') for v in pj.get('variants') or [] if v.get('price') is not None]
    price_min = min(prices) if prices else None
    price_max = max(prices) if prices else None
    available = any(v.get('available') for v in pj.get('variants') or [])
    tags = pj.get('tags').split(',') if isinstance(pj.get('tags'), str) else pj.get('tags') or []
    return Product(
        id=str(pj.get('id')) if pj.get('id') else None,
        title=pj.get('title') or handle or 'Unknown',
        handle=handle,
        url=url,
        image=image,
        price_min=float(price_min) if price_min is not None else None,
        price_max=float(price_max) if price_max is not None else None,
        available=bool(available) if available is not None else None,
        tags=[t.strip() for t in tags if t and isinstance(t, str)],
    )

def discover_links(base: str, html: str) -> dict[str,str]:
    soup = BeautifulSoup(html, 'lxml')
    links = {}
    for a in soup.find_all('a', href=True):
        href = a['href']
        if href.startswith('#') or href.startswith('mailto:') or href.startswith('tel:'):
            continue
        if href.startswith('http'):
            if urlparse(href).netloc != urlparse(base).netloc:
                continue
            abs_url = href
        else:
            abs_url = urljoin(base, href)
        text = a.get_text(' ', strip=True).lower()
        links.setdefault(abs_url, text)
    return links

def find_by_keywords(links: dict[str,str], keywords: list[str]) -> Optional[str]:
    for url, text in links.items():
        for k in keywords:
            if k in url.lower() or k in text.lower():
                return url
    return None

def extract_socials(html: str) -> SocialHandles:
    soup = BeautifulSoup(html, 'lxml')
    from urllib.parse import urlparse
    found = {}
    for a in soup.find_all('a', href=True):
        href = a['href']
        if not href.startswith('http'):
            continue
        host = urlparse(href).netloc.lower()
        parts = host.split('.')
        base = '.'.join(parts[-2:])
        if base in {
            'instagram.com','facebook.com','fb.com','tiktok.com','twitter.com','x.com',
            'youtube.com','youtu.be','pinterest.com','linkedin.com'
        }:
            key = SOCIAL_DOMAINS[base] if base in SOCIAL_DOMAINS else None
            if not key:
                continue
            if 'share' in href or 'intent/tweet' in href:
                continue
            found[key] = href
    return SocialHandles(**found)

def get_hero_products(base: str, html: str) -> list[Product]:
    soup = BeautifulSoup(html, 'lxml')
    prods = []
    seen = set()
    for a in soup.find_all('a', href=True):
        href = a['href']
        if '/products/' in href:
            href_abs = href if href.startswith('http') else urljoin(base, href)
            if href_abs in seen:
                continue
            seen.add(href_abs)
            title = a.get_text(' ', strip=True) or None
            handle = href_abs.rstrip('/').split('/products/')[-1]
            prods.append(Product(title=title or handle, handle=handle, url=href_abs))
        if len(prods) >= 20:
            break
    return prods

def fetch_page(url: str) -> tuple[int, str]:
    r = _get(url)
    return r.status_code, r.text if r.ok else ''

def analyze_store(website_url: str, include_competitors: bool = False) -> BrandContext:
    base = normalize_base(website_url)
    status, html = fetch_page(base)
    if status == 404:
        raise FileNotFoundError('Website not found (404)')
    if status >= 500 or not html:
        raise RuntimeError(f'Failed to fetch website. Status: {status}')
    brand_name = tldextract.extract(base).domain.capitalize()

    ctx = BrandContext(brand=brand_name, website_url=base)
    ctx.raw_notes['shopify_like'] = str(is_shopify_store(html))

    links = discover_links(base, html)

    try:
        pj = paginate_products_json(base)
        ctx.whole_catalog = [parse_product_json(p, base) for p in pj]
        ctx.raw_notes['product_count'] = str(len(ctx.whole_catalog))
    except Exception as e:
        ctx.raw_notes['products_error'] = str(e)

    try:
        ctx.hero_products = get_hero_products(base, html)[:12]
    except Exception as e:
        ctx.raw_notes['hero_error'] = str(e)

    policies = {}
    for cand in [
        '/policies/privacy-policy','/policies/refund-policy','/policies/return-policy',
        '/policies/terms-of-service','/policies/shipping-policy',
        '/pages/privacy-policy','/pages/return-policy','/pages/refund-policy',
        '/pages/terms-of-service','/pages/shipping-policy'
    ]:
        url = urljoin(base, cand)
        s, t = fetch_page(url)
        if s == 200 and t:
            text = clean_text(t)
            if 'privacy' in cand and 'privacy' in text.lower():
                policies['privacy_policy'] = url
            if 'refund' in cand and 'refund' in text.lower():
                policies['refunds_policy'] = url
            if 'return' in cand and 'return' in text.lower():
                policies['returns_policy'] = url
            if 'terms' in cand and ('terms' in text.lower() or 'conditions' in text.lower()):
                policies['terms_of_service'] = url
            if 'shipping' in cand and 'shipping' in text.lower():
                policies['shipping_policy'] = url
    if 'privacy_policy' not in policies:
        u = find_by_keywords(links, ['privacy']); 
        if u: policies['privacy_policy'] = u
    if 'returns_policy' not in policies:
        u = find_by_keywords(links, ['return']);
        if u: policies['returns_policy'] = u
    if 'refunds_policy' not in policies:
        u = find_by_keywords(links, ['refund']);
        if u: policies['refunds_policy'] = u
    if 'terms_of_service' not in policies:
        u = find_by_keywords(links, ['terms']);
        if u: policies['terms_of_service'] = u
    if 'shipping_policy' not in policies:
        u = find_by_keywords(links, ['shipping','delivery']);
        if u: policies['shipping_policy'] = u
    ctx.policy_links = PolicyLinks(**policies)

    ctx.socials = extract_socials(html)

    important = {}
    u = find_by_keywords(links, ['track','order tracking'])
    if not u:
        for cand in ['/pages/track-order','/pages/order-tracking','/tools/track','/a/track']:
            s, t = fetch_page(urljoin(base, cand))
            if s == 200:
                u = urljoin(base, cand); break
    if u: important['order_tracking'] = u

    u = find_by_keywords(links, ['blog'])
    if not u:
        for cand in ['/blogs','/blogs/news']:
            s, t = fetch_page(urljoin(base, cand))
            if s == 200:
                u = urljoin(base, cand); break
    if u: important['blogs'] = u

    u = find_by_keywords(links, ['contact'])
    if not u:
        for cand in ['/pages/contact','/pages/contact-us','/contact']:
            s, t = fetch_page(urljoin(base, cand))
            if s == 200:
                u = urljoin(base, cand); break
    if u: important['contact_us'] = u

    about = None
    u = find_by_keywords(links, ['about','our story','story'])
    if not u:
        for cand in ['/pages/about','/pages/about-us','/pages/our-story','/pages/story']:
            s, t = fetch_page(urljoin(base, cand))
            if s == 200:
                u = urljoin(base, cand); break
    if u:
        important['about'] = u
        s, t = fetch_page(u)
        if s == 200:
            about = clean_text(t)[:5000]
    ctx.about_text = about
    ctx.important_links = ImportantLinks(**important)

    contact = Contact()
    pages_to_scan = [html]
    if ctx.important_links.contact_us:
        s, t = fetch_page(str(ctx.important_links.contact_us))
        if s == 200: pages_to_scan.append(t)
    text_all = ' '.join(clean_text(p) for p in pages_to_scan)
    contact.emails = extract_emails(text_all)
    contact.phones = extract_phones(text_all)
    contact.contact_page = ctx.important_links.contact_us
    ctx.contact = contact

    faqs = []
    faq_urls = []
    u = find_by_keywords(links, ['faq','faqs','help'])
    if u: faq_urls.append(u)
    for cand in ['/pages/faq','/pages/faqs','/pages/support','/apps/help-center','/pages/help-center']:
        faq_urls.append(urljoin(base, cand))
    seen = set()
    for u in faq_urls[:5]:
        if u in seen: continue
        seen.add(u)
        s, t = fetch_page(u)
        if s != 200 or not t: continue
        pairs = find_faq_pairs(t)
        for q,a in pairs[:50]:
            faqs.append(FAQ(question=q, answer=a, url=u))
        if len(faqs) >= 50: break
    ctx.faqs = faqs

    return ctx
