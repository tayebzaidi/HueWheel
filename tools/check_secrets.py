#!/usr/bin/env python3
"""Stop secrets and personal details reaching this public repo.

  check_secrets.py --staged    what is about to be committed (pre-commit hook)
  check_secrets.py --pre-push  the commits about to be pushed, with their messages
  check_secrets.py --all       every commit on every branch (also run by CI)

Reports the file, line and rule, never the matched text, because this output can
end up in logs. Exits 1 if anything is found.

Besides the patterns below it looks for the exact values in firmware/include/secrets.h
and in .private-denylist (one value per line). Both are git-ignored, so the real
values never have to be written down in a tracked file.
Python standard library only.
"""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SECRETS = ROOT / "firmware/include/secrets.h"
DENYLIST = ROOT / ".private-denylist"
ZERO = "0" * 40

FORBIDDEN_FILES = re.compile(
    rb"(^|/)(secrets\.h|\.hue-backup\.json|\.private-denylist|\.env(\..*)?|id_(rsa|ed25519|ecdsa))$"
    rb"|\.(pem|key|p12|pfx)$"
)

PATTERNS = {
    "private IPv4 address": rb"\b(?:10|192\.168|172\.(?:1[6-9]|2\d|3[01]))(?:\.\d{1,3}){2,3}\b",
    "private IPv6 address": rb"\bfd[0-9a-f]{2}:[0-9a-f:]{4,}",
    "MAC address": rb"\b(?:[0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}\b",
    "UUID (Hue resource id)": rb"\b[0-9a-fA-F]{8}-(?:[0-9a-fA-F]{4}-){3}[0-9a-fA-F]{12}\b",
    "long hex id": rb"\b[0-9a-fA-F]{16,}\b",
    "API key or token": rb"\b(?=[A-Za-z0-9_-]*\d)(?=[A-Za-z0-9_-]*[A-Za-z])[A-Za-z0-9_-]{32,}\b",
    "known credential format": rb"ghp_[A-Za-z0-9]{20,}|github_pat_\w{20,}|sk-ant-[\w-]{20,}|AKIA[0-9A-Z]{16}",
    "private key": rb"BEGIN [A-Z ]*PRIVATE KEY",
    "home directory path": rb"/(?:home|Users)/[A-Za-z][\w.-]*",
    "email address": rb"[\w.+-]+@[\w-]+(?:\.[\w-]+)*\.[A-Za-z]{2,}",
}
PATTERNS = {name: re.compile(p) for name, p in PATTERNS.items()}

# Public addresses that are meant to appear. No personal address belongs here.
ALLOWED_EMAILS = {b"noreply@anthropic.com", b"git@github.com"}


def git(*args, stdin=None):
    return subprocess.run(["git", *args], cwd=ROOT, input=stdin, capture_output=True, check=True).stdout


def exact_values():
    values = set()
    if SECRETS.exists():
        values |= set(re.findall(rb'#define \w+ "([^"]+)"', SECRETS.read_bytes()))
    if DENYLIST.exists():
        values |= {v.strip() for v in DENYLIST.read_bytes().splitlines()}
    return {v.lower() for v in values if len(v) >= 4 and not v.startswith(b"your-")}


def scan_text(data, exact):
    """Yields (line number, rule) for each problem in one file or message."""
    lowered = data.lower()
    for value in exact:
        at = lowered.find(value)
        if at >= 0:
            yield data.count(b"\n", 0, at) + 1, "private value from secrets.h or .private-denylist"
    if b"\0" in data:  # binary: exact values only, patterns would just be noise
        return
    for name, pattern in PATTERNS.items():
        for m in pattern.finditer(data):
            if name == "email address" and m.group().lower() in ALLOWED_EMAILS:
                continue
            yield data.count(b"\n", 0, m.start()) + 1, name


def scan_file(where, path, data, exact):
    problems = []
    if FORBIDDEN_FILES.search(path):
        problems.append(f"{where}{path.decode(errors='replace')}: file must never be committed")
    for line, rule in scan_text(data, exact):
        problems.append(f"{where}{path.decode(errors='replace')}:{line}: {rule}")
    return problems


def scan_staged(exact):
    problems = []
    names = git("diff", "--cached", "--name-only", "--no-renames", "--diff-filter=ACM", "-z")
    for path in filter(None, names.split(b"\0")):
        data = git("show", b":" + path)
        problems += scan_file("", path, data, exact)
    return problems


def scan_commits(commits, exact):
    problems = []
    seen = set()
    for c in commits:
        message = git("log", "-1", "--format=%B", c)
        for line, rule in scan_text(message, exact):
            problems.append(f"{c[:8]} commit message, line {line}: {rule}")
        raw = git("diff-tree", "--root", "-r", "-m", "--no-commit-id", "--no-renames",
                  "--diff-filter=ACM", "-z", c)
        fields = raw.split(b"\0")
        for meta, path in zip(fields[::2], fields[1::2]):
            blob = meta.split()[3].decode()
            if (blob, path) in seen:
                continue
            seen.add((blob, path))
            problems += scan_file(f"{c[:8]} ", path, git("cat-file", "blob", blob), exact)
    return problems


def commits_being_pushed():
    commits = []
    for line in sys.stdin.read().splitlines():
        _, local, _, remote = line.split()
        if local == ZERO:  # deleting a branch
            continue
        spec = [local, "--not", "--remotes"] if remote == ZERO else [f"{remote}..{local}"]
        commits += git("rev-list", *spec).decode().split()
    return commits


def main():
    mode = sys.argv[1] if len(sys.argv) == 2 else ""
    exact = exact_values()
    if mode == "--staged":
        problems = scan_staged(exact)
    elif mode == "--pre-push":
        problems = scan_commits(commits_being_pushed(), exact)
    elif mode == "--all":
        problems = scan_commits(git("rev-list", "--all").decode().split(), exact)
    else:
        sys.exit(__doc__)
    if problems:
        print("BLOCKED: possible secret or personal information:", file=sys.stderr)
        for p in sorted(set(problems)):
            print(f"  {p}", file=sys.stderr)
        print("Remove it, then try again. See 'Secrets and personal information' in CLAUDE.md.",
              file=sys.stderr)
        sys.exit(1)
    print("Secret scan passed.")


if __name__ == "__main__":
    main()
