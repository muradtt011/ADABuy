from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required
from sqlalchemy.orm import selectinload

from ..extensions import db
from ..models import Listing, User
from ..utils import admin_required

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

@admin_bp.route("/")
@login_required
@admin_required
def dashboard():
    status = (request.args.get("status") or "all").strip().lower()
    q = (request.args.get("q") or "").strip()

    query = Listing.query.options(selectinload(Listing.seller))

    if status == "active":
        query = query.filter_by(is_active=True)
    elif status == "inactive":
        query = query.filter_by(is_active=False)

    if q:
        like = f"%{q}%"
        query = query.filter((Listing.title.ilike(like)) | (Listing.description.ilike(like)))

    listings = query.order_by(Listing.created_at.desc()).all()

    return render_template("admin/dashboard.html", listings=listings, status=status, q=q)

@admin_bp.route("/remove-listing/<int:listing_id>", methods=["POST"])
@login_required
@admin_required
def remove_listing(listing_id: int):
    listing = db.session.get(Listing, listing_id)
    if not listing:
        flash("Listing not found.", "danger")
        return redirect(url_for("admin.dashboard"))

    if not listing.is_active:
        flash("Listing is already removed.", "info")
        return redirect(url_for("admin.dashboard"))

    listing.is_active = False
    db.session.commit()
    flash("Listing removed.", "success")
    return redirect(url_for("admin.dashboard"))

# Optional future feature per SRS: deactivate abusive user accounts.
@admin_bp.route("/users")
@login_required
@admin_required
def users():
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template("admin/users.html", users=users)

@admin_bp.route("/users/<int:user_id>/toggle-active", methods=["POST"])
@login_required
@admin_required
def toggle_user_active(user_id: int):
    user = db.session.get(User, user_id)
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for("admin.users"))

    if user.is_admin:
        flash("Admin accounts cannot be deactivated from this UI.", "warning")
        return redirect(url_for("admin.users"))

    user.is_active = not user.is_active
    db.session.commit()
    flash("User status updated.", "success")
    return redirect(url_for("admin.users"))
