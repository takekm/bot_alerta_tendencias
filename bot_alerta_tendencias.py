#Importamos librerías
import yfinance as yf
import pandas as pd
import numpy as np
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import datetime
from datetime import timedelta
from html import escape

#Tickers a evaluar
tickers=["XLF.BA","XLK.BA","XLE.BA","ARKK.BA","QQQ.BA","SPY.BA","MSFT.BA","AAPL.BA","AMZN.BA","GOOGL.BA","IBM.BA","KO.BA","MCD.BA","MELI.BA","CELU.BA","HARG.BA","LOMA.BA","MOLI.BA","PAMP.BA","TXAR.BA","YPFD.BA","TM.BA","XOM.BA","JNJ.BA","PG.BA","GGAL.BA","TSM.BA"]

tickers_cedear = [
    "XLF.BA","XLK.BA","XLE.BA","ARKK.BA","QQQ.BA","SPY.BA",  # ETFs
    "MSFT.BA","AAPL.BA","AMZN.BA","GOOGL.BA","IBM.BA","KO.BA","MCD.BA",
    "MELI.BA","TM.BA","XOM.BA","JNJ.BA","PG.BA","TSM.BA"
]

tickers_acciones = ["CELU.BA","HARG.BA","LOMA.BA","MOLI.BA","PAMP.BA","TXAR.BA","YPFD.BA","GGAL.BA"]

#Declaramos fechas
fecha_hoy = datetime.date.today()
fecha_cierre = fecha_hoy+ timedelta(days=1) #Agregar un día porque la descarga de yfinance es exclusivo en su límite superior.
fecha_inicio = fecha_cierre - datetime.timedelta(days=180)
#Pasamos a string
fecha_hoy_str=fecha_hoy.strftime("%Y-%m-%d")
fecha_cierre_str=fecha_cierre.strftime("%Y-%m-%d")
fecha_inicio_str=fecha_inicio.strftime("%Y-%m-%d")

#Datos de autenticación de mailing
smtp_server = "smtp.gmail.com"
smtp_port = 587
remitente = "tkamada07@gmail.com"
password = "jfiv fmlb mzfq uxap"  
destinatario = "takeshikamada@hotmail.com"
mensaje = MIMEMultipart()
mensaje["From"] = "BOT Python - Take"
mensaje["To"] = destinatario
mensaje["Subject"] = "Resumen de tendencias"

#Funcón para formatear separadores de miles con . y decimales con ,
def formatear_numero(valor):
    try:
        # 1. Redondeamos
        num = round(float(valor),1)
        # 2. Usamos formato estándar con ',' como miles y '.' como decimal
        s = f"{num:,.1f}"   
        # 3. Invertimos separadores: ',' -> '.' y '.' -> ','
        s = s.replace(",", "X").replace(".", ",").replace("X", ".")
        return s
    except (ValueError, TypeError):
        return "Sin Dato"


# Registros tabulares (además de los mensajes de texto)
registros_cedear   = []
registros_acciones = []
registros_general  = []

def agregar_registro(a_que_lista, ticker, señal, SMALP_LD, SMALP_TD, SMACP_LD, SMACP_TD,
                     streak_ruedas=None, dias_calendario=None):
    a_que_lista.append({
        "Ticker": ticker,
        "Señal": señal,
        "SMA20_ayer": SMALP_LD,
        "SMA20_hoy":  SMALP_TD,
        "SMA5_ayer":  SMACP_LD,
        "SMA5_hoy":   SMACP_TD,
        "Rachas (ruedas)": streak_ruedas if streak_ruedas is not None else "—",
        "Rachas (días)":   dias_calendario if dias_calendario is not None else "—",
    })



