#!/usr/bin/env python3
"""Remove the PineApple-Pi login gate for local prototype mode.

Run from the repository root:
    python3 remove_login_v2.py

Designed for the compact backend/main.py layout using:
    def me(...)
    @app.get('/api/auth/status')
    def status(...)

Creates a timestamped backup and refuses partial matching.
"""
from pathlib import Path
from datetime import datetime, timezone
import ast
import re
import shutil
import sys

ROOT = Path.cwd()
MAIN = ROOT / "backend/main.py"
APPJS = ROOT / "frontend/assets/app.js"
INDEX = ROOT / "frontend/index.html"
ENV = ROOT / ".env"


def die(msg):
    print(f"[x] {msg}", file=sys.stderr)
    raise SystemExit(1)


def load(path):
    if not path.is_file():
        die(f"Missing required file: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def backup(paths):
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    base = ROOT / ".login-removal-backup" / stamp
    for path in paths:
        if path.exists():
            dst = base / path.relative_to(ROOT)
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, dst)
    return base


def patch_main(src):
    me_pattern = re.compile(
        r"^def me\(pineapple_session:str\|None=Cookie\(None,alias=settings\.cookie\)\):.*$",
        re.M,
    )
    status_pattern = re.compile(
        r"^def status\(pineapple_session:str\|None=Cookie\(None,alias=settings\.cookie\)\):.*$",
        re.M,
    )

    if len(me_pattern.findall(src)) != 1:
        die("Expected exactly one compact me() authentication function. No files changed.")
    if len(status_pattern.findall(src)) != 1:
        die("Expected exactly one compact auth status function. No files changed.")

    local_admin = (
        "{'id':0,'username':'local-prototype','role':'administrator','enabled':True}"
    )
    src = me_pattern.sub(
        "def me(pineapple_session:str|None=Cookie(None,alias=settings.cookie)):\n"
        "    # Prototype mode: authentication intentionally disabled.\n"
        f"    return {local_admin}",
        src,
    )
    src = status_pattern.sub(
        "def status(pineapple_session:str|None=Cookie(None,alias=settings.cookie)):\n"
        "    return {'setup_required':False,'authenticated':True,"
        "'user':{'username':'local-prototype','role':'administrator'}}",
        src,
    )

    # Keep setup/login/logout endpoints for compatibility, but normal navigation
    # no longer depends on them.
    ast.parse(src)
    return src


def patch_frontend(src):
    changes = 0
    replacements = (
        (r"setup_required\s*:\s*true", "setup_required: false"),
        (r"authenticated\s*:\s*false", "authenticated: true"),
        (r"state\.authenticated\s*=\s*false", "state.authenticated = true"),
    )
    for pattern, replacement in replacements:
        src, n = re.subn(pattern, replacement, src)
        changes += n

    marker = "/* PineApple-Pi local prototype no-login mode */"
    if marker not in src:
        src += f'''\n\n{marker}\nwindow.addEventListener("DOMContentLoaded", () => {{\n  const auth = document.querySelector("#auth, #authScreen, #login, #loginScreen, .auth-screen, .login-screen");\n  if (auth) auth.hidden = true;\n}});\n'''
        changes += 1
    return src, changes


def patch_index(src):
    count = 0
    for ident in ("auth", "authScreen", "login", "loginScreen"):
        pattern = re.compile(rf'(<[^>]+id=["\']{ident}["\'][^>]*)(>)', re.I)
        def repl(m):
            nonlocal count
            tag = m.group(1)
            if not re.search(r"\shidden(?:\s|=|$)", tag):
                tag += " hidden"
                count += 1
            return tag + m.group(2)
        src = pattern.sub(repl, src)
    return src, count


def patch_env():
    if not ENV.exists():
        return
    text = ENV.read_text(encoding="utf-8")
    if re.search(r"^AUTH_REQUIRED=", text, re.M):
        text = re.sub(r"^AUTH_REQUIRED=.*$", "AUTH_REQUIRED=false", text, flags=re.M)
    else:
        text += "\nAUTH_REQUIRED=false\n"
    # Keep AP changes disabled in no-login mode.
    if re.search(r"^ENABLE_AP_CHANGES=", text, re.M):
        text = re.sub(r"^ENABLE_AP_CHANGES=.*$", "ENABLE_AP_CHANGES=false", text, flags=re.M)
    else:
        text += "ENABLE_AP_CHANGES=false\n"
    ENV.write_text(text, encoding="utf-8")
    ENV.chmod(0o600)


def main():
    if not (ROOT / ".git").is_dir():
        die("Run this script from the PineApple-Pi Git repository root.")

    main_src = load(MAIN)
    js_src = load(APPJS)
    index_src = load(INDEX)

    new_main = patch_main(main_src)
    new_js, js_changes = patch_frontend(js_src)
    new_index, index_changes = patch_index(index_src)

    base = backup([MAIN, APPJS, INDEX, ENV])
    MAIN.write_text(new_main, encoding="utf-8")
    APPJS.write_text(new_js, encoding="utf-8")
    INDEX.write_text(new_index, encoding="utf-8")
    patch_env()

    print("[+] Login gate removed for local prototype mode")
    print("[+] /api/auth/status now reports authenticated=true")
    print("[+] Protected API dependencies receive a local administrator")
    print(f"[+] Frontend changes: {js_changes}")
    print(f"[+] Login containers hidden: {index_changes}")
    print(f"[+] Backup: {base}")
    print("[!] ENABLE_AP_CHANGES has been forced to false")
    print("[!] Anyone who can reach the dashboard can now open it")


if __name__ == "__main__":
    main()
