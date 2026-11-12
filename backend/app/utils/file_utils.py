"""
File validation + hashing helpers for uploads.

- `validate_upload` raises HTTPException on bad type/size/empty.
- `sha256_bytes` is used for dedupe: identical bytes -> identical hash ->
  the unique index on documents.file_hash blocks re-uploads.
"""
import hashlib
from fastapi import HTTPException, status, UploadFile

from app.config.settings import settings

ALLOWED_EXTENSIONS = {"pdf", "docx", "txt"}
MAX_BYTES = settings.MAX_UPLOAD_MB * 1024 * 1024


def get_extension(filename: str) -> str:
    if "." not in filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename has no extension",
        )
    ext = filename.rsplit(".", 1)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {ext}. Allowed: {sorted(ALLOWED_EXTENSIONS)}",
        )
    return ext


async def read_and_validate(file: UploadFile) -> tuple[bytes, str, str]:
    """Return (raw_bytes, extension, sha256_hex). Raises on invalid file."""
    ext = get_extension(file.filename or "")
    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="File is empty")
    if len(raw) > MAX_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds {settings.MAX_UPLOAD_MB} MB limit",
        )
    return raw, ext, sha256_bytes(raw)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
