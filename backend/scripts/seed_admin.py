"""
Create an admin user directly in the DB.
Run:
    python -m scripts.seed_admin
Override via env: ADMIN_EMAIL, ADMIN_PASSWORD, ADMIN_NAME
"""
import os
import logging

from pymongo.errors import DuplicateKeyError

from app.config.logging_config import configure_logging
from app.repositories import user_repository as repo
from app.utils.security import hash_password

configure_logging()
logger = logging.getLogger(__name__)

email = os.getenv("ADMIN_EMAIL", "admin@thesqora.local")
password = os.getenv("ADMIN_PASSWORD", "Admin12345!")
name = os.getenv("ADMIN_NAME", "THESQORA Admin")

try:
    user = repo.create_user(
        name=name, email=email,
        password_hash=hash_password(password),
        role="admin", department="Engineering",
    )
    print(f"✅ Admin created: {user['email']} (id={user['id']})")
except DuplicateKeyError:
    print(f"ℹ️  Admin already exists: {email}")
