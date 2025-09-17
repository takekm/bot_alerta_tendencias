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
tickers=["XLF.BA","XLK.BA","XLE.BA","ARKK.BA","QQQ.BA","SPY.BA","MSFT.BA","AAPL.BA","AMZN.BA","GOOGL.BA","IBM.BA","KO.BA","MCD.BA","MELI.BA","CELU.BA","HARG.BA","LOMA.BA","MOLI.BA","PAMP.BA","TXAR.BA","YPFD.BA","TM.BA","XOM.BA","JNJ.BA","PG.BA","GGAL.BA"]

tickers_cedear = [
    "XLF.BA","XLK.BA","XLE.BA","ARKK.BA","QQQ.BA","SPY.BA",  # ETFs
    "MSFT.BA","AAPL.BA","AMZN.BA","GOOGL.BA","IBM.BA","KO.BA","MCD.BA",
    "MELI.BA","TM.BA","XOM.BA","JNJ.BA","PG.BA"
]

tickers_acciones = ["CELU.BA","HARG.BA","LOMA.BA","MOLI.BA","PAMP.BA","TXAR.BA","YPFD.BA","GGAL.BA"]

#Declaramos fechas
fecha_hoy = datetime.date.today()+ timedelta(days=1) #Agregar un día porque la descarga de yfinance es exclusivo en su límite superior.
fecha_hoy_inicio = fecha_hoy - datetime.timedelta(days=180)
#Pasamos a string
fecha_hoy_str=fecha_hoy.strftime("%Y-%m-%d")
fecha_hoy_inicio_str=fecha_hoy_inicio.strftime("%Y-%m-%d")

#Datos de autenticación de mailing
smtp_server = "smtp.gmail.com"
smtp_port = 587
remitente = "tkamada07@gmail.com"
password = "awxt imrp xuvj aosh"  
destinatario = "takeshikamada@hotmail.com"
mensaje = MIMEMultipart()
mensaje["From"] = "BOT Python - Take"
mensaje["To"] = destinatario
mensaje["Subject"] = "Resumen de tendencias"
#Lista y df vacíos
df_precios_concatenado=pd.DataFrame()
mensajes_general=[]
mensajes_cedear=[]
mensajes_acciones=[]
#Recorremos cada ticker
for ticker in tickers:
    data = yf.download(ticker, start=fecha_hoy_inicio_str, end=fecha_hoy_str, progress=False)

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

    # 3) Estado solo donde haya ambas SMAs
    estado = pd.Series(index=df.index, dtype="object")
    mask_ok = df["SMA5"].notna() & df["SMA20"].notna()
    estado[mask_ok] = np.where(df.loc[mask_ok, "SMA5"] > df.loc[mask_ok, "SMA20"], "Alcista", "Bajista")

    # 4) Tomar los últimos DOS estados válidos
    ult2 = estado.dropna().tail(2)
   

    if len(ult2) < 2:
        mensajes_general.append(f"{ticker}: datos insuficientes (necesita ≥ 50 velas).")
        # igual acumulá el df si lo usás después
        df_precios_concatenado = pd.concat([df_precios_concatenado, df], ignore_index=True)
        continue

    prev, curr = ult2.iloc[-2], ult2.iloc[-1]

    if prev == "Alcista" and curr == "Bajista":
        if ticker in tickers_cedear:
            mensajes_cedear.append(f"{ticker}: Inicio de tendencia Bajista → VENDER")
        elif ticker in tickers_acciones:
            mensajes_acciones.append(f"{ticker}: Inicio de tendencia Bajista → VENDER")
        else:
            mensajes_general.append(f"{ticker}: Inicio de tendencia Bajista → VENDER")
    elif prev == "Bajista" and curr == "Alcista":
        if ticker in tickers_cedear:
            mensajes_cedear.append(f"{ticker}: Inicio de tendencia Alcista → COMPRAR")
        elif ticker in tickers_acciones:
            mensajes_acciones.append(f"{ticker}: Inicio de tendencia Alcista → COMPRAR")
        else:
            mensajes_general.append(f"{ticker}: Inicio de tendencia Alcista → COMPRAR")
    elif prev == "Bajista" and curr == "Bajista":
        if ticker in tickers_cedear:
            mensajes_cedear.append(f"{ticker}: Se mantiene Bajista")
        elif ticker in tickers_acciones:
            mensajes_acciones.append(f"{ticker}: Se mantiene Bajista")
        else:
            mensajes_general.append(f"{ticker}: Se mantiene Bajista")
    else:
        if ticker in tickers_cedear:
            mensajes_cedear.append(f"{ticker}: Se mantiene Alcista")
        elif ticker in tickers_acciones:
            mensajes_acciones.append(f"{ticker}: Se mantiene Alcista")
        else:
            mensajes_general.append(f"{ticker}: Se mantiene Alcista")


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
                  Ventana analizada: <strong>{fecha_hoy_inicio_str}</strong> a <strong>{fecha_hoy_str}</strong>
                </p>

                <h3 style="margin:16px 0 8px 0; color:#111827;">CEDEARs</h3>
                <ul style="padding-left:18px; margin:8px 0 16px 0;">
                  {lista_cedear}
                </ul>

                <h3 style="margin:16px 0 8px 0; color:#111827;">Acciones locales</h3>
                <ul style="padding-left:18px; margin:8px 0 16px 0;">
                  {lista_acciones}
                </ul>

                <h3 style="margin:16px 0 8px 0; color:#111827;">Otros</h3>
                <ul style="padding-left:18px; margin:8px 0 16px 0;">
                  {lista_general}
                </ul>

                <hr style="border:0; border-top:1px solid #e5e7eb; margin:16px 0;">
                <p style="font-size:12px; color:#6b7280; margin:0;">
                  * Señales basadas en cruce y estado de SMA5 vs SMA20 con <em>min_periods</em>. No constituye recomendación de inversión.
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