from celery import Celery
from engine.optimization_bundle import assemble_bundle
from config import Config

celery = Celery('optimization_worker', broker='redis://localhost:6379/0')

@celery.task
async def run_optimization(cluster_id, model_sha256, workload_type, context_target):
    config = Config()
    optimization_bundle = assemble_bundle(cluster_id, model_sha256, workload_type, context_target)
    return optimization_bundle