"""Application configuration and scanner paths."""
import os
import shutil
from pathlib import Path

from pydantic_settings import BaseSettings


def _which(cmd: str) -> str | None:
    """Return path to executable if found, else None."""
    path = shutil.which(cmd)
    return path if path else None


class Settings(BaseSettings):
    """Application settings."""

    app_name: str = "Security Scanning App"
    debug: bool = False

    # Upload and temp storage
    upload_dir: Path = Path("/tmp/security-scan-uploads")
    max_upload_size_mb: int = 100

    # Scanner paths (auto-detected if not set)
    trivy_path: str | None = None
    checkov_path: str | None = None
    infracost_path: str | None = None

    # Infracost (optional - cost scanning)
    infracost_api_key: str | None = None

    # GitHub (optional - for private repo cloning)
    github_token: str | None = None

    model_config = {"env_prefix": "SCAN_", "extra": "ignore"}


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def get_infracost_api_key() -> str | None:
    """Infracost API key from settings or INFRACOST_API_KEY env."""
    s = get_settings()
    return s.infracost_api_key or os.environ.get("INFRACOST_API_KEY")


def get_github_token() -> str | None:
    """GitHub token for private repo cloning (GITHUB_TOKEN or SCAN_GITHUB_TOKEN)."""
    s = get_settings()
    return s.github_token or os.environ.get("GITHUB_TOKEN") or os.environ.get("SCAN_GITHUB_TOKEN")


def get_trivy_path() -> str | None:
    s = get_settings()
    if s.trivy_path:
        return s.trivy_path
    return _which("trivy")


def get_checkov_path() -> str | None:
    s = get_settings()
    if s.checkov_path:
        return s.checkov_path
    return _which("checkov")


def get_infracost_path() -> str | None:
    s = get_settings()
    if s.infracost_path:
        return s.infracost_path
    return _which("infracost")
