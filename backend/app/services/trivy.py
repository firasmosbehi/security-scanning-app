"""Trivy scanner wrapper for filesystem and image scanning."""
import json
import subprocess
import uuid
from pathlib import Path

from app.config import get_trivy_path
from app.models.schemas import Finding, FindingCategory, Severity


def _map_severity(s: str) -> Severity:
    """Map Trivy severity to unified enum."""
    m = {
        "CRITICAL": Severity.CRITICAL,
        "HIGH": Severity.HIGH,
        "MEDIUM": Severity.MEDIUM,
        "LOW": Severity.LOW,
        "UNKNOWN": Severity.INFO,
    }
    return m.get(s.upper(), Severity.INFO)


def _parse_trivy_json(data: dict, target_prefix: str = "") -> list[Finding]:
    """Parse Trivy JSON output into unified Finding list."""
    findings: list[Finding] = []
    results = data.get("Results", [])

    for result in results:
        target = result.get("Target", "")
        vulnerabilities = result.get("Vulnerabilities", [])
        misconfigurations = result.get("Misconfigurations", [])

        for vuln in vulnerabilities:
            finding = Finding(
                id=str(uuid.uuid4()),
                severity=_map_severity(vuln.get("Severity", "UNKNOWN")),
                category=FindingCategory.SECURITY,
                title=vuln.get("Title", vuln.get("VulnerabilityID", "Unknown vulnerability")),
                message=vuln.get("Description", ""),
                file_path=target if target else None,
                line_number=None,
                scanner="trivy",
                remediation=f"Upgrade to {vuln.get('FixedVersion', 'fixed version')}" if vuln.get("FixedVersion") else None,
                cve_id=vuln.get("VulnerabilityID"),
            )
            findings.append(finding)

        for mis in misconfigurations:
            resolution = mis.get("Resolution", "")
            finding = Finding(
                id=str(uuid.uuid4()),
                severity=_map_severity(mis.get("Severity", "UNKNOWN")),
                category=FindingCategory.SECURITY,
                title=mis.get("Title", "Misconfiguration"),
                message=mis.get("Message", ""),
                file_path=target if target else None,
                line_number=mis.get("PrimaryLineNumber"),
                scanner="trivy",
                remediation=resolution or None,
                cve_id=None,
            )
            findings.append(finding)

    return findings


def run_trivy_fs(path: str | Path) -> list[Finding]:
    """Run Trivy filesystem scan on a directory path."""
    trivy_path = get_trivy_path()
    if not trivy_path:
        return []

    path_str = str(Path(path).resolve())
    cmd = [
        trivy_path,
        "fs",
        "--format", "json",
        "--scanners", "vuln,misconfig,secret",
        path_str,
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
            cwd=None,
        )
        if result.returncode not in (0, 1):  # Trivy returns 1 when findings exist
            return []

        data = json.loads(result.stdout) if result.stdout else {}
        return _parse_trivy_json(data)
    except (subprocess.TimeoutExpired, json.JSONDecodeError):
        return []


def run_trivy_image(image_ref: str) -> list[Finding]:
    """Run Trivy image scan on a container image reference."""
    trivy_path = get_trivy_path()
    if not trivy_path:
        return []

    cmd = [
        trivy_path,
        "image",
        "--format", "json",
        "--scanners", "vuln,misconfig",
        image_ref,
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600,  # Image pulls can take time
            cwd=None,
        )
        if result.returncode not in (0, 1):
            return []

        data = json.loads(result.stdout) if result.stdout else {}
        return _parse_trivy_json(data)
    except (subprocess.TimeoutExpired, json.JSONDecodeError):
        return []
