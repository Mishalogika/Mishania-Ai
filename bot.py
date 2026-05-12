import os
import random
import requests
from datetime import timedelta, datetime, timezone
from telegram import Update, BotCommand, ChatPermissions
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes
from groq import Groq

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GROQ_API_KEY = "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"

client = Groq(api_key=GROQ_API_KEY)
user_histories = {}
warned_users = {}

async def set_commands(app):
    await app.bot.set_my_commands([
        BotCommand("start", "Начать разговор"),
        BotCommand("clear", "Очистить историю чата"),
        BotCommand("members", "Количество участников"),
        BotCommand("kick", "Кикнуть участника"),
        BotCommand("ban", "Забанить участника"),
        BotCommand("unban", "Разбанить участника"),
        BotCommand("mute", "Замутить /mute 10m / 1h / 1d"),
        BotCommand("unmute", "Размутить участника"),
        BotCommand("warn", "Предупредить участника"),
        BotCommand("warns", "Посмотреть предупреждения"),
        BotCommand("clearwarns", "Сбросить предупреждения"),
        BotCommand("pin", "Закрепить сообщение"),
        BotCommand("unpin", "Открепить сообщение"),
        BotCommand("promote", "Сделать админом"),
        BotCommand("demote", "Снять с админа"),
        BotCommand("choose", "Выбрать случайного участника"),
        BotCommand("cube", "Рандомное число /cube 1 100"),
        BotCommand("weather", "Погода /weather Одесса"),
        BotCommand("roll", "Бросить кубик /roll или /roll 20"),
        BotCommand("flip", "Орёл или решка"),
        BotCommand("joke", "Случайная шутка"),
        BotCommand("poll", "Создать опрос /poll Вопрос?Да|Нет"),
        BotCommand("info", "Инфо о пользователе"),
        BotCommand("gay", "Узнать % гейства"),
        BotCommand("iq", "Измерить IQ"),
        BotCommand("rate", "Оценить рандомно"),
        BotCommand("ship", "Шип двух людей"),
        BotCommand("slap", "Дать пощёчину"),
        BotCommand("hug", "Обнять"),
        BotCommand("rps", "Камень ножницы бумага /rps камень"),
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Йоу! Я Миханя — твой AI братан 😎 Спрашивай что хочешь!")

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

def is_admin(status):
    return status in ["administrator", "creator"]

async def kick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    message = update.message
    if chat.type not in ["group", "supergroup"]:
        await message.reply_text("Только для групп!")
        return
    if not message.reply_to_message:
        await message.reply_text("Ответь на сообщение пользователя!")
        return
    caller = await context.bot.get_chat_member(chat.id, message.from_user.id)
    if not is_admin(caller.status):
        await message.reply_text("❌ Только администраторы!")
        return
    target = message.reply_to_message.from_user
    try:
        await context.bot.ban_chat_member(chat.id, target.id)
        await context.bot.unban_chat_member(chat.id, target.id)
        await message.reply_text(f"👢 {target.first_name} был кикнут!")
    except Exception:
        await message.reply_text("❌ Не могу кикнуть — бот должен быть админом!")

async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    message = update.message
    if chat.type not in ["group", "supergroup"]:
        await message.reply_text("Только для групп!")
        return
    if not message.reply_to_message:
        await message.reply_text("Ответь на сообщение пользователя!")
        return
    caller = await context.bot.get_chat_member(chat.id, message.from_user.id)
    if not is_admin(caller.status):
        await message.reply_text("❌ Только администраторы!")
        return
    target = message.reply_to_message.from_user
    try:
        await context.bot.ban_chat_member(chat.id, target.id)
        await message.reply_text(f"🔨 {target.first_name} забанен!")
    except Exception:
        await message.reply_text("❌ Не могу забанить!")

async def unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    message = update.message
    if chat.type not in ["group", "supergroup"]:
        await message.reply_text("Только для групп!")
        return
    if not message.reply_to_message:
        await message.reply_text("Ответь на сообщение пользователя!")
        return
    caller = await context.bot.get_chat_member(chat.id, message.from_user.id)
    if not is_admin(caller.status):
        await message.reply_text("❌ Только администраторы!")
        return
    target = message.reply_to_message.from_user
    try:
        await context.bot.unban_chat_member(chat.id, target.id)
        await message.reply_text(f"✅ {target.first_name} разбанен!")
    except Exception:
        await message.reply_text("❌ Не могу разбанить!")

async def mute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    message = update.message
    if chat.type not in ["group", "supergroup"]:
        await message.reply_text("Только для групп!")
        return
    if not message.reply_to_message:
        await message.reply_text("Ответь на сообщение! Пример: /mute 10m или /mute 1h или /mute 1d")
        return
    caller = await context.bot.get_chat_member(chat.id, message.from_user.id)
    if not is_admin(caller.status):
        await message.reply_text("❌ Только администраторы!")
        return

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
            else:
                await message.reply_text("❌ Формат: /mute 10m или /mute 2h или /mute 1d")
                return
        except ValueError:
            await message.reply_text("❌ Неверный формат! Пример: /mute 10m")
            return

    target = message.reply_to_message.from_user
    until_date = datetime.now(timezone.utc) + duration if duration else None

    try:
        await context.bot.restrict_chat_member(
            chat.id, target.id,
            permissions=ChatPermissions(can_send_messages=False),
            until_date=until_date
        )
        await message.reply_text(f"🔇 {target.first_name} замучен на {duration_text}!")
    except Exception:
        await message.reply_text("❌ Не могу замутить — бот должен быть админом!")

async def unmute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    message = update.message
    if chat.type not in ["group", "supergroup"]:
        await message.reply_text("Только для групп!")
        return
    if not message.reply_to_message:
        await message.reply_text("Ответь на сообщение пользователя!")
        return
    caller = await context.bot.get_chat_member(chat.id, message.from_user.id)
    if not is_admin(caller.status):
        await message.reply_text("❌ Только администраторы!")
        return
    target = message.reply_to_message.from_user
    try:
        await context.bot.restrict_chat_member(
            chat.id, target.id,
            permissions=ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True
            )
        )
        await message.reply_text(f"🔊 {target.first_name} размучен!")
    except Exception:
        await message.reply_text("❌ Не могу размутить!")

async def warn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    message = update.message
    if chat.type not in ["group", "supergroup"]:
        await message.reply_text("Только для групп!")
        return
    if not message.reply_to_message:
        await message.reply_text("Ответь на сообщение пользователя!")
        return
    caller = await context.bot.get_chat_member(chat.id, message.from_user.id)
    if not is_admin(caller.status):
        await message.reply_text("❌ Только администраторы!")
        return
    target = message.reply_to_message.from_user
    key = f"{chat.id}:{target.id}"
    warned_users[key] = warned_users.get(key, 0) + 1
    count = warned_users[key]
    if count >= 3:
        try:
            await context.bot.ban_chat_member(chat.id, target.id)
            await context.bot.unban_chat_member(chat.id, target.id)
            warned_users[key] = 0
            await message.reply_text(f"⚠️ {target.first_name} получил 3 предупреждения и был кикнут!")
        except Exception:
            await message.reply_text(f"⚠️ {target.first_name} имеет {count}/3 предупреждений!")
    else:
        await message.reply_text(f"⚠️ {target.first_name} получил предупреждение {count}/3!")

async def warns(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    message = update.message
    if not message.reply_to_message:
        await message.reply_text("Ответь на сообщение пользователя!")
        return
    target = message.reply_to_message.from_user
    key = f"{chat.id}:{target.id}"
    count = warned_users.get(key, 0)
    await message.reply_text(f"⚠️ У {target.first_name} {count}/3 предупреждений")

async def clearwarns(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    message = update.message
    if not message.reply_to_message:
        await message.reply_text("Ответь на сообщение пользователя!")
        return
    caller = await context.bot.get_chat_member(chat.id, message.from_user.id)
    if not is_admin(caller.status):
        await message.reply_text("❌ Только администраторы!")
        return
    target = message.reply_to_message.from_user
    key = f"{chat.id}:{target.id}"
    warned_users[key] = 0
    await message.reply_text(f"✅ Предупреждения {target.first_name} сброшены!")

async def pin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    message = update.message
    if not message.reply_to_message:
        await message.reply_text("Ответь на сообщение которое хочешь закрепить!")
        return
    caller = await context.bot.get_chat_member(chat.id, message.from_user.id)
    if not is_admin(caller.status):
        await message.reply_text("❌ Только администраторы!")
        return
    try:
        await context.bot.pin_chat_message(chat.id, message.reply_to_message.message_id)
        await message.reply_text("📌 Сообщение закреплено!")
    except Exception:
        await message.reply_text("❌ Не могу закрепить!")

async def unpin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    message = update.message
    caller = await context.bot.get_chat_member(chat.id, message.from_user.id)
    if not is_admin(caller.status):
        await message.reply_text("❌ Только администраторы!")
        return
    try:
        await context.bot.unpin_chat_message(chat.id)
        await message.reply_text("📌 Сообщение откреплено!")
    except Exception:
        await message.reply_text("❌ Не могу открепить!")

async def promote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    message = update.message
    if not message.reply_to_message:
        await message.reply_text("Ответь на сообщение пользователя!")
        return
    caller = await context.bot.get_chat_member(chat.id, message.from_user.id)
    if caller.status != "creator":
        await message.reply_text("❌ Только создатель группы может назначать админов!")
        return
    target = message.reply_to_message.from_user
    try:
        await context.bot.promote_chat_member(
            chat.id, target.id,
            can_delete_messages=True,
            can_restrict_members=True,
            can_pin_messages=True,
            can_invite_users=True
        )
        await message.reply_text(f"⭐ {target.first_name} теперь администратор!")
    except Exception:
        await message.reply_text("❌ Не могу назначить админа!")

async def demote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    message = update.message
    if not message.reply_to_message:
        await message.reply_text("Ответь на сообщение пользователя!")
        return
    caller = await context.bot.get_chat_member(chat.id, message.from_user.id)
    if caller.status != "creator":
        await message.reply_text("❌ Только создатель группы!")
        return
    target = message.reply_to_message.from_user
    try:
        await context.bot.promote_chat_member(
            chat.id, target.id,
            can_delete_messages=False,
            can_restrict_members=False,
            can_pin_messages=False,
            can_invite_users=False
        )
        await message.reply_text(f"⬇️ {target.first_name} снят с админа!")
    except Exception:
        await message.reply_text("❌ Не могу снять с админа!")

async def choose(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type not in ["group", "supergroup"]:
        await update.message.reply_text("Только для групп!")
        return
    try:
        admins = await context.bot.get_chat_administrators(chat.id)
        chosen = random.choice(admins)
        await update.message.reply_text(f"🎲 Случайный участник: {chosen.user.first_name}!")
    except Exception:
        await update.message.reply_text("❌ Не могу получить список!")

async def cube(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        args = context.args
        if len(args) != 2:
            await update.message.reply_text("Использование: /cube 1 100")
            return
        num1, num2 = int(args[0]), int(args[1])
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
        "Моя жена сказала что я слишком много времени за компом. Я ответил: 'Это не баг это фича!' 😆",
        "— Как называется медведь без ушей? — Медвь! 🐻",
        "Купил книгу 'Как не быть бедным'. Внутри один лист: 'Будь богатым!' 📚",
        "Я сказал жене что она рисует брови слишком высоко. Она выглядела удивлённой. 😮",
        "— Папа, почему солнце встаёт на востоке? — Сынок, не трогай это, оно хотя бы работает! ☀️",
        "Программист пошёл в магазин. Жена сказала: 'Купи хлеб, и если будут яйца — возьми десяток'. Он вернулся с 10 буханками хлеба. 🍞",
    ]
    await update.message.reply_text(random.choice(jokes))

async def poll(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not context.args:
            await update.message.reply_text("Использование: /poll Вопрос?Вариант1|Вариант2")
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
        await context.bot.send_poll(chat_id=update.effective_chat.id, question=question.strip() + "?", options=options[:10])
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {e}")

async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.reply_to_message.from_user if update.message.reply_to_message else update.effective_user
    text = (
        f"👤 *Информация о пользователе*\n"
        f"Имя: {user.first_name}\n"
        f"Фамилия: {user.last_name or '—'}\n"
        f"Username: @{user.username or '—'}\n"
        f"ID: `{user.id}`\n"
        f"Бот: {'Да' if user.is_bot else 'Нет'}"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def gay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.reply_to_message.from_user if update.message.reply_to_message else update.effective_user
    percent = random.randint(0, 100)
    bar = "🌈" * (percent // 10) + "⬜" * (10 - percent // 10)
    await update.message.reply_text(f"🏳️‍🌈 {user.first_name} гей на {percent}%\n{bar}")

async def iq(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.reply_to_message.from_user if update.message.reply_to_message else update.effective_user
    score = random.randint(0, 200)
    if score < 70:
        comment = "🥴 Ну... старайся!"
    elif score < 100:
        comment = "😐 Средненько"
    elif score < 130:
        comment = "🧠 Неплохо!"
    elif score < 160:
        comment = "🎓 Умник!"
    else:
        comment = "🚀 Гений!"
    await update.message.reply_text(f"🧠 IQ {user.first_name}: {score}\n{comment}")

async def rate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.reply_to_message.from_user if update.message.reply_to_message else update.effective_user
    score = random.randint(0, 10)
    stars = "⭐" * score + "☆" * (10 - score)
    await update.message.reply_text(f"📊 {user.first_name} оценён на {score}/10\n{stars}")

async def ship(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        await update.message.reply_text("Ответь на сообщение второго человека!")
        return
    user1 = update.effective_user.first_name
    user2 = update.message.reply_to_message.from_user.first_name
    percent = random.randint(0, 100)
    hearts = "❤️" * (percent // 10) + "🖤" * (10 - percent // 10)
    await update.message.reply_text(f"💕 {user1} + {user2} = {percent}%\n{hearts}")

async def slap(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        await update.message.reply_text("Ответь на сообщение!")
        return
    user1 = update.effective_user.first_name
    user2 = update.message.reply_to_message.from_user.first_name
    await update.message.reply_text(f"👋 {user1} дал пощёчину {user2}! ШЛЁП!")

async def hug(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        await update.message.reply_text("Ответь на сообщение!")
        return
    user1 = update.effective_user.first_name
    user2 = update.message.reply_to_message.from_user.first_name
    await update.message.reply_text(f"🤗 {user1} обнял {user2}! Тепло и уютно~")

async def rps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choices = {"камень": "🪨", "ножницы": "✂️", "бумага": "📄"}
    if not context.args or context.args[0].lower() not in choices:
        await update.message.reply_text("Использование: /rps камень или /rps ножницы или /rps бумага")
        return
    player = context.args[0].lower()
    bot_choice = random.choice(list(choices.keys()))
    wins = {"камень": "ножницы", "ножницы": "бумага", "бумага": "камень"}
    if player == bot_choice:
        result = "🤝 Ничья!"
    elif wins[player] == bot_choice:
        result = "🎉 Ты победил!"
    else:
        result = "😈 Я победил!"
    await update.message.reply_text(
        f"Ты: {choices[player]} {player}\nЯ: {choices[bot_choice]} {bot_choice}\n{result}"
    )

app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
app.post_init = set_commands
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("clear", clear))
app.add_handler(CommandHandler("members", members))
app.add_handler(CommandHandler("kick", kick))
app.add_handler(CommandHandler("ban", ban))
app.add_handler(CommandHandler("unban", unban))
app.add_handler(CommandHandler("mute", mute))
app.add_handler(CommandHandler("unmute", unmute))
app.add_handler(CommandHandler("warn", warn))
app.add_handler(CommandHandler("warns", warns))
app.add_handler(CommandHandler("clearwarns", clearwarns))
app.add_handler(CommandHandler("pin", pin))
app.add_handler(CommandHandler("unpin", unpin))
app.add_handler(CommandHandler("promote", promote))
app.add_handler(CommandHandler("demote", demote))
app.add_handler(CommandHandler("choose", choose))
app.add_handler(CommandHandler("cube", cube))
app.add_handler(CommandHandler("weather", weather))
app.add_handler(CommandHandler("roll", roll))
app.add_handler(CommandHandler("flip", flip))
app.add_handler(CommandHandler("joke", joke))
app.add_handler(CommandHandler("poll", poll))
app.add_handler(CommandHandler("info", info))
app.add_handler(CommandHandler("gay", gay))
app.add_handler(CommandHandler("iq", iq))
app.add_handler(CommandHandler("rate", rate))
app.add_handler(CommandHandler("ship", ship))
app.add_handler(CommandHandler("slap", slap))
app.add_handler(CommandHandler("hug", hug))
app.add_handler(CommandHandler("rps", rps))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("Миханя запущен...")
app.run_polling()
