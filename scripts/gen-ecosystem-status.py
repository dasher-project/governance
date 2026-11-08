#!/usr/bin/env python3
"""RFC 0023 item 5: regenerate ecosystem.json — the machine-readable status of
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
ENGINE_PATHS = {  # repo -> DasherCore submodule path
    "dasher-android": "third_party/DasherCore",
    "dasher-gtk": "DasherCore",
    "dasher-windows": "DasherCore",
    "dasher-apple": "DasherCore",
    "dasher-web": "wasm-build/dashercore-src",
}

# RFC 0023 amendment (2026-11-08): the shared UI string catalogue.
# None = this frontend consumes no shared-resources submodule.
SHARED_PATHS = {
    "dasher-android": "shared-resources",
    "dasher-gtk": "shared-resources",
    "dasher-windows": "shared-resources",
    "dasher-apple": "SharedResources",
    "dasher-web": None,
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


def tag_map(repo_url):
    """sha → tag name for v* tags, via ls-remote.

    The gitlink sha a superproject records is the COMMIT sha, so for
    annotated tags map the peeled (^{}) sha, not the tag-object sha.
    Lightweight tags have no peeled line and map directly.
    """
    out = subprocess.run(
        ["git", "ls-remote", "--tags", repo_url, "v*"],
        capture_output=True, text=True, check=True).stdout
    shas, peels = {}, {}
    for line in out.splitlines():
        sha, ref = line.split("\t")
        tag = ref.split("refs/tags/")[1]
        if tag.endswith("^{}"):
            peels[tag[:-3]] = sha
        else:
            shas[tag] = sha
    return {peels.get(tag, sha): tag for tag, sha in shas.items()}


def main():
    tags = engine_tags()
    latest = tags[0]
    engine_map = tag_map(f"https://github.com/{ENGINE}.git")
    capi = None
    try:
        import base64
        hdr = base64.b64decode(api(f"repos/{ENGINE}/contents/src/dasher.h")["content"]).decode()
        import re
        m = re.search(r"#define\s+DASHER_CAPI_VERSION\s+(\d+)", hdr)
        capi = int(m.group(1)) if m else None
    except Exception as e:  # noqa: BLE001 — degrade, never fail the report
        print(f"warning: capi lookup failed: {e}", file=sys.stderr)

    dsr_latest = None
    dsr_map = {}
    try:
        dsr_sorted = subprocess.run(
            ["git", "ls-remote", "--tags", "--sort=-v:refname",
             "https://github.com/dasher-project/dasher-shared-resources.git", "v*"],
            capture_output=True, text=True, check=True).stdout
        dsr_lines = [l.split("refs/tags/")[1] for l in dsr_sorted.splitlines()
                     if not l.rstrip().endswith("^{}")]
        dsr_latest = dsr_lines[0] if dsr_lines else None
        dsr_map = tag_map("https://github.com/dasher-project/dasher-shared-resources.git")
    except Exception:
        pass

    frontends = {}
    for repo, sub in ENGINE_PATHS.items():
        entry = {"latest": None, "engine_pin": "unknown", "behind": None}
        try:
            rel = api(f"repos/dasher-project/{repo}/releases/latest")
            entry["latest"] = rel.get("tag_name")
        except Exception:  # noqa: BLE001
            pass  # no releases yet
        try:
            pin_sha = api(f"repos/dasher-project/{repo}/contents/{sub}")["sha"]
            # Tag name if the pin points at a tag (the ls-remote map handles
            # both lightweight and annotated tags); short sha otherwise.
            entry["engine_pin"] = engine_map.get(pin_sha) or f"git-{pin_sha[:10]}"
            # Engine commits between the pin and latest, via the compare API:
            # compare/{pin}...{latest} — ahead_by = commits `latest` has that
            # `pin` lacks (backwards-looking names; this is the drift number).
            cmp = api(f"repos/{ENGINE}/compare/{pin_sha}...{latest}")
            entry["behind"] = cmp.get("ahead_by")
        except Exception as e:  # noqa: BLE001
            print(f"warning: {repo}: {e}", file=sys.stderr)
        # Shared string catalogue pin + drift (RFC 0023 amendment)
        ssub = SHARED_PATHS.get(repo)
        if ssub:
            try:
                sha = api(f"repos/dasher-project/{repo}/contents/{ssub}")["sha"]
                pin = dsr_map.get(sha) or f"git-{sha[:10]}"
                entry["shared_resources_pin"] = pin
                if dsr_latest:
                    cmp2 = api(f"repos/dasher-project/dasher-shared-resources/compare/{sha}...{dsr_latest}")
                    entry["shared_resources_behind"] = cmp2.get("ahead_by")
            except Exception:  # noqa: BLE001
                pass
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
