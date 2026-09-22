from mmdistance.config import EgoConfig, FilterConfig
from mmdistance.filters import apply_spatial_filter, is_static
from mmdistance.models import Detection


def test_lane_ground_and_snr_gates():
    cfg = FilterConfig(
        range_min_m=1,
        range_max_m=25,
        azimuth_max_deg=12,
        elevation_min_deg=-6,
        elevation_max_deg=8,
        snr_min_db=8,
    )
    detections = [
        Detection(x=0.2, y=10.0, z=0.3, vr=-4.0, snr_db=15),  # keep
        Detection(x=8.0, y=10.0, z=0.3, vr=-1.0, snr_db=15),  # wide azimuth
        Detection(x=0.2, y=10.0, z=-2.0, vr=0.0, snr_db=15),  # ground
        Detection(x=0.2, y=10.0, z=0.3, vr=-4.0, snr_db=3),  # weak
        Detection(x=0.2, y=-4.0, z=0.3, vr=1.0, snr_db=15),  # behind
        Detection(x=0.2, y=40.0, z=0.3, vr=-2.0, snr_db=15),  # too far
    ]
    kept, stats = apply_spatial_filter(detections, cfg)
    assert len(kept) == 1
    assert kept[0].y == 10.0
    assert stats.dropped_azimuth == 1
    assert stats.dropped_elevation == 1
    assert stats.dropped_snr == 1
    assert stats.dropped_behind == 1
    assert stats.dropped_range == 1


def test_static_matches_ego_speed_on_boresight():
    ego = EgoConfig(speed_mps=12.0, static_vr_tol_mps=0.8)
    sign = Detection(x=0.0, y=10.0, z=0.4, vr=-12.0, snr_db=18)
    car = Detection(x=0.0, y=10.0, z=0.4, vr=-18.0, snr_db=18)
    assert is_static(sign, ego)
    assert not is_static(car, ego)
