# bd.py
import pyodbc

def get_connection():
    return pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=192.168.7.247;"
        "DATABASE=CobAuto;"
        "UID=analista;"
        "PWD=Analista$2025;"
    )


def guardar_envio(
    proceso_id,
    usuario,
    numero,
    mensaje,
    estado,
    documento,
    idcartera,
    archivo
):
    conn = get_connection()
    cursor = conn.cursor()

    numero = str(numero).strip()
    mensaje = str(mensaje).strip()
    documento = str(documento).strip()
    idcartera = str(idcartera).strip()

    cursor.execute("""
        INSERT INTO whatsapp_envios 
        (proceso_id, usuario, archivo_nombre, numero, mensaje, estado, documento, idcartera, intento)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)
    """, proceso_id, usuario, archivo, numero, mensaje, estado, documento, idcartera)

    conn.commit()
    conn.close()


def crear_proceso(proceso_id, usuario, archivo, total):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO whatsapp_procesos
        (proceso_id, usuario, archivo_nombre, total, enviados, errores, estado)
        VALUES (?, ?, ?, ?, 0, 0, 'PENDIENTE')
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


def obtener_y_bloquear_envio(usuario):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE TOP (1) whatsapp_envios
        SET estado = 'EN_PROCESO'
        OUTPUT 
            INSERTED.id, 
            INSERTED.numero, 
            INSERTED.mensaje, 
            ISNULL(INSERTED.intento, 0)
        WHERE id = (
            SELECT TOP 1 id
            FROM whatsapp_envios
            WHERE usuario = ?
            AND (
                estado IN ('PENDIENTE', 'REINTENTO')
                
                -- 🔥 RECUPERA PROCESOS TRABADOS
                OR (
                    estado = 'EN_PROCESO' 
                    AND DATEDIFF(MINUTE, fecha_envio, GETDATE()) > 5
                )
            )
            AND ISNULL(intento, 0) < 3
            ORDER BY id ASC
        )
    """, (usuario,))

    row = cursor.fetchone()
    conn.commit()
    conn.close()

    return row


def actualizar_envio(id_envio, estado, observacion=None):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE whatsapp_envios
        SET estado = ?, 
            observacion = ?, 
            fecha_envio = GETDATE(),
            intento = ISNULL(intento, 0) + 1
        WHERE id = ?
    """, estado, observacion, id_envio)

    conn.commit()
    conn.close()