import base64
import hashlib
import logging
import os
import queue
import threading
import time
from typing import Optional
from contextlib import asynccontextmanager
from glob import glob

import uvicorn

# from api.v1.download_models import download_models
from api.v1.logger_config import setup_logging
from api.v1.services.Pdf2MD import processPdf2MD
from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, UploadFile
from SQLiteManager import SQLiteORM
from starlette.middleware.cors import CORSMiddleware
from starlette.status import HTTP_404_NOT_FOUND
from sqlite3 import OperationalError

setup_logging(is_debug_mode=False)
LOG = logging.getLogger()

DB_FILE = "data/minerU-server.db"

SQL_CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS file_task (
    task_id TEXT PRIMARY KEY,
    input_file_path TEXT NOT NULL,
    md_file_path TEXT,
    status TEXT,
    content_list_json_path TEXT
);
"""


def initialize_database() -> str:
    global DB_FILE
    try:
        db = SQLiteORM(DB_FILE)
        db.create_table(SQL_CREATE_USERS_TABLE)
        db.close()
    except OperationalError:
        DB_FILE = "../minerU-server.db"
        db = SQLiteORM(DB_FILE)
        db.create_table(SQL_CREATE_USERS_TABLE)
        db.close()


q = queue.Queue(maxsize=20)


def producer():
    while True:
        try:
            dbP = SQLiteORM(DB_FILE)
            waitingList = dbP.read("file_task", {"status": "waiting"})
            for waiting in waitingList:
                q.put(waiting)
                dbP.update(
                    "file_task", {"status": "processing"}, {"task_id": waiting[0]}
                )
        except Exception as e:
            LOG.error(f"Producer encountered an error: {e}")
        finally:
            dbP.close()
        time.sleep(5)


def consumer():
    while True:
        item = q.get()
        try:
            LOG.info(f"Processing task {item[0]} from queue")
            task_id = item[0]
            input_path = item[1]
            # output_path = os.path.join(input_path, os.path.splitext(input_path)[0])
            output_path = os.path.dirname(input_path)
            success = processPdf2MD(input_path=input_path, output_path=output_path)
            LOG.info(f"Finished task {item[0]} from queue")
            dbC = SQLiteORM(DB_FILE)
            if success:
                md_path = glob(os.path.join(output_path, "**/*.md"))[0]
                content_list_path = glob(
                    os.path.join(output_path, "**/*content_list.json")
                )[0]

                dbC.update(
                    "file_task",
                    {
                        "status": "success",
                        "md_file_path": md_path,
                        "content_list_json_path": content_list_path,
                    },
                    {"task_id": task_id},
                )
                LOG.info(f"Task {task_id} completed successfully")
            else:
                dbC.update("file_task", {"status": "error"}, {"task_id": task_id})
                LOG.error(f"Task {task_id} failed due to an error")
        except Exception as e:
            LOG.error(
                f"Consumer encountered an error processing task {task_id}: {e}\n{e.with_traceback()}"
            )
            dbC.update("file_task", {"status": "error"}, {"task_id": task_id})
        finally:
            dbC = SQLiteORM(DB_FILE)
            dbC.close()
            q.task_done()
        time.sleep(1)


@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_database()
    # download_models()
    producer_thread = threading.Thread(target=producer, daemon=True)
    producer_thread.start()

    consumer_thread = threading.Thread(target=consumer, daemon=True)
    consumer_thread.start()

    yield

    print("Shutting down...")

    # reset processing tasks to waiting
    dbP = SQLiteORM(DB_FILE)
    processing_list = dbP.read("file_task", {"status": "processing"})
    for task in processing_list:
        dbP.update("file_task", {"status": "waiting"}, {"task_id": task[0]})


current_script_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
app = FastAPI(lifespan=lifespan)
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/upload")
async def handle(
    background_task: BackgroundTasks,
    file: UploadFile = File(...),
    user_name: Optional[str] = Form(...),
):
    try:
        LOG.info(f"Received upload request: {file.filename} from user {user_name}")
        doc_id = hashlib.md5((file.filename + user_name).encode("utf-8")).hexdigest()

        file_path = os.path.join(current_script_dir, f"{doc_id}")
        if not os.path.exists(file_path):
            os.makedirs(file_path)

        file_path = os.path.join(file_path, f"{file.filename}")

        await file.seek(0)
        with open(file_path, "wb") as f:
            while chunk := await file.read(1024):
                f.write(chunk)
        LOG.info(f"File saved at: {file_path}")

        dbM = SQLiteORM(DB_FILE)
        try:
            dbM.create(
                "file_task",
                {
                    "task_id": doc_id,
                    "file_path": file_path,
                    "md_file_path": None,
                    "content_list_json_path": None,
                    "status": "waiting",
                },
            )
        finally:
            dbM.close()

        return {"message": "success", "task_id": doc_id, "filename": file.filename}
    except Exception as e:
        LOG.error(f"Error during file upload: {e}")
        return {"message": str(e), "task_id": None, "filename": file.filename}


@app.get("/download/{task_id}")
async def download_file(task_id: str):
    max_retries = 5  # Maximum number of retries before giving up
    retry_delay = 2  # Delay between retries in seconds

    try:
        db = SQLiteORM(DB_FILE)
        try:
            result = db.read("file_task", {"task_id": task_id})
        finally:
            db.close()

        if not result:
            LOG.warning(f"Task ID {task_id} not found")
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND, detail="Task ID not found"
            )

        task_id = result[0][0]
        input_file_path = result[0][1]
        md_file_path = result[0][2]
        status = result[0][3]
        content_list_file_path = result[0][4]

        if status == "waiting" or status == "processing":
            LOG.info(f"Task {task_id} is still being processed")
            return {"message": status, "task_id": task_id, "filename": result[0][1]}

        if status == "success":
            for attempt in range(max_retries):
                if os.path.exists(md_file_path):
                    with open(md_file_path, "rb") as file:
                        file_data = file.read()
                        base64_data = base64.b64encode(file_data).decode("utf-8")
                    LOG.info(
                        f"File successfully processed and ready for download: {md_file_path}"
                    )
                    return {
                        "message": "success",
                        "task_id": task_id,
                        "filename": os.path.basename(input_file_path),
                        "data": base64_data,
                    }
                else:
                    LOG.info(f"File not found, retrying {attempt + 1}/{max_retries}...")
                    time.sleep(retry_delay)

            LOG.error(f"File not found after {max_retries} retries: {md_file_path}")
            raise HTTPException(
                status_code=500, detail="File not found after processing"
            )

        if status == "error":
            LOG.error(f"Task {task_id} encountered an error during processing")
            raise HTTPException(
                status_code=500, detail="Error occurred during file processing"
            )

    except Exception as e:
        LOG.error(f"Error during file download: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", reload=True)
