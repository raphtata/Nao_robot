import json
import socket
import time
import base64

import cv2
import matplotlib.pyplot as plt
import numpy as np
import streamlit as st

from config import load_config


EDGES = [
    ("head", "neck"),
    ("neck", "shoulder_left"),
    ("neck", "shoulder_right"),
    ("shoulder_left", "elbow_left"),
    ("elbow_left", "wrist_left"),
    ("shoulder_right", "elbow_right"),
    ("elbow_right", "wrist_right"),
]


st.set_page_config(page_title="Kinect Skeleton Viewer", layout="wide")
st.title("Kinect 360 Skeleton Viewer (UDP)")

cfg = load_config()
default_host = cfg["udp_host"]
default_port = cfg["udp_port_viewer"]

col_a, col_b, col_c = st.columns([2, 1, 1])
with col_a:
    udp_host = st.text_input("UDP host", value=default_host)
with col_b:
    udp_port = st.number_input("Viewer UDP port", min_value=1, max_value=65535, value=default_port)
with col_c:
    auto_refresh = st.checkbox("Auto refresh", value=True)

refresh_ms = st.slider("Refresh interval (ms)", min_value=30, max_value=500, value=50, step=10)

if "sock" not in st.session_state:
    st.session_state.sock = None
if "sock_host" not in st.session_state:
    st.session_state.sock_host = None
if "sock_port" not in st.session_state:
    st.session_state.sock_port = None
if "last_frame" not in st.session_state:
    st.session_state.last_frame = None
if "last_error" not in st.session_state:
    st.session_state.last_error = ""


def ensure_socket(host, port):
    must_rebind = (
        st.session_state.sock is None
        or st.session_state.sock_host != host
        or st.session_state.sock_port != port
    )
    if not must_rebind:
        return

    if st.session_state.sock is not None:
        try:
            st.session_state.sock.close()
        except Exception:
            pass

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind((host, int(port)))
    s.setblocking(False)

    st.session_state.sock = s
    st.session_state.sock_host = host
    st.session_state.sock_port = int(port)


try:
    ensure_socket(udp_host, udp_port)
except Exception as e:
    st.error("Socket bind error: %s" % str(e))
    st.stop()


def poll_frames(max_packets=30):
    sock = st.session_state.sock
    latest = None
    while True:
        try:
            data, _addr = sock.recvfrom(65535)
            latest = json.loads(data.decode("utf-8", errors="ignore"))
            max_packets -= 1
            if max_packets <= 0:
                break
        except BlockingIOError:
            break
        except Exception as e:
            st.session_state.last_error = str(e)
            break

    if latest is not None:
        st.session_state.last_frame = latest


def decode_camera_frame(frame):
    return None
    if not frame:
        return None
    b64 = frame.get("camera_jpeg_b64", "")
    if not b64:
        return None
    try:
        data = base64.b64decode(b64)
        arr = np.frombuffer(data, dtype=np.uint8)
        img_bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if img_bgr is None:
            return None
        return cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    except Exception as e:
        st.session_state.last_error = "camera decode error: %s" % str(e)
        return None


poll_frames()

frame = st.session_state.last_frame

left, right = st.columns([2, 1])

with left:
    st.subheader("Skeleton render")
    if not frame or "joints" not in frame:
        st.info("No skeleton frame received yet. Start a sender (mock or real Kinect provider).")
    else:
        joints = frame.get("joints", {})

        fig, ax = plt.subplots(figsize=(7, 7))

        # Apply Y translation to center skeleton in graph
        Y_OFFSET = 0.4
        
        xs = []
        ys = []
        for _name, p in joints.items():
            xs.append(p.get("x", 0.0))
            ys.append(p.get("y", 0.0) + Y_OFFSET)

        ax.scatter(xs, ys, s=80, c='red', zorder=3)

        for a, b in EDGES:
            if a in joints and b in joints:
                ax.plot(
                    [joints[a]["x"], joints[b]["x"]],
                    [joints[a]["y"] + Y_OFFSET, joints[b]["y"] + Y_OFFSET],
                    linewidth=3,
                    color='blue',
                    zorder=2,
                )

        # Fixed axis limits for stable render (typical MediaPipe world landmark range)
        ax.set_xlim(-0.8, 0.8)
        ax.set_ylim(-0.6, 0.6)
        ax.invert_yaxis()
        
        ax.set_xlabel("X (meters)", fontsize=10)
        ax.set_ylabel("Y (meters)", fontsize=10)
        ax.set_title("Upper-body skeleton (3D world coordinates)", fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.set_facecolor('#f0f0f0')

        st.pyplot(fig)

    st.subheader("Camera preview (with skeleton overlay)")
    camera_rgb = decode_camera_frame(frame)
    if camera_rgb is None:
        st.info("No camera preview received yet from streamer.")
    else:
        st.image(camera_rgb, channels="RGB", width="stretch")

with right:
    st.subheader("Status")
    if frame:
        st.success("Frame received")
        st.write("timestamp:", frame.get("timestamp"))
        st.write("joint count:", len(frame.get("joints", {})))
    else:
        st.warning("Waiting for data")

    if st.session_state.last_error:
        st.error(st.session_state.last_error)

    st.subheader("Raw JSON")
    st.code(json.dumps(frame, indent=2) if frame else "{}", language="json")

st.caption("Note: this viewer shows any skeleton stream in the expected UDP JSON format.")

if auto_refresh:
    time.sleep(refresh_ms / 1000.0)
    st.rerun()
