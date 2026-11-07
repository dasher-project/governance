#!/usr/bin/env python3
"""RFC 0022 item 5: regenerate ecosystem.json — the machine-readable status of
every Dasher v6 frontend (latest release + engine pin + how many engine
releases behind). Run by .github/workflows/ecosystem-status.yml (weekly + on
demand); the website can render a status table from this file.

Usage: scripts/gen-ecosystem-status.sh > ecosystem.json   (needs gh, git)
"""
import json
import subprocess
import sys
from datetime import datetime, timezone

ENGINE = "dasher-project/DasherCore"
FRONTENDS = {  # repo -> submodule path
    "dasher-android": "third_party/DasherCore",
    "dasher-gtk": "DasherCore",
    "dasher-windows": "DasherCore",
    "dasher-apple": "DasherCore",
    "dasher-web": "wasm-build/dashercore-src",
}


def gh(*args, check=True):
    r = subprocess.run(["gh", *args], capture_output=True, text=True)
    if check and r.returncode != 0:
        raise RuntimeError(f"gh {' '.join(args)}: {r.stderr.strip()}")
    return r.stdout.strip()


def api(path):
    return json.loads(gh("api", path))


def engine_tags():
    out = subprocess.run(
        ["git", "ls-remote", "--tags", "--sort=-v:refname",
         f"https://github.com/{ENGINE}.git", "v*"],
        capture_output=True, text=True, check=True).stdout
    tags = [line.split("refs/tags/")[1] for line in out.splitlines()
            if not line.rstrip().endswith("^{}")]
    return tags  # newest first


def main():
    tags = engine_tags()
    latest = tags[0]
    capi = None
    try:
        import base64
        hdr = base64.b64decode(api(f"repos/{ENGINE}/contents/src/dasher.h")["content"]).decode()
        import re
        m = re.search(r"#define\s+DASHER_CAPI_VERSION\s+(\d+)", hdr)
        capi = int(m.group(1)) if m else None
    except Exception as e:  # noqa: BLE001 — degrade, never fail the report
        print(f"warning: capi lookup failed: {e}", file=sys.stderr)

    frontends = {}
    for repo, sub in FRONTENDS.items():
        entry = {"latest": None, "engine_pin": "unknown", "behind": None}
        try:
            rel = api(f"repos/dasher-project/{repo}/releases/latest")
            entry["latest"] = rel.get("tag_name")
        except Exception:  # noqa: BLE001
            pass  # no releases yet
        try:
            pin_sha = api(f"repos/dasher-project/{repo}/contents/{sub}")["sha"]
            # Tag name if the pin is a tag; short sha otherwise
            try:
                entry["engine_pin"] = api(f"repos/{ENGINE}/git/tags/{pin_sha}")["tag"]
            except Exception:  # noqa: BLE001
                entry["engine_pin"] = f"git-{pin_sha[:10]}"
            # Engine commits between the pin and latest, via the compare API:
            # compare/{pin}...{latest} — ahead_by = commits `latest` has that
            # `pin` lacks (backwards-looking names; this is the drift number).
            cmp = api(f"repos/{ENGINE}/compare/{pin_sha}...{latest}")
            entry["behind"] = cmp.get("ahead_by")
        except Exception as e:  # noqa: BLE001
            print(f"warning: {repo}: {e}", file=sys.stderr)
        frontends[repo] = entry

    doc = {
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "engine": {"latest": latest, "capi_version": capi},
        "frontends": frontends,
    }
    json.dump(doc, sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()
