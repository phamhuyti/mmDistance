from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Optional

from mmdistance.config import EgoConfig, TrackerConfig
from mmdistance.filters import is_static
from mmdistance.models import Cluster, Detection, Track


@dataclass
class _FilterState:
    r: float
    vr: float
    p_rr: float = 1.0
    p_rv: float = 0.0
    p_vr: float = 0.0
    p_vv: float = 1.0
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    snr_db: float = 0.0


@dataclass
class _InternalTrack:
    track_id: int
    state: _FilterState
    hits: int = 1
    misses: int = 0
    age: int = 1

    def snapshot(self, min_hits: int, static: bool) -> Track:
        st = self.state
        return Track(
            track_id=self.track_id,
            x=st.x,
            y=st.y,
            z=st.z,
            range_m=st.r,
            vr=st.vr,
            snr_db=st.snr_db,
            hits=self.hits,
            misses=self.misses,
            age=self.age,
            confirmed=self.hits >= min_hits,
            static=static,
        )


class FrontTargetTracker:
    """Nearest-neighbor tracks with a 2-state [range, vr] Kalman filter."""

    def __init__(self, cfg: TrackerConfig, ego: EgoConfig | None = None):
        self.cfg = cfg
        self.ego = ego or EgoConfig()
        self._tracks: list[_InternalTrack] = []
        self._next_id = 1

    def update(self, clusters: list[Cluster], dt: float | None = None) -> list[Track]:
        dt = self.cfg.default_dt if dt is None or dt <= 0 else dt
        for track in self._tracks:
            self._predict(track.state, dt)

        assigned: set[int] = set()
        used_clusters: set[int] = set()
        cost = []
        for t_index, track in enumerate(self._tracks):
            for c_index, cluster in enumerate(clusters):
                dist = math.hypot(track.state.x - cluster.x, track.state.y - cluster.y)
                if dist <= self.cfg.gate_m:
                    cost.append((dist, t_index, c_index))
        cost.sort()
        for _, t_index, c_index in cost:
            if t_index in assigned or c_index in used_clusters:
                continue
            assigned.add(t_index)
            used_clusters.add(c_index)
            self._correct(self._tracks[t_index], clusters[c_index])

        for t_index, track in enumerate(self._tracks):
            if t_index not in assigned:
                track.misses += 1
                track.age += 1

        for c_index, cluster in enumerate(clusters):
            if c_index in used_clusters:
                continue
            self._tracks.append(
                _InternalTrack(
                    track_id=self._next_id,
                    state=_FilterState(
                        r=cluster.range_m,
                        vr=cluster.vr,
                        x=cluster.x,
                        y=cluster.y,
                        z=cluster.z,
                        snr_db=cluster.snr_db,
                    ),
                )
            )
            self._next_id += 1

        self._tracks = [track for track in self._tracks if track.misses <= self.cfg.max_misses]
        return [track.snapshot(self.cfg.min_hits, self._is_static(track)) for track in self._tracks]

    def select_primary(self, tracks: list[Track]) -> Optional[Track]:
        candidates = [
            track
            for track in tracks
            if track.confirmed and not track.static and track.y > 0
        ]
        if not candidates:
            return None
        moving = [track for track in candidates if track.vr < -0.3]
        pool = moving or candidates
        return min(pool, key=lambda track: track.range_m)

    def _is_static(self, track: _InternalTrack) -> bool:
        state = track.state
        return is_static(
            Detection(x=state.x, y=state.y, z=state.z, vr=state.vr),
            self.ego,
        )

    def _predict(self, state: _FilterState, dt: float) -> None:
        q_r = self.cfg.process_var_range * dt
        q_v = self.cfg.process_var_vr * dt
        if state.r > 1e-3:
            ux, uy = state.x / state.r, state.y / state.r
        else:
            ux, uy = 0.0, 1.0
        state.r = max(0.0, state.r + state.vr * dt)
        state.x = ux * state.r
        state.y = uy * state.r
        p00, p01, p10, p11 = state.p_rr, state.p_rv, state.p_vr, state.p_vv
        state.p_rr = p00 + dt * (p10 + p01) + dt * dt * p11 + q_r
        state.p_rv = p01 + dt * p11
        state.p_vr = p10 + dt * p11
        state.p_vv = p11 + q_v

    def _correct(self, track: _InternalTrack, cluster: Cluster) -> None:
        track.hits += 1
        track.misses = 0
        track.age += 1
        state = track.state
        r_var = self.cfg.meas_var_range
        v_var = self.cfg.meas_var_vr

        k_r = state.p_rr / (state.p_rr + r_var)
        innov_r = cluster.range_m - state.r
        state.r += k_r * innov_r
        state.p_rr *= 1.0 - k_r
        state.p_rv *= 1.0 - k_r

        k_v = state.p_vv / (state.p_vv + v_var)
        innov_v = cluster.vr - state.vr
        state.vr += k_v * innov_v
        state.p_vv *= 1.0 - k_v
        state.p_vr *= 1.0 - k_v

        alpha = 0.4
        state.x = (1 - alpha) * state.x + alpha * cluster.x
        state.y = (1 - alpha) * state.y + alpha * cluster.y
        state.z = (1 - alpha) * state.z + alpha * cluster.z
        state.snr_db = cluster.snr_db
