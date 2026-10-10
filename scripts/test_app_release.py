import json
import subprocess
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


@pytest.mark.parametrize("text", ["[]", "42", '"x"', "null"])
def test_read_manifest_refuses_a_manifest_that_is_not_an_object(text):
    with pytest.raises(ar.Refused, match="object"):
        ar.read_manifest(text)


@pytest.mark.parametrize("version", ["01.2.3", "1.02.3", "1.2.03", "\u0661.2.3", "1.2", "v1.2.3"])
def test_read_manifest_refuses_leading_zeros_and_non_ascii_digits(version):
    with pytest.raises(ar.Refused, match="X.Y.Z"):
        ar.read_manifest(json.dumps({"id": "m", "name": "M", "version": version}))


def test_release_tags_with_leading_zeros_or_non_ascii_digits_are_ignored():
    assert ar.newest_release(["v01.2.3", "v\u0661.2.3", "v1.2.3"]) == (1, 2, 3)
    assert ar.newest_release(["v01.2.3"]) is None


@pytest.mark.parametrize("text", ["{not json", "[]", "null"])
def test_check_library_refuses_a_broken_library_json(text):
    with pytest.raises(ar.Refused, match="library.json"):
        ar.check_library("1.0.0", text)


def test_changelog_must_be_a_list_of_strings():
    assert ar.changelog_of({"changelog": ["1.0.0: a"]}) == ["1.0.0: a"]
    assert ar.changelog_of({}) == []
    for bad in ("1.0.0: a", [1, 2], ["1.0.0: a", None], {"a": "b"}):
        with pytest.raises(ar.Refused, match="changelog"):
            ar.changelog_of({"changelog": bad})


ZEROS = "0" * 40


def test_first_release_must_come_from_a_push_that_bumps_the_version():
    bumped = lambda: False  # noqa: E731 - the introducing commit is not in `before`
    assert ar.first_release_skip("push", "a" * 40, bumped) is None


def test_first_release_skipped_when_the_version_was_already_there():
    reason = ar.first_release_skip("push", "a" * 40, lambda: True)
    assert "not bumped" in reason


def test_first_release_skipped_on_workflow_dispatch():
    reason = ar.first_release_skip("workflow_dispatch", "", lambda: pytest.fail("not needed"))
    assert "workflow_dispatch" in reason


@pytest.mark.parametrize("before", ["", ZEROS])
def test_first_release_skipped_for_a_new_branch(before):
    reason = ar.first_release_skip("push", before, lambda: pytest.fail("not needed"))
    assert "creates the branch" in reason


def test_first_release_skipped_when_before_is_unknown_to_git():
    assert "cannot tell" in ar.first_release_skip("push", "a" * 40, lambda: None)


def test_before_must_be_a_hex_sha(capsys):
    assert ar.main(["release", "--event", "push", "--before=--upload-pack=x"]) == 1
    assert "::error::--before" in capsys.readouterr().out


def _repo(tmp_path, monkeypatch, versions):
    """A repo with one crosspad-app.json commit per entry of versions, oldest first."""
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


@pytest.fixture
def run(tmp_path, monkeypatch):
    """Run `release`; returns (exit code, API calls, GITHUB_OUTPUT lines)."""
    out = tmp_path.parent / (tmp_path.name + "-out.txt")
    monkeypatch.setenv("GITHUB_OUTPUT", str(out))
    monkeypatch.setenv("GITHUB_REPOSITORY", "CrossPad/crosspad-mixer")
    monkeypatch.setenv("GITHUB_TOKEN", "t")
    calls = []
    monkeypatch.setattr(ar, "api", lambda method, path, token, body=None: calls.append((method, path, token, body)))

    def go(event, before):
        rc = ar.main(["release", "--event", event, "--before", before])
        return rc, calls, (out.read_text().splitlines() if out.exists() else [])
    return go


def test_first_release_on_a_push_that_bumps_publishes_a_prerelease(tmp_path, monkeypatch, run):
    shas = _repo(tmp_path, monkeypatch, ["0.12.0", "0.12.1", "0.12.1"])
    rc, calls, out = run("push", shas[0])
    assert rc == 0
    (method, path, token, body), = calls
    assert (method, path, token) == ("POST", "/repos/CrossPad/crosspad-mixer/releases", "t")
    assert body["tag_name"] == "v0.12.1" and body["target_commitish"] == shas[1]
    assert body["prerelease"] is True and body["draft"] is False
    assert body["body"] == "- 0.12.1: change 1"
    assert out == ["released=true", "app_id=mixer", "version=0.12.1", f"sha={shas[1]}"]


