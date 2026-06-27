import os
import logging
import requests

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.getenv("TOKEN")

API_KEY = "d9357a603b3025c9f4bdab0e35a3ee6a"

logging.basicConfig(level=logging.INFO)


# ----------------------------
# API запрос
# ----------------------------
session = requests.Session()

def get_stats(player: str, platform: str):
    url = "https://api.mozambiquehe.re/bridge"

    params = {
        "auth": API_KEY,
        "player": player,
        "platform": platform
    }

    headers = {
        "Accept": "application/json, text/plain, */*",
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        ),
        "Referer": "https://apexlegendsstatus.com/",
        "Origin": "https://apexlegendsstatus.com",
        "Connection": "keep-alive"
    }

    try:
        r = session.get(url, params=params, headers=headers, timeout=15)

        logging.info(f"[{platform}] status: {r.status_code}")

        if r.status_code != 200:
            logging.warning(f"[{platform}] body: {r.text[:200]}")
            return None

        return r.json()

    except Exception as e:
        logging.error(f"[{platform}] error: {e}")
        return None


# ----------------------------
# авто-платформа
# ----------------------------
def get_stats_auto(player: str):
    platforms = ["PC", "PS4", "X1"]

    for platform in platforms:
        data = get_stats(player, platform)

        if isinstance(data, dict) and data.get("global"):
            return data, platform

    return None, None


# ----------------------------
# /rank команда
# ----------------------------
async def rank(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.args:
        await update.message.reply_text("Использование: /rank nickname")
        return

    player = context.args[0]

    msg = await update.message.reply_text("🔎 Ищу игрока...")

    data, platform = get_stats_auto(player)

    if not data:
        await msg.edit_text("❌ Игрок не найден или API временно недоступен.")
        return

    try:
        global_data = data.get("global", {})
        rank_data = global_data.get("rank", {})

        level = global_data.get("level", "—")

        rp = rank_data.get("rankScore", "—")
        rank_name = rank_data.get("rankName", "—")
        rank_div = rank_data.get("rankDiv", "")

        rank_full = f"{rank_name} {rank_div}".strip()

        # realtime статус
        realtime = data.get("realtime", {})
        status = realtime.get("currentStateAsText", "Unknown")

        await msg.edit_text(
            f"🎮 Игрок: {player}\n"
            f"🖥 Платформа: {platform}\n\n"
            f"📊 Уровень: {level}\n"
            f"🏆 Ранг: {rank_full}\n"
            f"⭐ RP: {rp}\n\n"
            f"📡 Статус: {status}"
        )

    except Exception as e:
        await msg.edit_text(f"⚠️ Ошибка обработки данных: {e}")


# ----------------------------
# запуск бота
# ----------------------------
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("rank", rank))

    print("Bot started...")
    app.run_polling()


if __name__ == "__main__":
    main()
