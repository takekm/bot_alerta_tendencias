#Importamos librerías
import yfinance as yf
import pandas as pd
import numpy as np
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import datetime
from datetime import timedelta
from html import escape
from io import BytesIO

#Tickers a evaluar
tickers_cedear = [
    # Big Tech
    "AAPL","MSFT","AMZN","GOOGL","META","NVDA","TSLA",
    "NFLX","AMD","INTC","ORCL","IBM",

    # Consumo masivo
    "KO","PEP","PG","WMT","DIS","MCD","NKE","COST",

    # Finanzas
    "JPM","GS","BRK-B","C","BAC","AXP","V","MA",

    # Energía y materias primas
    "XOM","CVX","SHEL","BP","RIO","VALE","BHP",

    # Salud
    "PFE","JNJ","MRK","ABBV","LLY",

    # Empresas globales con presencia local
    "MELI","GLOB","BABA","TSM","VIST",

    # ETFs
    "SPY","IWM","QQQ","DIA","OIH","XLE","XLI","XLF","XLK","IYR",
    "XLP","XLY","BBH","GLD","USO","UNG","MCHI","EWJ","EFA","ARKK","IJH","IJR"
]
tickers_acciones = [
    # Bancos
    "GGAL.BA", "BMA.BA", "SUPV.BA", "BBAR.BA", "BRIO.BA",

    # Energía & Oil & Gas
    "YPFD.BA", "PAMP.BA", "TRAN.BA", "EDN.BA", "CEPU.BA",
    "METR.BA", "DGCU2.BA", "VIST.BA", "CAPX.BA", "LAR.BA", 

    # Acero, materiales e industria
    "TXAR.BA", "ALUA.BA", "AUSO.BA", "MOLA.BA", "MOLI.BA", "LOMA.BA",
    "HARG.BA", "CELU.BA",

    # Consumo & retail
    "TGSU2.BA", "CRES.BA", "DYCA.BA", "SEMI.BA", "CARC.BA", "MIRG.BA",
    "AGRO.BA", "INTR.BA",

    # Telecomunicaciones & tecnología
    "TECO2.BA", "CTIO.BA", "COME.BA",

    # Seguros, servicios & otros
    "VALO.BA", "IRSA.BA", "IRCP.BA", "CVH.BA", "EDLH.BA", "POLL.BA",
    "OEST.BA", "GAMI.BA", "GRIM.BA",

    # Panel General con buen volumen
    "BOLT.BA", "RICH.BA", "SAMI.BA"
]

tickers_cripto = [
    "BTC-USD", "ETH-USD", "BNB-USD", "SOL-USD"
]

tickers= tickers_cedear +  tickers_acciones +  tickers_cripto

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


#Función para generar una tabla resumen consolidada de todos los tickers
def agregar_registro(a_que_lista, ticker, señal, cierre, Var_nominal, Var_pct, cruce , racha, RSI14):
    a_que_lista.append({
        "Ticker": ticker,
        "Señal": señal,
        "Cierre": cierre,
        "vs LD $":Var_nominal,
        "vs LD %": Var_pct,
        "cruce":  cruce,
        "Rachas (ruedas)": "—" if pd.isna(racha) else racha,
        "RSI14":  RSI14
    })

#Calculador de RSI
def rsi_wilder(close, window=14):
    delta = close.diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    # Inicialización con medias simples, luego suavizado tipo Wilder
    avg_gain = gain.rolling(window=window, min_periods=window).mean()
    avg_loss = loss.rolling(window=window, min_periods=window).mean()

    # A partir de la 1ra ventana, usar la recursión de Wilder
    avg_gain = avg_gain.combine_first(
        gain.ewm(alpha=1/window, adjust=False).mean()
    )
    avg_loss = avg_loss.combine_first(
        loss.ewm(alpha=1/window, adjust=False).mean()
    )

    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi

    #df vacío para alojar los datos concatenados
df_precios_concatenado=pd.DataFrame()

# Registros tabulares (además de los mensajes de texto)
registros_cedear   = []
registros_acciones = []
registros_cripto = []
registros_general  = []

