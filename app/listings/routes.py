from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import List

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from ..extensions import db
from ..models import Listing
from ..utils import save_image

listings_bp = Blueprint("listings", __name__)

DEFAULT_CATEGORIES = ["Textbooks", "Electronics", "Equipment", "Other"]

def _parse_price(value: str):
    if value is None or value == "":
        return None
    try:
        d = Decimal(value)
        return d
    except (InvalidOperation, ValueError):
        return None

@listings_bp.route("/")
@login_required
def index():
    q = (request.args.get("q") or "").strip()
    category = (request.args.get("category") or "").strip()
    min_price_raw = (request.args.get("min_price") or "").strip()
    max_price_raw = (request.args.get("max_price") or "").strip()

    min_price = _parse_price(min_price_raw)
    max_price = _parse_price(max_price_raw)

    query = Listing.query.filter_by(is_active=True)

    if q:
        like = f"%{q}%"
        query = query.filter((Listing.title.ilike(like)) | (Listing.description.ilike(like)))

    if category:
        query = query.filter(Listing.category == category)

    if min_price is not None:
        query = query.filter(Listing.price >= min_price)

    if max_price is not None:
        query = query.filter(Listing.price <= max_price)

    listings = query.order_by(Listing.created_at.desc()).all()

    # Distinct categories from DB + defaults
    db_cats = [c[0] for c in db.session.query(Listing.category).distinct().all() if c[0]]
    categories = sorted(set(DEFAULT_CATEGORIES + db_cats))

    return render_template(
        "listings/index.html",
        listings=listings,
        categories=categories,
        filters={"q": q, "category": category, "min_price": min_price_raw, "max_price": max_price_raw},
    )

@listings_bp.route("/listing/<int:listing_id>")
@login_required
def detail(listing_id: int):
    listing = db.session.get(Listing, listing_id)
    if not listing:
        abort(404)

    # If inactive, show "Listing unavailable" unless admin (admin can still see details).
    if not listing.is_active and not current_user.is_admin:
        return render_template("listings/unavailable.html")

    return render_template("listings/detail.html", listing=listing)

