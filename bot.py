import os
import random
import requests
from datetime import timedelta
from telegram import Update, BotCommand, ChatPermissions
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
        BotCommand("members", "Количество участников"),
        BotCommand("kick", "Кикнуть участника"),
        BotCommand("mute", "Замутить /mute 10m или 1h или 1d"),
        BotCommand("unmute", "Размутить участника"),
        BotCommand("choose", "Выбрать случайного участника"),
        BotCommand("cube", "Рандомное число /cube 1 100"),
        BotCommand("weather", "Погода /weather Одесса"),
        BotCommand("roll", "Бросить кубик /roll или /roll 20"),
        BotCommand("flip", "Орёл или решка"),
        BotCommand("joke", "Случайная шутка"),
        BotCommand("poll", "Создать опрос /poll Вопрос?Да|Нет"),
        BotCommand("info", "Инфо о пользователе"),
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
        await message.reply_text("Ответь на сообщение! Пример: /mute 10m или /mute 1h или /mute 1d")
        return
    caller = await context.bot.get_chat_member(chat.id, message.from_user.id)
    if caller.status not in ["administrator", "creator"]:
        await message.reply_text("❌ Только администраторы могут мутить!")
        return

    # Парсим время
    duration = None
    duration_text = "навсегда"
    if context.args:
        arg = context.args[0].lower()
        try:
            if arg.endswith("m"):
                duration = timedelta(minutes=int(arg[:-1]))
                duration_text = f"{arg[:-1]} минут"
            elif arg.endswith("h"):
                duration = timedelta(hours=int(arg[:-1]))
                duration_text = f"{arg[:-1]} часов"
            elif arg.endswith("d"):
                duration = timedelta(days=int(arg[:-1]))
                duration_text = f"{arg[:-1]} дней"
        except ValueError:
            await message.reply_text("❌ Неверный формат! Пример: /mute 10m или /mute 1h или /mute 1d")
            return

    target_user = message.reply_to_message.from_user
    until_date = None
    if duration:
        from datetime import datetime, timezone
        until_date = datetime.now(timezone.utc) + duration

    try:
        await context.bot.restrict_chat_member(
            chat.id, target_user.id,
            permissions=ChatPermissions(can_send_messages=False),
            until_date=until_date
        )
        await message.reply_text(f"🔇 {target_user.first_name} замучен на {duration_text}!")
    except Exception:
        await message.reply_text("❌ Не могу замутить — убедись что бот администратор!")

async def unmute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    message = update.message
    if chat.type not in ["group", "supergroup"]:
        await message.reply_text("Эта команда только для групп!")
        return
    if not message.reply_to_message:
        await message.reply_text("Ответь на сообщение пользователя которого хочешь размутить!")
        return
    caller = await context.bot.get_chat_member(chat.id, message.from_user.id)
    if caller.status not in ["administrator", "creator"]:
        await message.reply_text("❌ Только администраторы могут размучивать!")
        return
    target_user = message.reply_to_message.from_user
    try:
        await context.bot.restrict_chat_member(
            chat.id, target_user.id,
            permissions=ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True
            )
        )
        await message.reply_text(f"🔊 {target_user.first_name} размучен!")
    except Exception:
        await message.reply_text("❌ Не могу размутить — убедись что бот администратор!")

async def choose(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type not in ["group", "supergroup"]:
        await update.message.reply_text("Эта команда только для групп!")
        return
    try:
        admins = await context.bot.get_chat_administrators(chat.id)
        chosen = random.choice(admins)
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
        await update.message.reply_text(f"🎲 Случайное число от {num1} до {num2}: *{result}*", parse_mode="Markdown")
    except ValueError:
        await update.message.reply_text("❌ Введи два числа! Например: /cube 1 100")

async def weather(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not context.args:
            await update.message.reply_text("Использование: /weather Одесса")
            return
        city = " ".join(context.args)
        url = f"https://wttr.in/{city}?format=3&lang=ru&m"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            await update.message.reply_text(f"🌤 {response.text}")
        else:
            await update.message.reply_text("❌ Не могу получить погоду!")
    except Exception:
        await update.message.reply_text("❌ Ошибка при получении погоды!")

async def roll(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sides = 6
    if context.args:
        try:
            sides = int(context.args[0])
        except ValueError:
            pass
    result = random.randint(1, sides)
    await update.message.reply_text(f"🎲 Бросаю кубик d{sides}... выпало *{result}*!", parse_mode="Markdown")

async def flip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = random.choice(["🦅 Орёл!", "🪙 Решка!"])
    await update.message.reply_text(result)

async def joke(update: Update, context: ContextTypes.DEFAULT_TYPE):
    jokes = [
        "Почему программисты путают Хэллоуин и Рождество? Потому что Oct 31 == Dec 25! 😄",
        "— Официант, у меня в супе муха! — Тише, а то все захотят! 😂",
        "Моя жена сказала, что я слишком много времени провожу за компьютером. Я ответил: 'Это не баг, это фича!' 😆",
        "— Как называется медведь без ушей? — Медвь! 🐻",
        "Купил книгу 'Как не быть бедным'. Внутри один лист: 'Будь богатым!' 📚",
        "Я сказал жене, что она рисует брови слишком высоко. Она выглядела удивлённой. 😮",
        "— Папа, почему солнце встаёт на востоке? — Сынок, не трогай это, оно хотя бы работает! ☀️",
    ]
    await update.message.reply_text(random.choice(jokes))

async def poll(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not context.args:
            await update.message.reply_text("Использование: /poll Вопрос?Вариант1|Вариант2|Вариант3")
            return
        text = " ".join(context.args)
        if "?" not in text:
            await update.message.reply_text("❌ Формат: /poll Вопрос?Вариант1|Вариант2")
            return
        question, options_text = text.split("?", 1)
        options = [o.strip() for o in options_text.split("|") if o.strip()]
        if len(options) < 2:
            await update.message.reply_text("❌ Нужно минимум 2 варианта!")
            return
        await context.bot.send_poll(
            chat_id=update.effective_chat.id,
            question=question.strip() + "?",
            options=options[:10]
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {e}")

async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.reply_to_message:
        user = update.message.reply_to_message.from_user
    else:
        user = update.effective_user
    text = (
        f"👤 *Информация о пользователе*\n"
        f"Имя: {user.first_name}\n"
        f"Фамилия: {user.last_name or '—'}\n"
        f"Username: @{user.username or '—'}\n"
        f"ID: `{user.id}`\n"
        f"Бот: {'Да' if user.is_bot else 'Нет'}"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
app.post_init = set_commands
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("clear", clear))
app.add_handler(CommandHandler("members", members))
app.add_handler(CommandHandler("kick", kick))
app.add_handler(CommandHandler("mute", mute))
app.add_handler(CommandHandler("unmute", unmute))
app.add_handler(CommandHandler("choose", choose))
app.add_handler(CommandHandler("cube", cube))
app.add_handler(CommandHandler("weather", weather))
app.add_handler(CommandHandler("roll", roll))
app.add_handler(CommandHandler("flip", flip))
app.add_handler(CommandHandler("joke", joke))
app.add_handler(CommandHandler("poll", poll))
app.add_handler(CommandHandler("info", info))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("Миханя запущен...")
app.run_polling()
