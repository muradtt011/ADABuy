# ADABuy (Team 11) — Flask + SQLite Marketplace

ADABuy is a lightweight campus marketplace web app for ADA University students/staff to buy/sell/exchange second‑hand items.
It implements the SRS requirements (registration with `@ada.edu.az` emails, login, listing CRUD, search/filtering, and admin moderation).

## Tech Stack
- Python 3.10+ (works on 3.8+)
- Flask
- Flask-Login (sessions)
- Flask-SQLAlchemy (ORM; helps prevent SQL injection)
- SQLite (default DB)

## Quick Start

### 1) Create & activate a virtual environment
```bash
python -m venv venv
# Windows: venv\Scripts\activate
source venv/bin/activate
```

### 2) Install dependencies
```bash
pip install -r requirements.txt
```

### 3) Initialize the database (and optionally seed sample data)
```bash
flask --app run.py init-db
flask --app run.py seed-db
```

### 4) Create an admin user (optional but recommended)
```bash
flask --app run.py create-admin admin@ada.edu.az "Admin123!" "Admin User"
```

### 5) Run the server
```bash
flask --app run.py run
# then open http://127.0.0.1:5000
```

> By default, the SQLite database is created at `instance/adabuy.sqlite`.

## Default Categories
The UI provides a small set of common categories, but you can freely type a category if you want to extend it.

## Image Uploads
Each listing supports **one optional image**. Uploaded images are stored in `app/static/uploads/`.
Allowed extensions: `png`, `jpg`, `jpeg`, `gif`, `webp`.

## Notes
- No payment/shipping is implemented (offline exchange), per MVP constraints.
- All marketplace pages are protected behind login (unauthenticated users are redirected to login).

## Project Structure
```
adabuy/
  run.py
  requirements.txt
  instance/adabuy.sqlite
  app/
    __init__.py
    models.py
    utils.py
    auth/routes.py
    listings/routes.py
    admin/routes.py
    templates/...
    static/css/styles.css
```
