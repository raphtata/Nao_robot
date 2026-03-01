# -*- coding: utf-8 -*-
"""Mapping from 3D world landmarks (metres, hip-centred) to NAO joint angles.

MediaPipe world-landmark coordinate system:
  x : positive = right of image (subject's left)
  y : positive = UP
  z : positive = towards camera

Reliable DOFs from a single webcam (3 per arm + head):
  ShoulderPitch, ShoulderRoll, ElbowRoll
  HeadYaw, HeadPitch

ElbowYaw is locked to 0 because it requires precise forearm rotation
around the upper-arm axis, which a single 2D camera cannot estimate.
"""

import math


# ---------------------------------------------------------------------------
# NAO joint limits (radians)
# ---------------------------------------------------------------------------

JOINT_LIMITS = {
    "HeadYaw": (-2.0, 2.0),
    "HeadPitch": (-0.6, 0.5),
    "LShoulderPitch": (-1.5, 1.5),
    "LShoulderRoll": (-0.3, 1.3),
    "LElbowYaw": (-2.0, 2.0),
    "LElbowRoll": (-1.5, -0.03),
    "RShoulderPitch": (-1.5, 1.5),
    "RShoulderRoll": (-1.3, 0.3),
    "RElbowYaw": (-2.0, 2.0),
    "RElbowRoll": (0.03, 1.5),
}


# ---------------------------------------------------------------------------
# Vector helpers
# ---------------------------------------------------------------------------

def _clamp(value, low, high):
    return max(low, min(high, value))


def _vec(a, b):
    """Return vector from point a to point b."""
    return (b["x"] - a["x"], b["y"] - a["y"], b["z"] - a["z"])


def _norm3(v):
    mag = math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])
    if mag < 1e-6:
        return (0.0, 1.0, 0.0)
    return (v[0] / mag, v[1] / mag, v[2] / mag)


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _safe_get(joints, name):
    p = joints.get(name)
    if not p:
        raise KeyError("Missing joint: %s" % name)
    return p


# ---------------------------------------------------------------------------
# Shoulder pitch from 3D world points
# ---------------------------------------------------------------------------

def _shoulder_pitch_3d(shoulder, elbow):
    """Compute NAO shoulder pitch from 3D world coordinates.

    Runtime-calibrated convention for these landmarks:
      - elbow above shoulder  -> dy < 0 -> negative pitch (arm up)
      - elbow below shoulder  -> dy > 0 -> positive pitch (arm down)

    z-towards-camera: arm forward -> dz > 0 -> keeps pitch near 0
    Backward-guard: dz < 0 clamped to 0 so arm never swings behind.
    """
    dy = float(elbow["y"] - shoulder["y"])
    dz = float(elbow["z"] - shoulder["z"])
    forward_depth = max(dz, 0.0)
    return math.atan2(dy, forward_depth + 1e-4)


def _shoulder_roll_3d(shoulder, elbow, sign=1.0):
    """Compute NAO shoulder roll from 3D world coordinates.

    Measures how far the arm is abducted (moved away from the body).
    sign = +1 for left arm, -1 for right arm.
    """
    dx = float(elbow["x"] - shoulder["x"])
    dy = float(elbow["y"] - shoulder["y"])
    dz = float(elbow["z"] - shoulder["z"])
    lateral = abs(dx)
    vertical = math.sqrt(dy * dy + dz * dz)
    roll = math.atan2(lateral, max(1e-6, vertical))
    return sign * roll


# ---------------------------------------------------------------------------
# Elbow flexion (roll) from 3D world points
# ---------------------------------------------------------------------------

def _elbow_flexion_3d(shoulder, elbow, wrist):
    """Angle between upper and lower arm segments (always positive)."""
    upper = _norm3(_vec(shoulder, elbow))
    lower = _norm3(_vec(elbow, wrist))
    cos_angle = _clamp(_dot(upper, lower), -1.0, 1.0)
    return math.acos(cos_angle)


# ---------------------------------------------------------------------------
# Main conversion
# ---------------------------------------------------------------------------

def skeleton_to_nao_angles(joints):
    """Convert 3D world-landmark skeleton to NAO joint angles.

    Expects joints dict with keys:
      head, neck,
      shoulder_left, elbow_left, wrist_left,
      shoulder_right, elbow_right, wrist_right

    Each joint has {"x": float, "y": float, "z": float} in metres (y-UP).
    """
    head = _safe_get(joints, "head")
    neck = _safe_get(joints, "neck")

    sl = _safe_get(joints, "shoulder_left")
    el = _safe_get(joints, "elbow_left")
    wl = _safe_get(joints, "wrist_left")

    sr = _safe_get(joints, "shoulder_right")
    er = _safe_get(joints, "elbow_right")
    wr = _safe_get(joints, "wrist_right")

    # ---- Head (y-UP) ----
    n2h = _norm3(_vec(neck, head))
    head_yaw = math.atan2(n2h[0], max(1e-6, abs(n2h[2])))
    # n2h[1] > 0 = head above neck (normal). Pitch should be ~0 in this case.
    # Forward tilt (looking down) pushes head forward -> n2h[2] increases.
    head_pitch = math.atan2(n2h[2], n2h[1])  # 0 when head straight up, + when tilted forward

    # ---- Left arm ----
    l_shoulder_pitch = _shoulder_pitch_3d(sl, el)
    l_shoulder_roll = _shoulder_roll_3d(sl, el, sign=1.0)
    l_elbow_roll = -_elbow_flexion_3d(sl, el, wl)
    l_elbow_yaw = 0.0  # locked: unreliable from single camera

    # ---- Right arm ----
    r_shoulder_pitch = _shoulder_pitch_3d(sr, er)
    r_shoulder_roll = _shoulder_roll_3d(sr, er, sign=-1.0)
    r_elbow_roll = _elbow_flexion_3d(sr, er, wr)
    r_elbow_yaw = 0.0  # locked: unreliable from single camera

    raw = {
        "HeadYaw": head_yaw,
        "HeadPitch": head_pitch,
        "LShoulderPitch": l_shoulder_pitch,
        "LShoulderRoll": l_shoulder_roll,
        "LElbowYaw": l_elbow_yaw,
        "LElbowRoll": l_elbow_roll,
        "RShoulderPitch": r_shoulder_pitch,
        "RShoulderRoll": r_shoulder_roll,
        "RElbowYaw": r_elbow_yaw,
        "RElbowRoll": r_elbow_roll,
    }

    clamped = {}
    for joint, angle in raw.items():
        low, high = JOINT_LIMITS[joint]
        clamped[joint] = _clamp(angle, low, high)

    return clamped


class ExponentialSmoother(object):
    def __init__(self, alpha=0.35):
        self.alpha = alpha
        self.prev = {}

    def apply(self, angles):
        out = {}
        for k, v in angles.items():
            if k not in self.prev:
                out[k] = v
            else:
                out[k] = self.alpha * v + (1.0 - self.alpha) * self.prev[k]
        self.prev = out.copy()
        return out
