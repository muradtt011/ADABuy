import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

class Config:
    # SECURITY: Set SECRET_KEY in env for production.
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-me")

    # DB
    INSTANCE_DIR = BASE_DIR / "instance"
    INSTANCE_DIR.mkdir(exist_ok=True)
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{(INSTANCE_DIR / 'adabuy.sqlite').as_posix()}",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Uploads
    UPLOAD_FOLDER = (BASE_DIR / "app" / "static" / "uploads").as_posix()
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024  # 2MB
    ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

    # Session / cookies
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True
