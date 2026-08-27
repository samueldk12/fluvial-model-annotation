"""
Módulo de Gerenciamento de Hardware e Dispositivos (GPU AMD DirectML / CUDA / CPU).
"""

import torch

def get_device():
    """
    Retorna o dispositivo de aceleração por hardware prioritário:
    1. GPU AMD Radeon (via DirectML no Windows)
    2. GPU NVIDIA (via CUDA)
    3. CPU (Fallback)
    """
    try:
        import torch_directml
        device = torch_directml.device()
        device_name = torch_directml.device_name(0).strip()
        return device, f"GPU AMD ({device_name})"
    except Exception:
        pass
        
    if torch.cuda.is_available():
        return torch.device("cuda"), f"GPU NVIDIA ({torch.cuda.get_device_name(0)})"
        
    return torch.device("cpu"), "CPU"
