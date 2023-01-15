from fastapi import FastAPI, File, HTTPException, status, UploadFile
from fastapi.responses import RedirectResponse, JSONResponse, FileResponse
from .schema import TestTaskArgs
from . import celery_worker
from zlib import crc32
from pathlib import Path
from dotenv import load_dotenv
import os
from uuid import uuid4

load_dotenv('.env')

MEDIA_DIR = Path(os.environ.get("MEDIA_DIR"))
MEDIA_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI()


@app.get("/")
def root_redirect():
    return RedirectResponse("/docs")

@app.post("/test_task")
def run_test_task(args: TestTaskArgs):
    
    task = celery_worker.test_task.delay(args.a, args.b, args.c)
    return JSONResponse(dict(task.get()))


@app.post("/task",
    status_code=status.HTTP_202_ACCEPTED)
def add_task(
    model: str, 
    upload_file: UploadFile = File(format=[".mp3",".ogg",".flac"])):
    
    file_ext = upload_file.filename.split('.')[-1]
    file_bytes = upload_file.file.read()
    filehash = crc32(file_bytes) ^ len(file_bytes)
    id = str(uuid4())

    filename = f"{id}.{file_ext}"
    filepath = MEDIA_DIR/ filename
    
    if not filepath.is_file():
        filepath.write_bytes(file_bytes)

    task = celery_worker.test_transcribe.apply_async(args=(model, filehash, filename), task_id=id)

    return JSONResponse({
        "id": id
    })

@app.get("/files/{task_uuid}")
def get_file(task_uuid:str):

    files = [f for f in MEDIA_DIR.glob(f"**/{task_uuid}.*") if f.is_file()]
    if not files:
        return HTTPException(404)

    return FileResponse(files[0])
