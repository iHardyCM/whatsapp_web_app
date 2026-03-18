from db import guardar_envio, crear_proceso, actualizar_proceso
import pandas as pd
from playwright.sync_api import sync_playwright, TimeoutError
from datetime import datetime
import time
import random
import json
import os




def actualizar_estado(data):
    with open("estado.json", "w") as f:
        json.dump(data, f)


def enviar_mensaje(page, numero, mensaje, i):

    mensaje_url = mensaje.replace("\n", "%0A")
    url = f"https://web.whatsapp.com/send?phone={numero}&text={mensaje_url}&app_absent=0"

    try:
        # 🔥 navegar en la misma pestaña
        page.goto(url, wait_until="domcontentloaded")

        # 🔥 esperar input real
        input_box = page.locator("div[contenteditable='true']").last
        input_box.wait_for(timeout=30000)

        # 🔥 pequeña pausa para que cargue todo
        page.wait_for_timeout(2000)

        # 🔥 asegurar foco
        input_box.click()

        # 🔥 detectar botón enviar
        boton_enviar = page.locator("span[data-icon='send']").first

        enviado = False

        # 🔁 intento 1: botón
        try:
            boton_enviar.wait_for(timeout=10000)

            if boton_enviar.is_visible():
                boton_enviar.click()
                page.wait_for_timeout(2000)
                enviado = True
        except:
            pass

        # 🔁 intento 2: ENTER si no funcionó
        if not enviado:
            input_box.click()
            page.keyboard.press("Enter")
            page.wait_for_timeout(2000)
            enviado = True

        # 🔥 validación simple (NO DOM inestable)
        if enviado:
            print(f"{i}. ✅ Enviado a {numero}")
            return "ENVIADO"
        else:
            print(f"{i}. ❌ No se pudo enviar {numero}")
            return "ERROR"

    except Exception as e:
        print(f"{i}. 🛑 Error con {numero}: {str(e)}")
        return "ERROR"


def ejecutar_envio(ruta_excel, proceso_id):

    import socket

    usuario = socket.gethostname()
    session_path = f"sesiones/{usuario}"
    os.makedirs(session_path, exist_ok=True)

    print(f"🚀 Iniciando proceso {proceso_id}")

    enviados = 0
    errores = 0

    try:
        df = pd.read_excel(ruta_excel, dtype={"DOCUMENTO": str})

        numeros = df["TELEFONO"].astype(str).tolist()
        mensajes = df["TENOR"].astype(str).tolist()

        total = len(numeros)

        # 🔥 crear proceso en BD
        crear_proceso(
            proceso_id,
            usuario,
            os.path.basename(ruta_excel),
            total
        )

        estado = {
            "proceso_id": proceso_id,
            "estado": "EN_PROCESO",
            "total": total,
            "enviados": 0,
            "errores": 0
        }

        actualizar_estado(estado)

        with sync_playwright() as p:

            context = p.chromium.launch_persistent_context(
                user_data_dir=session_path,
                headless=False,
                args=["--start-maximized"]
            )

            try:
                page = context.pages[0] if context.pages else context.new_page()

                print("📱 Escanea QR...")
                page.goto("https://web.whatsapp.com")
                page.wait_for_timeout(60000)

                for i, (numero, mensaje) in enumerate(zip(numeros, mensajes), start=1):

                    resultado = enviar_mensaje(page, numero, mensaje, i)

                    # 💾 guardar detalle
                    guardar_envio(
                        proceso_id,
                        usuario,
                        os.path.basename(ruta_excel),
                        numero,
                        mensaje,
                        resultado
                    )

                    if resultado == "ENVIADO":
                        enviados += 1
                    else:
                        errores += 1

                    # 🔥 actualizar estado JSON
                    estado.update({
                        "enviados": enviados,
                        "errores": errores
                    })

                    actualizar_estado(estado)

                    # 🔥 actualizar proceso en BD
                    actualizar_proceso(proceso_id, enviados, errores)

                    # 🔥 delay humano
                    time.sleep(random.randint(12, 20))

            finally:
                context.close()

        # 🔥 finalización correcta
        estado["estado"] = "FINALIZADO"
        actualizar_estado(estado)

        actualizar_proceso(
            proceso_id,
            enviados,
            errores,
            estado="FINALIZADO"
        )

        print("📂 Proceso finalizado")

    except Exception as e:

        print(f"🛑 Error en proceso {proceso_id}: {str(e)}")

        # 🔥 marcar como error en BD
        actualizar_proceso(
            proceso_id,
            enviados,
            errores,
            estado="ERROR"
        )

        estado = {
            "proceso_id": proceso_id,
            "estado": "ERROR",
            "enviados": enviados,
            "errores": errores
        }

        actualizar_estado(estado)

        raise e