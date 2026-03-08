from celery import Celery
from engine.validation_runner import run_validation
from config import Config

celery = Celery('validation_worker', broker='redis://localhost:6379/0')

@celery.task
async def run_validation_task(optimization_bundle):
    config = Config()
    validation_result = run_validation(optimization_bundle)
    return validation_result