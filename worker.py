import time
import socket
import random
from playwright.sync_api import sync_playwright
from sender import enviar_mensaje, sesion_activa
from db import (
    obtener_y_bloquear_envio,
    actualizar_envio,
    actualizar_proceso,
    get_connection
)

usuario = socket.gethostname()

print(f"🟢 Worker iniciado en {usuario}")


with sync_playwright() as p:

    context = p.chromium.launch_persistent_context(
        user_data_dir=f"sesiones/{usuario}",
        headless=False,
        args=["--start-maximized"]
    )

    page = context.pages[0] if context.pages else context.new_page()

    print("📱 Abriendo WhatsApp...")
    page.goto("https://web.whatsapp.com")
    page.wait_for_timeout(60000)  # QR

    while True:
        try:

            # 🔒 validar sesión
            if not sesion_activa(page):
                print("🔒 Sesión caída - esperando reconexión...")

                start_time = time.time()

                while not sesion_activa(page):
                    if time.time() - start_time > 300:
                        print("❌ Sesión no recuperada")
                        break
                    time.sleep(5)

                print("✅ Sesión reestablecida")
                page.goto("https://web.whatsapp.com")
                page.wait_for_timeout(5000)

            # 📥 obtener envío
            envio = obtener_y_bloquear_envio(usuario)

            if envio:
                id_envio, numero, mensaje, intento = envio

                print(f"📤 Procesando {numero}")

                # 🔥 comportamiento humano: solo leer
                if random.random() < 0.15:
                    print(f"👀 Solo leyendo chat {numero}")

                    page.goto(f"https://web.whatsapp.com/send?phone={numero}&app_absent=0")
                    time.sleep(random.randint(5, 10))

                    actualizar_envio(id_envio, "LEIDO")

                    time.sleep(random.randint(5, 15))
                    continue

                # 🧠 pausa antes de actuar
                if random.random() < 0.3:
                    time.sleep(random.randint(2, 6))

                try:
                    resultado = enviar_mensaje(page, numero, mensaje, id_envio)

                    # 🔥 lógica de reintento
                    if resultado == "ENVIADO":
                        actualizar_envio(id_envio, "ENVIADO")

                    elif resultado == "SIN_WHATSAPP":
                        actualizar_envio(id_envio, "SIN_WHATSAPP")

                    else:
                        if intento >= 2:
                            actualizar_envio(id_envio, "ERROR_FINAL")
                        else:
                            actualizar_envio(id_envio, "REINTENTO")

                except Exception as e:
                    print(f"❌ Error: {e}")
                    actualizar_envio(id_envio, "ERROR", str(e))

                # 🔥 actualizar métricas del proceso (DASHBOARD)
                conn = get_connection()
                cursor = conn.cursor()

                # enviados y errores
                cursor.execute("""
                    SELECT 
                        SUM(CASE WHEN estado = 'ENVIADO' THEN 1 ELSE 0 END),
                        SUM(CASE WHEN estado = 'ERROR_FINAL' THEN 1 ELSE 0 END)
                    FROM whatsapp_envios
                    WHERE proceso_id = (
                        SELECT proceso_id FROM whatsapp_envios WHERE id = ?
                    )
                """, (id_envio,))

                enviados, errores = cursor.fetchone()
                enviados = enviados or 0
                errores = errores or 0

                # obtener proceso_id
                cursor.execute("""
                    SELECT proceso_id 
                    FROM whatsapp_envios 
                    WHERE id = ?
                """, (id_envio,))

                proceso_id = cursor.fetchone()[0]

                actualizar_proceso(proceso_id, enviados, errores)

                # 🔥 verificar si terminó
                cursor.execute("""
                    SELECT COUNT(*)
                    FROM whatsapp_envios
                    WHERE proceso_id = ?
                    AND estado IN ('PENDIENTE','REINTENTO','EN_PROCESO')
                """, (proceso_id,))

                pendientes = cursor.fetchone()[0]

                if pendientes == 0:
                    actualizar_proceso(proceso_id, enviados, errores, "FINALIZADO")

                conn.close()

                # 🔥 pausa post envío
                if random.random() < 0.2:
                    time.sleep(random.randint(10, 20))

            else:
                print("⏳ Sin envíos pendientes...")

            # ⏱️ delay base
            time.sleep(random.randint(3, 7))

        except Exception as e:
            print(f"🛑 Error general: {e}")
            time.sleep(10)