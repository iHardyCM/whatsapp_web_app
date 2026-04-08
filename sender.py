# sender.py
import time
import random


def escribir_humano(page, mensaje):
    input_box = page.locator("div[contenteditable='true']").last

    for letra in mensaje:

        # 🔥 salto de línea humano (SHIFT + ENTER)
        if letra == "\n":
            input_box.press("Shift+Enter")
            time.sleep(random.uniform(0.2, 0.5))
            continue

        input_box.type(letra)

        time.sleep(random.uniform(0.04, 0.15))

        if letra in [".", ","]:
            time.sleep(random.uniform(0.3, 0.7))

        # error humano
        if random.random() < 0.015:
            input_box.type("x")
            time.sleep(random.uniform(0.05, 0.1))
            input_box.press("Backspace")

    time.sleep(random.uniform(0.8, 2))


def sesion_activa(page):
    try:
        if page.locator("canvas").count() > 0:
            return False

        if page.locator("text=Usa WhatsApp en tu teléfono").count() > 0:
            return False

        if page.locator("#pane-side").count() > 0:
            return True

        return True

    except:
        return False


def enviar_mensaje(page, numero, mensaje, i):

    url = f"https://web.whatsapp.com/send?phone={numero}&app_absent=0"

    try:
        # 🧠 comportamiento humano: pausa antes de navegar
        if random.random() < 0.4:
            time.sleep(random.randint(2, 5))

        page.goto(url, wait_until="domcontentloaded")

        # 🧠 simular carga + atención
        page.wait_for_timeout(random.randint(2000, 4000))

        # 🔥 validar si no tiene WhatsApp
        try:
            if page.locator("text=invitar a WhatsApp").count() > 0:
                print(f"{i}. ⚠️ Número sin WhatsApp: {numero}")
                return "SIN_WHATSAPP"
        except:
            pass

        # 🧠 simular que "mira el chat"
        if random.random() < 0.5:
            time.sleep(random.randint(2, 6))

        input_box = page.locator("div[contenteditable='true']").last
        input_box.wait_for(timeout=30000)

        input_box.click()

        # 🧠 pausa antes de escribir (como pensar)
        if random.random() < 0.4:
            time.sleep(random.randint(2, 5))

        # ✨ escribir humano
        escribir_humano(page, mensaje)

        # 🧠 pausa antes de enviar
        time.sleep(random.uniform(0.5, 1.5))

        input_box.press("Enter")

        # 🧠 quedarse un rato después de enviar
        page.wait_for_timeout(random.randint(2000, 5000))

        print(f"{i}. ✅ Enviado a {numero}")
        return "ENVIADO"

    except Exception as e:
        print(f"{i}. 🛑 Error con {numero}: {str(e)}")
        return "ERROR"