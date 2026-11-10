"""Widget Wall GitHub release update detection.

Detection only: no downloading, installation, or automatic execution.
"""

import json
import re
import urllib.error
import urllib.request
from urllib.parse import urlsplit
from dataclasses import dataclass
from typing import Optional


CURRENT_VERSION = "0.3.0"
RELEASE_API = (
    "https://api.github.com/repos/"
    "ColorsOfFractals/Widget_Wall/releases/latest"
)

_VERSION_PATTERN = re.compile(
    r"^v?(\d+)\.(\d+)\.(\d+)$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class UpdateResult:
    status: str
    current_version: str
    latest_version: Optional[str] = None
    release_url: Optional[str] = None
    message: str = ""


def parse_version(value):
    if not isinstance(value, str):
        raise ValueError("Version must be a string")

    match = _VERSION_PATTERN.fullmatch(value.strip())

    if not match:
        raise ValueError(f"Unsupported version: {value!r}")

    return tuple(int(part) for part in match.groups())



def is_trusted_release_url(value):
    if not isinstance(value, str):
        return False

    try:
        parsed = urlsplit(value)
    except ValueError:
        return False

    if parsed.scheme != "https":
        return False

    if parsed.netloc != "github.com":
        return False

    if parsed.query or parsed.fragment:
        return False

    base = "/ColorsOfFractals/Widget_Wall/releases"

    if parsed.path == base:
        return True

    if parsed.path.startswith(base + "/tag/"):
        tag = parsed.path[len(base + "/tag/"):]

        if not tag or "/" in tag:
            return False

        return True

    return False

def evaluate_release(release, current_version=CURRENT_VERSION):
    if not isinstance(release, dict):
        raise ValueError("Release response must be an object")

    tag = release.get("tag_name")
    url = release.get("html_url")

    if not isinstance(tag, str):
        raise ValueError("Release tag missing")

    current = parse_version(current_version)
    latest = parse_version(tag)

    if latest > current:
        status = "UPDATE_AVAILABLE"
        message = f"Widget Wall {tag} is available."
    else:
        status = "UP_TO_DATE"
        message = "Widget Wall is up to date."

    return UpdateResult(
        status=status,
        current_version=current_version,
        latest_version=tag,
        release_url=url if is_trusted_release_url(url) else None,
        message=message,
    )


def check_for_updates(current_version=CURRENT_VERSION, timeout=5):
    request = urllib.request.Request(
        RELEASE_API,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "Widget-Wall-Update-Checker",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            release = json.load(response)

        return evaluate_release(release, current_version)

    except (
        urllib.error.URLError,
        TimeoutError,
        OSError,
        ValueError,
        TypeError,
        json.JSONDecodeError,
    ) as exc:
        return UpdateResult(
            status="CHECK_FAILED",
            current_version=current_version,
            message=f"Update check unavailable: {exc}",
        )