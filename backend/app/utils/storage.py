"""Temporary file storage for uploads."""
import shutil
import uuid
import zipfile
from pathlib import Path

from app.config import get_settings


def ensure_upload_dir() -> Path:
    """Ensure upload directory exists."""
    d = get_settings().upload_dir
    d.mkdir(parents=True, exist_ok=True)
    return d


def save_upload(file_content: bytes, filename: str, scan_id: str | None = None) -> Path:
    """
    Save uploaded file and extract if zip. Returns path to extracted directory or file.
    """
    upload_dir = ensure_upload_dir()
    scan_id = scan_id or str(uuid.uuid4())
    target_dir = upload_dir / scan_id
    target_dir.mkdir(exist_ok=True)

    # Save raw file
    ext = Path(filename).suffix.lower()
    raw_path = target_dir / filename
    raw_path.write_bytes(file_content)

    if ext in (".zip",):
        # Extract zip
        extract_dir = target_dir / "extracted"
        extract_dir.mkdir(exist_ok=True)
        with zipfile.ZipFile(raw_path, "r") as zf:
            zf.extractall(extract_dir)
        return extract_dir

    # For single file (e.g. docker-compose.yml), return parent so we have a directory
    return target_dir


def cleanup_scan(scan_id: str) -> None:
    """Remove scan files after processing."""
    upload_dir = get_settings().upload_dir
    path = upload_dir / scan_id
    if path.exists():
        shutil.rmtree(path, ignore_errors=True)
