import requests
import schedule
import time
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = "TEU_TOKEN"
CHAT_ID = "TEU_CHAT_ID"

API_URL = "https://apidatos.ree.es/es/datos/mercados/precios-mercados-tiempo-real"


def obter_prezos():
    params = {
        "start_date": datetime.now().strftime("%Y-%m-%dT00:00"),
        "end_date": datetime.now().strftime("%Y-%m-%dT23:59"),
        "time_trunc": "hour"
    }

    r = requests.get(API_URL, params=params)
    data = r.json()

    prezos = data["included"][0]["attributes"]["values"]

    resultado = []

    for p in prezos:
        hora = p["datetime"].split("T")[1][:5]
        prezo = round(p["value"]/1000, 5)
        resultado.append((hora, prezo))

    return resultado


async def prezo_actual(update: Update, context: ContextTypes.DEFAULT_TYPE):

    hora_actual = datetime.now().hour
    prezos = obter_prezos()

    hora, prezo = prezos[hora_actual]

    await update.message.reply_text(
        f"⚡ Prezo agora ({hora})\n{prezo} €/kWh"
    )


async def prezos_hoxe(update: Update, context: ContextTypes.DEFAULT_TYPE):

    prezos = obter_prezos()

    texto = "⚡ Prezos de hoxe\n\n"

    for hora, prezo in prezos:
        texto += f"{hora} → {prezo} €/kWh\n"

    await update.message.reply_text(texto)


async def horas_baratas(update: Update, context: ContextTypes.DEFAULT_TYPE):

    prezos = obter_prezos()

    prezos_ordenados = sorted(prezos, key=lambda x: x[1])[:5]

    texto = "🟢 Horas máis baratas hoxe:\n\n"

    for hora, prezo in prezos_ordenados:
        texto += f"{hora} → {prezo} €/kWh\n"

    await update.message.reply_text(texto)


def enviar_resumo():

    prezos = obter_prezos()

    baratas = sorted(prezos, key=lambda x: x[1])[:3]

    texto = "⚡ Resumo luz hoxe\n\n🟢 Mellores horas:\n"

    for hora, prezo in baratas:
        texto += f"{hora} → {prezo} €/kWh\n"

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": texto
    })


async def scheduler():

    schedule.every().day.at("09:00").do(enviar_resumo)

    while True:
        schedule.run_pending()
        await asyncio.sleep(30)


app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("prezo", prezo_actual))
app.add_handler(CommandHandler("hoxe", prezos_hoxe))
app.add_handler(CommandHandler("baratas", horas_baratas))

print("Bot funcionando...")

app.run_polling()