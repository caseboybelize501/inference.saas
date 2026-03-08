import asyncio
import httpx
import os
import json
from hw_scanner import scan_hardware
from model_watcher import watch_models
from telemetry import send_telemetry
from opt_applier import apply_optimization
from server_probe import probe_servers
from config import Config

async def main():
    config = Config()
    cluster_profile = scan_hardware()
    cluster_profile['servers'] = probe_servers()
    cluster_profile['models'] = watch_models()
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{config.IOAS_ENDPOINT}/api/clusters/register", json=cluster_profile)
        response.raise_for_status()
        data = response.json()
        cluster_id = data['cluster_id']
        agent_token = data['agent_token']
        while True:
            telemetry_data = send_telemetry(cluster_id)
            await client.post(f"{config.IOAS_ENDPOINT}/api/telemetry/ingest", json=telemetry_data, headers={'Authorization': f'Bearer {agent_token}'})
            await asyncio.sleep(30)

if __name__ == "__main__":
    asyncio.run(main())