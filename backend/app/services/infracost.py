"""Infracost scanner wrapper for Terraform cost estimation."""
import json
import subprocess
import uuid
from pathlib import Path

from app.config import get_infracost_api_key, get_infracost_path
from app.models.schemas import Finding, FindingCategory, Severity


def run_infracost(path: str | Path) -> list[Finding]:
    """
    Run Infracost cost breakdown on a Terraform directory.
    Requires INFRACOST_API_KEY to be set. Returns cost-related findings.
    """
    if not get_infracost_api_key():
        return []

    infracost_path = get_infracost_path()
    if not infracost_path:
        return []

    path_str = str(Path(path).resolve())
    cmd = [
        infracost_path,
        "breakdown",
        "--path", path_str,
        "--format", "json",
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
            cwd=path_str,
            env={
                **__import__("os").environ,
                "INFRACOST_API_KEY": get_infracost_api_key() or "",
            },
        )
        if result.returncode != 0:
            return []

        data = json.loads(result.stdout) if result.stdout else {}
        return _parse_infracost_json(data, path_str)
    except (subprocess.TimeoutExpired, json.JSONDecodeError):
        return []


def _parse_infracost_json(data: dict, base_path: str) -> list[Finding]:
    """Parse Infracost JSON into cost findings."""
    findings: list[Finding] = []

    projects = data.get("projects", [])
    currency = data.get("currency", "USD")

    for project in projects:
        name = project.get("name", "default")
        total_monthly = project.get("totalMonthlyCost")
        if total_monthly is None:
            continue
        try:
            cost_val = float(total_monthly)
        except (TypeError, ValueError):
            cost_val = 0.0

        # Create a summary finding for the project
        finding = Finding(
            id=str(uuid.uuid4()),
            severity=Severity.INFO,
            category=FindingCategory.COST,
            title=f"Terraform cost estimate: {name}",
            message=f"Estimated monthly cost: {currency} {cost_val:.2f}",
            file_path=base_path,
            line_number=None,
            scanner="infracost",
            remediation="Review and optimize resource sizing, use spot/reserved instances where appropriate.",
            cve_id=None,
        )
        findings.append(finding)

    return findings
