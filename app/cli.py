from __future__ import annotations

from decimal import Decimal

import click
from flask import Flask
from werkzeug.security import generate_password_hash

from .extensions import db
from .models import User, Listing
from .utils import is_ada_email, validate_password

def register_cli(app: Flask) -> None:
    @app.cli.command("init-db")
    def init_db():
        """Create all database tables."""
        with app.app_context():
            db.create_all()
        print("✅ Database initialized.")

    @app.cli.command("seed-db")
    def seed_db():
        """Insert demo users and listings (safe to run multiple times)."""
        with app.app_context():
            db.create_all()

            if User.query.count() > 0:
                print("ℹ️  Database already has users; skipping seed.")
                return

            users = [
                User(
                    name="Alice Student",
                    email="alice.student@ada.edu.az",
                    password_hash=generate_password_hash("Alice123!"),
                    is_admin=False,
                ),
                User(
                    name="Bob Seller",
                    email="bob.seller@ada.edu.az",
                    password_hash=generate_password_hash("Bob12345!"),
                    is_admin=False,
                ),
                User(
                    name="Admin User",
                    email="admin@ada.edu.az",
                    password_hash=generate_password_hash("Admin123!"),
                    is_admin=True,
                ),
            ]
            db.session.add_all(users)
            db.session.flush()

            listings = [
                Listing(
                    title="Calculus Textbook (Used)",
                    description="Good condition, some highlights. Pickup on campus.",
                    category="Textbooks",
                    price=Decimal("15.00"),
                    seller_id=users[0].id,
                ),
                Listing(
                    title="Logitech Mouse",
                    description="Wireless mouse, works perfectly. Includes USB receiver.",
                    category="Electronics",
                    price=Decimal("10.00"),
                    seller_id=users[1].id,
                ),
                Listing(
                    title="Arduino Starter Kit",
                    description="Great for ITE labs. Most parts included.",
                    category="Equipment",
                    price=Decimal("25.00"),
                    seller_id=users[1].id,
                ),
            ]
            db.session.add_all(listings)
            db.session.commit()

        print("Seed data inserted (3 users, 3 listings).")
        print("Demo logins:")
        print("- alice.student@ada.edu.az / Alice123!")
        print("- bob.seller@ada.edu.az / Bob12345!")
        print("- admin@ada.edu.az / Admin123! (admin)")

    @app.cli.command("create-admin")
    @click.argument("email")
    @click.argument("password")
    @click.argument("name")
    def create_admin(email: str, password: str, name: str):
        """Create an admin user.

        Usage:
            flask --app run.py create-admin admin@ada.edu.az "Admin123!" "Admin User"
        """
        email_norm = email.strip().lower()

        if not is_ada_email(email_norm):
            raise click.ClickException("Email must be an @ada.edu.az address.")

        pw_errors = validate_password(password)
        if pw_errors:
            raise click.ClickException("Password does not meet complexity rules:\n- " + "\n- ".join(pw_errors))

        with app.app_context():
            db.create_all()
            if User.query.filter_by(email=email_norm).first():
                raise click.ClickException("A user with that email already exists.")

            user = User(
                name=name.strip(),
                email=email_norm,
                password_hash=generate_password_hash(password),
                is_admin=True,
            )
            db.session.add(user)
            db.session.commit()

        print("Admin user created.")
