#Importamos librerías
import yfinance as yf
import pandas as pd
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import datetime
from datetime import timedelta

#Ticker a evaluar
ticker="MSFT.BA"

#Declaramos fechas
fecha_hoy = datetime.date.today()
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
mensaje["Subject"] = "Correo de prueba en Python"

# Descargar datos 
data = yf.download(ticker, start=fecha_hoy_inicio_str, end=fecha_hoy_str).reset_index()
data['Ticker']=data.columns.get_level_values(1)[1]
# después de tu download + reset_index
if isinstance(data.columns, pd.MultiIndex):
    data.columns = data.columns.get_level_values(0)

df_precios=data.copy()
# Aseguramos que la columna Date sea de tipo fecha
df_precios["Date"] = pd.to_datetime(df_precios["Date"])
df_precios = df_precios.sort_values("Date")  # ordenar por fecha

# Calcular medias móviles
df_precios["SMA50"] = df_precios["Close"].rolling(20).mean()
df_precios["SMA5"] = df_precios["Close"].rolling(1).mean()

# Regla simple: SMA50 vs SMA200
df_precios["SMA Cross"] = df_precios.apply(
    lambda row: "Alcista" if row["SMA5"] > row["SMA50"] else "Bajista",
    axis=1
)

if (df_precios["SMA Cross"].iloc[-2]=="Alcista") & (df_precios["SMA Cross"].iloc[-1]=="Bajista"):
    cuerpo="Inicio de Tendencia Bajista: VENDER"
elif (df_precios["SMA Cross"].iloc[-2]=="Bajista") & (df_precios["SMA Cross"].iloc[-1]=="Alcista"):
    cuerpo="Inicio de Tendencia Alcista: COMPRAR"
elif (df_precios["SMA Cross"].iloc[-2]=="Bajista") & (df_precios["SMA Cross"].iloc[-1]=="Bajista"):
    cuerpo="Se mantiene bajista"
elif (df_precios["SMA Cross"].iloc[-2]=="Bajista") & (df_precios["SMA Cross"].iloc[-1]=="Bajista"):
    cuerpo="Se mantiene alcista"
print(cuerpo)
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