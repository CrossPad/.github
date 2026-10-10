#!/usr/bin/env python3
"""Tag an app version and publish it as a GitHub prerelease.

Run by .github/workflows/app-release.yml (reusable) inside the app repo's
checkout. Standard library and git only: it runs on the crosspad-light org
runner (no gh). It holds GITHUB_TOKEN and nothing else: app repos have no bot
key. The announcer Worker relays `app-released` to crosspad-apps and
platform-idf after `release.published`. Spec: platform-idf docs/superpowers/
specs/2026-10-10-release-automation-design.md, "CrossPad/.github".

  app_release.py release --event NAME --before SHA
      outputs released, app_id, version, sha to $GITHUB_OUTPUT

No backfill: while the repo has no vX.Y.Z tag, only a push that itself bumps the
version publishes (the existing versions get no tags, no burst of pings).
"""
import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request

NUM = r"(0|[1-9][0-9]*)"  # ASCII digits, no leading zeros
VERSION = re.compile(rf"{NUM}\.{NUM}\.{NUM}")
APP_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")
RELEASE_TAG = re.compile(rf"v{NUM}\.{NUM}\.{NUM}")
SHA = re.compile(r"[0-9a-f]{40,64}")


class Refused(Exception):
    pass


def _load_object(text: str, what: str) -> dict:
    try:
        doc = json.loads(text)
    except ValueError as e:
        raise Refused(f"{what} is not valid JSON: {e}") from e
    if not isinstance(doc, dict):
        raise Refused(f"{what} must be a JSON object")
    return doc


def read_manifest(text: str) -> tuple[str, str, str]:
    doc = _load_object(text, "crosspad-app.json")
    version = str(doc.get("version", ""))
    if not VERSION.fullmatch(version):
        raise Refused(f"crosspad-app.json version {version!r}: must be X.Y.Z (the app manager's release rule)")
    app_id = str(doc.get("id", ""))
    if not APP_ID.fullmatch(app_id):
        # The id goes to $GITHUB_OUTPUT (and on to the announcer), so no newlines or odd characters.
        raise Refused(f"crosspad-app.json id {app_id!r}: letters, digits, '.', '_' and '-' only")
    return app_id, str(doc.get("name") or app_id), version


def changelog_of(doc: dict) -> list[str]:
    entries = doc.get("changelog", [])
    if not isinstance(entries, list) or not all(isinstance(e, str) for e in entries):
        raise Refused("crosspad-app.json changelog must be a list of strings")
    return entries


def check_library(version: str, library_text: str | None) -> str | None:
    if library_text is None:
        return None
    lib = str(_load_object(library_text, "library.json").get("version", ""))
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


def _is_ancestor(commit: str, of: str) -> bool | None:
    """None when git cannot tell (an unknown object)."""
    rc = subprocess.run(["git", "merge-base", "--is-ancestor", commit, of], capture_output=True).returncode
    return {0: True, 1: False}.get(rc)


def first_release_skip(event: str, before: str, introduced_before) -> str | None:
    """Why the first release of a repo with no release tag must not happen, or None.

    Only a push that bumps the version may publish: the version's introducing
    commit must not be an ancestor of the push's `before`. introduced_before is
    called only when needed and returns True, False or None (git cannot tell).
    """
    if event != "push":
        return f"no vX.Y.Z tag yet and the event is {event or 'unknown'}, not a push: nothing released"
    if not before or set(before) == {"0"}:
        return "no vX.Y.Z tag yet and this push creates the branch: nothing released"
    was = introduced_before()
    if was is None:
        return "no vX.Y.Z tag yet and cannot tell whether this push bumped the version: nothing released"
    if was:
        return "no vX.Y.Z tag yet and the version was not bumped in this push: nothing released"
    return None


def _introducing_sha(version: str) -> str:
    shas = git("log", "--first-parent", "--format=%H", "--", "crosspad-app.json").split()
    history = []
    for sha in shas:
        v = _version_at(sha)
        history.append((sha, v))
        if v != version:
            break
    return introducing_commit(history, version)


def _version_at(sha: str) -> str | None:
    try:
        doc = json.loads(git("show", f"{sha}:crosspad-app.json"))
    except (subprocess.CalledProcessError, ValueError):
        return None
    return str(doc.get("version")) if isinstance(doc, dict) else None


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


def cmd_release(event: str, before: str) -> int:
    if before and not SHA.fullmatch(before):
        raise Refused(f"--before {before!r}: not a commit sha")
    app_id, name, version = read_manifest(open("crosspad-app.json", encoding="utf-8").read())
    lib = open("library.json", encoding="utf-8").read() if os.path.exists("library.json") else None
    problem = check_library(version, lib)
    if problem:
        raise Refused(problem)
    tags = git("tag", "-l", "v*").split()
    tag = f"v{version}"
    ancestor = tag in tags and _is_ancestor(f"refs/tags/{tag}", "HEAD") is True
    action, why = decide(version, tags, ancestor)
    if action == "release" and newest_release(tags) is None:
        action, why = "noop", first_release_skip(
            event, before, lambda: _is_ancestor(_introducing_sha(version), before)) or ""
        if not why:
            action = "release"
    if action == "noop":
        print(f"::notice::{why}" if why.startswith("no vX.Y.Z") else why)
        _output(released="false")
        return 0
    sha = _introducing_sha(version)
    changelog = changelog_of(_load_object(git("show", f"{sha}:crosspad-app.json"), "crosspad-app.json"))
    notes = notes_for(changelog, version) or f"{name} {version}"
    api("POST", f"/repos/{os.environ['GITHUB_REPOSITORY']}/releases", os.environ["GITHUB_TOKEN"],
        {"tag_name": tag, "target_commitish": sha, "name": f"{name} {version}", "body": notes,
         "draft": False, "prerelease": True})
    print(f"released {tag} at {sha}")
    _output(released="true", app_id=app_id, version=version, sha=sha)
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("release")
    r.add_argument("--event", required=True, help="github.event_name of the caller")
    r.add_argument("--before", required=True, help="github.event.before ('' outside a push)")
    ns = ap.parse_args(argv)
    try:
        return cmd_release(ns.event, ns.before)
    except (Refused, OSError, ValueError, subprocess.CalledProcessError) as e:
        print("::error::" + str(e).replace("\r", "").replace("\n", "%0A"))
        return 1


if __name__ == "__main__":
    sys.exit(main())
