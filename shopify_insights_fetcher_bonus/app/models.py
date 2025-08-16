from pydantic import BaseModel, HttpUrl, Field
from typing import List, Optional, Dict

class Product(BaseModel):
    id: Optional[str] = None
    title: str
    handle: Optional[str] = None
    url: Optional[HttpUrl] = None
    image: Optional[HttpUrl] = None
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    available: Optional[bool] = None
    tags: List[str] = Field(default_factory=list)

class FAQ(BaseModel):
    question: str
    answer: str
    url: Optional[HttpUrl] = None

class PolicyLinks(BaseModel):
    privacy_policy: Optional[HttpUrl] = None
    returns_policy: Optional[HttpUrl] = None
    refunds_policy: Optional[HttpUrl] = None
    terms_of_service: Optional[HttpUrl] = None
    shipping_policy: Optional[HttpUrl] = None

class SocialHandles(BaseModel):
    instagram: Optional[HttpUrl] = None
    facebook: Optional[HttpUrl] = None
    tiktok: Optional[HttpUrl] = None
    twitter: Optional[HttpUrl] = None
    youtube: Optional[HttpUrl] = None
    pinterest: Optional[HttpUrl] = None
    linkedin: Optional[HttpUrl] = None

class Contact(BaseModel):
    emails: List[str] = Field(default_factory=list)
    phones: List[str] = Field(default_factory=list)
    contact_page: Optional[HttpUrl] = None

class ImportantLinks(BaseModel):
    order_tracking: Optional[HttpUrl] = None
    contact_us: Optional[HttpUrl] = None
    blogs: Optional[HttpUrl] = None
    about: Optional[HttpUrl] = None

class BrandContext(BaseModel):
    brand: Optional[str] = None
    website_url: HttpUrl
    whole_catalog: List[Product] = Field(default_factory=list)
    hero_products: List[Product] = Field(default_factory=list)
    policy_links: PolicyLinks = PolicyLinks()
    faqs: List[FAQ] = Field(default_factory=list)
    socials: SocialHandles = SocialHandles()
    contact: Contact = Contact()
    about_text: Optional[str] = None
    important_links: ImportantLinks = ImportantLinks()
    raw_notes: Dict[str, str] = Field(default_factory=dict)
    competitors: List[str] = Field(default_factory=list)
