from __future__ import annotations
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, Float, Boolean, ForeignKey, Text

class Base(DeclarativeBase):
    pass

class Brand(Base):
    __tablename__ = 'brands'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255))
    website_url: Mapped[str] = mapped_column(String(512), unique=True)
    about_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    products = relationship('Product', back_populates='brand', cascade='all, delete-orphan')
    faqs = relationship('FAQ', back_populates='brand', cascade='all, delete-orphan')

class Product(Base):
    __tablename__ = 'products'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    brand_id: Mapped[int] = mapped_column(ForeignKey('brands.id', ondelete='CASCADE'))
    external_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    title: Mapped[str] = mapped_column(String(512))
    handle: Mapped[str | None] = mapped_column(String(512), nullable=True)
    url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    image: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    price_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    price_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    available: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    tags: Mapped[str | None] = mapped_column(Text, nullable=True)

    brand = relationship('Brand', back_populates='products')

class FAQ(Base):
    __tablename__ = 'faqs'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    brand_id: Mapped[int] = mapped_column(ForeignKey('brands.id', ondelete='CASCADE'))
    question: Mapped[str] = mapped_column(Text)
    answer: Mapped[str] = mapped_column(Text)
    url: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    brand = relationship('Brand', back_populates='faqs')
