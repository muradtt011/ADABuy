from __future__ import annotations

from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user
from werkzeug.security import check_password_hash, generate_password_hash

from ..extensions import db
from ..models import LoginAttempt, User
from ..utils import is_ada_email, validate_password

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("listings.index"))

    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""

        errors = []
        if not name:
            errors.append("Name is required.")
        if not is_ada_email(email):
            errors.append("Only @ada.edu.az emails may register.")
        if User.query.filter_by(email=email).first():
            errors.append("This email is already registered. Please log in.")
        pw_errors = validate_password(password)
        errors.extend(pw_errors)

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("auth/register.html", form={"name": name, "email": email})

        user = User(
            name=name,
            email=email,
            password_hash=generate_password_hash(password),
            is_admin=False,
            is_active=True,
        )
        db.session.add(user)
        db.session.commit()

        flash("Registration successful. Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html", form={})

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("listings.index"))

    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        ip = request.headers.get("X-Forwarded-For", request.remote_addr)

        user = User.query.filter_by(email=email).first()

        success = False
        if user and user.is_active and check_password_hash(user.password_hash, password):
            success = True
            login_user(user)
            flash("Welcome back!", "success")
        else:
            flash("Invalid credentials or account inactive.", "danger")

        # Track attempts (requirement explicitly mentions tracking failed attempts).
        attempt = LoginAttempt(
            email=email,
            ip_address=ip,
            attempted_at=datetime.utcnow(),
            success=success,
            user_id=user.id if user else None,
        )
        db.session.add(attempt)
        db.session.commit()

        if success:
            return redirect(url_for("listings.index"))
        return redirect(url_for("auth.login"))

    return render_template("auth/login.html")

@auth_bp.route("/logout")
def logout():
    if current_user.is_authenticated:
        logout_user()
        flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))
