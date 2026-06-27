import os
TOKEN = os.getenv("TOKEN")
import logging
import requests

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
#apexlegendsapi
API_KEY = "d9357a603b3025c9f4bdab0e35a3ee6a"

logging.basicConfig(level=logging.INFO)


# ----------------------------
# Запрос к Apex API
# ----------------------------
def get_stats(player: str, platform: str):
    url = "https://api.mozambiquehe.re/bridge"

    params = {
        "auth": API_KEY,
        "player": player,
        "platform": platform
    }

    try:
        r = requests.get(url, params=params, timeout=15)
        data = r.json()

        # API может вернуть Error
        if isinstance(data, dict) and data.get("Error"):
            return None

        return data

    except Exception:
        return None


# ----------------------------
# Автоопределение платформы
# ----------------------------
def get_stats_auto(player: str):
    platforms = ["PC", "PS4", "X1"]

    for platform in platforms:
        data = get_stats(player, platform)

        if data:
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
        await msg.edit_text("❌ Игрок не найден ни на одной платформе.")
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
# запуск бота
# ----------------------------
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("rank", rank))

    print("Bot started...")
    app.run_polling()


if __name__ == "__main__":
    main()
