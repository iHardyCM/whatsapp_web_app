from fastapi import FastAPI, UploadFile, File, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import os
import uuid
import json
import socket
import pandas as pd

from db import existe_proceso_activo, crear_proceso, guardar_envio, get_connection


app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

archivo_actual = None


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    global archivo_actual

    contenido = await file.read()
    archivo_actual = contenido

    return {"mensaje": "Archivo cargado correctamente"}


@app.post("/start")
def start():
    global archivo_actual

    usuario = socket.gethostname()

    if existe_proceso_activo(usuario):
        return {"error": "Ya tienes un proceso en ejecución ⚠️"}

    if not archivo_actual:
        return {"error": "No hay archivo cargado"}

    proceso_id = str(uuid.uuid4())

    from io import BytesIO
    df = pd.read_excel(BytesIO(archivo_actual), dtype=str)

    # 🔥 normalizar columnas
    df.columns = df.columns.str.strip().str.upper()

    required_cols = ["TELEFONO", "TENOR", "DOCUMENTO", "IDCARTERA"]

    for col in required_cols:
        if col not in df.columns:
            return {"error": f"Falta columna: {col}"}

    total = len(df)

    # 🔥 crear proceso
    crear_proceso(
        proceso_id,
        usuario,
        "excel_upload",
        total
    )

    # 🔥 insertar cola en BD
    for row in df.itertuples():

        numero = str(row.TELEFONO).strip()

        documento = str(row.DOCUMENTO).strip()

        # 🔥 limpiar cosas raras tipo 123456.0
        if documento.endswith(".0"):
            documento = documento[:-2]

        # normalizar número (opcional)
        if not numero.startswith("51"):
            numero = "51" + numero

        guardar_envio(
            proceso_id,
            usuario,
            numero,
            str(row.TENOR),
            "PENDIENTE",
            str(row.DOCUMENTO),
            str(row.IDCARTERA),
            "excel_upload"
        )

    # 🔥 estado inicial
    estado = {
        "proceso_id": proceso_id,
        "estado": "PENDIENTE",
        "total": total,
        "enviados": 0,
        "errores": 0
    }

    with open(f"estado_{proceso_id}.json", "w") as f:
        json.dump(estado, f)

    return {
        "mensaje": "Proceso en cola 🟡",
        "proceso_id": proceso_id
    }


@app.get("/status/{proceso_id}")
def status(proceso_id: str):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT total, enviados, errores, estado
        FROM whatsapp_procesos
        WHERE proceso_id = ?
    """, (proceso_id,))

    row = cursor.fetchone()
    conn.close()

    if row:
        total, enviados, errores, estado = row
        return {
            "total": total,
            "enviados": enviados,
            "errores": errores,
            "estado": estado
        }

    return {}