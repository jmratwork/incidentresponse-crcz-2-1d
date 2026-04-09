#!/usr/bin/env python3
"""Validate allowed drift between canonical and compatibility Ansible role trees."""

from __future__ import annotations

import argparse
import hashlib
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class DriftIssue:
    kind: str
    path: str
    detail: str


def _file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _collect_files(root: Path) -> dict[str, Path]:
    files: dict[str, Path] = {}
    for item in root.rglob("*"):
        if not item.is_file():
            continue
        rel_path = item.relative_to(root)
        rel_parts = rel_path.parts
        if "__pycache__" in rel_parts or rel_path.suffix == ".pyc":
            continue
        files[rel_path.as_posix()] = item
    return files


def _load_allowlist(path: Path) -> dict[str, set[str]]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}

    entries = data.get("allowed_drift", [])
    if not isinstance(entries, list):
        raise ValueError("'allowed_drift' must be a list")

    parsed: dict[str, set[str]] = {}
    for idx, entry in enumerate(entries, start=1):
        if not isinstance(entry, dict):
            raise ValueError(f"Entry {idx} in allowlist must be a mapping")
        rel_path = entry.get("path")
        if not isinstance(rel_path, str) or not rel_path:
            raise ValueError(f"Entry {idx} must define a non-empty 'path'")

        kinds = entry.get("kinds", ["any"])
        if isinstance(kinds, str):
            kinds = [kinds]
        if not isinstance(kinds, list) or not kinds:
            raise ValueError(f"Entry {idx} has invalid 'kinds' value")

        parsed.setdefault(rel_path, set()).update(str(kind) for kind in kinds)

    return parsed


def _is_allowed(allowlist: dict[str, set[str]], issue: DriftIssue) -> bool:
    allowed = allowlist.get(issue.path)
    if not allowed:
        return False
    return "any" in allowed or issue.kind in allowed


def find_drift(canonical_root: Path, mirror_root: Path) -> list[DriftIssue]:
    canonical_files = _collect_files(canonical_root)
    mirror_files = _collect_files(mirror_root)

    issues: list[DriftIssue] = []
    for rel_path in sorted(set(canonical_files) | set(mirror_files)):
        canonical_file = canonical_files.get(rel_path)
        mirror_file = mirror_files.get(rel_path)

        if canonical_file and mirror_file:
            if _file_digest(canonical_file) != _file_digest(mirror_file):
                issues.append(
                    DriftIssue(
                        kind="content",
                        path=rel_path,
                        detail="content differs between canonical and mirror",
                    )
                )
            continue

        if canonical_file:
            issues.append(
                DriftIssue(
                    kind="missing_in_mirror",
                    path=rel_path,
                    detail="present only in canonical",
                )
            )
        else:
            issues.append(
                DriftIssue(
                    kind="missing_in_canonical",
                    path=rel_path,
                    detail="present only in mirror",
                )
            )

    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--canonical-root",
        default="provisioning/case-1d/provisioning/roles",
        type=Path,
    )
    parser.add_argument("--mirror-root", default="provisioning/roles", type=Path)
    parser.add_argument(
        "--allowlist",
        default="provisioning/roles-sync-allowlist.yml",
        type=Path,
    )
    args = parser.parse_args()

    allowlist = _load_allowlist(args.allowlist)
    all_issues = find_drift(args.canonical_root, args.mirror_root)

    unauthorized = [issue for issue in all_issues if not _is_allowed(allowlist, issue)]
    stale_allowlist = [
        entry
        for entry in sorted(allowlist)
        if all(issue.path != entry for issue in all_issues)
    ]

    if unauthorized:
        print("ERROR: unapproved drift detected between canonical and mirror roles:")
        for issue in unauthorized:
            print(f"  - [{issue.kind}] {issue.path}: {issue.detail}")

    if stale_allowlist:
        print("ERROR: stale allowlist entries without matching drift:")
        for entry in stale_allowlist:
            print(f"  - {entry}")

    if unauthorized or stale_allowlist:
        return 1

    print(
        "Roles sync check passed. Drift is limited to allowlisted compatibility exceptions."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
