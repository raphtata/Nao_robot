import os
from dotenv import load_dotenv


def load_config():
    """Load config from projet_kinect/.env (fallback: .env.example)."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_path = os.path.join(base_dir, ".env")
    env_example_path = os.path.join(base_dir, ".env.example")

    if os.path.exists(env_path):
        load_dotenv(env_path, override=False)
    else:
        load_dotenv(env_example_path, override=False)

    return {
        "udp_host": os.getenv("UDP_HOST", "127.0.0.1"),
        "udp_port": int(os.getenv("UDP_PORT", "5006")),
        "udp_port_viewer": int(os.getenv("UDP_PORT_VIEWER", "5007")),
        "fps": int(os.getenv("FPS", "20")),
        "camera_index": int(os.getenv("CAMERA_INDEX", "0")),
        "show_preview": os.getenv("SHOW_PREVIEW", "1") == "1",
        "pose_model_path": os.getenv("POSE_MODEL_PATH", ""),
        "nao_ip": os.getenv("NAO_IP", "169.254.201.219"),
        "nao_port": int(os.getenv("NAO_PORT", "9559")),
    }
