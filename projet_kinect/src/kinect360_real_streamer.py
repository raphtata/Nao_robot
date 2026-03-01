"""
Kinect 360 skeleton streamer using OpenCV (DirectShow) + MediaPipe Pose.

Captures RGB frames, uses MediaPipe **world landmarks** (3D in metres,
hip-centred) for skeleton extraction, applies a One Euro filter for
smooth real-time tracking, and sends the upper-body skeleton via UDP
as JSON to both the NAO mirror and the Streamlit viewer.
"""

import importlib
import json
import os
import socket
import time
import base64

import cv2
import mediapipe as mp
import numpy as np

from config import load_config
from one_euro_filter import PoseFilter


# ---------------------------------------------------------------------------
# MediaPipe backend resolution (supports both legacy and tasks API)
# ---------------------------------------------------------------------------

def _resolve_pose_backend():
    """Return (backend_name, module, draw_module_or_None)."""
    if hasattr(mp, "solutions") and hasattr(mp.solutions, "pose"):
        return "solutions", mp.solutions.pose, mp.solutions.drawing_utils
    try:
        mp_vision = importlib.import_module("mediapipe.tasks.python.vision")
        return "tasks", mp_vision, None
    except Exception:
        raise RuntimeError(
            "MediaPipe Pose API not found. mediapipe location: %s"
            % getattr(mp, "__file__", "unknown")
        )


POSE_BACKEND, MP_POSE_MODULE, MP_DRAW_MODULE = _resolve_pose_backend()
MP = MP_POSE_MODULE.PoseLandmark


# ---------------------------------------------------------------------------
# Landmark helpers  (world landmarks: metres, hip-centred)
# ---------------------------------------------------------------------------

def _wl_to_joint(world_landmarks, idx):
    """Extract a world landmark as {x, y, z} in metres."""
    lm = world_landmarks[idx]
    return {"x": float(lm.x), "y": float(lm.y), "z": float(lm.z)}


def _frame_to_skeleton(world_landmarks):
    """Build skeleton dict from MediaPipe *world* landmarks (3D metres)."""
    l_sh = _wl_to_joint(world_landmarks, MP.LEFT_SHOULDER)
    r_sh = _wl_to_joint(world_landmarks, MP.RIGHT_SHOULDER)
    neck = {
        "x": 0.5 * (l_sh["x"] + r_sh["x"]),
        "y": 0.5 * (l_sh["y"] + r_sh["y"]),
        "z": 0.5 * (l_sh["z"] + r_sh["z"]),
    }
    return {
        "timestamp": time.time(),
        "joints": {
            "head": _wl_to_joint(world_landmarks, MP.NOSE),
            "neck": neck,
            "shoulder_left": l_sh,
            "elbow_left": _wl_to_joint(world_landmarks, MP.LEFT_ELBOW),
            "wrist_left": _wl_to_joint(world_landmarks, MP.LEFT_WRIST),
            "shoulder_right": r_sh,
            "elbow_right": _wl_to_joint(world_landmarks, MP.RIGHT_ELBOW),
            "wrist_right": _wl_to_joint(world_landmarks, MP.RIGHT_WRIST),
        },
    }


# ---------------------------------------------------------------------------
# Preview drawing (tasks backend – solutions uses built-in draw_landmarks)
# ---------------------------------------------------------------------------

UPPER_BODY_IDS = [
    MP.NOSE, MP.LEFT_SHOULDER, MP.RIGHT_SHOULDER,
    MP.LEFT_ELBOW, MP.RIGHT_ELBOW, MP.LEFT_WRIST, MP.RIGHT_WRIST,
]

UPPER_BODY_EDGES = [
    (MP.NOSE, MP.LEFT_SHOULDER),
    (MP.NOSE, MP.RIGHT_SHOULDER),
    (MP.LEFT_SHOULDER, MP.RIGHT_SHOULDER),
    (MP.LEFT_SHOULDER, MP.LEFT_ELBOW),
    (MP.LEFT_ELBOW, MP.LEFT_WRIST),
    (MP.RIGHT_SHOULDER, MP.RIGHT_ELBOW),
    (MP.RIGHT_ELBOW, MP.RIGHT_WRIST),
]


def _draw_tasks_preview(img_bgr, landmarks):
    h, w = img_bgr.shape[:2]

    def xy(idx):
        lm = landmarks[idx]
        return int(lm.x * w), int(lm.y * h)

    for idx in UPPER_BODY_IDS:
        cv2.circle(img_bgr, xy(idx), 5, (60, 220, 60), -1)
    for a, b in UPPER_BODY_EDGES:
        cv2.line(img_bgr, xy(a), xy(b), (220, 180, 40), 2)


def _encode_preview_jpeg_b64(img_bgr, max_width=960, jpeg_quality=70):
    h, w = img_bgr.shape[:2]
    out = img_bgr
    if w > max_width:
        scale = float(max_width) / float(w)
        out = cv2.resize(out, (max_width, int(h * scale)), interpolation=cv2.INTER_AREA)

    ok, encoded = cv2.imencode(
        ".jpg",
        out,
        [int(cv2.IMWRITE_JPEG_QUALITY), int(jpeg_quality)],
    )
    if not ok:
        return ""
    return base64.b64encode(encoded.tobytes()).decode("ascii")


# ---------------------------------------------------------------------------
# Camera source
# ---------------------------------------------------------------------------

def _open_camera(camera_index):
    """Open the Kinect 360 RGB camera via DirectShow backend."""
    cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
    if not cap.isOpened():
        cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        raise RuntimeError(
            "Cannot open camera index %s. "
            "Run: python projet_kinect/src/detect_cameras.py to find the right index."
            % camera_index
        )
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print("[kinect] camera index=%s  resolution=%dx%d" % (camera_index, w, h))
    return cap


