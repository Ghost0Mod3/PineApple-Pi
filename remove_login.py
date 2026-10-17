#!/usr/bin/env python3
"""Safely remove PineApple-Pi's login gate from a supported repository checkout.

Run from the repository root:
    python3 remove_login.py

The script creates a timestamped backup under .login-removal-backup/ before
changing files. It refuses to modify files when the expected structures are
not found.
"""
from __future__ import annotations

import ast
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path.cwd()
BACKEND = ROOT / "backend" / "main.py"
FRONTEND = ROOT / "frontend" / "assets" / "app.js"
INDEX = ROOT / "frontend" / "index.html"
ENV = ROOT / ".env"

AUTH_FUNCTION_NAMES = {
    "current_user",
    "get_current_user",
    "require_user",
    "require_auth",
    "require_admin",
    "authenticated_user",
}


def fail(message: str) -> None:
    print(f"[x] {message}", file=sys.stderr)
    raise SystemExit(1)


def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        fail(f"Missing required file: {path.relative_to(ROOT)}")


def backup(paths: list[Path]) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dest = ROOT / ".login-removal-backup" / stamp
    for path in paths:
        if path.exists():
            target = dest / path.relative_to(ROOT)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
    return dest


def find_function_span(source: str, name: str) -> tuple[int, int, str] | None:
    tree = ast.parse(source)
    lines = source.splitlines(keepends=True)
    offsets = [0]
    for line in lines:
        offsets.append(offsets[-1] + len(line))
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            start = offsets[node.lineno - 1]
            end = offsets[node.end_lineno]
            indent = " " * node.col_offset
            return start, end, indent
    return None


def patch_backend(source: str) -> tuple[str, str]:
    # Prefer replacing a known authentication dependency with a synthetic local admin.
    for name in AUTH_FUNCTION_NAMES:
        span = find_function_span(source, name)
        if not span:
            continue
        start, end, indent = span
        original = source[start:end]
        first_line = original.splitlines()[0]
        is_async = first_line.lstrip().startswith("async def")
        signature = first_line.strip()
        # Preserve the existing signature so FastAPI dependency wiring remains valid.
        replacement = (
            f"{indent}{signature}\n"
            f"{indent}    # Prototype mode: dashboard authentication intentionally disabled.\n"
            f"{indent}    return {{\"id\": 0, \"username\": \"local-prototype\", "
            f"\"role\": \"administrator\", \"enabled\": True}}\n"
        )
        return source[:start] + replacement + source[end:], name

    # Some builds use a dependency named get_user_from_session.
    for name in ("get_user_from_session", "session_user"):
        span = find_function_span(source, name)
        if span:
            start, end, indent = span
            original = source[start:end]
            signature = original.splitlines()[0].strip()
            replacement = (
                f"{indent}{signature}\n"
                f"{indent}    return {{\"id\": 0, \"username\": \"local-prototype\", "
                f"\"role\": \"administrator\", \"enabled\": True}}\n"
            )
            return source[:start] + replacement + source[end:], name

    fail("No supported backend authentication function was found. No files were changed.")


def patch_frontend(source: str) -> tuple[str, int]:
    changed = 0
    patterns = [
        # Common state toggles in the PineApple-Pi prototypes.
        (r"showAuth\(\s*\)", "showDashboard()"),
        (r"showLogin\(\s*\)", "showDashboard()"),
        (r"renderLogin\(\s*\)", "renderDashboard()"),
        (r"state\.authenticated\s*=\s*false", "state.authenticated = true"),
        (r"authenticated\s*:\s*false", "authenticated: true"),
        (r"isAuthenticated\s*:\s*false", "isAuthenticated: true"),
    ]
    result = source
    for pattern, replacement in patterns:
        result, count = re.subn(pattern, replacement, result)
        changed += count

    # Do not require a frontend match if the backend dependency was patched. Add a
    # load-time fallback that hides common auth containers and reveals the app.
    marker = "/* PineApple-Pi prototype no-login mode */"
    if marker not in result:
        result += f'''\n\n{marker}\nwindow.addEventListener("DOMContentLoaded", () => {{\n  const auth = document.querySelector("#auth, #authScreen, #login, #loginScreen, .auth-screen, .login-screen");\n  const app = document.querySelector("#app, #dashboard, #mainApp, .dashboard-shell, .app-shell");\n  if (auth) auth.hidden = true;\n  if (app) {{ app.hidden = false; app.style.display = ""; }}\n}});\n'''
        changed += 1
    return result, changed


def patch_index(source: str) -> tuple[str, int]:
    changed = 0
    result = source
    # Hide common login containers at initial render while retaining markup for rollback.
    for ident in ("auth", "authScreen", "login", "loginScreen"):
        pattern = rf'(<[^>]+id=["\']{ident}["\'][^>]*)(>)'
        def repl(match: re.Match[str]) -> str:
            nonlocal changed
            tag = match.group(1)
            if " hidden" not in tag:
                changed += 1
                tag += " hidden"
            return tag + match.group(2)
        result = re.sub(pattern, repl, result, flags=re.I)
    return result, changed


def patch_env() -> None:
    if not ENV.exists():
        return
    text = read(ENV)
    if re.search(r"^AUTH_REQUIRED=", text, flags=re.M):
        text = re.sub(r"^AUTH_REQUIRED=.*$", "AUTH_REQUIRED=false", text, flags=re.M)
    else:
        text += "\nAUTH_REQUIRED=false\n"
    ENV.write_text(text, encoding="utf-8")
    ENV.chmod(0o600)


def validate_python(source: str) -> None:
    ast.parse(source)


def main() -> None:
    if not (ROOT / ".git").exists():
        fail("Run this script from the PineApple-Pi Git repository root.")

    backend_source = read(BACKEND)
    frontend_source = read(FRONTEND)
    index_source = read(INDEX)

    patched_backend, auth_name = patch_backend(backend_source)
    patched_frontend, frontend_changes = patch_frontend(frontend_source)
    patched_index, index_changes = patch_index(index_source)
    validate_python(patched_backend)

    backup_dir = backup([BACKEND, FRONTEND, INDEX, ENV])
    BACKEND.write_text(patched_backend, encoding="utf-8")
    FRONTEND.write_text(patched_frontend, encoding="utf-8")
    INDEX.write_text(patched_index, encoding="utf-8")
    patch_env()

    print("[+] Login gate removed for local prototype mode")
    print(f"[+] Backend function patched: {auth_name}")
    print(f"[+] Frontend changes: {frontend_changes}")
    print(f"[+] Initial login containers hidden: {index_changes}")
    print(f"[+] Backup created: {backup_dir}")
    print("[!] Anyone who can reach the dashboard can now use it.")
    print("[!] Keep ENABLE_AP_CHANGES=false while the AP is open or power is unstable.")


if __name__ == "__main__":
    main()
