"""Unified schemas for scan findings across all scanners."""
from enum import Enum

from pydantic import BaseModel, Field


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class FindingCategory(str, Enum):
    SECURITY = "security"
    COST = "cost"
    PERFORMANCE = "performance"


class Finding(BaseModel):
    """Unified finding model for all scanner outputs."""

    id: str = Field(description="Unique identifier for the finding")
    severity: Severity = Field(description="Severity level")
    category: FindingCategory = Field(default=FindingCategory.SECURITY)
    title: str = Field(description="Short title of the finding")
    message: str = Field(description="Detailed description")
    file_path: str | None = Field(default=None, description="Affected file path")
    line_number: int | None = Field(default=None, description="Line number if applicable")
    scanner: str = Field(description="Source scanner: trivy, checkov, infracost")
    remediation: str | None = Field(default=None, description="How to fix the issue")
    cve_id: str | None = Field(default=None, description="CVE identifier for vulnerabilities")
