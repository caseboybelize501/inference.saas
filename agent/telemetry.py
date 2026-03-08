from pynvml import *
import asyncio
import httpx

def send_telemetry(cluster_id):
    nvmlInit()
    device_count = nvmlDeviceGetCount()
    telemetry_data = {
        'cluster_id': cluster_id,
        'gpus': []
    }
    for i in range(device_count):
        handle = nvmlDeviceGetHandleByIndex(i)
        memory_info = nvmlDeviceGetMemoryInfo(handle)
        utilization = nvmlDeviceGetUtilizationRates(handle)
        power_info = nvmlDeviceGetPowerUsage(handle)
        telemetry_data['gpus'].append({
            'id': nvmlDeviceGetName(handle).decode(),
            'vram_used': memory_info.used / (1024 ** 3),
            'gpu_util': utilization.gpu,
            'memory_util': utilization.memory,
            'power_usage': power_info / 1000
        })
    nvmlShutdown()
    return telemetry_data