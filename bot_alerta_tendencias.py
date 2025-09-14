import yfinance as yf
import pandas as pd
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import datetime
from datetime import timedelta

#Declaramos fechas
fecha_hoy = datetime.date.today()
fecha_hoy_ly = fecha_hoy - datetime.timedelta(days=365)
#Pasamos a string
fecha_hoy_str=fecha_hoy.strftime("%Y-%m-%d")
fecha_hoy_ly_str=fecha_hoy_ly.strftime("%Y-%m-%d")

#Datos de autenticación de mailing
smtp_server = "smtp.gmail.com"
smtp_port = 587
remitente = "tkamada07@gmail.com"
password = "awxt imrp xuvj aosh"  
destinatario = "takeshikamada@hotmail.com"
mensaje = MIMEMultipart()
mensaje["From"] = "BOT Python - Take"
mensaje["To"] = destinatario
mensaje["Subject"] = "Correo de prueba en Python"

# Descargar datos de Apple
data = yf.download("AAPL", start=fecha_hoy_ly_str, end=fecha_hoy_str).reset_index()
#Generamos una columna con el nombre del ticker
data['Ticker']=data.columns.get_level_values(1)[1]
# reset_index para darle formato al df
if isinstance(data.columns, pd.MultiIndex):
    data.columns = data.columns.get_level_values(0)
#Generamos una copia
df_precios=data.copy()
# Aseguramos que la columna Date sea de tipo fecha
df_precios["Date"] = pd.to_datetime(df_precios["Date"])
df_precios = df_precios.sort_values("Date")  # ordenar por fecha
# Calcular medias móviles
df_precios["SMA50"] = df_precios["Close"].rolling(50).mean()
df_precios["SMA5"] = df_precios["Close"].rolling(5).mean()

#Medias Móviles Simples
# Regla simple: SMA50 vs SMA200
df_precios["SMA Cross"] = df_precios.apply(
    lambda row: "Alcista" if row["SMA5"] > row["SMA50"] else "Bajista",
    axis=1
)