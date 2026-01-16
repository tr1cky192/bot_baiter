import random
from datetime import time
import pytz
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

TELEGRAM_BOT_TOKEN = "8507633938:AAFRcZ9hTODKM7WRkcI5kHpBAx3admkoAsM"
TIMEZONE = pytz.timezone("Europe/Kyiv")
POST_TIME = time(hour=13, minute=28, tzinfo=TIMEZONE)

BANTER_MESSAGES = [
    "🎯 {user}, сьогодні твоя черга тягнути катку 😎",
    "🔥 {user}, готуйся — вся тима розраховує на тебе!",
    "💥 {user}, не забудь: сьогодні без фідів 😏",
    "😈 {user}, якщо програємо — знаємо кого винити (жарт 😄)",
    "🧠 {user}, включай мозок — сьогодні твій день!"
]


active_users = set()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Я бот, який щодня байтить рандомного гравця на катку в CS 😎\n"
        "Напиши /activate у групі, щоб увімкнути."
    )


async def track_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type not in ["group", "supergroup"]:
        return

    user = update.effective_user
    if user and not user.is_bot:
        active_users.add(user.id)


async def daily_banter(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.chat_id

    if not active_users:
        await context.bot.send_message(chat_id=chat_id, text="Нема активних гравців для байту сьогодні.")
        return

    user_id = random.choice(list(active_users))
    user = await context.bot.get_chat(user_id)
    username = f"@{user.username}" if user.username else user.first_name

    message = random.choice(BANTER_MESSAGES).format(user=username)
    await context.bot.send_message(chat_id=chat_id, text=message)


async def activate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    context.job_queue.run_daily(
        daily_banter,
        time=POST_TIME,
        chat_id=chat_id,
        name=str(chat_id)
    )

    await update.message.reply_text("Активовано! Я буду щодня байтити рандомного гравця")


if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("activate", activate))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, track_users))

    print("Бот запущено...")
    app.run_polling()
