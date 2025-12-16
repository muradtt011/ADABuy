import os
from app import create_app

app = create_app()

if __name__ == "__main__":
    # For local dev only. Prefer: flask --app run.py run
    app.run(debug=True)
