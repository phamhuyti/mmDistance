from mmdistance.alerts import evaluate_alert
from mmdistance.config import AlertConfig, EgoConfig, read_ego_speed
from mmdistance.models import Track
from mmdistance.outputs import GpioAlertSink, SqliteSink
from mmdistance.pipeline import Pipeline
from mmdistance.simulate import approaching_car_frames


def _track(range_m: float) -> Track:
    return Track(track_id=1, x=0, y=range_m, z=0, range_m=range_m, vr=-4, snr_db=12, hits=4, confirmed=True)


def test_alert_bands():
    cfg = AlertConfig(enabled=True, warn_range_m=12, danger_range_m=6)
    assert evaluate_alert(None, cfg).level == "none"
    assert evaluate_alert(_track(20), cfg).level == "info"
    assert evaluate_alert(_track(10), cfg).level == "warn"
    assert evaluate_alert(_track(4), cfg).level == "danger"
    assert evaluate_alert(_track(4), AlertConfig(enabled=False)).level == "off"


def test_sqlite_and_gpio_sinks(tmp_path):
    db = tmp_path / "run.db"
    sqlite = SqliteSink(db)
    gpio = GpioAlertSink(AlertConfig(enabled=True, gpio_warn_pin=0, gpio_danger_pin=0))
    pipe = Pipeline()
    for frame in approaching_car_frames(n_frames=6, dt=0.05, start_range_m=8, vr=-4):
        result = pipe.process(frame, dt=0.05)
        sqlite.emit(result)
        gpio.emit(result)
    sqlite.close()
    import sqlite3

    rows = sqlite3.connect(db).execute("select count(*) from frames").fetchone()[0]
    assert rows == 6
    assert gpio.last_level in {"info", "warn", "danger"}


def test_ego_speed_file(tmp_path):
    path = tmp_path / "speed.txt"
    path.write_text("9.5\n")
    assert read_ego_speed(EgoConfig(speed_mps=0.0, speed_file=str(path))) == 9.5
