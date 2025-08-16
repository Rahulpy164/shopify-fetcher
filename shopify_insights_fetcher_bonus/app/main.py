from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
from .models import BrandContext
from .scraper.shopify_scraper import analyze_store
from .scraper.competitor_finder import guess_competitors
from .config import settings
from .db.session import init_engine
from .db.models import Base as SA_Base, Brand as SA_Brand, Product as SA_Product, FAQ as SA_FAQ
from sqlalchemy.orm import Session

app = FastAPI(title="Shopify Store Insights-Fetcher", version="1.1.0")

class AnalyzeRequest(BaseModel):
    website_url: HttpUrl
    include_competitors: bool = False
    persist: bool = False

class AnalyzeResponse(BrandContext):
    competitor_contexts: list[BrandContext] = []

@app.on_event("startup")
def startup():
    engine, _ = init_engine()
    if engine:
        SA_Base.metadata.create_all(engine)

@app.post("/analyze", response_model=AnalyzeResponse, responses={401: {"description":"Website not found"}, 500:{"description":"Internal error"}})
def analyze(req: AnalyzeRequest):
    try:
        ctx = analyze_store(str(req.website_url), include_competitors=False)
    except FileNotFoundError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if req.persist and settings.MYSQL_URL:
        engine, SessionLocal = init_engine()
        if not engine or not SessionLocal:
            raise HTTPException(status_code=500, detail="DB not initialized")
        with SessionLocal() as db:
            _persist(db, ctx)

    # --- BONUS: competitor analysis ---
    comp_contexts = []
    if req.include_competitors:
        comp_sites = guess_competitors(ctx.brand or "", str(ctx.website_url), max_results=3)
        for comp in comp_sites:
            try:
                cctx = analyze_store(comp, include_competitors=False)
                comp_contexts.append(cctx)
                if req.persist and settings.MYSQL_URL:
                    engine, SessionLocal = init_engine()
                    if engine and SessionLocal:
                        with SessionLocal() as db:
                            _persist(db, cctx)
            except Exception:
                # ignore individual competitor failures
                pass

    resp = ctx.model_copy(update={"competitor_contexts": comp_contexts})
    return resp

def _persist(db: Session, ctx: BrandContext):
    brand = db.query(SA_Brand).filter(SA_Brand.website_url == str(ctx.website_url)).one_or_none()
    if not brand:
        brand = SA_Brand(name=ctx.brand or '', website_url=str(ctx.website_url), about_text=ctx.about_text)
        db.add(brand); db.flush()
    else:
        brand.name = ctx.brand or brand.name
        brand.about_text = ctx.about_text or brand.about_text
        db.flush()

    db.query(SA_Product).filter(SA_Product.brand_id == brand.id).delete()
    for p in ctx.whole_catalog:
        db.add(SA_Product(
            brand_id=brand.id,
            external_id=p.id,
            title=p.title,
            handle=p.handle,
            url=str(p.url) if p.url else None,
            image=str(p.image) if p.image else None,
            price_min=p.price_min,
            price_max=p.price_max,
            available=p.available,
            tags=','.join(p.tags) if p.tags else None
        ))

    db.query(SA_FAQ).filter(SA_FAQ.brand_id == brand.id).delete()
    for f in ctx.faqs:
        db.add(SA_FAQ(
            brand_id=brand.id,
            question=f.question,
            answer=f.answer,
            url=str(f.url) if f.url else None
        ))
    db.commit()
