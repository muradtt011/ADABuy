import logging
import os
from logging.handlers import RotatingFileHandler

from flask import Flask, render_template
from dotenv import load_dotenv

from .config import Config
from .extensions import db, login_manager
from .models import User

def _configure_logging(app: Flask) -> None:
    """Log technical errors to a rotating log file (required for reliability)."""
    os.makedirs("logs", exist_ok=True)

    handler = RotatingFileHandler("logs/adabuy.log", maxBytes=1_000_000, backupCount=3)
    handler.setLevel(logging.INFO)

    formatter = logging.Formatter("[%(asctime)s] %(levelname)s in %(module)s: %(message)s")
    handler.setFormatter(formatter)

    # Avoid duplicate handlers in reloads
    if not any(isinstance(h, RotatingFileHandler) for h in app.logger.handlers):
        app.logger.addHandler(handler)

    app.logger.setLevel(logging.INFO)

def create_app(config_class=Config) -> Flask:
    load_dotenv()

    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)

    # Ensure upload folder exists
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # Extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "warning"

    @login_manager.user_loader
    def load_user(user_id: str):
        return db.session.get(User, int(user_id))

    # Logging
    _configure_logging(app)

    # Blueprints
    from .auth.routes import auth_bp
    from .listings.routes import listings_bp
    from .admin.routes import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(listings_bp)
    app.register_blueprint(admin_bp)

    # Error handlers (user-friendly pages)
    @app.errorhandler(403)
    def forbidden(e):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template("errors/500.html"), 500

    # CLI commands
    from .cli import register_cli
    register_cli(app)

    return app