# ---------------------------------------------------------------------------
# Pose model initialization
# ---------------------------------------------------------------------------

def _create_pose(pose_model_path_cfg):
    if POSE_BACKEND == "solutions":
        return MP_POSE_MODULE.Pose(
            static_image_mode=False,
            model_complexity=1,
            enable_segmentation=False,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    default_model = os.path.join(base_dir, "models", "pose_landmarker_full.task")
    model_path = pose_model_path_cfg or default_model
    if not os.path.exists(model_path):
        raise RuntimeError(
            "POSE_MODEL_PATH not found: %s\n"
            "Download from: https://storage.googleapis.com/mediapipe-models/"
            "pose_landmarker/pose_landmarker_full/float16/latest/pose_landmarker_full.task\n"
            "Then set POSE_MODEL_PATH in projet_kinect/.env" % model_path
        )

    base_options_mod = importlib.import_module("mediapipe.tasks.python.core.base_options")
    vision_core_mod = importlib.import_module(
        "mediapipe.tasks.python.vision.core.vision_task_running_mode"
    )
    options = MP_POSE_MODULE.PoseLandmarkerOptions(
        base_options=base_options_mod.BaseOptions(model_asset_path=model_path),
        running_mode=vision_core_mod.VisionTaskRunningMode.IMAGE,
        num_poses=1,
        min_pose_detection_confidence=0.5,
        min_pose_presence_confidence=0.5,
        min_tracking_confidence=0.5,
    )
    return MP_POSE_MODULE.PoseLandmarker.create_from_options(options)


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def main():
    cfg = load_config()
    host = cfg["udp_host"]
    port_nao = cfg["udp_port"]
    port_viewer = cfg["udp_port_viewer"]
    fps = max(1, cfg["fps"])
    show_preview = cfg["show_preview"]
    camera_index = cfg["camera_index"]

    nao_target = (host, port_nao)
    viewer_target = (host, port_viewer) if port_viewer != port_nao else None

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    dt = 1.0 / float(fps)

    cap = _open_camera(camera_index)
    pose_cm = _create_pose(cfg.get("pose_model_path", ""))

    pose_filter = PoseFilter(freq=float(fps), min_cutoff=1.5, beta=0.01)

    print("[kinect] mediapipe backend=%s  (world landmarks 3D)" % POSE_BACKEND)
    print("[kinect] streaming skeleton UDP -> %s:%s (FPS=%s)" % (host, port_nao, fps))
    if viewer_target is not None:
        print("[kinect] streaming viewer camera+pose UDP -> %s:%s" % (host, port_viewer))
    else:
        print("[kinect] viewer stream disabled because UDP_PORT_VIEWER == UDP_PORT")

    with pose_cm as pose:
        try:
            while True:
                t0 = time.time()
                ok, frame_bgr = cap.read()
                if not ok:
                    continue
                frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)

                if POSE_BACKEND == "solutions":
                    result = pose.process(frame_rgb)
                    has_pose = bool(result.pose_landmarks)
                    img_landmarks = result.pose_landmarks.landmark if has_pose else None
                    world_landmarks = result.pose_world_landmarks.landmark if has_pose else None
                else:
                    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
                    result = pose.detect(mp_image)
                    has_pose = bool(result.pose_landmarks and len(result.pose_landmarks) > 0)
                    img_landmarks = result.pose_landmarks[0] if has_pose else None
                    world_landmarks = (
                        result.pose_world_landmarks[0]
                        if has_pose and result.pose_world_landmarks
                        else None
                    )

                skeleton = None
                if has_pose and world_landmarks is not None:
                    skeleton = _frame_to_skeleton(world_landmarks)
                    skeleton["joints"] = pose_filter.filter(
                        skeleton["joints"], skeleton["timestamp"]
                    )

                annotated = frame_bgr.copy()
                if has_pose and img_landmarks is not None:
                    if POSE_BACKEND == "solutions":
                        MP_DRAW_MODULE.draw_landmarks(
                            annotated,
                            result.pose_landmarks,
                            MP_POSE_MODULE.POSE_CONNECTIONS,
                        )
                    else:
                        _draw_tasks_preview(annotated, img_landmarks)
                cv2.putText(
                    annotated,
                    "Skeleton -> NAO:%s Viewer:%s" % (
                        port_nao,
                        port_viewer if viewer_target is not None else "off",
                    ),
                    (10, 28),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (50, 220, 50) if has_pose else (50, 50, 220),
                    2,
                    cv2.LINE_AA,
                )

                if skeleton is not None:
                    payload_nao = json.dumps(skeleton).encode("utf-8")
                    sock.sendto(payload_nao, nao_target)

                if viewer_target is not None:
                    viewer_msg = {
                        "timestamp": time.time(),
                        "joints": skeleton["joints"] if skeleton is not None else {},
                        "has_pose": bool(skeleton is not None),
                        "camera_jpeg_b64": _encode_preview_jpeg_b64(annotated),
                    }
                    payload_viewer = json.dumps(viewer_msg).encode("utf-8")
                    sock.sendto(payload_viewer, viewer_target)

                if show_preview:
                    cv2.imshow("Kinect 360 Skeleton Provider", annotated)
                    key = cv2.waitKey(1) & 0xFF
                    if key == 27 or key == ord("q"):
                        break

                elapsed = time.time() - t0
                if elapsed < dt:
                    time.sleep(dt - elapsed)

        except KeyboardInterrupt:
            pass
        finally:
            cap.release()
            cv2.destroyAllWindows()
            print("[kinect] stopped")


if __name__ == "__main__":
    main()
