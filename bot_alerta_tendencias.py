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
tickers_cedear = [
    # Big Tech
    "AAPL.BA", "MSFT.BA", "AMZN.BA", "GOOGL.BA", "META.BA", "NVDA.BA", "TSLA.BA",
    "NFLX.BA", "AMD.BA", "INTC.BA", "ORCL.BA","IBM.BA",

    # Consumo masivo
    "KO.BA", "PEP.BA", "PG.BA", "WMT.BA", "DISN.BA", "MCD.BA", "NKE.BA", "COST.BA",

    # Finanzas
    "JPM.BA", "GS.BA", "BRKB.BA", "C.BA", "BAC.BA", "AXP.BA", "V.BA", "MA.BA",

    # Energía y materias primas
    "XOM.BA", "CVX.BA", "SHEL.BA", "BP.BA", "RIO.BA", "VALE.BA", "BHP.BA",

    # Salud
    "PFE.BA", "JNJ.BA", "MRK.BA", "ABBV.BA", "LLY.BA",

    # Empresas globales con presencia local
    "MELI.BA", "GLOB.BA", "BABA.BA", "TSM.BA", "VIST.BA",

    # ETFs CEDEARs
    "SPY.BA", "QQQ.BA", "ARKK.BA", "XLF.BA", "XLK.BA", "XLE.BA", "XLI.BA", "XLP.BA", "XLY.BA", "IJH","IJR"

]

