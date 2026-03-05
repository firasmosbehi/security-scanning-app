"""Scan API endpoints."""
import uuid
from typing import Any

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile

from app.services.orchestrator import TargetType, run_scan
from app.utils.storage import save_upload

router = APIRouter(prefix="/scans", tags=["scans"])

# In-memory scan state (replace with DB in production)
_scans: dict[str, dict[str, Any]] = {}


def _get_scan(scan_id: str) -> dict | None:
    return _scans.get(scan_id)


@router.post("")
async def create_scan(
    background_tasks: BackgroundTasks,
    target_type: str = Form(...),
    docker_image_ref: str | None = Form(None),
    github_url: str | None = Form(None),
    file: UploadFile | None = File(None),
):
    """
    Create and run a scan. Provide one of:
    - file: Upload a zip or config file
    - docker_image_ref: Image from any registry (e.g. nginx:latest, ghcr.io/owner/img:tag)
    - github_url: GitHub repo (e.g. https://github.com/user/repo or user/repo)
    """
    scan_id = str(uuid.uuid4())
    _scans[scan_id] = {"status": "pending", "findings": [], "error": None}

    if target_type == TargetType.DOCKER_IMAGE and docker_image_ref:
        def do_image_scan():
            try:
                _scans[scan_id]["status"] = "running"
                findings = run_scan(None, target_type, docker_image_ref=docker_image_ref)
                _scans[scan_id]["findings"] = [f.model_dump() for f in findings]
                _scans[scan_id]["status"] = "completed"
            except Exception as e:
                _scans[scan_id]["status"] = "failed"
                _scans[scan_id]["error"] = str(e)

        background_tasks.add_task(do_image_scan)
        return {"scan_id": scan_id, "status": "pending", "message": "Scan started"}

    if target_type == TargetType.GITHUB_REPO and github_url and github_url.strip():
        from app.utils.github import clone_repo

        def do_github_scan():
            try:
                _scans[scan_id]["status"] = "running"
                target_path = clone_repo(github_url.strip(), scan_id)
                findings = run_scan(str(target_path), TargetType.GITHUB_REPO)
                _scans[scan_id]["findings"] = [f.model_dump() for f in findings]
                _scans[scan_id]["status"] = "completed"
            except Exception as e:
                _scans[scan_id]["status"] = "failed"
                _scans[scan_id]["error"] = str(e)

        background_tasks.add_task(do_github_scan)
        return {"scan_id": scan_id, "status": "pending", "message": "Cloning and scanning repo"}

    if not file or not file.filename:
        valid_sources = []
        if target_type == TargetType.DOCKER_IMAGE:
            valid_sources.append("docker_image_ref")
        if target_type == TargetType.GITHUB_REPO:
            valid_sources.append("github_url")
        if valid_sources:
            raise HTTPException(400, f"Provide {' or '.join(valid_sources)} for this target type")
        raise HTTPException(400, "File upload required for this target type")

    content = await file.read()
    if not content:
        raise HTTPException(400, "Empty file")

    from app.config import get_settings
    settings = get_settings()
    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(400, f"File too large (max {settings.max_upload_size_mb}MB)")

    try:
        target_path = save_upload(content, file.filename, scan_id)
    except Exception as e:
        raise HTTPException(400, f"Invalid upload: {e}")

    def do_scan():
        try:
            _scans[scan_id]["status"] = "running"
            findings = run_scan(str(target_path), target_type)
            _scans[scan_id]["findings"] = [f.model_dump() for f in findings]
            _scans[scan_id]["status"] = "completed"
        except Exception as e:
            _scans[scan_id]["status"] = "failed"
            _scans[scan_id]["error"] = str(e)

    background_tasks.add_task(do_scan)
    return {"scan_id": scan_id, "status": "pending", "message": "Scan started"}


@router.get("/{scan_id}")
async def get_scan(scan_id: str):
    """Get scan status and results."""
    scan = _get_scan(scan_id)
    if not scan:
        raise HTTPException(404, "Scan not found")
    return scan
