"""Scan orchestrator - dispatches to scanners based on target type and aggregates results."""
from pathlib import Path

from app.models.schemas import Finding
from app.services import checkov, infracost, trivy


class TargetType:
    """Supported scan target types."""

    CODE = "code"
    DOCKER_IMAGE = "docker_image"
    DOCKER_COMPOSE = "docker_compose"
    KUBERNETES = "kubernetes"
    TERRAFORM = "terraform"
    ANSIBLE = "ansible"
    GITHUB_REPO = "github_repo"


def run_scan(target_path: str | Path, target_type: str, docker_image_ref: str | None = None) -> list[Finding]:
    """
    Run appropriate scanners based on target type.
    - target_path: Path to extracted upload (directory) or N/A for image-only scans
    - target_type: One of TargetType values
    - docker_image_ref: Image reference (e.g. nginx:latest) when target_type is DOCKER_IMAGE
    """
    findings: list[Finding] = []

    path = Path(target_path) if target_path else None

    if target_type == TargetType.DOCKER_IMAGE and docker_image_ref:
        findings.extend(trivy.run_trivy_image(docker_image_ref))
        return findings

    # github_repo uses same scanners as code (Trivy fs + Checkov)
    if target_type == TargetType.GITHUB_REPO:
        target_type = TargetType.CODE

    if not path or not path.exists():
        return findings

    # Filesystem/code scan with Trivy
    if target_type in (TargetType.CODE, TargetType.KUBERNETES, TargetType.TERRAFORM):
        findings.extend(trivy.run_trivy_fs(path))

    # Cost scan with Infracost (Terraform only)
    if target_type == TargetType.TERRAFORM:
        findings.extend(infracost.run_infracost(path))

    # IaC scan with Checkov
    if target_type == TargetType.DOCKER_COMPOSE:
        # Find docker-compose files
        compose_files = list(path.rglob("docker-compose*.yml")) + list(path.rglob("docker-compose*.yaml"))
        compose_files += list(path.rglob("compose*.yml")) + list(path.rglob("compose*.yaml"))
        for f in compose_files[:10]:  # Limit to avoid long scans
            findings.extend(checkov.run_checkov(path, f))
        if not compose_files:
            findings.extend(checkov.run_checkov(path))
    elif target_type in (TargetType.KUBERNETES, TargetType.TERRAFORM, TargetType.ANSIBLE):
        findings.extend(checkov.run_checkov(path))
    elif target_type == TargetType.CODE:
        # For generic code, run Checkov on directory (detects Dockerfile, Terraform, etc.)
        findings.extend(checkov.run_checkov(path))

    return findings
