import random
from datetime import datetime, timedelta
import pytz
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import asyncio
import re
import logging
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TIMEZONE = pytz.timezone("Europe/Kyiv")
POST_HOUR = 20
POST_MINUTE = 00

active_users = set()
chat_ids = set()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привіт! Я бот, який щодня байтить рандомного гравця\n\n"
        "У групі: напиши /activate\n"
        "У приваті: просто пиши — я відповім"
    )


async def activate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_ids.add(chat_id)
    await update.message.reply_text("Активовано! Я буду щодня байтити рандомного гравця")


async def add_me(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    active_users.add(user.id)
    await update.message.reply_text(f"{user.first_name} доданий до активних гравців!")


async def show_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not active_users:
        await update.message.reply_text("Поки що немає активних користувачів.")
        return
    users_text = ", ".join(str(uid) for uid in active_users)
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
                username = f"@{user.username}" if user.username else user.first_name

                prompt = f"""
Ти дружній, веселий та гострий AI-бот. 
Придумай короткий, смішний або трішки провокативний байт для користувача {username}.
Можна використати геймерський сленг. 
Відповідь максимум 1-2 речення.
"""

                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "Ти веселий AI-асистент, який робить добрі підколки."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=60,
                    temperature=0.9
                )

                message = response.choices[0].message.content.strip()
                await app.bot.send_message(chat_id=chat_id, text=message)

            except Exception as e:
                logger.error(f"Помилка при байті: {e}")


async def ai_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text
    chat_type = update.effective_chat.type
    bot_username = (await context.bot.get_me()).username.lower()
    logger.info(f"Повідомлення: {text}")

    if chat_type in ["group", "supergroup"]:
        if f"@{bot_username}" not in text.lower():
            return  
        clean_text = re.sub(f"@{bot_username}", "", text, flags=re.IGNORECASE).strip()
    else:
        clean_text = text.strip()

    await update.message.reply_text("Думаю...")

    if not OPENAI_API_KEY or OPENAI_API_KEY.startswith("PASTE"):
        await update.message.reply_text("OpenAI ключ не підключений. Я поки що відповідаю вручну")
        return

    urls = re.findall(r'(https?://\S+)', clean_text)
    match_url = urls[0] if urls else None

    if match_url:
        prompt = f"""
Ти спортивний аналітик у дружньому чаті.

Проаналізуй матч за посиланням: {match_url}

Дай:
1. Короткий аналіз команд
2. Хто фаворит
3. Можливий рахунок
4. Один цікавий факт або ризик

Пиши українською, неформально.
"""
    else:
        prompt = f"""
Ти дружній AI-бот у Telegram чаті. Відповідай коротко, весело і по-людськи.

Повідомлення користувача: "{clean_text}"
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Ти дружній AI-асистент у геймерському чаті."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.8
        )

        reply = response.choices[0].message.content
        logger.info("✅ AI відповів.")
        await update.message.reply_text(reply)

    except Exception as e:
        logger.error(f"Помилка AI: {e}")
        await update.message.reply_text("AI зараз недоступний. Перевір ключ або інтернет.")


if __name__ == "__main__":
    print("Бот запускається...")

    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("activate", activate))
    app.add_handler(CommandHandler("addme", add_me))
    app.add_handler(CommandHandler("users", show_users))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ai_handler))

    async def post_init(app):
        app.create_task(daily_banter(app))

    app.post_init = post_init

    print("Бот запущено...")
    app.run_polling()
