#Importamos librerías
import yfinance as yf
import pandas as pd
import numpy as np
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import datetime
from datetime import timedelta

#Tickers a evaluar
tickers=["XLF.BA","XLK.BA","XLE.BA","ARKK.BA","QQQ.BA","SPY.BA","MSFT.BA","BYD.BA","TM.BA","XOM.BA","JNJ.BA","PG.BA"]

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
mensajes=[]
#Recorremos cada ticker
for ticker in tickers:
    data = yf.download(ticker, start=fecha_hoy_inicio_str, end=fecha_hoy_str, progress=False)

    # 1) No romper si no hay datos
    if data is None or data.empty:
        mensajes.append(f"{ticker}: sin datos en el rango.")
        continue

    df = data.reset_index().copy()
    df["Ticker"] = ticker
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values("Date")

    # 2) SMAs con min_periods para evitar señales prematuras
    df["SMA5"]  = df["Close"].rolling(5,  min_periods=5).mean()
    df["SMA50"] = df["Close"].rolling(50, min_periods=50).mean()

    # 3) Estado solo donde haya ambas SMAs
    estado = pd.Series(index=df.index, dtype="object")
    mask_ok = df["SMA5"].notna() & df["SMA50"].notna()
    estado[mask_ok] = np.where(df.loc[mask_ok, "SMA5"] > df.loc[mask_ok, "SMA50"], "Alcista", "Bajista")

    # 4) Tomar los últimos DOS estados válidos
    ult2 = estado.dropna().tail(2)

    if len(ult2) < 2:
        mensajes.append(f"{ticker}: datos insuficientes (necesita ≥ 50 velas).")
        # igual acumulá el df si lo usás después
        df_precios_concatenado = pd.concat([df_precios_concatenado, df], ignore_index=True)
        continue

    prev, curr = ult2.iloc[-2], ult2.iloc[-1]

    if prev == "Alcista" and curr == "Bajista":
        mensajes.append(f"{ticker}: Inicio de tendencia Bajista → VENDER")
    elif prev == "Bajista" and curr == "Alcista":
        mensajes.append(f"{ticker}: Inicio de tendencia Alcista → COMPRAR")
    elif curr == "Bajista":
        mensajes.append(f"{ticker}: Se mantiene Bajista")
    else:
        mensajes.append(f"{ticker}: Se mantiene Alcista")

    df_precios_concatenado = pd.concat([df_precios_concatenado, df], ignore_index=True)


cuerpo = "\n".join(mensajes)

# Cuerpo del correo
mensaje.attach(MIMEText(cuerpo, "plain"))
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