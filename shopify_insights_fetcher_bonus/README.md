# Shopify Store Insights-Fetcher (FastAPI)

A Python backend that scrapes a Shopify-based store (without using the official Shopify API) and returns structured brand insights as JSON.

## Mandatory Features
- Whole product catalog via `/products.json` pagination.
- Hero products from homepage.
- Policy links (privacy, returns/refund, terms, shipping).
- FAQs extraction from common pages.
- Social handles (IG, FB, TikTok, Twitter/X, YouTube, Pinterest, LinkedIn).
- Contact details (emails, phones) + contact page.
- About text.
- Important links (order tracking, contact, blogs, about).
- Proper HTTP errors: 401 (not found), 500 (internal).

## Bonus Features
- Competitor analysis (SerpAPI or DuckDuckGo fallback).
- MySQL persistence with SQLAlchemy.

## Tech
- FastAPI, Pydantic v2, Requests, BeautifulSoup4, lxml
- SQLAlchemy (optional MySQL)
- Pydantic Settings (.env)

## Quickstart
```bash
python3 -m venv .venv
source .venv/bin/activate             # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.sample .env                   # set MYSQL_URL and SERPAPI_KEY if desired
uvicorn app.main:app --reload
```

Open Swagger UI at: `http://127.0.0.1:8000/docs`

### Example (no DB, no competitors)
```bash
curl -X POST http://127.0.0.1:8000/analyze   -H "Content-Type: application/json"   -d '{"website_url": "https://memy.co.in"}'
```

### Example (with competitors + persist)
```bash
curl -X POST http://127.0.0.1:8000/analyze   -H "Content-Type: application/json"   -d '{"website_url":"https://memy.co.in","include_competitors": true,"persist": true}'
```

### Environment Variables (.env)
```
MYSQL_URL=mysql+mysqlconnector://user:password@localhost:3306/shopify_insights
REQUEST_TIMEOUT=20
USER_AGENT=ShopifyInsightsFetcher/1.0 (+https://example.com; contact@example.com)
MAX_PAGES=10
LOG_LEVEL=INFO
SERPAPI_KEY=
```

### Postman
Import `postman_collection.json` into Postman for a ready-to-run request.
