import random
from datetime import datetime, timedelta
import pytz
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import asyncio
TELEGRAM_BOT_TOKEN = "8507633938:AAFRcZ9hTODKM7WRkcI5kHpBAx3admkoAsM"

TIMEZONE = pytz.timezone("Europe/Kyiv")
POST_HOUR = 14
POST_MINUTE = 27

BANTER_MESSAGES = [
    "🎯 {user}, сьогодні твоя черга тягнути катку 😎",
    "🔥 {user}, готуйся — вся тима розраховує на тебе!",
    "💥 {user}, не забудь: сьогодні без фідів 😏",
    "😈 {user}, якщо програємо — знаємо кого винити (жарт 😄)",
    "🧠 {user}, включай мозок — сьогодні твій день!",
    "... {user}, ти або граєш або сі дивищ крінгу!"
    "... {user}, Юрі ти що сплє?!"
]

active_users = set()
chat_ids = set()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Я бот, який щодня байтить рандомного гравця 😎\n"
        "Напиши /activate у групі, щоб увімкнути."
    )


async def track_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type not in ["group", "supergroup"]:
        return
    user = update.effective_user
    if user and not user.is_bot:
        active_users.add(user.id)

async def show_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not active_users:
        await update.message.reply_text("Поки що немає активних користувачів 😢")
        return

    # Виводимо список user_id
    users_text = ", ".join(str(user_id) for user_id in active_users)
    await update.message.reply_text(f"Активні користувачі: {users_text}")

async def daily_banter(app):
    while True:
        now = datetime.now(TIMEZONE)
        next_run = now.replace(hour=POST_HOUR, minute=POST_MINUTE, second=0, microsecond=0)
        if next_run < now:
            next_run += timedelta(days=1)
        wait_seconds = (next_run - now).total_seconds()
        await asyncio.sleep(wait_seconds)

        for chat_id in chat_ids:
            if not active_users:
                await app.bot.send_message(chat_id=chat_id, text="Нема активних гравців для байту сьогодні.")
                continue
            user_id = random.choice(list(active_users))
            try:
                user = await app.bot.get_chat(user_id)
            except:
                continue
            username = f"@{user.username}" if user.username else user.first_name
            message = random.choice(BANTER_MESSAGES).format(user=username)
            await app.bot.send_message(chat_id=chat_id, text=message)


async def activate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_ids.add(chat_id)
    await update.message.reply_text("Активовано! Я буду щодня байтити рандомного гравця 😎")

async def add_me(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    active_users.add(user.id)
    await update.message.reply_text(f"{user.first_name} доданий до активних гравців!")


if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("addme", add_me))
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("activate", activate))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, track_users))
    app.add_handler(CommandHandler("users", show_users))
    async def post_init(app):
        app.create_task(daily_banter(app))

    app.post_init = post_init

    print("Бот запущено...")
    app.run_polling()
