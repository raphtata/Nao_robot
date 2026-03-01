# -*- coding: utf-8 -*-
"""
Receive UDP skeleton frames and mirror upper-body gestures on NAO.
Python 2.7 script (NAOqi).
"""

import json
import os
import socket
import sys
import time


def load_env_py27(base_dir):
    env = {}
    path = os.path.join(base_dir, ".env")
    fallback = os.path.join(base_dir, ".env.example")
    use_path = path if os.path.exists(path) else fallback
    if os.path.exists(use_path):
        with open(use_path, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


HIP_JOINTS = [
    "LHipYawPitch",
    "LHipRoll",
    "LHipPitch",
    "RHipRoll",
    "RHipPitch",
]


def lock_hips(motion):
    """Keep hip motors fixed at their current position for stability."""
    try:
        hip_targets = motion.getAngles(HIP_JOINTS, True)
    except Exception:
        hip_targets = [0.0] * len(HIP_JOINTS)

    motion.setStiffnesses(HIP_JOINTS, 1.0)
    motion.setAngles(HIP_JOINTS, hip_targets, 0.05)
    return hip_targets


def main():
    if sys.version_info[0] != 2:
        print("[nao_mirror] This script must run with Python 2.7 (not Python %s)." % sys.version.split()[0])
        print("[nao_mirror] Run: C:\\Python27\\python.exe .\\projet_kinect\\src\\nao_mirror_py27.py")
        sys.exit(1)

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env = load_env_py27(base_dir)

    udp_host = env.get("UDP_HOST", "127.0.0.1")
    udp_port = int(env.get("UDP_PORT", "5006"))

    nao_ip = str(env.get("NAO_IP", "169.254.201.219"))
    nao_port = int(env.get("NAO_PORT", "9559"))

    # NAOqi SDK local (same pattern as nao_voice_conversation_py27.py)
    lib_path = os.path.join(os.path.dirname(base_dir), "lib")

    choregraphe_bin = env.get(
        "CHOREGRAPHE_BIN",
        r"C:\Program Files (x86)\Softbank Robotics\Choregraphe Suite 2.5\bin",
    )

    # Required on Windows so naoqi/_qi dependent DLLs can be resolved.
    # Keep local lib first, then optional Choregraphe bin.
    path_parts = []
    if os.path.isdir(lib_path):
        path_parts.append(lib_path)
    if os.path.isdir(choregraphe_bin):
        path_parts.append(choregraphe_bin)

    current_path = os.environ.get("PATH", "")
    for p in reversed(path_parts):
        if p not in current_path:
            current_path = p + os.pathsep + current_path
    os.environ["PATH"] = current_path

    if lib_path not in sys.path:
        sys.path.insert(0, lib_path)

    try:
        from naoqi import ALProxy
    except Exception as e:
        print("[nao_mirror] import naoqi failed: %s" % str(e))
        print("[nao_mirror] lib path: %s" % lib_path)
        print("[nao_mirror] CHOREGRAPHE_BIN: %s" % choregraphe_bin)
        print("[nao_mirror] Hint: verify Python 2.7 32-bit and NAOqi DLL compatibility")
        raise

    # Import local mapping from same folder
    src_dir = os.path.dirname(os.path.abspath(__file__))
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)
    from mapping import skeleton_to_nao_angles, ExponentialSmoother

    motion = ALProxy(str("ALMotion"), nao_ip, nao_port)

    motion.setStiffnesses("Head", 1.0)
    motion.setStiffnesses("LArm", 1.0)
    motion.setStiffnesses("RArm", 1.0)
    hip_targets = lock_hips(motion)

    names = [
        "HeadYaw",
        "HeadPitch",
        "LShoulderPitch",
        "LShoulderRoll",
        "LElbowYaw",
        "LElbowRoll",
        "RShoulderPitch",
        "RShoulderRoll",
        "RElbowYaw",
        "RElbowRoll",
    ]

    smoother = ExponentialSmoother(alpha=0.55)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((udp_host, udp_port))
    sock.settimeout(2.0)

    print("[nao_mirror] listening on udp %s:%s" % (udp_host, udp_port))
    print("[nao_mirror] connected to NAO %s:%s" % (nao_ip, nao_port))

    try:
        while True:
            try:
                data, _addr = sock.recvfrom(65535)
            except socket.timeout:
                continue

            try:
                msg = json.loads(data)
                joints = msg.get("joints", {})
                angles = skeleton_to_nao_angles(joints)
                angles = smoother.apply(angles)

                values = [clamp(float(angles[n]), -3.0, 3.0) for n in names]
                motion.setAngles(names, values, 0.12)
                motion.setAngles(HIP_JOINTS, hip_targets, 0.05)
            except Exception as e:
                print("[nao_mirror] frame error: %s" % str(e))

    except KeyboardInterrupt:
        print("[nao_mirror] stopping...")
    finally:
        try:
            motion.setStiffnesses("Head", 0.0)
            motion.setStiffnesses("LArm", 0.0)
            motion.setStiffnesses("RArm", 0.0)
            motion.setStiffnesses(HIP_JOINTS, 0.0)
        except:
            pass


if __name__ == "__main__":
    main()