tickers_acciones = [
    # Bancos
    "GGAL.BA", "BMA.BA", "SUPV.BA", "BBAR.BA", "BPAT.BA", "BRIO.BA",

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
    "BTC-USD", "ETH-USD", "BNB-USD",
    "XRP-USD", "SOL-USD", "ADA-USD", "DOGE-USD", "TRX-USD",
    "DOT-USD", "AVAX-USD", "BCH-USD",
    "LTC-USD", "MATIC-USD", "LINK-USD", "XLM-USD",
    "ATOM-USD", "ETC-USD", "XMR-USD", "NEAR-USD", 
    "OP-USD", "INJ-USD", "SUI-USD", "HBAR-USD",
    "MKR-USD", "AAVE-USD", "IMX-USD", "FIL-USD", "ICP-USD"
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
def agregar_registro(a_que_lista, ticker, señal, cierre, SMALP_LD, SMALP_TD, SMACP_LD, SMACP_TD,streak_ruedas=None):
    a_que_lista.append({
        "Ticker": ticker,
        "Señal": señal,
        "Cierre": cierre,
        "SMA20_ayer": SMALP_LD,
        "SMA20_hoy":  SMALP_TD,
        "SMA5_ayer":  SMACP_LD,
        "SMA5_hoy":   SMACP_TD,
        "Rachas (ruedas)": streak_ruedas if streak_ruedas is not None else "—",
    })


#df vacío para alojar los datos concatenados
df_precios_concatenado=pd.DataFrame()

# Registros tabulares (además de los mensajes de texto)
registros_cedear   = []
registros_acciones = []
registros_cripto = []
registros_general  = []


#Recorremos cada ticker
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
    # 1) No romper si no hay datos
    if data is None or data.empty:
        continue

    df = data.reset_index().copy()
    df["Ticker"] = ticker
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values("Date")

    # 2) SMAs con min_periods para evitar señales prematuras
    df["EMA5"]  = df["Close"].ewm(span=5,  adjust=False, min_periods=5).mean()
    df["EMA20"] = df["Close"].ewm(span=20, adjust=False, min_periods=20).mean()

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
    else:
        SMALP_TD ="Sin Dato"
        SMACP_TD= "Sin Dato"
        cierre="Sin Dato"
    
    #Formateamos 
    SMALP_LD=formatear_numero(SMALP_LD)
    SMACP_LD=formatear_numero(SMACP_LD)
    SMALP_TD=formatear_numero(SMALP_TD)
    SMACP_TD=formatear_numero(SMACP_TD)
    cierre=formatear_numero(cierre)

    # 3) Estado solo donde haya ambas SMAs
    estado = pd.Series(index=df.index, dtype="object")
    mask_ok = df["EMA5"].notna() & df["EMA20"].notna()
    estado[mask_ok] = np.where(df.loc[mask_ok, "EMA5"] > df.loc[mask_ok, "EMA20"], "Alcista", "Bajista")

    # --- cálculo de streak del estado actual ---
    estado_valid   = estado[mask_ok]                  # solo donde hay EMA5 y EMA20
    fechas_valid   = df.loc[mask_ok, "Date"]

    if estado_valid.dropna().empty:
        streak_ruedas = None
        
    else:
        # Agrupar por rachas consecutivas (run-length encoding)
        grupos = (estado_valid != estado_valid.shift()).cumsum()
        tamanio_grupo = grupos.groupby(grupos).transform("size")
        # Racha actual = tamaño del último grupo
        streak_ruedas = int(tamanio_grupo.iloc[-1])



    # 4) Tomar los últimos DOS estados válidos
    ult2 = estado.dropna().tail(2)
   

    if len(ult2) < 2:
        
        # igual acumulá el df si lo usás después
        df_precios_concatenado = pd.concat([df_precios_concatenado, df], ignore_index=True)
        continue

    prev, curr = ult2.iloc[-2], ult2.iloc[-1]

    if prev == "Alcista" and curr == "Bajista":
        if ticker in tickers_cedear:
            señal="Inicio de tendencia Bajista → VENDER"
            agregar_registro(registros_cedear, ticker, señal, cierre, SMALP_LD, SMALP_TD, SMACP_LD, SMACP_TD,streak_ruedas)
        elif ticker in tickers_acciones:
            señal="Inicio de tendencia Bajista → VENDER"
            agregar_registro(registros_acciones, ticker, señal, cierre, SMALP_LD, SMALP_TD, SMACP_LD, SMACP_TD,streak_ruedas)
        elif ticker in tickers_cripto:
            señal="Inicio de tendencia Bajista → VENDER"
            agregar_registro(registros_cripto, ticker, señal, cierre, SMALP_LD, SMALP_TD, SMACP_LD, SMACP_TD,streak_ruedas)
        else:
            señal="Inicio de tendencia Bajista → VENDER"
            agregar_registro(registros_general, ticker, señal, cierre, SMALP_LD, SMALP_TD, SMACP_LD, SMACP_TD,streak_ruedas)
    elif prev == "Bajista" and curr == "Alcista":
        if ticker in tickers_cedear:
            señal="Inicio de tendencia Alcista → COMPRAR"
            agregar_registro(registros_cedear, ticker, señal, cierre, SMALP_LD, SMALP_TD, SMACP_LD, SMACP_TD,streak_ruedas)
        elif ticker in tickers_acciones:
            señal="Inicio de tendencia Alcista → COMPRAR"
            agregar_registro(registros_acciones, ticker, señal, cierre, SMALP_LD, SMALP_TD, SMACP_LD, SMACP_TD,streak_ruedas)
        elif ticker in tickers_cripto:
            señal="Inicio de tendencia Alcista → COMPRAR"
            agregar_registro(registros_cripto, ticker, señal, cierre, SMALP_LD, SMALP_TD, SMACP_LD, SMACP_TD,streak_ruedas)
        else:
            señal="Inicio de tendencia Alcista → COMPRAR"
            agregar_registro(registros_general, ticker, señal, cierre, SMALP_LD, SMALP_TD, SMACP_LD, SMACP_TD,streak_ruedas)
    elif prev == "Bajista" and curr == "Bajista":
        if ticker in tickers_cedear:
            señal="Se mantiene Bajista"
            agregar_registro(registros_cedear, ticker, señal, cierre, SMALP_LD, SMALP_TD, SMACP_LD, SMACP_TD,streak_ruedas)
        elif ticker in tickers_acciones:
            señal="Se mantiene Bajista"
            agregar_registro(registros_acciones, ticker, señal, cierre, SMALP_LD, SMALP_TD, SMACP_LD, SMACP_TD,streak_ruedas)
        elif ticker in tickers_cripto:
            señal="Se mantiene Bajista"
            agregar_registro(registros_cripto, ticker, señal, cierre, SMALP_LD, SMALP_TD, SMACP_LD, SMACP_TD,streak_ruedas)
        else:
            señal="Se mantiene Bajista"
            agregar_registro(registros_general, ticker, señal, cierre, SMALP_LD, SMALP_TD, SMACP_LD, SMACP_TD,streak_ruedas)
    else:
        if ticker in tickers_cedear:
            señal="Se mantiene Alcista"
            agregar_registro(registros_cedear, ticker, señal, cierre, SMALP_LD, SMALP_TD, SMACP_LD, SMACP_TD,streak_ruedas)
        elif ticker in tickers_acciones:
            señal="Se mantiene Alcista"
            agregar_registro(registros_acciones, ticker, señal, cierre, SMALP_LD, SMALP_TD, SMACP_LD, SMACP_TD,streak_ruedas)
        elif ticker in tickers_cripto:
            señal="Se mantiene Alcista"
            agregar_registro(registros_cripto, ticker, señal, cierre, SMALP_LD, SMALP_TD, SMACP_LD, SMACP_TD,streak_ruedas)
        else:
            señal="Se mantiene Alcista"
            agregar_registro(registros_general, ticker, señal, cierre, SMALP_LD, SMALP_TD, SMACP_LD, SMACP_TD,streak_ruedas)


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
        <th style="text-align:right; padding:8px; border-bottom:1px solid #e5e7eb;">EMA20 ayer</th>
        <th style="text-align:right; padding:8px; border-bottom:1px solid #e5e7eb;">EMA20 hoy</th>
        <th style="text-align:right; padding:8px; border-bottom:1px solid #e5e7eb;">EMA5 ayer</th>
        <th style="text-align:right; padding:8px; border-bottom:1px solid #e5e7eb;">EMA5 hoy</th>
        <th style="text-align:right; padding:8px; border-bottom:1px solid #e5e7eb;">Racha (ruedas)</th>
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
          <td style="padding:8px; border-bottom:1px solid #f3f4f6; text-align:right;">${r['SMA20_ayer']}</td>
          <td style="padding:8px; border-bottom:1px solid #f3f4f6; text-align:right;">${r['SMA20_hoy']}</td>
          <td style="padding:8px; border-bottom:1px solid #f3f4f6; text-align:right;">${r['SMA5_ayer']}</td>
          <td style="padding:8px; border-bottom:1px solid #f3f4f6; text-align:right;">${r['SMA5_hoy']}</td>
          <td style="padding:8px; border-bottom:1px solid #f3f4f6; text-align:right;">{r['Rachas (ruedas)']}</td>
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
        </td>""
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

    
