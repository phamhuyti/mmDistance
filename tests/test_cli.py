import json

from mmdistance.cli import main
from mmdistance.config import AppConfig


def test_default_config_roundtrip(tmp_path):
    src = tmp_path / "cfg.toml"
    src.write_text("[filter]\nazimuth_max_deg = 9.5\n")
    cfg = AppConfig.load(src)
    assert cfg.filter.azimuth_max_deg == 9.5
    assert cfg.radar.data_baud == 921600


def test_simulate_cli_emits_json_and_locks_target(capsys):
    assert main(["simulate", "--frames", "16"]) == 0
    out = capsys.readouterr().out.strip().splitlines()
    assert len(out) == 16
    last = json.loads(out[-1])
    assert last["primary"] is not None
    assert last["primary"]["range_m"] < 20
    assert last["n_filtered"] <= last["n_raw"]
