import subprocess
import psutil
from pynvml import *

def scan_hardware():
    nvmlInit()
    device_count = nvmlDeviceGetCount()
    gpus = []
    for i in range(device_count):
        handle = nvmlDeviceGetHandleByIndex(i)
        memory_info = nvmlDeviceGetMemoryInfo(handle)
        gpus.append({
            'id': nvmlDeviceGetName(handle).decode(),
            'vram': memory_info.total / (1024 ** 3)
        })
    nvmlShutdown()
    return {
        'gpus': gpus,
        'system_ram': psutil.virtual_memory().total / (1024 ** 3)
    }