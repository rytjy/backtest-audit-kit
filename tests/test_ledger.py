"""Ledger audits: one command must work from the repo root, no docs read."""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _run(*args):
    env = dict(os.environ)
    env["PYTHONPATH"] = ROOT
    return subprocess.run(
        [sys.executable, "-m", "auditkit.ledger", *args],
        cwd=ROOT, env=env, capture_output=True, text=True, timeout=120,
    )


def test_batch_examples_from_repo_root():
    r = _run("batch", "examples/ledger/manifest.json")
    assert r.returncode == 0, r.stderr
    assert "批量审计 · 3 个数据集" in r.stdout
    assert "control-cost-free" in r.stdout
    assert "样本膨胀" in r.stdout
    assert "范围声明" in r.stdout


def test_run_marks_missing_inputs_unverified():
    r = _run("run", "examples/ledger/clustered.json")
    assert r.returncode == 0, r.stderr
    assert "look-ahead" in r.stdout
    assert "UNVERIFIED" in r.stdout


def test_relative_paths_resolve_against_manifest():
    r = _run("batch", "examples/ledger/manifest.json", "--json")
    assert r.returncode == 0, r.stderr
    assert '"kind": "ledger"' in r.stdout
