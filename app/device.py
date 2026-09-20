# python
# file: app/device.py
import os
import shutil
import subprocess
from typing import Dict, Any

from fastapi import APIRouter

router = APIRouter()

def get_device_info() -> Dict[str, Any]:
    info = {}
    nvidia = shutil.which("nvidia-smi")
    if nvidia:
        try:
            out = subprocess.check_output([nvidia, "--query-gpu=name,memory.total", "--format=csv"]).decode().strip()
            info["nvidia_smi"] = out
        except Exception as e:
            info["nvidia_smi_error"] = str(e)
    else:
        info["nvidia_smi"] = None

    info["CUDA_VISIBLE_DEVICES"] = os.environ.get("CUDA_VISIBLE_DEVICES")

    try:
        import torch
        info["torch_version"] = torch.__version__
        info["torch_cuda_available"] = torch.cuda.is_available()
        info["torch_cuda_count"] = torch.cuda.device_count()
        if torch.cuda.is_available():
            info["torch_current_device"] = torch.cuda.current_device()
            info["torch_device_name"] = torch.cuda.get_device_name(0)
    except Exception as e:
        info["torch_error"] = str(e)

    try:
        import tensorflow as tf
        gpus = tf.config.list_physical_devices("GPU")
        info["tensorflow_gpus"] = [str(g) for g in gpus]
    except Exception as e:
        info["tensorflow_error"] = str(e)

    return info

@router.get("/device")
async def device_endpoint():
    """REST-Endpoint zum Abrufen der Device-Infos."""
    return get_device_info()

async def on_startup():
    """Beim App-Startup einmal ausführen (z.\,B. Logging)."""
    info = get_device_info()
    print("Device check (startup):", info)