for ticker in tickers:
    data = yf.download(    
    ticker,
    start=fecha_inicio_str,
    end=fecha_cierre_str,
    interval="1d",
    auto_adjust=True,
    progress=False,
    threads=True
    ).reset_index()
    data.columns = data.columns.get_level_values(0)

    df = data.reset_index().copy()
    df["Ticker"] = ticker
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values("Date")

    # 2) SMAs con min_periods para evitar señales prematuras
    df["EMA5"]  = df["Close"].ewm(span=5,  adjust=False, min_periods=5).mean()
    df["EMA20"] = df["Close"].ewm(span=20, adjust=False, min_periods=20).mean()

    df["Cruce"] = np.where(
    (df["EMA5"].shift(1) < df["EMA20"].shift(1)) & (df["EMA5"] > df["EMA20"]),
    "Cambio a Alcista",  # Cruce hacia arriba
    np.where(
        (df["EMA5"].shift(1) > df["EMA20"].shift(1)) & (df["EMA5"] < df["EMA20"]),
        "Cambio a Bajista",  # Cruce hacia abajo
        np.where(
            (df["EMA5"] > df["EMA20"]),
            "Alcista",  # EMA5 sigue arriba
            np.where(
                (df["EMA5"] < df["EMA20"]),
                "Bajista",  # EMA5 sigue abajo
                "Sin Dato"
                )
            )
        )
    )

    # 1) Definimos cuándo EMA5 está arriba/abajo (True/False)
    mask = df["EMA5"].notna() & df["EMA20"].notna() #Crea un booleano por fila que vale True solo donde ambas EMAs existen (evita los NaN de los primeros días).
    up = df.loc[mask, "EMA5"] > df.loc[mask, "EMA20"]   # True=Alcista, False=Bajista

    # 2) Identificamos grupos consecutivos (cada cambio True<->False inicia grupo nuevo)
    grp = (up != up.shift()).cumsum() #up.shift() corre la serie 1 hacia abajo (compara “hoy” con “ayer”). - cumsum() acumula esos cambios y crea un ID de grupo para cada tramo consecutivo de la misma condición.

    # 3) Racha de días dentro de cada grupo (1,2,3,...)
    df.loc[mask, "Racha_dias"] = up.groupby(grp).cumcount() + 1 #groupby(grp).cumcount() cuenta 0,1,2,… dentro de cada grupo.
    df["Racha_dias"] = df["Racha_dias"].astype("Int64")

    # 4) Variación nominal y porcentual vs. el día anterior
    df["Var_nominal"] = df["Close"].diff()              # Close_t - Close_{t-1}
    df["Var_pct"]     = df["Close"].pct_change() * 100  # % respecto al cierre anterior

    # 5) Calculador RSI
    df["RSI14"] = rsi_wilder(df["Close"], 14)

    #Señal de compra
    N = 3  # ventana para aceptar el cruce de RSI
    # 1) Cruce alcista de EMAs hoy (ayer EMA5<=EMA20 y hoy EMA5>EMA20)
    cruce_alcista = (df["EMA5"].shift(1) <= df["EMA20"].shift(1)) & (df["EMA5"] > df["EMA20"])
    # 2) RSI cruza 30 hacia arriba (ayer <30 y hoy >=30)
    rsi_sale_30 = (df["RSI14"].shift(1) < 30) & (df["RSI14"] >= 30)
    # 3) Aceptar si el cruce de RSI ocurrió hoy o en las N-1 barras anteriores
    rsi_sale_30_rolling = rsi_sale_30.rolling(N, min_periods=1).max().astype(bool)
    # 4) Señal de compra
    df["BUY"] = cruce_alcista & rsi_sale_30_rolling

    #Señal de Salida
    # Señal de venta básica
    cruce_bajista = (df["EMA5"].shift(1) >= df["EMA20"].shift(1)) & (df["EMA5"] < df["EMA20"])
    sobrecompra = (df["RSI14"] > 70)
    df["SELL"] = cruce_bajista | sobrecompra

    if len(df.tail(2))>=2:
        SMALP_LD =df["EMA20"].iloc[-2]
        SMACP_LD=df["EMA5"].iloc[-2]
    else:
        SMALP_LD ="Sin Dato"
        SMACP_LD= "Sin Dato"
        
    if len(df.tail(2))>=1:
        SMALP_TD =df["EMA20"].iloc[-1]
        SMACP_TD=df["EMA5"].iloc[-1]
        cierre=df["Close"].iloc[-1]
        cruce=df["Cruce"].iloc[-1]
        racha=df["Racha_dias"].iloc[-1]
        Var_nominal=df["Var_nominal"].iloc[-1]
        Var_pct=df["Var_pct"].iloc[-1]
        RSI14=df["RSI14"].iloc[-1]
        BUY=df["BUY"].iloc[-1]
        SELL=df["SELL"].iloc[-1]
        
    else:
        SMALP_TD ="Sin Dato"
        SMACP_TD= "Sin Dato"
        cierre="Sin Dato"
        cruce="Sin Dato"
        racha="Sin Dato"
        Var_nominal="Sin Dato"
        Var_pct="Sin Dato"
        RSI14="Sin Dato"
        BUY="Sin Dato"
        SELL="Sin Dato"
        
    #Formateamos 
    SMALP_LD=formatear_numero(SMALP_LD)
    SMACP_LD=formatear_numero(SMACP_LD)
    SMALP_TD=formatear_numero(SMALP_TD)
    SMACP_TD=formatear_numero(SMACP_TD)
    cierre=formatear_numero(cierre)
    Var_nominal=formatear_numero(Var_nominal)
    Var_pct=formatear_numero(Var_pct)
    RSI14=formatear_numero(RSI14)
    
    if SELL==True:
        señal="VENDER"
        if ticker in tickers_cedear:
            agregar_registro(registros_cedear, ticker, señal, cierre, Var_nominal, Var_pct, cruce, racha, RSI14)
        elif ticker in tickers_acciones:
            agregar_registro(registros_acciones, ticker, señal, cierre, Var_nominal, Var_pct, cruce,racha, RSI14)
        elif ticker in tickers_cripto:
            agregar_registro(registros_cripto, ticker, señal, cierre, Var_nominal, Var_pct, cruce,racha, RSI14)
        else:
            agregar_registro(registros_general, ticker, señal, cierre, Var_nominal, Var_pct, cruce,racha, RSI14)
    elif BUY==True:
        señal="COMPRAR"
        if ticker in tickers_cedear:
            
            agregar_registro(registros_cedear, ticker, señal, cierre, Var_nominal, Var_pct, cruce,racha, RSI14)
        elif ticker in tickers_acciones:
            agregar_registro(registros_acciones, ticker, señal, cierre, Var_nominal, Var_pct, cruce,racha, RSI14)
        elif ticker in tickers_cripto:
            agregar_registro(registros_cripto, ticker, señal, cierre, Var_nominal, Var_pct, cruce,racha, RSI14)
        else:
            agregar_registro(registros_general, ticker, señal, cierre, Var_nominal, Var_pct, cruce,racha, RSI14)
    elif (SELL==False) & (BUY==False) & (cruce=="Bajista"):
        señal="Se mantiene Bajista"
        if ticker in tickers_cedear:
            agregar_registro(registros_cedear, ticker, señal, cierre, Var_nominal, Var_pct, cruce,racha, RSI14)
        elif ticker in tickers_acciones:
            agregar_registro(registros_acciones, ticker, señal, cierre, Var_nominal, Var_pct, cruce,racha, RSI14)
        elif ticker in tickers_cripto:
            agregar_registro(registros_cripto, ticker, señal, cierre, Var_nominal, Var_pct, cruce,racha, RSI14)
        else:
            agregar_registro(registros_general, ticker, señal, cierre, Var_nominal, Var_pct, cruce,racha, RSI14)
    else:
        señal="Se mantiene Alcista"
        if ticker in tickers_cedear:
            agregar_registro(registros_cedear, ticker, señal, cierre, Var_nominal, Var_pct, cruce,racha, RSI14)
        elif ticker in tickers_acciones:
            agregar_registro(registros_acciones, ticker, señal, cierre, Var_nominal, Var_pct, cruce,racha, RSI14)
        elif ticker in tickers_cripto:
            agregar_registro(registros_cripto, ticker, señal, cierre, Var_nominal, Var_pct, cruce,racha, RSI14)
        else:
            agregar_registro(registros_general, ticker, señal, cierre, Var_nominal, Var_pct, cruce,racha, RSI14)


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
        <th style="text-align:left; padding:8px; border-bottom:1px solid #e5e7eb;">Cierre</th>
        <th style="text-align:right; padding:8px; border-bottom:1px solid #e5e7eb;">vs LD $</th>
        <th style="text-align:right; padding:8px; border-bottom:1px solid #e5e7eb;">vs LD %</th>
        <th style="text-align:right; padding:8px; border-bottom:1px solid #e5e7eb;">cruce</th>
        <th style="text-align:right; padding:8px; border-bottom:1px solid #e5e7eb;">Racha (ruedas)</th>
        <th style="text-align:right; padding:8px; border-bottom:1px solid #e5e7eb;">RSI14</th>
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
          <td style="padding:8px; border-bottom:1px solid #f3f4f6; text-align:right;">${r['Cierre']}</td>
          <td style="padding:8px; border-bottom:1px solid #f3f4f6; text-align:right;">${r['vs LD $']}</td>
          <td style="padding:8px; border-bottom:1px solid #f3f4f6; text-align:right;">{r['vs LD %']}%</td>
          <td style="padding:8px; border-bottom:1px solid #f3f4f6; text-align:right;">{r['cruce']}</td>
          <td style="padding:8px; border-bottom:1px solid #f3f4f6; text-align:right;">{r['Rachas (ruedas)']}</td>
          <td style="padding:8px; border-bottom:1px solid #f3f4f6; text-align:right;">{r['RSI14']}</td>
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
tabla_cripto = construir_tabla_html(registros_cripto, "Cripto")
tabla_general  = construir_tabla_html(registros_general,  "Otros")

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
                Resumen de tendencias (EMA5 vs EMA20)
              </td>
            </tr>
            <tr>
              <td style="padding:16px 20px; color:#111827; font-size:14px; line-height:1.5;">
                <p style="margin:0 0 12px 0;">
                  Resumen del <strong>{fecha_hoy_str}</strong>
                </p>

                {tabla_cedear}
                {tabla_acciones}
                {tabla_cripto}
                {tabla_general}

                <hr style="border:0; border-top:1px solid #e5e7eb; margin:16px 0;">
                <p style="font-size:12px; color:#6b7280; margin:0;">
                  * Señales basadas en cruce y estado de EMA5 vs EMA20 con <em>min_periods</em>.
                </p>
                <p style="font-size:12px; color:#6b7280; margin:0;">
                  Racha (ruedas) cuenta velas (días de mercado con datos).
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