#Lista y df vacíos
df_precios_concatenado=pd.DataFrame()
mensajes_general=[]
mensajes_cedear=[]
mensajes_acciones=[]
#Recorremos cada ticker
for ticker in tickers:
    data = yf.download(ticker, start=fecha_inicio_str, end=fecha_cierre_str, progress=False)
    data.columns = data.columns.get_level_values(0)
    # 1) No romper si no hay datos
    if data is None or data.empty:
        mensajes_general.append(f"{ticker}: sin datos en el rango.")
        continue

    df = data.reset_index().copy()
    df["Ticker"] = ticker
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values("Date")

    # 2) SMAs con min_periods para evitar señales prematuras
    df["SMA5"]  = df["Close"].rolling(5,  min_periods=5).mean()
    df["SMA20"] = df["Close"].rolling(20, min_periods=20).mean()

    if len(df.tail(2))>=2:
        SMALP_LD =df["SMA20"].iloc[-2]
        SMACP_LD=df["SMA5"].iloc[-2]
    else:
        SMALP_LD ="Sin Dato"
        SMACP_LD= "Sin Dato"
    
    if len(df.tail(2))>=1:
        SMALP_TD =df["SMA20"].iloc[-1]
        SMACP_TD=df["SMA5"].iloc[-1]
    else:
        SMALP_TD ="Sin Dato"
        SMACP_TD= "Sin Dato"
    
    #Formateamos 
    SMALP_LD=formatear_numero(SMALP_LD)
    SMACP_LD=formatear_numero(SMACP_LD)
    SMALP_TD=formatear_numero(SMALP_TD)
    SMACP_TD=formatear_numero(SMACP_TD)
    

    # 3) Estado solo donde haya ambas SMAs
    estado = pd.Series(index=df.index, dtype="object")
    mask_ok = df["SMA5"].notna() & df["SMA20"].notna()
    estado[mask_ok] = np.where(df.loc[mask_ok, "SMA5"] > df.loc[mask_ok, "SMA20"], "Alcista", "Bajista")

    # --- cálculo de streak del estado actual ---
    estado_valid   = estado[mask_ok]                  # solo donde hay SMA5 y SMA20
    fechas_valid   = df.loc[mask_ok, "Date"]

    if estado_valid.dropna().empty:
        streak_ruedas = None
        dias_calendario = None
    else:
        # Agrupar por rachas consecutivas (run-length encoding)
        grupos = (estado_valid != estado_valid.shift()).cumsum()
        tamanio_grupo = grupos.groupby(grupos).transform("size")
        # Racha actual = tamaño del último grupo
        streak_ruedas = int(tamanio_grupo.iloc[-1])

        # También podés calcular días de calendario (incluye fines de semana)
        inicio_racha = fechas_valid.groupby(grupos).transform("first").iloc[-1]
        fin_racha    = fechas_valid.iloc[-1]
        dias_calendario = (fin_racha - inicio_racha).days + 1  # +1 para contar el día inicial


    # 4) Tomar los últimos DOS estados válidos
    ult2 = estado.dropna().tail(2)
   

    if len(ult2) < 2:
        mensajes_general.append(f"{ticker}: datos insuficientes")
        # igual acumulá el df si lo usás después
        df_precios_concatenado = pd.concat([df_precios_concatenado, df], ignore_index=True)
        continue

    prev, curr = ult2.iloc[-2], ult2.iloc[-1]

    if prev == "Alcista" and curr == "Bajista":
        if ticker in tickers_cedear:
            mensajes_cedear.append(f"{ticker}: Inicio de tendencia Bajista → VENDER | SMA20 ayer: ${SMALP_LD} - SMA20 hoy: ${SMALP_TD} | SMA5 ayer: ${SMACP_LD} - SMA5 hoy: ${SMACP_TD}")
            señal="Inicio de tendencia Bajista → VENDER"
            agregar_registro(registros_cedear, ticker, señal, SMALP_LD, SMALP_TD, SMACP_LD, SMACP_TD,streak_ruedas=streak_ruedas, dias_calendario=dias_calendario)
        elif ticker in tickers_acciones:
            mensajes_acciones.append(f"{ticker}: Inicio de tendencia Bajista → VENDER | SMA20 ayer: ${SMALP_LD} - SMA20 hoy: ${SMALP_TD} | SMA5 ayer: ${SMACP_LD} - SMA5 hoy: ${SMACP_TD}")
            señal="Inicio de tendencia Bajista → VENDER"
            agregar_registro(registros_acciones, ticker, señal, SMALP_LD, SMALP_TD, SMACP_LD, SMACP_TD,streak_ruedas=streak_ruedas, dias_calendario=dias_calendario)
        else:
            mensajes_general.append(f"{ticker}: Inicio de tendencia Bajista → VENDER | SMA20 ayer: ${SMALP_LD} - SMA20 hoy: ${SMALP_TD} | SMA5 ayer: ${SMACP_LD} - SMA5 hoy: ${SMACP_TD}")
            señal="Inicio de tendencia Bajista → VENDER"
            agregar_registro(registros_general, ticker, señal, SMALP_LD, SMALP_TD, SMACP_LD, SMACP_TD,streak_ruedas=streak_ruedas, dias_calendario=dias_calendario)
    elif prev == "Bajista" and curr == "Alcista":
        if ticker in tickers_cedear:
            mensajes_cedear.append(f"{ticker}: Inicio de tendencia Alcista → COMPRAR | SMA20 ayer: ${SMALP_LD} - SMA20 hoy: ${SMALP_TD} | SMA5 ayer: ${SMACP_LD} - SMA5 hoy: ${SMACP_TD}")
            señal="Inicio de tendencia Alcista → COMPRAR"
            agregar_registro(registros_cedear, ticker, señal, SMALP_LD, SMALP_TD, SMACP_LD, SMACP_TD,streak_ruedas=streak_ruedas, dias_calendario=dias_calendario)
        elif ticker in tickers_acciones:
            mensajes_acciones.append(f"{ticker}: Inicio de tendencia Alcista → COMPRAR | SMA20 ayer: ${SMALP_LD} - SMA20 hoy: ${SMALP_TD} | SMA5 ayer: ${SMACP_LD} - SMA5 hoy: ${SMACP_TD}")
            señal="Inicio de tendencia Alcista → COMPRAR"
            agregar_registro(registros_acciones, ticker, señal, SMALP_LD, SMALP_TD, SMACP_LD, SMACP_TD,streak_ruedas=streak_ruedas, dias_calendario=dias_calendario)
        else:
            mensajes_general.append(f"{ticker}: Inicio de tendencia Alcista → COMPRAR | SMA20 ayer: ${SMALP_LD} - SMA20 hoy: ${SMALP_TD} | SMA5 ayer: ${SMACP_LD} - SMA5 hoy: ${SMACP_TD}")
            señal="Inicio de tendencia Alcista → COMPRAR"
            agregar_registro(registros_general, ticker, señal, SMALP_LD, SMALP_TD, SMACP_LD, SMACP_TD,streak_ruedas=streak_ruedas, dias_calendario=dias_calendario)
    elif prev == "Bajista" and curr == "Bajista":
        if ticker in tickers_cedear:
            mensajes_cedear.append(f"{ticker}: Se mantiene Bajista | SMA20 ayer: ${SMALP_LD} - SMA20 hoy: ${SMALP_TD} | SMA5 ayer: ${SMACP_LD} - SMA5 hoy: ${SMACP_TD}")
            señal="Se mantiene Bajista"
            agregar_registro(registros_cedear, ticker, señal, SMALP_LD, SMALP_TD, SMACP_LD, SMACP_TD,streak_ruedas=streak_ruedas, dias_calendario=dias_calendario)
        elif ticker in tickers_acciones:
            mensajes_acciones.append(f"{ticker}: Se mantiene Bajista | SMA20 ayer: ${SMALP_LD} - SMA20 hoy: ${SMALP_TD} | SMA5 ayer: ${SMACP_LD} - SMA5 hoy: ${SMACP_TD}")
            señal="Se mantiene Bajista"
            agregar_registro(registros_acciones, ticker, señal, SMALP_LD, SMALP_TD, SMACP_LD, SMACP_TD,streak_ruedas=streak_ruedas, dias_calendario=dias_calendario)
        else:
            mensajes_general.append(f"{ticker}: Se mantiene Bajista | SMA20 ayer: ${SMALP_LD} - SMA20 hoy: ${SMALP_TD} | SMA5 ayer: ${SMACP_LD} - SMA5 hoy: ${SMACP_TD}")
            señal="Se mantiene Bajista"
            agregar_registro(registros_general, ticker, señal, SMALP_LD, SMALP_TD, SMACP_LD, SMACP_TD,streak_ruedas=streak_ruedas, dias_calendario=dias_calendario)
    else:
        if ticker in tickers_cedear:
            mensajes_cedear.append(f"{ticker}: Se mantiene Alcista | SMA20 ayer: ${SMALP_LD} - SMA20 hoy: ${SMALP_TD} | SMA5 ayer: ${SMACP_LD} - SMA5 hoy: ${SMACP_TD}")
            señal="Se mantiene Alcista"
            agregar_registro(registros_cedear, ticker, señal, SMALP_LD, SMALP_TD, SMACP_LD, SMACP_TD,streak_ruedas=streak_ruedas, dias_calendario=dias_calendario)
        elif ticker in tickers_acciones:
            mensajes_acciones.append(f"{ticker}: Se mantiene Alcista | SMA20 ayer: ${SMALP_LD} - SMA20 hoy: ${SMALP_TD} | SMA5 ayer: ${SMACP_LD} - SMA5 hoy: ${SMACP_TD}")
            señal="Se mantiene Alcista"
            agregar_registro(registros_acciones, ticker, señal, SMALP_LD, SMALP_TD, SMACP_LD, SMACP_TD,streak_ruedas=streak_ruedas, dias_calendario=dias_calendario)
        else:
            mensajes_general.append(f"{ticker}: Se mantiene Alcista | SMA20 ayer: ${SMALP_LD} - SMA20 hoy: ${SMALP_TD} | SMA5 ayer: ${SMACP_LD} - SMA5 hoy: ${SMACP_TD}")
            señal="Se mantiene Alcista"
            agregar_registro(registros_general, ticker, señal, SMALP_LD, SMALP_TD, SMACP_LD, SMACP_TD,streak_ruedas=streak_ruedas, dias_calendario=dias_calendario)


    df_precios_concatenado = pd.concat([df_precios_concatenado, df], ignore_index=True)


