"""The one-command path must work from a clean directory, with no docs read."""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _run(tmp_path, csv_text, *extra):
    p = tmp_path / "trades.csv"
    p.write_text(csv_text, encoding="utf-8")
    env = dict(os.environ)
    env["PYTHONPATH"] = ROOT
    return subprocess.run(
        [sys.executable, "-m", "auditkit.cli", str(p), *extra],
        cwd=str(tmp_path), env=env, capture_output=True, text=True, timeout=120,
    )


CLEAN = "date,equity\n" + "\n".join(
    "2021-%02d-%02d,%.2f" % (1 + i // 28, 1 + i % 28, 10000 * (1 + 0.0004 * i))
    for i in range(120)
)


def test_clean_series_runs_and_reports_three_checks(tmp_path):
    r = _run(tmp_path, CLEAN, "--trials", "20")
    out = r.stdout
    assert "look-ahead" in out
    assert "multiple testing" in out
    assert "out-of-sample decay" in out
    assert r.returncode in (0, 1, 2)


def test_without_trials_is_unverified_not_pass(tmp_path):
    r = _run(tmp_path, CLEAN)
    assert r.returncode == 2
    assert "UNVERIFIED" in r.stdout


def test_time_travel_fails_lookahead(tmp_path):
    rows = ["date,equity", "2021-01-05,101.0", "2021-01-04,102.0", "2021-01-06,103.0"]
    r = _run(tmp_path, "\n".join(rows) + "\n")
    assert "时间戳倒退" in r.stdout
    assert r.returncode == 1


def test_json_mode_has_all_verdicts(tmp_path):
    import json as _json
    r = _run(tmp_path, CLEAN, "--json", "--trials", "5")
    payload = _json.loads(r.stdout)
    assert set(payload["verdicts"]) == {"look-ahead", "multiple testing", "out-of-sample decay"}
