"""Artifact store: versioning, metadata, rollback, idempotent scoring."""

from engine.artifact import PROMOTED, DRAFT, ROLLED_BACK


def test_create_add_version_get(store):
    store.create("skill", "s", "v1 content")
    store.add_version("skill", "s", "v2 content", parent=1)

    meta = store.meta("skill", "s")
    assert [m["version"] for m in meta] == [1, 2]
    assert meta[1]["parent"] == 1

    latest = store.get("skill", "s")
    assert latest["content"] == "v2 content"
    assert latest["version"] == 2

    old = store.get_version("skill", "s", 1)
    assert old["content"] == "v1 content"


def test_rollback_path(store):
    store.create("skill", "s", "a")
    store.add_version("skill", "s", "b")
    assert store.get("skill", "s")["content"] == "b"
    # rollback = read parent version + add as new version
    parent = store.get_version("skill", "s", 1)
    store.add_version("skill", "s", parent["content"], parent=1)
    assert store.get("skill", "s")["content"] == "a"


def test_status_transitions(store):
    store.create("prompt", "p", "x")
    store.set_status("prompt", "p", 1, PROMOTED)
    assert store.meta("prompt", "p")[0]["status"] == PROMOTED
    store.set_status("prompt", "p", 1, ROLLED_BACK)
    assert store.meta("prompt", "p")[0]["status"] == ROLLED_BACK


def test_set_score_idempotent(store):
    store.create("rule", "r", "x")
    store.set_score("rule", "r", 1, 0.9, {"a": 1.0}, ["t1"])
    store.set_score("rule", "r", 1, 0.95, {"a": 1.0, "b": 0.5}, ["t1", "t2"])
    meta = store.meta("rule", "r")
    assert meta[0]["score"] == 0.95
    assert len(meta) == 1  # no duplicate versions
    assert meta[0]["grades"] == {"a": 1.0, "b": 0.5}


def test_bad_kind_rejected(store):
    import pytest as _pt
    with _pt.raises(ValueError):
        store.create("weights", "m", "x")


def test_list(store):
    store.create("skill", "s", "a")
    store.create("prompt", "p", "b")
    rows = store.list()
    assert len(rows) == 2
    assert {r["id"] for r in rows} == {"s", "p"}


def test_get_nonexistent_does_not_create_dir(store):
    res = store.get("skill", "ghost-artifact")
    assert res is None
    ghost_dir = store.root / "skill" / "ghost-artifact"
    assert not ghost_dir.exists()
