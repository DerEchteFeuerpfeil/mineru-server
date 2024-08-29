import base64
import hashlib
import logging
import os
import queue
import threading
import time
from typing import Optional

import uvicorn
from api.v1.download_models import download_models
from api.v1.logger_config import setup_logging
from api.v1.services.Pdf2MD import processPdf2MD
from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, UploadFile
from SQLiteManager import SQLiteORM
from starlette.middleware.cors import CORSMiddleware
from starlette.status import HTTP_404_NOT_FOUND

setup_logging(is_debug_mode=False)
log = logging.getLogger()

db_file = "minerU-server.db"

sql_create_users_table = """
CREATE TABLE IF NOT EXISTS file_task (
    task_id TEXT PRIMARY KEY,
    file_path TEXT NOT NULL,
    md_file_path TEXT,
    status TEXT
);
"""


def initialize_database():
    db = SQLiteORM(db_file)
    db.create_table(sql_create_users_table)
    db.close()


initialize_database()

current_script_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
app = FastAPI()
origins = ["*"]

app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"]
)


@app.post("/upload")
async def handle(background_task: BackgroundTasks, file: UploadFile = File(...), user_name: Optional[str] = Form(...)):
    try:
        log.info(f"Received upload request: {file.filename} from user {user_name}")
        doc_id = hashlib.md5((file.filename + user_name).encode("utf-8")).hexdigest()

        file_path = os.path.join(current_script_dir, f"{doc_id}")
        if not os.path.exists(file_path):
            os.makedirs(file_path)
        md_file_path = file_path
        file_path = os.path.join(file_path, f"{file.filename}")

        await file.seek(0)
        with open(file_path, "wb") as f:
            while chunk := await file.read(1024):
                f.write(chunk)
        log.info(f"File saved at: {file_path}")

        dbM = SQLiteORM(db_file)
        try:
            dbM.create(
                "file_task",
                {"task_id": doc_id, "file_path": file_path, "md_file_path": md_file_path, "status": "waiting"},
            )
        finally:
            dbM.close()

        return {"message": "success", "task_id": doc_id, "filename": file.filename}
    except Exception as e:
        log.error(f"Error during file upload: {e}")
        return {"message": str(e), "task_id": None, "filename": file.filename}


@app.get("/download/{task_id}")
async def download_file(task_id: str):
    max_retries = 5  # Maximum number of retries before giving up
    retry_delay = 2  # Delay between retries in seconds

    try:
        db = SQLiteORM(db_file)
        try:
            result = db.read("file_task", {"task_id": task_id})
        finally:
            db.close()

        if not result:
            log.warning(f"Task ID {task_id} not found")
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Task ID not found")

        status = result[0][3]
        md_file_path = result[0][2]
        file_path = result[0][1]
        filename = os.path.basename(file_path)
        dest_name = os.path.splitext(filename)[0]

        new_md_file_path = os.path.join(md_file_path, f"{dest_name}.md")

        if status == "waiting" or status == "processing":
            log.info(f"Task {task_id} is still being processed")
            return {"message": status, "task_id": task_id, "filename": result[0][1]}

        if status == "success":
            for attempt in range(max_retries):
                if os.path.exists(new_md_file_path):
                    with open(new_md_file_path, "rb") as file:
                        file_data = file.read()
                        base64_data = base64.b64encode(file_data).decode("utf-8")
                    log.info(f"File successfully processed and ready for download: {new_md_file_path}")
                    return {"message": "success", "task_id": task_id, "filename": result[0][1], "data": base64_data}
                else:
                    log.info(f"File not found, retrying {attempt + 1}/{max_retries}...")
                    time.sleep(retry_delay)

            log.error(f"File not found after {max_retries} retries: {new_md_file_path}")
            raise HTTPException(status_code=500, detail="File not found after processing")

        if status == "error":
            log.error(f"Task {task_id} encountered an error during processing")
            raise HTTPException(status_code=500, detail="Error occurred during file processing")

    except Exception as e:
        log.error(f"Error during file download: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


q = queue.Queue(maxsize=20)


def producer():
    while True:
        try:
            dbP = SQLiteORM(db_file)
            waitingList = dbP.read("file_task", {"status": "waiting"})
            for waiting in waitingList:
                q.put(waiting)
                dbP.update("file_task", {"status": "processing"}, {"task_id": waiting[0]})
        except Exception as e:
            log.error(f"Producer encountered an error: {e}")
        finally:
            dbP.close()
        time.sleep(5)


def consumer():
    while True:
        item = q.get()
        try:
            log.info(f"Processing task {item[0]} from queue")
            success = processPdf2MD(item)
            dbC = SQLiteORM(db_file)
            if success:
                filename = os.path.basename(item[1])
                dest_name, _ = os.path.splitext(filename)
                base_dir = os.path.dirname(item[1])
                full_path = os.path.join(base_dir, dest_name, "auto")
                dbC.update("file_task", {"status": "success", "md_file_path": full_path}, {"task_id": item[0]})
                log.info(f"Task {item[0]} completed successfully")
            else:
                dbC.update("file_task", {"status": "error"}, {"task_id": item[0]})
                log.error(f"Task {item[0]} failed due to an error")
        except Exception as e:
            log.error(f"Consumer encountered an error processing task {item[0]}: {e}")
        finally:
            dbC.close()
            q.task_done()
        time.sleep(1)


@app.on_event("startup")
async def startup_event():
    download_models()
    producer_thread = threading.Thread(target=producer, daemon=True)
    producer_thread.start()

    consumer_thread = threading.Thread(target=consumer, daemon=True)
    consumer_thread.start()


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", reload=True)
