"""GitHub repo cloning for scans."""
import re
import subprocess
import uuid
from pathlib import Path

from app.config import get_github_token, get_settings


def normalize_github_url(url: str) -> str:
    """
    Normalize GitHub URL to HTTPS format for cloning.
    - github.com/user/repo -> https://github.com/user/repo.git
    - user/repo -> https://github.com/user/repo.git
    - git@github.com:user/repo.git -> https://github.com/user/repo.git
    """
    url = url.strip()
    # user/repo shorthand
    if re.match(r"^[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+$", url):
        return f"https://github.com/{url}.git"
    # git@ format
    if url.startswith("git@github.com:"):
        repo = url.replace("git@github.com:", "").rstrip(".git")
        return f"https://github.com/{repo}.git"
    # Already https
    if url.startswith("https://github.com/"):
        return url if url.endswith(".git") else f"{url}.git"
    if url.startswith("http://github.com/"):
        return url.replace("http://", "https://", 1) if url.endswith(".git") else f"{url}.git"
    return url


def clone_repo(github_url: str, scan_id: str) -> Path:
    """
    Clone a GitHub repo to a temp directory. Returns path to cloned repo.
    Uses GITHUB_TOKEN for private repos if set.
    """
    upload_dir = get_settings().upload_dir
    work_dir = upload_dir / scan_id
    work_dir.mkdir(parents=True, exist_ok=True)
    target_dir = work_dir / "repo"

    clone_url = normalize_github_url(github_url)
    token = get_github_token()

    # Embed token for private repos: https://TOKEN@github.com/user/repo.git
    if token:
        if "github.com" in clone_url and "@" not in clone_url:
            clone_url = clone_url.replace("https://", f"https://{token}@", 1)

    cmd = [
        "git",
        "clone",
        "--depth", "1",
        "--single-branch",
        clone_url,
        str(target_dir),
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=120,
        cwd=work_dir,
    )

    if result.returncode != 0:
        err = result.stderr or result.stdout or "Clone failed"
        if "Authentication failed" in err or "could not read Username" in err:
            raise PermissionError("GitHub auth failed. Use GITHUB_TOKEN for private repos.")
        raise RuntimeError(f"Git clone failed: {err}")

    # git clone creates a subdir with repo name when cloning to existing dir - no, we clone INTO target_dir
    # Actually: git clone URL target_dir clones into target_dir. The target_dir becomes the repo root.
    # So we're good - target_dir is the repo root.

    return target_dir
