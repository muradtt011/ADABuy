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

@listings_bp.route("/listing/create", methods=["GET", "POST"])
@login_required
def create():
    if request.method == "POST":
        title = (request.form.get("title") or "").strip()
        description = (request.form.get("description") or "").strip()
        category = (request.form.get("category") or "").strip()
        price_raw = (request.form.get("price") or "").strip()
        price = _parse_price(price_raw)

        errors: List[str] = []
        if not title:
            errors.append("Title is required.")
        if not description:
            errors.append("Description is required.")
        if not category:
            errors.append("Category is required.")
        if price is None:
            errors.append("Price must be a valid number.")
        elif price < 0:
            errors.append("Price must be non-negative.")

        image_file = request.files.get("image")
        image_filename = None
        if image_file and image_file.filename:
            image_filename = save_image(image_file)
            if image_filename is None:
                errors.append("Invalid image type. Allowed: png, jpg, jpeg, gif, webp.")

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template(
                "listings/form.html",
                mode="create",
                categories=DEFAULT_CATEGORIES,
                form={"title": title, "description": description, "category": category, "price": price_raw},
            )

        listing = Listing(
            title=title,
            description=description,
            category=category,
            price=price,
            image_filename=image_filename,
            seller_id=current_user.id,
        )
        db.session.add(listing)
        db.session.commit()

        flash("Listing created successfully.", "success")
        return redirect(url_for("listings.my_listings"))

    return render_template(
        "listings/form.html",
        mode="create",
        categories=DEFAULT_CATEGORIES,
        form={},
    )

@listings_bp.route("/my-listings")
@login_required
def my_listings():
    listings = Listing.query.filter_by(seller_id=current_user.id).order_by(Listing.created_at.desc()).all()
    return render_template("listings/my_listings.html", listings=listings)

@listings_bp.route("/listing/<int:listing_id>/edit", methods=["GET", "POST"])
@login_required
def edit(listing_id: int):
    listing = db.session.get(Listing, listing_id)
    if not listing:
        abort(404)

    if listing.seller_id != current_user.id and not current_user.is_admin:
        abort(403)

    if request.method == "POST":
        title = (request.form.get("title") or "").strip()
        description = (request.form.get("description") or "").strip()
        category = (request.form.get("category") or "").strip()
        price_raw = (request.form.get("price") or "").strip()
        price = _parse_price(price_raw)

        errors: List[str] = []
        if not title:
            errors.append("Title is required.")
        if not description:
            errors.append("Description is required.")
        if not category:
            errors.append("Category is required.")
        if price is None:
            errors.append("Price must be a valid number.")
        elif price < 0:
            errors.append("Price must be non-negative.")

        image_file = request.files.get("image")
        if image_file and image_file.filename:
            image_filename = save_image(image_file)
            if image_filename is None:
                errors.append("Invalid image type. Allowed: png, jpg, jpeg, gif, webp.")
            else:
                listing.image_filename = image_filename

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template(
                "listings/form.html",
                mode="edit",
                categories=DEFAULT_CATEGORIES,
                form={"title": title, "description": description, "category": category, "price": price_raw},
                listing=listing,
            )

        listing.title = title
        listing.description = description
        listing.category = category
        listing.price = price
        db.session.commit()

        flash("Listing updated successfully.", "success")
        return redirect(url_for("listings.my_listings"))

    return render_template(
        "listings/form.html",
        mode="edit",
        categories=DEFAULT_CATEGORIES,
        form={"title": listing.title, "description": listing.description, "category": listing.category, "price": str(listing.price)},
        listing=listing,
    )

@listings_bp.route("/listing/<int:listing_id>/delete", methods=["GET", "POST"])
@login_required
def delete(listing_id: int):
    listing = db.session.get(Listing, listing_id)
    if not listing:
        abort(404)

    if listing.seller_id != current_user.id and not current_user.is_admin:
        abort(403)

    if request.method == "POST":
        if not listing.is_active:
            flash("Listing is already removed.", "info")
            return redirect(url_for("listings.my_listings"))
        listing.is_active = False
        db.session.commit()
        flash("Listing removed.", "success")
        return redirect(url_for("listings.my_listings"))

    return render_template("listings/confirm_delete.html", listing=listing)
