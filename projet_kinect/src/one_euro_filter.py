"""
One Euro Filter for real-time signal smoothing.

Designed for human pose tracking: adapts cutoff frequency based on speed.
Slow movements are heavily smoothed, fast movements pass through with
minimal lag.

Reference: Casiez, Roussel, Vogel, 2012 -
  "1-Euro Filter: A Simple Speed-based Low-pass Filter for Noisy Input
   in Interactive Systems"
"""

import math
import time


class LowPassFilter(object):
    """Simple first-order low-pass filter."""

    def __init__(self, alpha=1.0):
        self._alpha = alpha
        self._y = None
        self._initialized = False

    def __call__(self, value, alpha=None):
        if alpha is not None:
            self._alpha = alpha
        if not self._initialized:
            self._y = value
            self._initialized = True
        else:
            self._y = self._alpha * value + (1.0 - self._alpha) * self._y
        return self._y

    @property
    def last(self):
        return self._y

    def reset(self):
        self._initialized = False
        self._y = None


class OneEuroFilter(object):
    """
    One Euro Filter for a single scalar signal.

    Parameters
    ----------
    freq : float
        Estimated signal frequency (Hz). Typically your FPS.
    min_cutoff : float
        Minimum cutoff frequency (Hz). Lower = more smoothing at rest.
    beta : float
        Speed coefficient. Higher = less lag on fast movements.
    d_cutoff : float
        Cutoff frequency for the derivative filter (Hz).
    """

    def __init__(self, freq=30.0, min_cutoff=1.0, beta=0.007, d_cutoff=1.0):
        self.freq = freq
        self.min_cutoff = min_cutoff
        self.beta = beta
        self.d_cutoff = d_cutoff
        self._x_filt = LowPassFilter()
        self._dx_filt = LowPassFilter()
        self._last_time = None

    @staticmethod
    def _alpha(cutoff, freq):
        tau = 1.0 / (2.0 * math.pi * cutoff)
        te = 1.0 / freq
        return 1.0 / (1.0 + tau / te)

    def __call__(self, x, t=None):
        if self._last_time is not None and t is not None:
            dt = t - self._last_time
            if dt > 1e-9:
                self.freq = 1.0 / dt
        self._last_time = t

        prev = self._x_filt.last
        dx = 0.0 if prev is None else (x - prev) * self.freq
        edx = self._dx_filt(dx, alpha=self._alpha(self.d_cutoff, self.freq))

        cutoff = self.min_cutoff + self.beta * abs(edx)
        return self._x_filt(x, alpha=self._alpha(cutoff, self.freq))

    def reset(self):
        self._x_filt.reset()
        self._dx_filt.reset()
        self._last_time = None


class OneEuroFilter3D(object):
    """
    One Euro Filter for a 3D point (x, y, z).

    Each axis is filtered independently.
    """

    def __init__(self, freq=30.0, min_cutoff=1.0, beta=0.007, d_cutoff=1.0):
        self._filters = [
            OneEuroFilter(freq, min_cutoff, beta, d_cutoff)
            for _ in range(3)
        ]

    def __call__(self, x, y, z, t=None):
        return (
            self._filters[0](x, t),
            self._filters[1](y, t),
            self._filters[2](z, t),
        )

    def reset(self):
        for f in self._filters:
            f.reset()


class PoseFilter(object):
    """
    One Euro Filter bank for a set of named 3D joints.

    Usage::

        pf = PoseFilter(freq=20, min_cutoff=1.5, beta=0.01)
        filtered_joints = pf.filter(joints_dict, timestamp)

    Each joint in ``joints_dict`` is a dict with keys x, y, z.
    Returns a new dict with the same structure, filtered.
    """

    def __init__(self, freq=20.0, min_cutoff=1.5, beta=0.01, d_cutoff=1.0):
        self.freq = freq
        self.min_cutoff = min_cutoff
        self.beta = beta
        self.d_cutoff = d_cutoff
        self._filters = {}

    def _ensure(self, name):
        if name not in self._filters:
            self._filters[name] = OneEuroFilter3D(
                self.freq, self.min_cutoff, self.beta, self.d_cutoff
            )

    def filter(self, joints, t=None):
        out = {}
        for name, pt in joints.items():
            self._ensure(name)
            fx, fy, fz = self._filters[name](
                float(pt["x"]), float(pt["y"]), float(pt["z"]), t
            )
            out[name] = {"x": fx, "y": fy, "z": fz}
        return out

    def reset(self):
        for f in self._filters.values():
            f.reset()
        self._filters.clear()