def test_no_tags_and_no_bump_in_this_push_is_not_backfilled(tmp_path, monkeypatch, run, capsys):
    shas = _repo(tmp_path, monkeypatch, ["0.12.1", "0.12.1"])
    rc, calls, out = run("push", shas[0])  # the version was already there before this push
    assert (rc, calls, out) == (0, [], ["released=false"])
    assert "::notice::" in capsys.readouterr().out


def test_no_tags_workflow_dispatch_is_a_noop(tmp_path, monkeypatch, run, capsys):
    _repo(tmp_path, monkeypatch, ["0.12.0", "0.12.1"])
    rc, calls, out = run("workflow_dispatch", "")
    assert (rc, calls, out) == (0, [], ["released=false"])
    assert "::notice::" in capsys.readouterr().out


def test_no_tags_new_branch_push_is_a_noop(tmp_path, monkeypatch, run):
    _repo(tmp_path, monkeypatch, ["0.12.0", "0.12.1"])
    assert run("push", ZEROS) == (0, [], ["released=false"])


def test_no_tags_and_a_before_git_does_not_have_is_a_noop(tmp_path, monkeypatch, run):
    _repo(tmp_path, monkeypatch, ["0.12.0", "0.12.1"])
    assert run("push", "b" * 40) == (0, [], ["released=false"])


def test_once_a_release_tag_exists_a_dispatch_may_catch_up(tmp_path, monkeypatch, run):
    shas = _repo(tmp_path, monkeypatch, ["0.12.0", "0.12.1"])
    subprocess.run(["git", "tag", "v0.12.0", shas[0]], check=True)
    rc, calls, out = run("workflow_dispatch", "")
    assert rc == 0 and calls[0][3]["tag_name"] == "v0.12.1" and out[0] == "released=true"


def test_release_is_a_noop_when_the_tag_is_already_below_head(tmp_path, monkeypatch, run):
    shas = _repo(tmp_path, monkeypatch, ["0.12.1", "0.12.1"])
    subprocess.run(["git", "tag", "v0.12.1", shas[0]], check=True)
    assert run("push", shas[0]) == (0, [], ["released=false"])


def test_release_refuses_when_library_json_disagrees(tmp_path, monkeypatch, run, capsys):
    shas = _repo(tmp_path, monkeypatch, ["0.12.0", "0.12.1"])
    (tmp_path / "library.json").write_text(json.dumps({"version": "0.12.0"}))
    rc, calls, _ = run("push", shas[0])
    assert (rc, calls) == (1, [])
    assert "::error::" in capsys.readouterr().out


@pytest.mark.parametrize("manifest", ["{not json", "[]"])
def test_a_bad_manifest_is_a_clean_error_not_a_traceback(tmp_path, monkeypatch, run, capsys, manifest):
    shas = _repo(tmp_path, monkeypatch, ["0.12.0"])
    (tmp_path / "crosspad-app.json").write_text(manifest)
    rc, calls, _ = run("push", shas[0])
    assert (rc, calls) == (1, [])
    assert capsys.readouterr().out.startswith("::error::")


def test_a_missing_manifest_is_a_clean_error(tmp_path, monkeypatch, run, capsys):
    monkeypatch.chdir(tmp_path)
    rc, calls, _ = run("push", "a" * 40)
    assert (rc, calls) == (1, [])
    assert capsys.readouterr().out.startswith("::error::")


def test_a_committed_manifest_with_a_bad_changelog_is_a_clean_error(tmp_path, monkeypatch, run, capsys):
    shas = _repo(tmp_path, monkeypatch, ["0.11.0"])
    (tmp_path / "crosspad-app.json").write_text(
        json.dumps({"id": "mixer", "version": "0.12.0", "changelog": [1, 2]}))
    subprocess.run(["git", "commit", "-qam", "bad"], check=True)
    rc, calls, _ = run("push", shas[0])
    assert (rc, calls) == (1, [])
    out = capsys.readouterr().out
    assert out.startswith("::error::") and "changelog" in out
