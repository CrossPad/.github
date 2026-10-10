#!/usr/bin/env python3
"""Tag and publish an app version, then tell crosspad-apps and platform-idf.

Run by .github/workflows/app-release.yml (reusable) inside the app repo's
checkout. Standard library and git only: it runs on the crosspad-light org
runner (no gh). Spec: platform-idf docs/superpowers/specs/2026-10-10-release-
automation-design.md, "CrossPad/.github".

  app_release.py release     # GITHUB_TOKEN; outputs released, app_id, version, sha
  app_release.py dispatch --app-id ID --version V --sha SHA   # BOT_TOKEN
"""
import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request

VERSION = re.compile(r"\d+\.\d+\.\d+")
APP_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")
RELEASE_TAG = re.compile(r"v(\d+)\.(\d+)\.(\d+)")
DISPATCH_TARGETS = ("CrossPad/crosspad-apps", "CrossPad/platform-idf")


class Refused(Exception):
    pass


def read_manifest(text: str) -> tuple[str, str, str]:
    try:
        doc = json.loads(text)
    except ValueError as e:
        raise Refused(f"crosspad-app.json is not valid JSON: {e}") from e
    version = str(doc.get("version", ""))
    if not VERSION.fullmatch(version):
        raise Refused(f"crosspad-app.json version {version!r}: must be X.Y.Z (the app manager's release rule)")
    app_id = str(doc.get("id", ""))
    if not APP_ID.fullmatch(app_id):
        # The id is passed on to the next steps and to the dispatch payload.
        raise Refused(f"crosspad-app.json id {app_id!r}: letters, digits, '.', '_' and '-' only")
    return app_id, doc.get("name", app_id), version


def check_library(version: str, library_text: str | None) -> str | None:
    if library_text is None:
        return None
    lib = str(json.loads(library_text).get("version", ""))
    return None if lib == version else f"library.json version {lib} differs from crosspad-app.json {version}"


def newest_release(tags) -> tuple[int, int, int] | None:
    vs = [tuple(int(x) for x in m.groups()) for m in map(RELEASE_TAG.fullmatch, tags) if m]
    return max(vs) if vs else None


def decide(version: str, tags, tag_is_ancestor: bool) -> tuple[str, str]:
    tag = f"v{version}"
    if tag in tags:
        if tag_is_ancestor:
            return "noop", f"{tag} already released"
        raise Refused(f"{tag} exists and is not an ancestor of this commit")
    newest = newest_release(tags)
    mine = tuple(int(x) for x in version.split("."))
    if newest is not None and mine <= newest:
        raise Refused(f"{version} is not above the newest release v{'.'.join(map(str, newest))}")
    return "release", tag


def introducing_commit(history, version: str) -> str:
    """history: [(sha, version-or-None)], newest first, first-parent."""
    pick = None
    for sha, v in history:
        if v != version:
            break
        pick = sha
    if pick is None:
        raise Refused(f"HEAD's crosspad-app.json is not version {version}")
    return pick


def notes_for(changelog, version: str) -> str:
    pat = re.compile(rf"{re.escape(version)}(?=[:\s(])")
    return "\n".join(f"- {e}" for e in changelog if pat.match(e))


def git(*args: str) -> str:
    return subprocess.run(["git", *args], check=True, capture_output=True, text=True).stdout


def _version_at(sha: str) -> str | None:
    try:
        return str(json.loads(git("show", f"{sha}:crosspad-app.json")).get("version"))
    except (subprocess.CalledProcessError, ValueError):
        return None


def api(method: str, path: str, token: str, body=None):
    req = urllib.request.Request(f"https://api.github.com{path}", method=method,
                                 data=None if body is None else json.dumps(body).encode(),
                                 headers={"Authorization": f"Bearer {token}",
                                          "Accept": "application/vnd.github+json",
                                          "User-Agent": "crosspad-app-release"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read()
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        raise Refused(f"{method} {path}: HTTP {e.code}: {e.read().decode(errors='replace')[:300]}") from e
    except urllib.error.URLError as e:
        raise Refused(f"{method} {path}: {e.reason}") from e


def _output(**kv) -> None:
    path = os.environ.get("GITHUB_OUTPUT")
    if path:
        with open(path, "a", encoding="utf-8") as f:
            for k, v in kv.items():
                f.write(f"{k}={v}\n")


def cmd_release() -> int:
    app_id, name, version = read_manifest(open("crosspad-app.json", encoding="utf-8").read())
    lib = open("library.json", encoding="utf-8").read() if os.path.exists("library.json") else None
    problem = check_library(version, lib)
    if problem:
        raise Refused(problem)
    tags = git("tag", "-l", "v*").split()
    tag = f"v{version}"
    ancestor = tag in tags and subprocess.run(
        ["git", "merge-base", "--is-ancestor", f"refs/tags/{tag}", "HEAD"]).returncode == 0
    action, why = decide(version, tags, ancestor)
    if action == "noop":
        print(why)
        _output(released="false")
        return 0
    shas = git("log", "--first-parent", "--format=%H", "--", "crosspad-app.json").split()
    history = []
    for sha in shas:
        v = _version_at(sha)
        history.append((sha, v))
        if v != version:
            break
    sha = introducing_commit(history, version)
    changelog = json.loads(git("show", f"{sha}:crosspad-app.json")).get("changelog", [])
    notes = notes_for(changelog, version) or f"{name} {version}"
    api("POST", f"/repos/{os.environ['GITHUB_REPOSITORY']}/releases", os.environ["GITHUB_TOKEN"],
        {"tag_name": tag, "target_commitish": sha, "name": f"{name} {version}", "body": notes,
         "draft": False, "prerelease": True})
    print(f"released {tag} at {sha}")
    _output(released="true", app_id=app_id, version=version, sha=sha)
    return 0


def cmd_dispatch(app_id: str, version: str, sha: str) -> int:
    payload = {"repo": os.environ["GITHUB_REPOSITORY"], "app_id": app_id, "version": version,
               "sha": sha, "tag": f"v{version}"}
    failed = []
    for target in DISPATCH_TARGETS:
        try:
            api("POST", f"/repos/{target}/dispatches", os.environ["BOT_TOKEN"],
                {"event_type": "app-released", "client_payload": payload})
            print(f"dispatched app-released to {target}")
        except Refused as e:  # one target down must not starve the other
            failed.append(f"{target}: {e}")
    if failed:
        raise Refused("; ".join(failed))
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("release")
    d = sub.add_parser("dispatch")
    d.add_argument("--app-id", required=True)
    d.add_argument("--version", required=True)
    d.add_argument("--sha", required=True)
    ns = ap.parse_args(argv)
    try:
        return cmd_release() if ns.cmd == "release" else cmd_dispatch(ns.app_id, ns.version, ns.sha)
    except Refused as e:
        print(f"::error::{e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
