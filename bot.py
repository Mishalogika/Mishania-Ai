import os
import random
import requests
from telegram import Update, BotCommand
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes
from groq import Groq

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GROQ_API_KEY = "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"

client = Groq(api_key=GROQ_API_KEY)

user_histories = {}

async def set_commands(app):
    await app.bot.set_my_commands([
        BotCommand("start", "Начать разговор"),
        BotCommand("clear", "Очистить историю чата"),
        BotCommand("members", "Количество участников группы"),
        BotCommand("kick", "Кикнуть участника"),
        BotCommand("mute", "Замутить участника"),
        BotCommand("choose", "Выбрать случайного участника"),
        BotCommand("cube", "Рандомное число между двумя /cube 1 100"),
        BotCommand("weather", "Погода /weather Одесса"),
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Йоу! Я Миханя — твой AI братан 😎 Спрашивай что хочешь!"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_text = update.message.text
    chat_type = update.message.chat.type
    bot_username = context.bot.username

    if chat_type in ["group", "supergroup"]:
        if f"@{bot_username}" not in user_text:
            return
        user_text = user_text.replace(f"@{bot_username}", "").strip()

    if not user_text:
        return

    if user_id not in user_histories:
        user_histories[user_id] = [
            {"role": "system", "content": "Ты AI-ассистент по имени Миханя. Отвечай по-русски, дружелюбно и с характером."}
        ]

    user_histories[user_id].append({"role": "user", "content": user_text})

    if len(user_histories[user_id]) > 21:
        system = user_histories[user_id][0]
        user_histories[user_id] = [system] + user_histories[user_id][-20:]

    thinking_msg = await update.message.reply_text("🧠 Думаю...")

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=user_histories[user_id]
    )

    reply = response.choices[0].message.content
    user_histories[user_id].append({"role": "assistant", "content": reply})

    await thinking_msg.delete()
    await update.message.reply_text(reply)

async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_histories[user_id] = [
        {"role": "system", "content": "Ты AI-ассистент по имени Миханя. Отвечай по-русски, дружелюбно и с характером."}
    ]
    await update.message.reply_text("Всё, забыл всё 🧹")

async def members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type not in ["group", "supergroup"]:
        await update.message.reply_text("Эта команда только для групп!")
        return
    count = await context.bot.get_chat_member_count(chat.id)
    await update.message.reply_text(f"👥 В этой группе {count} участников")

async def kick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    message = update.message
    if chat.type not in ["group", "supergroup"]:
        await message.reply_text("Эта команда только для групп!")
        return
    if not message.reply_to_message:
        await message.reply_text("Ответь на сообщение пользователя которого хочешь кикнуть!")
        return
    caller = await context.bot.get_chat_member(chat.id, message.from_user.id)
    if caller.status not in ["administrator", "creator"]:
        await message.reply_text("❌ Только администраторы могут кикать!")
        return
    target_user = message.reply_to_message.from_user
    try:
        await context.bot.ban_chat_member(chat.id, target_user.id)
        await context.bot.unban_chat_member(chat.id, target_user.id)
        await message.reply_text(f"👢 {target_user.first_name} был кикнут!")
    except Exception:
        await message.reply_text("❌ Не могу кикнуть — убедись что бот администратор!")

async def mute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    message = update.message
    if chat.type not in ["group", "supergroup"]:
        await message.reply_text("Эта команда только для групп!")
        return
    if not message.reply_to_message:
        await message.reply_text("Ответь на сообщение пользователя которого хочешь замутить!")
        return
    caller = await context.bot.get_chat_member(chat.id, message.from_user.id)
    if caller.status not in ["administrator", "creator"]:
        await message.reply_text("❌ Только администраторы могут мутить!")
        return
    target_user = message.reply_to_message.from_user
    try:
        from telegram import ChatPermissions
        await context.bot.restrict_chat_member(
            chat.id, target_user.id,
            permissions=ChatPermissions(can_send_messages=False)
        )
        await message.reply_text(f"🔇 {target_user.first_name} замучен!")
    except Exception:
        await message.reply_text("❌ Не могу замутить — убедись что бот администратор!")

async def choose(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type not in ["group", "supergroup"]:
        await update.message.reply_text("Эта команда только для групп!")
        return
    try:
        count = await context.bot.get_chat_member_count(chat.id)
        # Берём случайный offset
        offset = random.randint(0, max(0, count - 1))
        members_list = await context.bot.get_chat_administrators(chat.id)
        # Выбираем случайного из администраторов (Telegram API не даёт список всех участников)
        chosen = random.choice(members_list)
        name = chosen.user.first_name
        await update.message.reply_text(f"🎲 Случайный участник: {name}!")
    except Exception:
        await update.message.reply_text("❌ Не могу получить список участников!")

async def cube(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        args = context.args
        if len(args) != 2:
            await update.message.reply_text("Использование: /cube 1 100")
            return
        num1 = int(args[0])
        num2 = int(args[1])
        if num1 > num2:
            num1, num2 = num2, num1
        result = random.randint(num1, num2)
        await update.message.reply_text(f"🎲 Случайное число от {num1} до {num2}: **{result}**", parse_mode="Markdown")
    except ValueError:
        await update.message.reply_text("❌ Введи два числа! Например: /cube 1 100")

async def weather(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not context.args:
            await update.message.reply_text("Использование: /weather Одесса")
            return
        city = " ".join(context.args)
        url = f"https://wttr.in/{city}?format=3&lang=ru"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            await update.message.reply_text(f"🌤 {response.text}")
        else:
            await update.message.reply_text("❌ Не могу получить погоду!")
    except Exception:
        await update.message.reply_text("❌ Ошибка при получении погоды!")

app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
app.post_init = set_commands
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("clear", clear))
app.add_handler(CommandHandler("members", members))
app.add_handler(CommandHandler("kick", kick))
app.add_handler(CommandHandler("mute", mute))
app.add_handler(CommandHandler("choose", choose))
app.add_handler(CommandHandler("cube", cube))
app.add_handler(CommandHandler("weather", weather))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("Миханя запущен...")
app.run_polling()
