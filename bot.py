import os
TOKEN = os.getenv("TOKEN")

import logging
import re
import requests
from bs4 import BeautifulSoup

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

logging.basicConfig(level=logging.INFO)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"
}


# ----------------------------
# 1. ЗАПРОС СТРАНИЦЫ ПРОФИЛЯ
# ----------------------------
def fetch_profile(player: str, platform: str = "PC"):
    url = f"https://apexlegendsstatus.com/profile/{platform}/{player}"
    r = requests.get(url, headers=HEADERS, timeout=15)

    if r.status_code != 200:
        return None

    return r.text


# ----------------------------
# 2. ПАРСИНГ RP И РАНГА (JSON / HTML fallback)
# ----------------------------
def parse_stats(html: str):
    rp = None
    rank = None

    # ---------
    # ВАРИАНТ 1: JSON внутри страницы (если есть)
    # ---------
    try:
        soup = BeautifulSoup(html, "lxml")

        scripts = soup.find_all("script")
        for s in scripts:
            if s.string and "__NEXT_DATA__" in s.string:
                json_text = s.string

                start = json_text.find("{")
                end = json_text.rfind("}")
                data = json_text[start:end+1]

                import json
                obj = json.loads(data)

                # попытка достать rank
                rank_info = obj.get("props", {}) \
                              .get("pageProps", {}) \
                              .get("data", {}) \
                              .get("global", {}) \
                              .get("rank", {})

                if rank_info:
                    rank = rank_info.get("rankName")
                    div = rank_info.get("rankDiv")
                    score = rank_info.get("rankScore")

                    if rank and div:
                        rank = f"{rank} {div}"
                    if score:
                        rp = str(score)

                    return rp, rank
    except:
        pass

    # ---------
    # ВАРИАНТ 2: HTML fallback
    # ---------
    text = BeautifulSoup(html, "lxml").get_text(" ", strip=True)

    rp_match = re.search(r"([\d,.]+)\s*RP", text)
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
        if r in text:
            tier = re.search(rf"{r}\s*(IV|III|II|I)?", text)
            if tier:
                rank = tier.group(0)
                break

    return rp, rank


# ----------------------------
# 3. КОМАНДА /rank
# ----------------------------
async def rank(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.args:
        await update.message.reply_text("Использование: /rank nickname [platform]")
        return

    player = context.args[0]
    platform = context.args[1].upper() if len(context.args) > 1 else "PC"

    msg = await update.message.reply_text("🔎 Ищу игрока...")

    try:
        html = fetch_profile(player, platform)

        if not html:
            await msg.edit_text("❌ Игрок не найден или профиль недоступен.")
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

    except Exception as e:
        await msg.edit_text(f"⚠️ Ошибка: {e}")


# ----------------------------
# 4. ЗАПУСК БОТА
# ----------------------------
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("rank", rank))

    print("Bot started...")
    app.run_polling()


if __name__ == "__main__":
    main()
