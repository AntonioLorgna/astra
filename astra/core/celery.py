from celery import Celery
import os, logging

logger = logging.getLogger(__name__)

app = Celery()
app.conf.broker_url = os.environ.get("CELERY_BROKER_URL")
app.conf.result_backend = os.environ.get("CELERY_RESULT_BACKEND")
app.conf.task_track_started = True
app.conf.task_store_errors_even_if_ignored = True
app.conf.worker_concurrency = 1
app.conf.worker_prefetch_multiplier = 1
app.conf.worker_send_task_events = True

worker_transcribe_func = None


@app.task(
    bind=True,
    name="transcribe",
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 100, "countdown": 10},
)
def transcribe(self, model, filehash, file_webhook):
    job_id = self.request.id
    if worker_transcribe_func is None:
        raise Exception("Celery task started not from worker!")

    return worker_transcribe_func(job_id, model, filehash, file_webhook)
