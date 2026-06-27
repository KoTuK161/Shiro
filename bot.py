import os
import logging
import requests

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.getenv("TOKEN")
API_KEY = "d9357a603b3025c9f4bdab0e35a3ee6a"

logging.basicConfig(level=logging.INFO)


# ----------------------------
# Запрос к API
# ----------------------------
def get_stats(player: str, platform: str):
    url = "https://api.mozambiquehe.re/bridge"

    params = {
        "auth": API_KEY,
        "player": player,
        "platform": platform
    }

    headers = {
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0"
    }

    try:
        r = requests.get(url, params=params, headers=headers, timeout=15)

        # 🔥 ЛОГИ ДЛЯ ОТЛАДКИ
        logging.info(f"[{platform}] status: {r.status_code}")
        logging.info(f"[{platform}] text: {r.text[:200]}")

        # если не 200 — сразу мимо
        if r.status_code != 200:
            return None

        # безопасный JSON
        try:
            data = r.json()
        except Exception:
            logging.error(f"[{platform}] JSON decode failed")
            return None

        # API ошибка
        if isinstance(data, dict):
            if data.get("Error") or data.get("error"):
                return None

        return data

    except Exception as e:
        logging.error(f"[{platform}] request failed: {e}")
        return None


# ----------------------------
# Авто-платформа
# ----------------------------
def get_stats_auto(player: str):
    platforms = ["PC", "PS4", "X1"]

    for platform in platforms:
        data = get_stats(player, platform)

        if data and isinstance(data, dict):
            return data, platform

    return None, None


# ----------------------------
# /rank
# ----------------------------
async def rank(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.args:
        await update.message.reply_text("Использование: /rank nickname")
        return

    player = context.args[0]

    msg = await update.message.reply_text("🔎 Ищу игрока...")

    data, platform = get_stats_auto(player)

    if not data:
        await msg.edit_text("❌ Игрок не найден или API не отвечает.")
        return

    try:
        global_data = data.get("global", {})
        rank_data = global_data.get("rank", {})

        level = global_data.get("level", "—")

        rp = rank_data.get("rankScore", "Не найдено")
        rank_name = rank_data.get("rankName", "Не найдено")
        rank_div = rank_data.get("rankDiv", "")

        rank_full = f"{rank_name} {rank_div}".strip()

        await msg.edit_text(
            f"🎮 Игрок: {player}\n"
            f"🖥 Платформа: {platform} (auto)\n\n"
            f"📊 Уровень: {level}\n"
            f"🏆 Ранг: {rank_full}\n"
            f"⭐ RP: {rp}"
        )

    except Exception as e:
        await msg.edit_text(f"⚠️ Ошибка обработки данных: {e}")


# ----------------------------
# запуск
# ----------------------------
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("rank", rank))

    print("Bot started...")
    app.run_polling()


if __name__ == "__main__":
    main()