def construir_lista_html(items):
    """Convierte una lista de strings en <li> con color según la señal."""
    if not items:
        return '<li style="color:#6b7280;">— Sin señales —</li>'

    li = []
    for it in items:
        txt = escape(it)  # evita problemas con caracteres especiales
        estilo = "color:#111827;"  # negro por defecto

        # Heurística simple para colorear
        lower = it.lower()
        if "comprar" in lower or "alcista" in lower:
            estilo = "color:#065f46;"  # verde oscuro
        if "vender" in lower or "bajista" in lower:
            estilo = "color:#991b1b;"  # rojo oscuro
        if "se mantiene" in lower:
            estilo = "color:#374151;"  # gris

        li.append(f'<li style="{estilo}; margin:4px 0;">{txt}</li>')
    return "\n".join(li)

def construir_tabla_html(registros, titulo):
    if not registros:
        return f"""
        <h3 style="margin:16px 0 8px 0; color:#111827;">{titulo}</h3>
        <div style="color:#6b7280; font-size:14px; margin:8px 0 16px 0;">— Sin señales —</div>
        """

    # Estilo de la tabla
    thead = """
    <thead>
      <tr>
        <th style="text-align:left; padding:8px; border-bottom:1px solid #e5e7eb;">Ticker</th>
        <th style="text-align:left; padding:8px; border-bottom:1px solid #e5e7eb;">Señal</th>
        <th style="text-align:right; padding:8px; border-bottom:1px solid #e5e7eb;">SMA20 ayer</th>
        <th style="text-align:right; padding:8px; border-bottom:1px solid #e5e7eb;">SMA20 hoy</th>
        <th style="text-align:right; padding:8px; border-bottom:1px solid #e5e7eb;">SMA5 ayer</th>
        <th style="text-align:right; padding:8px; border-bottom:1px solid #e5e7eb;">SMA5 hoy</th>
        <th style="text-align:right; padding:8px; border-bottom:1px solid #e5e7eb;">Racha (ruedas)</th>
        <th style="text-align:right; padding:8px; border-bottom:1px solid #e5e7eb;">Racha (días)</th>
      </tr>
    </thead>
    """

    filas = []
    for r in registros:
        señal_low = r["Señal"].lower()
        color = "#111827"        # negro
        bg    = "transparent"    # fondo
        if "comprar" in señal_low or "alcista" in señal_low:
            color = "#065f46"    # verde oscuro
            bg    = "#ecfdf5"
        if "vender" in señal_low or "bajista" in señal_low:
            color = "#991b1b"    # rojo oscuro
            bg    = "#fef2f2"
        if "se mantiene" in señal_low:
            color = "#374151"
            bg    = "#f9fafb"

        filas.append(f"""
        <tr style="background:{bg};">
          <td style="padding:8px; border-bottom:1px solid #f3f4f6;">{r['Ticker']}</td>
          <td style="padding:8px; border-bottom:1px solid #f3f4f6; color:{color};">{r['Señal']}</td>
          <td style="padding:8px; border-bottom:1px solid #f3f4f6; text-align:right;">${r['SMA20_ayer']}</td>
          <td style="padding:8px; border-bottom:1px solid #f3f4f6; text-align:right;">${r['SMA20_hoy']}</td>
          <td style="padding:8px; border-bottom:1px solid #f3f4f6; text-align:right;">${r['SMA5_ayer']}</td>
          <td style="padding:8px; border-bottom:1px solid #f3f4f6; text-align:right;">${r['SMA5_hoy']}</td>
          <td style="padding:8px; border-bottom:1px solid #f3f4f6; text-align:right;">{r['Rachas (ruedas)']}</td>
          <td style="padding:8px; border-bottom:1px solid #f3f4f6; text-align:right;">{r['Rachas (días)']}</td>
        </tr>
        """)

    tbody = f"<tbody>{''.join(filas)}</tbody>"

    return f"""
    <h3 style="margin:16px 0 8px 0; color:#111827;">{titulo}</h3>
    <div style="overflow-x:auto; margin:8px 0 16px 0;">
      <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="border-collapse:collapse; font-size:14px; color:#111827;">
        {thead}
        {tbody}
      </table>
    </div>
    """

