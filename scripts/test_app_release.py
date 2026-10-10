import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import app_release as ar

MANIFEST = json.dumps({"name": "Mixer", "id": "mixer", "version": "0.12.1",
                       "changelog": ["0.12.1: fixes the desk", "0.12.1 (merged 0.11.2): also this",
                                     "0.12.0: older", "0.12.10: a different version"]})


def test_read_manifest():
    assert ar.read_manifest(MANIFEST) == ("mixer", "Mixer", "0.12.1")


def test_read_manifest_refuses_a_prerelease_version():
    with pytest.raises(ar.Refused, match="X.Y.Z"):
        ar.read_manifest(json.dumps({"id": "m", "name": "M", "version": "0.12.1-rc1"}))


@pytest.mark.parametrize("bad_id", ["", "a\nb", "a b", "x$(id)", '"; rm', "../x", ".hidden"])
def test_read_manifest_refuses_an_id_that_is_unsafe_to_pass_on(bad_id):
    with pytest.raises(ar.Refused, match="id"):
        ar.read_manifest(json.dumps({"id": bad_id, "name": "M", "version": "1.0.0"}))


def test_read_manifest_refuses_a_missing_id_or_broken_json():
    with pytest.raises(ar.Refused, match="id"):
        ar.read_manifest(json.dumps({"name": "M", "version": "1.0.0"}))
    with pytest.raises(ar.Refused, match="JSON"):
        ar.read_manifest("{not json")


def test_library_json_must_agree():
    assert ar.check_library("0.12.1", None) is None
    assert ar.check_library("0.12.1", json.dumps({"version": "0.12.1"})) is None
    assert "0.12.0" in ar.check_library("0.12.1", json.dumps({"version": "0.12.0"}))


def test_newest_release_ignores_non_release_tags():
    assert ar.newest_release(["v0.11.0", "v0.12.0", "v0.12.1-rc1", "nightly"]) == (0, 12, 0)
    assert ar.newest_release([]) is None


def test_introducing_commit_is_the_oldest_of_the_newest_run():
    history = [("h3", "0.12.1"), ("h2", "0.12.1"), ("h1", "0.12.0"), ("h0", "0.12.1")]
    assert ar.introducing_commit(history, "0.12.1") == "h2"


def test_introducing_commit_refuses_when_head_is_another_version():
    with pytest.raises(ar.Refused, match="not version"):
        ar.introducing_commit([("h1", "0.12.0")], "0.12.1")


def test_notes_take_only_this_versions_entries():
    notes = ar.notes_for(json.loads(MANIFEST)["changelog"], "0.12.1")
    assert notes == "- 0.12.1: fixes the desk\n- 0.12.1 (merged 0.11.2): also this"


def test_existing_tag_on_ancestor_is_a_noop():
    d = ar.decide(version="0.12.1", tags=["v0.12.0", "v0.12.1"], tag_is_ancestor=True)
    assert d == ("noop", "v0.12.1 already released")


def test_existing_tag_elsewhere_fails():
    with pytest.raises(ar.Refused, match="not an ancestor"):
        ar.decide(version="0.12.1", tags=["v0.12.1"], tag_is_ancestor=False)


def test_version_must_be_above_the_newest_tag():
    with pytest.raises(ar.Refused, match="not above"):
        ar.decide(version="0.11.9", tags=["v0.12.0"], tag_is_ancestor=False)


def test_new_version_releases():
    assert ar.decide(version="0.12.1", tags=["v0.12.0"], tag_is_ancestor=False) == ("release", "v0.12.1")


def test_dispatch_sends_app_released_to_both_targets(monkeypatch):
    calls = []
    monkeypatch.setenv("GITHUB_REPOSITORY", "CrossPad/crosspad-mixer")
    monkeypatch.setenv("BOT_TOKEN", "t")
    monkeypatch.setattr(ar, "api", lambda method, path, token, body=None: calls.append((method, path, token, body)))
    assert ar.cmd_dispatch("mixer", "0.12.1", "abc") == 0
    assert [c[1] for c in calls] == ["/repos/CrossPad/crosspad-apps/dispatches",
                                     "/repos/CrossPad/platform-idf/dispatches"]
    assert all(c[0] == "POST" and c[2] == "t" for c in calls)
    assert calls[0][3] == {"event_type": "app-released",
                           "client_payload": {"repo": "CrossPad/crosspad-mixer", "app_id": "mixer",
                                              "version": "0.12.1", "sha": "abc", "tag": "v0.12.1"}}