# Adjuntar HTML
mensaje.attach(MIMEText(html_body, "html"))

# === Adjuntar Excel ANTES de enviar ===
fname = f"precios_{fecha_hoy_str.replace('/','-').replace(':','-')}.xlsx"
buffer = BytesIO()
with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
    df_precios_concatenado.to_excel(writer, index=False, sheet_name="Precios")
    wb = writer.book; ws = writer.sheets["Precios"]
    nrows, ncols = df_precios_concatenado.shape
    ws.autofilter(0, 0, nrows, ncols-1)
    for i, col in enumerate(df_precios_concatenado.columns):
        ws.set_column(i, i, max(10, min(35, len(str(col)) + 2)))
buffer.seek(0)
adjunto = MIMEApplication(buffer.read(), _subtype="vnd.openxmlformats-officedocument.spreadsheetml.sheet")
adjunto.add_header("Content-Disposition", "attachment", filename=fname)
mensaje.attach(adjunto)

# === Enviar ===
try:
    servidor = smtplib.SMTP(smtp_server, smtp_port)
    servidor.starttls()
    servidor.login(remitente, password)
    servidor.send_message(mensaje)
    servidor.quit()
    print(f"Correo enviado exitosamente {destinatario}  ✅")
except Exception as e:
    print(f"Error al enviar el correo: {e}")