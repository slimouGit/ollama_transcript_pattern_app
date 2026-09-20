# python
import os
import shutil
import subprocess

# 1) nvidia-smi ausgeben (wenn installiert)
nvidia = shutil.which("nvidia-smi")
if nvidia:
    try:
        print("nvidia-smi output:")
        print(subprocess.check_output([nvidia, "--query-gpu=name,memory.total", "--format=csv"]).decode())
    except Exception as e:
        print("Fehler beim Aufruf von nvidia-smi:", e)
else:
    print("nvidia-smi nicht gefunden.")

# 2) CUDA_VISIBLE_DEVICES prüfen
print("CUDA_VISIBLE_DEVICES =", os.environ.get("CUDA_VISIBLE_DEVICES"))

# 3) PyTorch prüfen
try:
    import torch
    print("PyTorch version:", torch.__version__)
    print("torch.cuda.is_available():", torch.cuda.is_available())
    print("CUDA device count:", torch.cuda.device_count())
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("Verwendetes device für PyTorch:", device)
    # Beispiel: model.to(device)
except Exception as e:
    print("PyTorch nicht verfügbar oder Fehler:", e)

# 4) TensorFlow prüfen (optional)
try:
    import tensorflow as tf
    gpus = tf.config.list_physical_devices("GPU")
    print("TensorFlow GPUs:", gpus)
except Exception as e:
    print("TensorFlow nicht verfügbar oder Fehler:", e)