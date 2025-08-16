# Shopify Insights Fetcher

A Python FastAPI application that scrapes **Shopify store insights** without using the official Shopify API.

## 🚀 Features

### ✅ Mandatory Features
- Fetch **whole product catalog** (`/products.json` endpoint)
- Identify **hero products** (from homepage)
- Extract:
  - Privacy Policy
  - Return & Refund Policies
  - FAQs (single page / multiple page formats)
  - Social Handles (Instagram, Facebook, TikTok, etc.)
  - Contact Details (emails, phone numbers)
  - About Us / Brand context text
  - Important links (Order Tracking, Contact Us, Blogs)
- RESTful API endpoint:
  - `POST /analyze` → returns a structured JSON `BrandContext`
- Error handling:
  - `401` if website not found
  - `500` for internal server errors

### 🔹 Bonus Features
- **Competitor Analysis**:
  - Finds competitors via SerpAPI or DuckDuckGo
  - Scrapes the same insights for competitor stores
- **SQL Persistence**:
  - Persists brand, products, FAQs in MySQL (if enabled with `persist=true`)

---

## ⚙️ Installation

```bash
# Clone or unzip the project
cd shopify_insights_fetcher

# Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.sample .env
```

Set your environment values in `.env`:

```
MYSQL_URL=mysql+mysqlconnector://user:password@localhost:3306/shopify_insights
SERPAPI_KEY=your_serpapi_key_here   # optional (for competitor analysis)
```

---

## ▶️ Run

```bash
uvicorn app.main:app --reload
```

Open docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 📌 Usage

### Analyze a store
```bash
curl -X POST http://127.0.0.1:8000/analyze   -H "Content-Type: application/json"   -d '{"website_url":"https://memy.co.in"}'
```

### Analyze with competitors + persistence
```bash
curl -X POST http://127.0.0.1:8000/analyze   -H "Content-Type: application/json"   -d '{"website_url":"https://memy.co.in","include_competitors": true,"persist": true}'
```

---

## 📂 Project Structure

```
shopify_insights_fetcher/
│── app/
│   ├── main.py              # FastAPI entry point
│   ├── models.py            # Pydantic models
│   ├── scraper/
│   │   ├── brand_scraper.py # Scrapes brand info
│   │   ├── competitor_finder.py # Finds competitors
│   ├── db/
│   │   ├── database.py      # SQLAlchemy setup
│   │   ├── crud.py          # DB operations
│── requirements.txt
│── .env.sample
│── README.md
```

---

## 📖 API

- `POST /analyze`
  - **Input**: `{ "website_url": "<shopify_store_url>", "include_competitors": false, "persist": false }`
  - **Output**: JSON `BrandContext` with store insights

---

## 🛠️ Tech Stack

- **FastAPI** (API framework)
- **BeautifulSoup4 / Requests** (scraping)
- **SQLAlchemy + MySQL** (persistence)
- **Pydantic** (data validation)
- **Uvicorn** (server)

---

