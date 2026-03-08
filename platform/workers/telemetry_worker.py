from celery import Celery
from learning.perf_store import store_telemetry
from config import Config

celery = Celery('telemetry_worker', broker='redis://localhost:6379/0')

@celery.task
async def aggregate_and_store_telemetry(telemetry_data):
    config = Config()
    store_telemetry(telemetry_data)