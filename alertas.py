# ============================================================
#  BioCare Dashboard - Modulo 3: Sistema de Alertas
#  Genera alertas automaticas segun 3 reglas y permite
#  enviarlas por correo electronico (smtplib).
# ============================================================
import pandas as pd
from datetime import datetime
import calculos

# Fecha de referencia del sistema (ultima fecha del historial)
FECHA_HOY = pd.Timestamp("2026-05-31")

def generar_alertas(equipos, historial):
    """
    Genera una lista de alertas segun 4 reglas:
    - REGLA 1 (Critica): equipo de criticidad ALTA sin mantenimiento en mas de 30 dias
    - REGLA 2 (Alta): mantenimiento preventivo vencido (mas de 70 dias desde el ultimo preventivo)
    - REGLA 3 (Media): equipo con 3 o mas fallas correctivas en los ultimos 90 dias
    - REGLA 4 (Critica): equipo en estado Inoperativo (situacion mas urgente)
    """
    criticidad = calculos.calcular_criticidad(equipos, historial)
    nivel_por_eq = dict(zip(criticidad["cod"], criticidad["nivel"]))
    # Estados operativos actuales (incluye cambios del usuario)
    eq_estado = calculos.estado_equipos(equipos)
    estado_por_eq = dict(zip(eq_estado["codigo"], eq_estado["estado"]))
    alertas = []

    for cod, g in historial.groupby("codigo_equipo"):
        g = g.sort_values("fecha")
        nombre = equipos[equipos["codigo"]==cod]["nombre"].values[0]
        nivel = nivel_por_eq.get(cod, "BAJO")

        ultima = g["fecha"].max()
        dias_sin_mant = (FECHA_HOY - ultima).days

        # REGLA 4: equipo inoperativo (la mas urgente)
        if estado_por_eq.get(cod) == "Inoperativo":
            alertas.append({
                "equipo": cod, "nombre": nombre, "nivel": "CRITICA",
                "tipo": "Equipo inoperativo",
                "detalle": "El equipo esta fuera de servicio y requiere atencion urgente",
                "dias": dias_sin_mant, "antiguedad": dias_sin_mant, "color": "#d94862"
            })

        # REGLA 1: criticidad alta sin mantenimiento reciente
        if nivel == "ALTO" and dias_sin_mant > 30:
            alertas.append({
                "equipo": cod, "nombre": nombre, "nivel": "CRITICA",
                "tipo": "Equipo critico sin intervencion",
                "detalle": f"{dias_sin_mant} dias sin mantenimiento (criticidad alta)",
                "dias": dias_sin_mant, "antiguedad": dias_sin_mant, "color": "#d94862"
            })

        # REGLA 2: preventivo vencido
        prev = g[g["tipo_mantenimiento"]=="Preventivo"]
        if len(prev) > 0:
            ultimo_prev = prev["fecha"].max()
            dias_prev = (FECHA_HOY - ultimo_prev).days
            if dias_prev > 70:
                alertas.append({
                    "equipo": cod, "nombre": nombre, "nivel": "ALTA",
                    "tipo": "Mantenimiento preventivo vencido",
                    "detalle": f"{dias_prev} dias desde el ultimo preventivo (proximo al limite de 90)",
                    "dias": dias_prev, "antiguedad": dias_prev - 70, "color": "#dd9324"
                })

        # REGLA 3: fallas recurrentes recientes
        corr = g[g["tipo_mantenimiento"]=="Correctivo"]
        recientes = corr[corr["fecha"] > (FECHA_HOY - pd.Timedelta(days=90))]
        if len(recientes) >= 3:
            ultima_falla = recientes["fecha"].max()
            dias_ultima = (FECHA_HOY - ultima_falla).days
            alertas.append({
                "equipo": cod, "nombre": nombre, "nivel": "MEDIA",
                "tipo": "Fallas recurrentes",
                "detalle": f"{len(recientes)} fallas correctivas en los ultimos 90 dias",
                "dias": 0, "antiguedad": dias_ultima, "color": "#6c5ce0"
            })

    # Ordenar: criticas primero
    orden = {"CRITICA":0, "ALTA":1, "MEDIA":2}
    alertas.sort(key=lambda a: orden.get(a["nivel"], 9))
    return alertas


