from mmdistance.cluster import cluster_detections
from mmdistance.config import ClusterConfig, EgoConfig, TrackerConfig
from mmdistance.models import Detection
from mmdistance.pipeline import Pipeline
from mmdistance.simulate import approaching_car_frames
from mmdistance.tracker import FrontTargetTracker


def test_cluster_merges_nearby_car_points():
    dets = [
        Detection(x=0.1, y=12.0, z=0.4, vr=-5.0, snr_db=16),
        Detection(x=-0.2, y=12.3, z=0.3, vr=-4.8, snr_db=12),
        Detection(x=7.0, y=9.0, z=0.2, vr=0.0, snr_db=10),
    ]
    clusters = cluster_detections(dets, ClusterConfig(eps_m=1.2, min_points=1))
    assert len(clusters) == 2
    car = min(clusters, key=lambda item: item.range_m)
    assert car.n_points == 2
    assert 11.5 < car.y < 12.5


def test_tracker_holds_through_one_miss():
    tracker = FrontTargetTracker(TrackerConfig(min_hits=2, max_misses=3, gate_m=3.0))
    from mmdistance.cluster import _summarize

    cluster = _summarize([Detection(x=0, y=15, z=0.3, vr=-4, snr_db=14)])
    tracker.update([cluster], dt=0.05)
    tracks = tracker.update([cluster], dt=0.05)
    assert len(tracks) == 1
    tracks = tracker.update([], dt=0.05)
    assert len(tracks) == 1
    assert tracks[0].misses == 1
    assert tracks[0].confirmed


def test_pipeline_locks_approaching_car():
    pipe = Pipeline()
    last = None
    for frame in approaching_car_frames(n_frames=20, dt=0.05, start_range_m=20, vr=-6):
        last = pipe.process(frame, dt=0.05)
    assert last is not None
    assert last.primary is not None
    assert last.primary.range_m < 16
    assert last.primary.vr < -3
    assert last.filter_stats.n_out < last.filter_stats.n_in


def test_static_clutter_not_chosen_when_ego_moving():
    cfg_tracker = TrackerConfig(min_hits=2, gate_m=3)
    ego = EgoConfig(speed_mps=10.0, static_vr_tol_mps=1.0)
    tracker = FrontTargetTracker(cfg_tracker, ego)
    from mmdistance.cluster import _summarize

    sign = _summarize([Detection(x=0.2, y=8.0, z=0.5, vr=-10.0, snr_db=20)])
    car = _summarize([Detection(x=0.1, y=14.0, z=0.4, vr=-16.0, snr_db=15)])
    tracker.update([sign, car], dt=0.05)
    tracks = tracker.update([sign, car], dt=0.05)
    primary = tracker.select_primary(tracks)
    assert primary is not None
    assert primary.y > 10
