"""Checkov scanner wrapper for IaC scanning."""
import json
import subprocess
import uuid
from pathlib import Path

from app.config import get_checkov_path
from app.models.schemas import Finding, FindingCategory, Severity


def _map_severity(s: str | None) -> Severity:
    """Map Checkov severity to unified enum."""
    if not s:
        return Severity.MEDIUM
    m = {
        "CRITICAL": Severity.CRITICAL,
        "HIGH": Severity.HIGH,
        "MEDIUM": Severity.MEDIUM,
        "LOW": Severity.LOW,
    }
    return m.get(str(s).upper(), Severity.MEDIUM)


def _parse_checkov_json(data: list | dict) -> list[Finding]:
    """Parse Checkov JSON output into unified Finding list."""
    findings: list[Finding] = []

    # Checkov can output an array of framework results or a single object
    items = data if isinstance(data, list) else [data]

    for item in items:
        if isinstance(item, dict):
            results = item.get("results", {})
        else:
            continue

        failed_checks = results.get("failed_checks", [])
        for check in failed_checks:
            file_path = check.get("file_path") or check.get("file_abs_path")
            file_line_range = check.get("file_line_range", [])
            line_number = file_line_range[0] if file_line_range else None

            # Build remediation from guidance or fix
            guidance = check.get("guidance", "")
            fix = check.get("fix", "")
            remediation = guidance or fix or None

            check_result = check.get("check_result") or {}
            eval_keys = check_result.get("evaluated_keys", [])
            msg = check.get("check_id", "Check failed")
            if eval_keys:
                msg = f"Failed keys: {eval_keys}" if isinstance(eval_keys, list) else str(eval_keys)
            resource = check.get("resource", "")
            if resource:
                msg = f"{resource}: {msg}"

            finding = Finding(
                id=str(uuid.uuid4()),
                severity=_map_severity(check.get("severity")),
                category=FindingCategory.SECURITY,
                title=check.get("check_name", check.get("check_id", "Check failed")),
                message=msg,
                file_path=str(file_path) if file_path else None,
                line_number=line_number,
                scanner="checkov",
                remediation=remediation,
                cve_id=None,
            )
            findings.append(finding)

    return findings


def run_checkov(path: str | Path, file_path: str | Path | None = None) -> list[Finding]:
    """Run Checkov scan on a directory or single file."""
    checkov_path = get_checkov_path()
    if not checkov_path:
        return []

    path_str = str(Path(path).resolve())
    cmd = [checkov_path, "--quiet", "--output", "json"]

    if file_path:
        cmd.extend(["--file", str(Path(file_path).resolve())])
    else:
        cmd.extend(["--directory", path_str])

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
            cwd=path_str if not file_path else str(Path(path).parent),
        )
        # Checkov returns non-zero when there are failures
        if result.returncode not in (0, 1, 2):
            return []

        output = result.stdout or result.stderr or "[]"
        # Checkov may output to stderr in some cases
        if not output.strip():
            return []

        data = json.loads(output)
        return _parse_checkov_json(data)
    except (subprocess.TimeoutExpired, json.JSONDecodeError):
        return []
