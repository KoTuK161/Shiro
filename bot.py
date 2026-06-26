import os
from dotenv import load_dotenv
load_dotenv()
TOKEN = os.getenv("TOKEN")

import asyncio
import random
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

bot = Bot(TOKEN)
dp = Dispatcher()

# -------------------------
# Карты
# -------------------------

suits = ["♠", "♥", "♦", "♣"]

cards = [
    ("A", 11),
    ("2", 2),
    ("3", 3),
    ("4", 4),
    ("5", 5),
    ("6", 6),
    ("7", 7),
    ("8", 8),
    ("9", 9),
    ("10", 10),
    ("J", 10),
    ("Q", 10),
    ("K", 10)
]

# Игры пользователей
games = {}


def draw_card():
    rank, value = random.choice(cards)
    suit = random.choice(suits)
    return {
        "name": f"{rank}{suit}",
        "rank": rank,
        "value": value
    }


def hand_value(hand):
    total = sum(card["value"] for card in hand)

    aces = sum(1 for c in hand if c["rank"] == "A")

    while total > 21 and aces:
        total -= 10
        aces -= 1

    return total


def cards_text(hand):
    return " ".join(card["name"] for card in hand)


def keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="🎴 Взять карту", callback_data="hit")
    kb.button(text="✋ Хватит", callback_data="stand")
    return kb.as_markup()


# -------------------------
# Старт игры
# -------------------------

@dp.message(Command("blackjack"))
async def blackjack(message: Message):

    player = [draw_card(), draw_card()]
    dealer = [draw_card(), draw_card()]

    games[message.from_user.id] = {
        "player": player,
        "dealer": dealer
    }

    text = (
        f"🃏 Black Jack\n\n"

        f"Ваши карты:\n"
        f"{cards_text(player)}\n"
        f"Очки: {hand_value(player)}\n\n"

        f"Карта дилера:\n"
        f"{dealer[0]['name']} ❓"
    )

    await message.answer(text, reply_markup=keyboard())


# -------------------------
# Взять карту
# -------------------------

@dp.callback_query(F.data == "hit")
async def hit(callback: CallbackQuery):

    game = games.get(callback.from_user.id)

    if not game:
        await callback.answer("Игра не найдена")
        return

    game["player"].append(draw_card())

    score = hand_value(game["player"])

    if score > 21:

        text = (
            f"💥 Перебор!\n\n"

            f"Ваши карты:\n"
            f"{cards_text(game['player'])}\n"
            f"Очки: {score}\n\n"

            f"Вы проиграли."
        )

        del games[callback.from_user.id]

        await callback.message.edit_text(text)

        return

    text = (
        f"Ваши карты:\n"
        f"{cards_text(game['player'])}\n"
        f"Очки: {score}\n\n"

        f"Дилер:\n"
        f"{game['dealer'][0]['name']} ❓"
    )

    await callback.message.edit_text(text, reply_markup=keyboard())

    await callback.answer()


# -------------------------
# Хватит
# -------------------------

@dp.callback_query(F.data == "stand")
async def stand(callback: CallbackQuery):

    game = games.get(callback.from_user.id)

    if not game:
        await callback.answer("Игра не найдена")
        return

    player_score = hand_value(game["player"])

    while hand_value(game["dealer"]) < 17:
        game["dealer"].append(draw_card())

    dealer_score = hand_value(game["dealer"])

    if dealer_score > 21:
        result = "🎉 Дилер перебрал! Вы победили!"

    elif dealer_score > player_score:
        result = "😢 Победа дилера."

    elif dealer_score < player_score:
        result = "🏆 Вы победили!"

    else:
        result = "🤝 Ничья."

    text = (
        f"🃏 Игра окончена\n\n"

        f"Ваши карты:\n"
        f"{cards_text(game['player'])}\n"
        f"Очки: {player_score}\n\n"

        f"Карты дилера:\n"
        f"{cards_text(game['dealer'])}\n"
        f"Очки: {dealer_score}\n\n"

        f"{result}"
    )

    del games[callback.from_user.id]

    await callback.message.edit_text(text)

    await callback.answer()


# -------------------------

async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