def construir_correo(alertas):
    """Construye el texto del correo de alertas (lo que se enviaria)."""
    if not alertas:
        return "No hay alertas activas en este momento."
    criticas = sum(1 for a in alertas if a["nivel"]=="CRITICA")
    altas = sum(1 for a in alertas if a["nivel"]=="ALTA")
    medias = sum(1 for a in alertas if a["nivel"]=="MEDIA")

    texto = "SISTEMA BIOCARE DASHBOARD - REPORTE DE ALERTAS\n"
    texto += "Bioingenieros SAC | INCOR - EsSalud\n"
    texto += f"Fecha: {FECHA_HOY.strftime('%d/%m/%Y')}\n"
    texto += "="*50 + "\n\n"
    texto += f"Resumen: {len(alertas)} alertas activas "
    texto += f"({criticas} criticas, {altas} altas, {medias} medias)\n\n"
    for i, a in enumerate(alertas, 1):
        texto += f"{i}. [{a['nivel']}] {a['equipo']} - {a['nombre']}\n"
        texto += f"   {a['tipo']}: {a['detalle']}\n\n"
    texto += "="*50 + "\n"
    texto += "Este es un mensaje automatico del sistema BioCare Dashboard.\n"
    return texto


def enviar_correo_real(destinatario, asunto, cuerpo,
                       remitente, password, servidor="smtp.gmail.com", puerto=587):
    """
    Envia un correo REAL usando smtplib.
    NOTA: requiere credenciales validas. En la demo no se ejecuta
    automaticamente; se deja listo para cuando se configure.
    """
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    mensaje = MIMEMultipart()
    mensaje["From"] = remitente
    mensaje["To"] = destinatario
    mensaje["Subject"] = asunto
    mensaje.attach(MIMEText(cuerpo, "plain"))

    servidor_smtp = smtplib.SMTP(servidor, puerto)
    servidor_smtp.starttls()
    servidor_smtp.login(remitente, password)
    servidor_smtp.send_message(mensaje)
    servidor_smtp.quit()
    return True

def enviar_reporte_alertas(destinatario, cuerpo):
    """
    Envia el reporte de alertas al destinatario.

    Funciona en dos modos automaticamente:
    - MODO REAL: si existen las variables de entorno BIOCARE_EMAIL y
      BIOCARE_EMAIL_PASS, envia el correo de verdad por smtplib.
    - MODO DEMO: si no estan configuradas, simula el envio de forma
      segura (no expone ninguna credencial) y devuelve un mensaje de exito.

    Esto permite demostrar el envio en la sustentacion sin riesgo, y
    activar el envio real cuando se configuren las credenciales.

    Devuelve (exito, modo, mensaje).
    """
    import os
    remitente = os.environ.get("BIOCARE_EMAIL")
    password = os.environ.get("BIOCARE_EMAIL_PASS")
    asunto = "BioCare Dashboard - Reporte de Alertas de Mantenimiento"

    # MODO REAL: solo si ambas credenciales estan configuradas
    if remitente and password:
        try:
            enviar_correo_real(destinatario, asunto, cuerpo, remitente, password)
            return (True, "real", f"Correo enviado correctamente a {destinatario} desde {remitente}.")
        except Exception as e:
            return (False, "real", f"Error al enviar el correo real: {str(e)}")

    # MODO DEMO: simulacion segura (sin credenciales)
    return (True, "demo",
            f"[MODO DEMO] El reporte se genero correctamente y esta listo para enviarse a {destinatario}. "
            f"El envio real se activa configurando las credenciales de forma segura (variables de entorno).")


# Prueba
if __name__ == "__main__":
    equipos, historial = calculos.cargar_datos()
    alertas = generar_alertas(equipos, historial)
    print(f"Alertas generadas: {len(alertas)}")
    print(f"  Criticas: {sum(1 for a in alertas if a['nivel']=='CRITICA')}")
    print(f"  Altas:    {sum(1 for a in alertas if a['nivel']=='ALTA')}")
    print(f"  Medias:   {sum(1 for a in alertas if a['nivel']=='MEDIA')}")
    print("\nPrimeras 5 alertas:")
    for a in alertas[:5]:
        print(f"  [{a['nivel']}] {a['equipo']} - {a['tipo']}: {a['detalle']}")
    print("\n--- Vista previa del correo ---")
    print(construir_correo(alertas)[:400])
