"""
Local filesystem storage abstraction.

Why abstract now?
- Phase 4 uses the local `./storage` folder.
- Later, swap in S3/Cloudinary by implementing the same interface.
- MongoDB only stores `storage_key` (the relative path), never the binary.
"""
import os
from pathlib import Path

from app.config.settings import settings

BASE = Path(settings.STORAGE_DIR).resolve()


def _ensure_base() -> None:
    BASE.mkdir(parents=True, exist_ok=True)


def save(storage_key: str, data: bytes) -> None:
    _ensure_base()
    path = BASE / storage_key
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def load(storage_key: str) -> bytes:
    return (BASE / storage_key).read_bytes()


def delete(storage_key: str) -> None:
    try:
        (BASE / storage_key).unlink()
    except FileNotFoundError:
        pass


def make_key(file_hash: str, ext: str) -> str:
    # Directory sharding by first 2 chars avoids huge flat dirs.
    return os.path.join(file_hash[:2], f"{file_hash}.{ext}")
