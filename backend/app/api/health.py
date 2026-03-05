"""Health check and scanner availability endpoints."""
from fastapi import APIRouter

from app.config import get_checkov_path, get_infracost_api_key, get_infracost_path, get_settings, get_trivy_path

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def health():
    """Basic health check."""
    return {"status": "ok", "app": get_settings().app_name}


@router.get("/scanners")
async def scanners():
    """Check availability of security scanners."""
    trivy = get_trivy_path()
    checkov = get_checkov_path()
    infracost = get_infracost_path()
    infracost_api_key = get_infracost_api_key()

    return {
        "trivy": {"available": trivy is not None, "path": trivy},
        "checkov": {"available": checkov is not None, "path": checkov},
        "infracost": {
            "available": infracost is not None,
            "path": infracost,
            "api_key_set": bool(infracost_api_key),
        },
    }
