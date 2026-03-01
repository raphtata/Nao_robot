import json
import math
import socket
import time

from config import load_config


def _skeleton_frame(t):
    # Simple animated upper-body skeleton in camera coordinates
    amp = 0.18
    wave = math.sin(t)

    shoulder_y = 1.35
    elbow_y = 1.10 + 0.08 * math.sin(2.0 * t)
    wrist_y = 0.95 + 0.1 * math.sin(2.0 * t + 0.4)

    return {
        "timestamp": time.time(),
        "joints": {
            "head": {"x": 0.0, "y": 1.65 + 0.02 * math.sin(1.5 * t), "z": 1.0},
            "neck": {"x": 0.0, "y": 1.48, "z": 1.0},
            "shoulder_left": {"x": -0.22, "y": shoulder_y, "z": 1.0},
            "elbow_left": {"x": -0.25 - amp * wave, "y": elbow_y, "z": 0.92},
            "wrist_left": {"x": -0.28 - amp * wave, "y": wrist_y, "z": 0.88},
            "shoulder_right": {"x": 0.22, "y": shoulder_y, "z": 1.0},
            "elbow_right": {"x": 0.25 + amp * wave, "y": elbow_y, "z": 0.92},
            "wrist_right": {"x": 0.28 + amp * wave, "y": wrist_y, "z": 0.88},
        },
    }


def main():
    cfg = load_config()
    host = cfg["udp_host"]
    port_nao = cfg["udp_port"]
    port_viewer = cfg["udp_port_viewer"]
    fps = max(1, cfg["fps"])
    dt = 1.0 / float(fps)

    targets = [(host, port_nao)]
    if port_viewer != port_nao:
        targets.append((host, port_viewer))

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    print("[mock] sending skeleton to %s at ports %s (FPS=%s)" % (host, [p for _, p in targets], fps))

    t = 0.0
    try:
        while True:
            frame = _skeleton_frame(t)
            payload = json.dumps(frame).encode("utf-8")
            for target in targets:
                sock.sendto(payload, target)
            t += dt
            time.sleep(dt)
    except KeyboardInterrupt:
        print("[mock] stopped")


if __name__ == "__main__":
    main()
