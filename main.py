from fastapi import FastAPI, UploadFile, File, Request, BackgroundTasks
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import shutil
import os
import uuid
import json
from sender import ejecutar_envio
from db import existe_proceso_activo
import socket
import uuid

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

templates = Jinja2Templates(directory="templates")

archivo_actual = None
proceso_actual = None


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    global archivo_actual

    ruta = os.path.join(UPLOAD_DIR, file.filename)

    with open(ruta, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    archivo_actual = ruta

    return {"mensaje": "Archivo cargado correctamente"}


@app.post("/start")
def start(background_tasks: BackgroundTasks):
    global archivo_actual

    usuario = socket.gethostname()

    # 🚫 BLOQUEO POR USUARIO (NO GLOBAL)
    if existe_proceso_activo(usuario):
        return {"error": "Ya tienes un proceso en ejecución ⚠️"}

    if not archivo_actual:
        return {"error": "No hay archivo cargado"}

    proceso_id = str(uuid.uuid4())

    estado = {
        "proceso_id": proceso_id,
        "estado": "EN_PROCESO",
        "total": 0,
        "enviados": 0,
        "errores": 0
    }

    with open("estado.json", "w") as f:
        json.dump(estado, f)

    background_tasks.add_task(
        ejecutar_envio,
        archivo_actual,
        proceso_id
    )

    return {
        "mensaje": "Envío iniciado 🚀",
        "proceso_id": proceso_id
    }


@app.get("/status")
def status():
    if os.path.exists("estado.json"):
        with open("estado.json") as f:
            return json.load(f)
    return {}