import re
from bs4 import BeautifulSoup

EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", re.I)
PHONE_RE = re.compile(r"\+?\d[\d\s().-]{6,}\d")

def clean_text(html: str) -> str:
    soup = BeautifulSoup(html, 'lxml')
    for tag in soup(['script','style','noscript']):
        tag.decompose()
    text = soup.get_text(separator=' ')
    text = re.sub(r"\s+", ' ', text).strip()
    return text

def extract_emails(text: str) -> list[str]:
    return sorted(set(EMAIL_RE.findall(text)))

def extract_phones(text: str) -> list[str]:
    import re as _re
    candidates = set(PHONE_RE.findall(text))
    normalized = set()
    for c in candidates:
        s = _re.sub(r"[^\d+]", '', c)
        if len(s) >= 8:
            normalized.add(s)
    return sorted(normalized)

def find_faq_pairs(html_text: str) -> list[tuple[str,str]]:
    soup = BeautifulSoup(html_text, 'lxml')
    text = clean_text(html_text)
    qa = []
    qa_pattern = re.compile(r"Q\)?\s*[:)-]?\s*(.+?)\s*A\)\s*[:)-]?\s*(.+?)(?=Q\)|$)", re.I|re.S)
    for m in qa_pattern.finditer(text):
        q = m.group(1).strip()
        a = m.group(2).strip()
        if q and a:
            qa.append((q,a))
    if not qa:
        import re as _re
        for h in soup.find_all(_re.compile('^h[1-6]$')):
            q = h.get_text(strip=True)
            ans_parts = []
            for sib in h.find_all_next():
                if sib.name and _re.match('^h[1-6]$', sib.name): break
                if sib.name in ('script','style','noscript'): continue
                ans_parts.append(sib.get_text(' ', strip=True))
            a = ' '.join(ans_parts).strip()
            if q and a:
                qa.append((q,a))
            if len(qa) >= 30: break
    seen = set()
    result = []
    for q,a in qa:
        key = (q[:120].lower(), a[:120].lower())
        if key not in seen:
            seen.add(key)
            result.append((q,a))
    return result[:50]