tabla_cedear   = construir_tabla_html(registros_cedear,   "CEDEARs")
tabla_acciones = construir_tabla_html(registros_acciones, "Acciones locales")
tabla_general  = construir_tabla_html(registros_general,  "Otros")

# Secciones como listas HTML
lista_cedear   = construir_lista_html(mensajes_cedear)
lista_acciones = construir_lista_html(mensajes_acciones)
lista_general  = construir_lista_html(mensajes_general)

html_body = f"""
<!DOCTYPE html>
<html lang="es">
  <body style="font-family:Arial,Helvetica,sans-serif; background:#f9fafb; padding:0; margin:0;">
    <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="background:#f9fafb; padding:24px 0;">
      <tr>
        <td align="center">
          <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="640" style="background:#ffffff; border:1px solid #e5e7eb; border-radius:8px; overflow:hidden;">
            <tr>
              <td style="background:#0ea5e9; color:#ffffff; padding:16px 20px; font-size:18px; font-weight:bold;">
                Resumen de tendencias (SMA5 vs SMA20)
              </td>
            </tr>
            <tr>
              <td style="padding:16px 20px; color:#111827; font-size:14px; line-height:1.5;">
                <p style="margin:0 0 12px 0;">
                  Resumen del <strong>{fecha_hoy_str}</strong>
                </p>

                {tabla_cedear}
                {tabla_acciones}
                {tabla_general}

                <hr style="border:0; border-top:1px solid #e5e7eb; margin:16px 0;">
                <p style="font-size:12px; color:#6b7280; margin:0;">
                  * Señales basadas en cruce y estado de SMA5 vs SMA20 con <em>min_periods</em>.
                </p>
                <p style="font-size:12px; color:#6b7280; margin:0;">
                  Racha (ruedas) cuenta velas (días de mercado con datos).
                </p>
                <p style="font-size:12px; color:#6b7280; margin:0;">
                  Racha (días) usa calendario (puede ser > ruedas por fines de semana/feriados).
                </p>
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>
"""

# Cuerpo del correo
mensaje.attach(MIMEText(html_body, "html"))
try:
    # Conectar al servidor SMTP
    servidor = smtplib.SMTP(smtp_server, smtp_port)
    servidor.starttls()  # Seguridad TLS
    servidor.login(remitente, password)
    servidor.send_message(mensaje)
    servidor.quit()
    print(f"Correo enviado exitosamente {destinatario}  ✅")
except Exception as e:
    print(f"Error al enviar el correo: {e}")

    
