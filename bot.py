import os
TOKEN = os.getenv("TOKEN")

import logging
import re
import json
import requests

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

logging.basicConfig(level=logging.INFO)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36"
    )
}


# ----------------------------
# Получение страницы профиля
# ----------------------------
def fetch_profile(player: str, platform: str = "PC"):
    url = f"https://apexlegendsstatus.com/profile/{platform}/{player}"

    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        if r.status_code != 200:
            return None
        return r.text
    except:
        return None


# ----------------------------
# Парсинг RP и ранга (без bs4)
# ----------------------------
def parse_stats(html: str):
    rp = None
    rank = None

    # -------------------------
    # 1. Пытаемся достать JSON
    # -------------------------
    try:
        # ищем большой JSON в странице
        start = html.find("__NEXT_DATA__")
        if start != -1:
            json_start = html.find("{", start)
            json_end = html.rfind("}")
            raw_json = html[json_start:json_end + 1]

            data = json.loads(raw_json)

            rank_info = (
                data.get("props", {})
                    .get("pageProps", {})
                    .get("data", {})
                    .get("global", {})
                    .get("rank", {})
            )

            if rank_info:
                name = rank_info.get("rankName")
                div = rank_info.get("rankDiv")
                score = rank_info.get("rankScore")

                if name:
                    rank = f"{name} {div}" if div else name

                if score:
                    rp = str(score)

                return rp, rank

    except Exception:
        pass

    # -------------------------
    # 2. Fallback regex
    # -------------------------
    clean_text = re.sub(r"<[^>]+>", " ", html)

    rp_match = re.search(r"([\d,.]+)\s*RP", clean_text)
    if rp_match:
        rp = rp_match.group(1)

    ranks = [
        "Rookie",
        "Bronze",
        "Silver",
        "Gold",
        "Platinum",
        "Diamond",
        "Master",
        "Apex Predator"
    ]

    for r in ranks:
        if r in clean_text:
            tier = re.search(rf"{r}\s*(IV|III|II|I)?", clean_text)
            if tier:
                rank = tier.group(0)
                break

    return rp, rank


# ----------------------------
# /rank команда
# ----------------------------
async def rank(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.args:
        await update.message.reply_text(
            "Использование:\n/rank nickname [platform]\n"
            "Пример:\n/rank NickName PC"
        )
        return

    player = context.args[0]
    platform = context.args[1].upper() if len(context.args) > 1 else "PC"

    msg = await update.message.reply_text("🔎 Ищу игрока...")

    html = fetch_profile(player, platform)

    if not html:
        await msg.edit_text("❌ Профиль не найден или недоступен.")
        return

    rp, rank = parse_stats(html)

    rp = rp or "Не найдено"
    rank = rank or "Не найдено"

    await msg.edit_text(
        f"🎮 Игрок: {player}\n"
        f"🖥 Платформа: {platform}\n\n"
        f"🏆 Ранг: {rank}\n"
        f"⭐ RP: {rp}"
    )


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
