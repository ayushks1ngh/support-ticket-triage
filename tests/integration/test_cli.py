import json
from pathlib import Path

from support_triage.cli import main


def test_offline_classify_cli(tmp_path: Path) -> None:
    source = tmp_path / "tickets.json"
    output = tmp_path / "results.json"
    source.write_text(
        '[{"ticket_id":"T","subject":"Password reset","body":"Cannot sign in"}]',
        encoding="utf-8",
    )
    assert main(["classify", "--input", str(source), "--output", str(output), "--offline"]) == 0
    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["results"][0]["category"] == "account_auth"


def test_cli_returns_nonzero_and_writes_errors(tmp_path: Path) -> None:
    source = tmp_path / "tickets.json"
    output = tmp_path / "results.json"
    source.write_text('[{"ticket_id":"T","subject":"","body":"x"}]', encoding="utf-8")
    assert main(["classify", "--input", str(source), "--output", str(output), "--offline"]) == 2
    assert len(json.loads(output.read_text(encoding="utf-8"))["errors"]) == 1
