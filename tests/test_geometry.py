from mmdistance.config import MountConfig
from mmdistance.geometry import transform_detection
from mmdistance.models import Detection
from mmdistance.pipeline import Pipeline
from mmdistance.simulate import static_target_frames


def test_positive_yaw_moves_boresight_to_the_right():
    det = Detection(x=0.0, y=10.0, z=0.0, vr=-1.0)
    out = transform_detection(det, MountConfig(yaw_deg=10.0))
    assert out.x > 1.5
    assert out.y > 9.5


def test_positive_pitch_moves_boresight_up():
    det = Detection(x=0.0, y=10.0, z=0.0, vr=-1.0)
    out = transform_detection(det, MountConfig(pitch_deg=8.0))
    assert out.z > 1.0
    assert out.y > 9.5


def test_identity_mount_keeps_points():
    det = Detection(x=0.4, y=7.0, z=0.2, vr=0.1, snr_db=12)
    out = transform_detection(det, MountConfig())
    assert abs(out.x - 0.4) < 1e-9
    assert abs(out.y - 7.0) < 1e-9


def test_pipeline_applies_yaw_before_lane_filter():
    cfg_pipe = Pipeline()
    cfg_pipe.cfg.mount.yaw_deg = 25.0
    cfg_pipe.cfg.filter.azimuth_max_deg = 12.0
    last = None
    for frame in static_target_frames(range_m=10.0, n_frames=4):
        last = cfg_pipe.process(frame, dt=0.05)
    assert last is not None
    assert last.filter_stats.dropped_azimuth >= 1
    assert last.filter_stats.n_out == 0