def test_dispatch_tries_the_second_target_when_the_first_fails(monkeypatch):
    calls = []

    def api(method, path, token, body=None):
        calls.append(path)
        if "crosspad-apps" in path:
            raise ar.Refused("boom")

    monkeypatch.setenv("GITHUB_REPOSITORY", "CrossPad/crosspad-mixer")
    monkeypatch.setenv("BOT_TOKEN", "t")
    monkeypatch.setattr(ar, "api", api)
    with pytest.raises(ar.Refused, match="crosspad-apps"):
        ar.cmd_dispatch("mixer", "0.12.1", "abc")
    assert calls == ["/repos/CrossPad/crosspad-apps/dispatches", "/repos/CrossPad/platform-idf/dispatches"]


def _repo(tmp_path, monkeypatch, versions):
    """A repo with one crosspad-app.json commit per entry of versions, oldest first."""
    import subprocess
    env = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t",
           "GIT_COMMITTER_EMAIL": "t@t"}
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    monkeypatch.chdir(tmp_path)
    subprocess.run(["git", "init", "-q", "-b", "main"], check=True)
    shas = []
    for i, v in enumerate(versions):
        doc = {"id": "mixer", "name": "Mixer", "version": v, "changelog": [f"{v}: change {i}"]}
        Path("crosspad-app.json").write_text(json.dumps(doc))
        Path("other.txt").write_text(str(i))
        subprocess.run(["git", "add", "-A"], check=True)
        subprocess.run(["git", "commit", "-q", "-m", f"c{i}"], check=True)
        shas.append(subprocess.run(["git", "rev-parse", "HEAD"], check=True, capture_output=True,
                                   text=True).stdout.strip())
    return shas


def test_release_publishes_a_prerelease_at_the_introducing_commit(tmp_path, monkeypatch, capsys):
    shas = _repo(tmp_path, monkeypatch, ["0.12.0", "0.12.1", "0.12.1"])
    out = tmp_path / "out.txt"
    monkeypatch.setenv("GITHUB_OUTPUT", str(out))
    monkeypatch.setenv("GITHUB_REPOSITORY", "CrossPad/crosspad-mixer")
    monkeypatch.setenv("GITHUB_TOKEN", "t")
    calls = []
    monkeypatch.setattr(ar, "api", lambda method, path, token, body=None: calls.append((method, path, token, body)))
    assert ar.main(["release"]) == 0
    (method, path, token, body), = calls
    assert (method, path, token) == ("POST", "/repos/CrossPad/crosspad-mixer/releases", "t")
    assert body["tag_name"] == "v0.12.1" and body["target_commitish"] == shas[1]
    assert body["prerelease"] is True and body["draft"] is False
    assert body["body"] == "- 0.12.1: change 1"
    assert out.read_text().splitlines() == ["released=true", "app_id=mixer", "version=0.12.1", f"sha={shas[1]}"]


def test_release_is_a_noop_when_the_tag_is_already_below_head(tmp_path, monkeypatch):
    import subprocess
    _repo(tmp_path, monkeypatch, ["0.12.1", "0.12.1"])
    subprocess.run(["git", "tag", "v0.12.1", "HEAD~1"], check=True)
    out = tmp_path / "out.txt"
    monkeypatch.setenv("GITHUB_OUTPUT", str(out))
    monkeypatch.setattr(ar, "api", lambda *a, **k: pytest.fail("must not call the API"))
    assert ar.main(["release"]) == 0
    assert out.read_text() == "released=false\n"


def test_release_refuses_when_library_json_disagrees(tmp_path, monkeypatch, capsys):
    _repo(tmp_path, monkeypatch, ["0.12.1"])
    (tmp_path / "library.json").write_text(json.dumps({"version": "0.12.0"}))
    monkeypatch.setattr(ar, "api", lambda *a, **k: pytest.fail("must not call the API"))
    assert ar.main(["release"]) == 1
    assert "library.json" in capsys.readouterr().out
