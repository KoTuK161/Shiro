import os
from dotenv import load_dotenv
load_dotenv()
TOKEN = os.getenv("TOKEN")

import requests
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Хранилище игроков (ник -> платформа)
players = {}  # пример: {"JIeHuBblu_KoT": "PC"}

# Получение RP
def get_rp(nickname, platform="PC"):
    try:
        url = f"https://apexlegendsstatus.com/profile/{platform}/{nickname}"
        headers = {"User-Agent": "Mozilla/5.0"}

        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        rp_tag = soup.find(
            "p",
            class_="center-element general-stats general-stats-rank"
        )

        if rp_tag:
            return rp_tag.text.strip()
        else:
            return "RP не найден 😢"

    except Exception as e:
        return f"Ошибка: {e}"

# /add
async def add_player(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Используй: /add <ник>")
        return

    nickname = context.args[0]
    players[nickname] = "PC"

    await update.message.reply_text(f"✅ Добавлен: {nickname}")

# /remove
async def remove_player(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Используй: /remove <ник>")
        return

    nickname = context.args[0]

    if nickname in players:
        del players[nickname]
        await update.message.reply_text(f"❌ Удалён: {nickname}")
    else:
        await update.message.reply_text("Игрок не найден")

# /list
async def list_players(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not players:
        await update.message.reply_text("Список пуст 😢")
        return

    text = "📋 Игроки:\n"
    for p in players:
        text += f"- {p}\n"

    await update.message.reply_text(text)

# /rp (все или один)
async def rp_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        nickname = context.args[0]

        if nickname not in players:
            await update.message.reply_text("Игрок не добавлен")
            return

        rp = get_rp(nickname)
        await update.message.reply_text(f"{nickname}: {rp}")
    else:
        if not players:
            await update.message.reply_text("Нет игроков 😢")
            return

        text = "🏆 RP игроков:\n"
        for nickname in players:
            rp = get_rp(nickname)
            text += f"{nickname}: {rp}\n"

        await update.message.reply_text(text)

# Запуск
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("add", add_player))
    app.add_handler(CommandHandler("remove", remove_player))
    app.add_handler(CommandHandler("list", list_players))
    app.add_handler(CommandHandler("rp", rp_command))

    print("Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()
