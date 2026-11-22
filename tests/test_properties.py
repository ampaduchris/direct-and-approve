"""Extraction properties (REQ-031 and REQ-039), with a fixed derandomised profile (REQ-122)."""

from __future__ import annotations

import json
import random
import tempfile
import tomllib
from pathlib import Path

import pytest
from hypothesis import HealthCheck, given, settings, strategies as st

from helpers import DATE, FX1, Fx, run, tree_hash

settings.register_profile("ci", derandomize=True, max_examples=25, deadline=None,
                          suppress_health_check=[HealthCheck.function_scoped_fixture])
settings.load_profile("ci")


def entries_toml(mapping_text: str, order: list[int], rep_order: list[int]) -> str:
    """The fixture mapping with its replacements and entries written in another order."""
    data = tomllib.loads(mapping_text)
    head = '[meta]\nschema = 1\noutput = "method"\nmanifest = "method/MANIFEST.json"\n\n'
    reps = "".join(
        f'[[replacement]]\nfrom = {json.dumps(r["from"])}\nto = {json.dumps(r["to"])}\n\n'
        for r in (data["replacement"][i] for i in rep_order)
    )
    ents = ""
    for e in (data["entry"][i] for i in order):
        ents += "[[entry]]\n" + "".join(f"{k} = {json.dumps(v)}\n" for k, v in e.items()) + "\n"
    pats = "[forbidden]\npatterns = " + json.dumps(data["forbidden"]["patterns"]) + "\n"
    return head + reps + ents + pats


@pytest.mark.req("REQ-031")
@given(st.randoms(use_true_random=False))
def test_order_of_entries_and_replacements_does_not_change_the_output(rnd: random.Random):
    with tempfile.TemporaryDirectory() as tmp:
        fx = Fx(Path(tmp))
        text = fx.mapping.read_text()
        data = tomllib.loads(text)
        assert fx.extract().returncode == 0
        want = tree_hash(fx.out)
        order = list(range(len(data["entry"])))
        reps = list(range(len(data["replacement"])))
        rnd.shuffle(order)
        rnd.shuffle(reps)
        fx.set_mapping(entries_toml(text, order, reps))
        assert fx.extract().returncode == 0
        assert tree_hash(fx.out) == want


WORDS = st.text(alphabet=st.sampled_from("abAB .\n-/"), min_size=0, max_size=40)


@pytest.mark.req("REQ-039")
@given(text=WORDS, froms=st.lists(st.text(alphabet="abAB", min_size=1, max_size=3), min_size=1, max_size=3, unique=True),
       tos=st.lists(st.text(alphabet="xyXY<>", min_size=0, max_size=4), min_size=3, max_size=3))
def test_an_output_that_is_accepted_is_a_fixed_point_of_the_mapping(text, froms, tos):
    """Either the run refuses (a from string survived) or extracting the output again changes nothing."""
    reps = [{"from": f, "to": t} for f, t in zip(froms, tos)]
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        a, b = base / "a", base / "b"
        for folder in (a, b):
            (folder / "control").mkdir(parents=True)
            (folder / "repo").mkdir()
        (a / "control/CLAUDE.md").write_text(text, encoding="utf-8")
        mapping = ('[meta]\nschema = 1\noutput = "method"\nmanifest = "method/MANIFEST.json"\n\n'
                   + "".join(f"[[replacement]]\nfrom = {json.dumps(r['from'])}\nto = {json.dumps(r['to'])}\n\n" for r in reps)
                   + '[[entry]]\nkind = "copy"\nsource = "CLAUDE.md"\ntarget = "method/CLAUDE.md"\nreplace = true\n\n'
                   + "[forbidden]\npatterns = []\n")
        for folder in (a, b):
            (folder / "repo/extract.toml").write_text(mapping)
        first = run("extract.py", a / "control", "--repo", a / "repo", "--date", DATE)
        if first.returncode == 3:
            return  # the mapping itself was rejected: a to string held a from string (REQ-039)
        if first.returncode == 2:
            return  # a from string was created across a boundary and the marker check caught it (REQ-033)
        assert first.returncode == 0, first.stderr
        out1 = (a / "repo/method/CLAUDE.md").read_bytes()
        (b / "control/CLAUDE.md").write_bytes(out1)
        second = run("extract.py", b / "control", "--repo", b / "repo", "--date", DATE)
        assert second.returncode == 0, second.stderr
        assert (b / "repo/method/CLAUDE.md").read_bytes() == out1


@pytest.mark.req("REQ-039")
@given(froms=st.lists(st.text(alphabet="abc", min_size=1, max_size=4), min_size=1, max_size=3, unique=True),
       to=st.text(alphabet="abcx", min_size=0, max_size=6))
def test_load_rejects_exactly_the_mappings_where_a_to_contains_a_from(froms, to):
    import extract

    reps = [{"from": f, "to": "<ok>"} for f in froms]
    reps[0] = {"from": froms[0], "to": to}
    contains = any(f in to for f in froms)
    problems = extract.check_replacements(reps)
    assert bool(problems) == contains
