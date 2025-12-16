import re
import uuid
from functools import wraps
from typing import Iterable, Optional, Tuple, List

from flask import abort, current_app
from flask_login import current_user
from werkzeug.utils import secure_filename

ADA_DOMAIN = "@ada.edu.az"

def is_ada_email(email: str) -> bool:
    if not email:
        return False
    email = email.strip().lower()
    return email.endswith(ADA_DOMAIN)

def validate_password(password: str) -> List[str]:
    """Return a list of human-readable validation error messages."""
    errors: List[str] = []
    if password is None:
        return ["Password is required."]

    if len(password) < 8:
        errors.append("Password must be at least 8 characters long.")
    if not re.search(r"[A-Z]", password):
        errors.append("Password must include at least one uppercase letter.")
    if not re.search(r"[a-z]", password):
        errors.append("Password must include at least one lowercase letter.")
    if not re.search(r"\d", password):
        errors.append("Password must include at least one number.")
    if not re.search(r"[^A-Za-z0-9]", password):
        errors.append("Password must include at least one special character (e.g., !, @, #).")

    return errors

def allowed_image(filename: str) -> bool:
    if not filename or "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in current_app.config.get("ALLOWED_IMAGE_EXTENSIONS", set())

def save_image(file_storage) -> Optional[str]:
    """Save a single uploaded image to the uploads folder. Returns stored filename or None."""
    if not file_storage or not getattr(file_storage, "filename", ""):
        return None
    if not allowed_image(file_storage.filename):
        return None

    # Prevent path traversal and collisions
    original = secure_filename(file_storage.filename)
    ext = original.rsplit(".", 1)[1].lower()
    unique = f"{uuid.uuid4().hex}.{ext}"
    dest_path = current_app.config["UPLOAD_FOLDER"]
    file_storage.save(f"{dest_path}/{unique}")
    return unique

def admin_required(view_fn):
    @wraps(view_fn)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(403)
        if not getattr(current_user, "is_admin", False):
            abort(403)
        return view_fn(*args, **kwargs)
    return wrapper
