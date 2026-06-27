import os
import logging
import requests

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.getenv("TOKEN")
API_KEY = os.getenv("API_KEY")

logging.basicConfig(level=logging.INFO)


# ----------------------------
# API запрос
# ----------------------------
def detect_input_type(player: str):
    if player.isdigit() and len(player) == 17:
        return "steamid"
    return "nickname"

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
    input_type = detect_input_type(player)

    platforms = ["PC", "PS4", "X1"]

    for platform in platforms:
        data = get_stats(player, platform)

        if data and isinstance(data, dict) and data.get("global"):
            return data, platform, input_type

    return None, None, input_type


# ----------------------------
# /rank команда
# ----------------------------
async def rank(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.args:
        await update.message.reply_text("Использование: /rank nickname или SteamID")
        return

    player = context.args[0]

    msg = await update.message.reply_text("🔎 Ищу игрока...")

    data, platform, input_type = get_stats_auto(player)

    if not data:
        await msg.edit_text("❌ Игрок не найден или API не поддерживает этот ID.")
        return

    try:
        global_data = data.get("global", {})
        rank_data = global_data.get("rank", {})

        level = global_data.get("level", "—")

        rp = rank_data.get("rankScore", "—")
        rank_name = rank_data.get("rankName", "—")
        rank_div = rank_data.get("rankDiv", "")

        rank_full = f"{rank_name} {rank_div}".strip()

        await msg.edit_text(
            f"🎮 Игрок: {global_data.get('name', player)}\n"
            f"🆔 Тип ввода: {input_type}\n"
            f"🖥 Платформа: {platform}\n\n"
            f"📊 Уровень: {level}\n"
            f"🏆 Ранг: {rank_full}\n"
            f"⭐ RP: {rp}"
        )

    except Exception as e:
        await msg.edit_text(f"⚠️ Ошибка: {e}")

async def test(update: Update, context: ContextTypes.DEFAULT_TYPE):

    url = "https://api.mozambiquehe.re/bridge"

    params = {
        "auth": API_KEY,
        "player": "JIeHuBblu_KoT",
        "platform": "PC"
    }

    headers = {
        "Accept": "application/json, text/plain, */*",
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0 Safari/537.36"
        ),
        "Referer": "https://apexlegendsstatus.com/",
        "Origin": "https://apexlegendsstatus.com"
    }

    try:
        msg = await update.message.reply_text("🔎 TEST запрос выполняется...")

        r = requests.get(url, params=params, headers=headers, timeout=15)

        result_text = (
            f"📡 STATUS: {r.status_code}\n\n"
            f"📄 RAW RESPONSE:\n{r.text[:1500]}"
        )

        # пробуем распарсить JSON
        try:
            json_data = r.json()
            result_text += f"\n\n✅ JSON PARSED SUCCESSFULLY:\n{json_data}"
        except Exception:
            result_text += "\n\n❌ JSON PARSE FAILED"

        await msg.edit_text(result_text)

    except Exception as e:
        await update.message.reply_text(f"💥 REQUEST ERROR: {e}")

# ----------------------------
# запуск бота
# ----------------------------
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("rank", rank))
    app.add_handler(CommandHandler("test", test))

    print("Bot started...")
    app.run_polling()


if __name__ == "__main__":
    main()
