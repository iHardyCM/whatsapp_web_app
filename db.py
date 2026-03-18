import pyodbc

def get_connection():
    return pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=192.168.7.247;"
        "DATABASE=CobAuto;"
        "UID=analista;"
        "PWD=Analista$2025;"
    )


def guardar_envio(proceso_id, usuario, archivo, numero, mensaje, estado, observacion=None):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO whatsapp_envios 
        (proceso_id, usuario, archivo_nombre, numero, mensaje, estado, observacion)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, proceso_id, usuario, archivo, numero, mensaje, estado, observacion)

    conn.commit()
    conn.close()


def crear_proceso(proceso_id, usuario, archivo, total):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO whatsapp_procesos
        (proceso_id, usuario, archivo_nombre, total, enviados, errores, estado)
        VALUES (?, ?, ?, ?, 0, 0, 'EN_PROCESO')
    """, proceso_id, usuario, archivo, total)

    conn.commit()
    conn.close()


def actualizar_proceso(proceso_id, enviados, errores, estado=None):
    conn = get_connection()
    cursor = conn.cursor()

    if estado:
        cursor.execute("""
            UPDATE whatsapp_procesos
            SET enviados=?, errores=?, estado=?, fecha_fin=GETDATE()
            WHERE proceso_id=?
        """, enviados, errores, estado, proceso_id)
    else:
        cursor.execute("""
            UPDATE whatsapp_procesos
            SET enviados=?, errores=?
            WHERE proceso_id=?
        """, enviados, errores, proceso_id)

    conn.commit()
    conn.close()


def existe_proceso_activo(usuario):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM whatsapp_procesos
        WHERE usuario = ?
        AND estado = 'EN_PROCESO'
    """, (usuario,))

    result = cursor.fetchone()[0]

    conn.close()
    return result > 0