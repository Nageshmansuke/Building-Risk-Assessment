"""
WSGI entrypoint for QuakeGuard AI production deployment (Gunicorn / Waitress / uWSGI).
"""

from app import app, db

# Create tables if not present
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run()
