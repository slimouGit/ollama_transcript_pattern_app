from __future__ import annotations

import ctypes
import os
import platform
import shutil
import subprocess
from typing import Any

import requests

from .config import OLLAMA_MODEL, OLLAMA_URL


def _run_command(command: list[str], timeout: float = 3.0) -> str:
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except (OSError, subprocess.SubprocessError):
        return ""
    return result.stdout.strip() if result.returncode == 0 else ""


def _cpu_name() -> str | None:
    name = platform.processor().strip()
    if name:
        return name
    if os.name == "nt":
        output = _run_command(
            ["powershell", "-NoProfile", "-Command", "(Get-CimInstance Win32_Processor).Name"]
        )
        return output.splitlines()[0].strip() if output else None
    return None


def _memory_gb() -> float | None:
    if os.name == "nt":
        class MemoryStatus(ctypes.Structure):
            _fields_ = [
                ("length", ctypes.c_uint32),
                ("memory_load", ctypes.c_uint32),
                ("total_phys", ctypes.c_uint64),
                ("available_phys", ctypes.c_uint64),
                ("total_page_file", ctypes.c_uint64),
                ("available_page_file", ctypes.c_uint64),
                ("total_virtual", ctypes.c_uint64),
                ("available_virtual", ctypes.c_uint64),
                ("available_extended_virtual", ctypes.c_uint64),
            ]

        status = MemoryStatus()
        status.length = ctypes.sizeof(status)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
            return round(status.total_phys / (1024**3), 2)
    return None


def _gpu_info() -> dict[str, Any]:
    nvidia_smi = shutil.which("nvidia-smi")
    if nvidia_smi:
        output = _run_command(
            [
                nvidia_smi,
                "--query-gpu=name,memory.total",
                "--format=csv,noheader,nounits",
            ]
        )
        if output:
            first = output.splitlines()[0].split(",", 1)
            name = first[0].strip()
            vram = None
            if len(first) > 1:
                try:
                    vram = round(float(first[1].strip()) / 1024, 2)
                except ValueError:
                    pass
            return {"detected": True, "name": name, "vram_gb": vram, "source": "nvidia-smi"}

    if os.name == "nt":
        output = _run_command(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name",
            ]
        )
        names = [line.strip() for line in output.splitlines() if line.strip()]
        if names:
            return {"detected": True, "name": ", ".join(names), "vram_gb": None, "source": "Win32_VideoController"}

    return {"detected": False, "name": None, "vram_gb": None, "source": None}


def _ollama_runtime(model: str) -> dict[str, Any]:
    try:
        response = requests.get(f"{OLLAMA_URL}/api/ps", timeout=3)
        response.raise_for_status()
        models = response.json().get("models", [])
    except (requests.RequestException, ValueError, TypeError, AttributeError):
        return {
            "api_available": False,
            "actual_runtime_device": "unknown",
            "model": model,
            "reason": "Ollama /api/ps ist nicht erreichbar.",
        }

    selected = next(
        (item for item in models if item.get("name") == model or item.get("model") == model),
        models[0] if models else None,
    )
    if selected is None:
        return {
            "api_available": True,
            "actual_runtime_device": "unknown",
            "model": model,
            "reason": "Das Modell ist aktuell nicht als laufend gelistet.",
        }

    size_vram = selected.get("size_vram")
    if isinstance(size_vram, (int, float)):
        actual = "gpu" if size_vram > 0 else "cpu"
        reason = "Ollama /api/ps size_vram ausgewertet."
    else:
        actual = "unknown"
        reason = "Ollama meldet keine verwertbare VRAM-Nutzung."

    return {
        "api_available": True,
        "actual_runtime_device": actual,
        "model": selected.get("name") or selected.get("model") or model,
        "size_vram_bytes": size_vram,
        "reason": reason,
    }


def get_device_info(requested_device: str = "auto", model: str | None = None) -> dict[str, Any]:
    selected_model = model or OLLAMA_MODEL
    gpu = _gpu_info()
    runtime = _ollama_runtime(selected_model)
    return {
        "requested_device": requested_device,
        "actual_runtime_device": runtime.get("actual_runtime_device", "unknown"),
        "cpu_name": _cpu_name(),
        "gpu_detected": gpu["detected"],
        "gpu_name": gpu["name"],
        "gpu_vram_gb": gpu["vram_gb"],
        "ram_gb": _memory_gb(),
        "selected_ollama_model": selected_model,
        "ollama_runtime": runtime,
    }
