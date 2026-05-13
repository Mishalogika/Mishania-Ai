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
user_checklists = {}
user_coins = {}
last_daily = {}

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
        BotCommand("slowmode", "Медленный режим /slowmode 10"),
        BotCommand("adminlist", "Список админов"),
        BotCommand("everyone", "Упомянуть всех админов"),
        BotCommand("choose", "Выбрать случайного участника"),
        BotCommand("cube", "Рандомное число /cube 1 100"),
        BotCommand("weather", "Погода /weather Одесса"),
        BotCommand("roll", "Бросить кубик /roll или /roll 20"),
        BotCommand("flip", "Орёл или решка"),
        BotCommand("joke", "Случайная шутка"),
        BotCommand("poll", "Опрос /poll Вопрос?Да|Нет"),
        BotCommand("info", "Инфо о пользователе"),
        BotCommand("iq", "Измерить IQ"),
        BotCommand("rate", "Оценить рандомно"),
        BotCommand("slap", "Дать пощёчину"),
        BotCommand("hug", "Обнять"),
        BotCommand("rps", "Камень ножницы бумага"),
        BotCommand("music", "Найти песню /music название"),
        BotCommand("checklist", "Чеклист"),
        BotCommand("8ball", "Магический шар /8ball вопрос"),
        BotCommand("compliment", "Комплимент"),
        BotCommand("roast", "Подколоть"),
        BotCommand("truth", "Правда"),
        BotCommand("dare", "Действие"),
        BotCommand("ascii", "Текст в ASCII /ascii привет"),
        BotCommand("news", "Последние новости"),
        BotCommand("currency", "Курс валют"),
        BotCommand("daily", "Получить монеты"),
        BotCommand("balance", "Мой баланс"),
        BotCommand("top", "Топ богачей"),
        BotCommand("transfer", "Перевести монеты"),
        BotCommand("casino", "Казино /casino 10"),
        BotCommand("shop", "Магазин команд"),
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
        await update.message.reply_text("Только для групп!")
        return
    count = await context.bot.get_chat_member_count(chat.id)
    await update.message.reply_text(f"👥 В этой группе {count} участников")

def is_admin(status):
    return status in ["administrator", "creator"]

async def kick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat, message = update.effective_chat, update.message
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
        await message.reply_text("❌ Бот должен быть админом!")

async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat, message = update.effective_chat, update.message
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
    chat, message = update.effective_chat, update.message
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
    chat, message = update.effective_chat, update.message
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
            await message.reply_text("❌ Неверный формат!")
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
        await message.reply_text("❌ Бот должен быть админом!")

async def unmute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat, message = update.effective_chat, update.message
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
    chat, message = update.effective_chat, update.message
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
            await message.reply_text(f"⚠️ {target.first_name} получил 3 варна и был кикнут!")
        except Exception:
            await message.reply_text(f"⚠️ {target.first_name} имеет {count}/3 предупреждений!")
    else:
        await message.reply_text(f"⚠️ {target.first_name} получил предупреждение {count}/3!")

async def warns(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message.reply_to_message:
        await message.reply_text("Ответь на сообщение пользователя!")
        return
    target = message.reply_to_message.from_user
    key = f"{update.effective_chat.id}:{target.id}"
    count = warned_users.get(key, 0)
    await message.reply_text(f"⚠️ У {target.first_name} {count}/3 предупреждений")

async def clearwarns(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat, message = update.effective_chat, update.message
    if not message.reply_to_message:
        await message.reply_text("Ответь на сообщение пользователя!")
        return
    caller = await context.bot.get_chat_member(chat.id, message.from_user.id)
    if not is_admin(caller.status):
        await message.reply_text("❌ Только администраторы!")
        return
    target = message.reply_to_message.from_user
    warned_users[f"{chat.id}:{target.id}"] = 0
    await message.reply_text(f"✅ Варны {target.first_name} сброшены!")

async def pin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat, message = update.effective_chat, update.message
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
    chat, message = update.effective_chat, update.message
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
    chat, message = update.effective_chat, update.message
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
            can_delete_messages=True,
            can_restrict_members=True,
            can_pin_messages=True,
            can_invite_users=True
        )
        await message.reply_text(f"⭐ {target.first_name} теперь администратор!")
    except Exception:
        await message.reply_text("❌ Не могу назначить!")

async def demote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat, message = update.effective_chat, update.message
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
        await message.reply_text("❌ Не могу снять!")

async def slowmode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat, message = update.effective_chat, update.message
    caller = await context.bot.get_chat_member(chat.id, message.from_user.id)
    if not is_admin(caller.status):
        await message.reply_text("❌ Только администраторы!")
        return
    try:
        seconds = int(context.args[0]) if context.args else 0
        await context.bot.set_chat_slow_mode_delay(chat.id, seconds)
        if seconds == 0:
            await message.reply_text("✅ Медленный режим отключён!")
        else:
            await message.reply_text(f"🐌 Медленный режим: {seconds} секунд!")
    except Exception:
        await message.reply_text("❌ Использование: /slowmode 10")

async def adminlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type not in ["group", "supergroup"]:
        await update.message.reply_text("Только для групп!")
        return
    admins = await context.bot.get_chat_administrators(chat.id)
    text = "👑 *Администраторы группы:*\n"
    for a in admins:
        role = "Создатель 👑" if a.status == "creator" else "Админ ⭐"
        text += f"• {a.user.first_name} — {role}\n"
    await update.message.reply_text(text, parse_mode="Markdown")

async def everyone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type not in ["group", "supergroup"]:
        await update.message.reply_text("Только для групп!")
        return
    admins = await context.bot.get_chat_administrators(chat.id)
    mentions = " ".join([f"[{a.user.first_name}](tg://user?id={a.user.id})" for a in admins if not a.user.is_bot])
    await update.message.reply_text(f"📢 {mentions}", parse_mode="Markdown")

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
        if len(context.args) != 2:
            await update.message.reply_text("Использование: /cube 1 100")
            return
        num1, num2 = int(context.args[0]), int(context.args[1])
        if num1 > num2:
            num1, num2 = num2, num1
        result = random.randint(num1, num2)
        await update.message.reply_text(f"🎲 Случайное число от {num1} до {num2}: *{result}*", parse_mode="Markdown")
    except ValueError:
        await update.message.reply_text("❌ Введи два числа!")

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
    await update.message.reply_text(random.choice(["🦅 Орёл!", "🪙 Решка!"]))

async def joke(update: Update, context: ContextTypes.DEFAULT_TYPE):
    jokes = [
        "Почему программисты путают Хэллоуин и Рождество? Oct 31 == Dec 25! 😄",
        "— Официант, у меня в супе муха! — Тише, а то все захотят! 😂",
        "Программист пошёл в магазин. Жена: купи хлеб, если будут яйца — возьми десяток. Вернулся с 10 хлебами. 🍞",
        "— Как называется медведь без ушей? — Медвь! 🐻",
        "Оптимист: стакан наполовину полон. Пессимист: наполовину пуст. Программист: стакан в два раза больше чем нужно! 🥛",
        "— Почему Wi-Fi такой медленный? — Потому что провайдер тоже работает на удалёнке! 📡",
        "Купил книгу 'Как не быть бедным'. Внутри: 'Будь богатым!' 📚",
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

async def iq(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.reply_to_message.from_user if update.message.reply_to_message else update.effective_user
    score = random.randint(0, 200)
    comment = "🥴 Ну... старайся!" if score < 70 else "😐 Средненько" if score < 100 else "🧠 Неплохо!" if score < 130 else "🎓 Умник!" if score < 160 else "🚀 Гений!"
    await update.message.reply_text(f"🧠 IQ {user.first_name}: {score}\n{comment}")

async def rate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.reply_to_message.from_user if update.message.reply_to_message else update.effective_user
    score = random.randint(0, 10)
    stars = "⭐" * score + "☆" * (10 - score)
    await update.message.reply_text(f"📊 {user.first_name} оценён на {score}/10\n{stars}")

async def slap(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        await update.message.reply_text("Ответь на сообщение!")
        return
    user1 = update.effective_user.first_name
    user2 = update.message.reply_to_message.from_user.first_name
    actions = [
        f"👋 {user1} дал пощёчину {user2}! ШЛЁП!",
        f"🐟 {user1} ударил {user2} рыбой!",
        f"👠 {user1} треснул {user2} тапком!",
        f"🍳 {user1} огрел {user2} сковородкой!",
    ]
    await update.message.reply_text(random.choice(actions))

async def hug(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        await update.message.reply_text("Ответь на сообщение!")
        return
    user1 = update.effective_user.first_name
    user2 = update.message.reply_to_message.from_user.first_name
    await update.message.reply_text(f"🤗 {user1} крепко обнял {user2}!")

async def rps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choices = {"камень": "🪨", "ножницы": "✂️", "бумага": "📄"}
    if not context.args or context.args[0].lower() not in choices:
        await update.message.reply_text("Использование: /rps камень или /rps ножницы или /rps бумага")
        return
    player = context.args[0].lower()
    bot_choice = random.choice(list(choices.keys()))
    wins = {"камень": "ножницы", "ножницы": "бумага", "бумага": "камень"}
    result = "🤝 Ничья!" if player == bot_choice else "🎉 Ты победил!" if wins[player] == bot_choice else "😈 Я победил!"
    await update.message.reply_text(f"Ты: {choices[player]} {player}\nЯ: {choices[bot_choice]} {bot_choice}\n{result}")

async def music(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Использование: /music название песни")
        return
    query = " ".join(context.args)
    search_url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
    await update.message.reply_text(
        f"🎵 Ищу: *{query}*\n\n🔗 [Слушать на YouTube]({search_url})",
        parse_mode="Markdown"
    )

async def checklist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not context.args:
        await update.message.reply_text(
            "📋 Использование:\n"
            "/checklist создать\n"
            "/checklist добавить Задача\n"
            "/checklist список\n"
            "/checklist готово 1\n"
            "/checklist удалить 1"
        )
        return
    cmd = context.args[0].lower()
    if cmd == "создать":
        user_checklists[user_id] = []
        await update.message.reply_text("✅ Новый чеклист создан!")
    elif cmd == "добавить":
        if len(context.args) < 2:
            await update.message.reply_text("Укажи задачу!")
            return
        task = " ".join(context.args[1:])
        if user_id not in user_checklists:
            user_checklists[user_id] = []
        user_checklists[user_id].append({"task": task, "done": False})
        await update.message.reply_text(f"➕ Добавлено: {task}")
    elif cmd == "список":
        if user_id not in user_checklists or not user_checklists[user_id]:
            await update.message.reply_text("Список пустой!")
            return
        text = "📋 *Твой чеклист:*\n"
        for i, item in enumerate(user_checklists[user_id], 1):
            mark = "✅" if item["done"] else "⬜"
            text += f"{mark} {i}. {item['task']}\n"
        await update.message.reply_text(text, parse_mode="Markdown")
    elif cmd == "готово":
        try:
            idx = int(context.args[1]) - 1
            user_checklists[user_id][idx]["done"] = True
            await update.message.reply_text(f"✅ Пункт {idx+1} выполнен!")
        except (IndexError, ValueError):
            await update.message.reply_text("❌ Неверный номер!")
    elif cmd == "удалить":
        try:
            idx = int(context.args[1]) - 1
            removed = user_checklists[user_id].pop(idx)
            await update.message.reply_text(f"🗑 Удалено: {removed['task']}")
        except (IndexError, ValueError):
            await update.message.reply_text("❌ Неверный номер!")

async def eightball(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Использование: /8ball твой вопрос")
        return
    answers = [
        "🎱 Бесспорно!", "🎱 Предрешено!", "🎱 Определённо да!",
        "🎱 Можешь быть уверен!", "🎱 Мне кажется да", "🎱 Вероятнее всего",
        "🎱 Хороший знак", "🎱 Да", "🎱 Пока неясно",
        "🎱 Спроси позже", "🎱 Лучше не рассказывать",
        "🎱 Не рассчитывай на это", "🎱 Мой ответ — нет",
        "🎱 По моим данным нет", "🎱 Весьма сомнительно",
    ]
    question = " ".join(context.args)
    await update.message.reply_text(f"❓ {question}\n\n{random.choice(answers)}")

async def compliment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.reply_to_message.from_user if update.message.reply_to_message else update.effective_user
    compliments = [
        f"✨ {user.first_name} — ты просто огонь! 🔥",
        f"💫 {user.first_name} самый умный в этом чате!",
        f"🌟 {user.first_name} делает мир лучше!",
        f"💪 {user.first_name} — настоящая легенда!",
        f"🎯 {user.first_name} всегда попадает в точку!",
    ]
    await update.message.reply_text(random.choice(compliments))

async def roast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.reply_to_message.from_user if update.message.reply_to_message else update.effective_user
    roasts = [
        f"🔥 {user.first_name}, ты такой особенный... в плохом смысле!",
        f"😂 {user.first_name} — живое доказательство что эволюция иногда идёт назад!",
        f"💀 {user.first_name}, даже Google не знает зачем ты здесь!",
        f"🤣 {user.first_name} такой скучный, что даже его тень уходит!",
    ]
    await update.message.reply_text(random.choice(roasts))

async def truth(update: Update, context: ContextTypes.DEFAULT_TYPE):
    truths = [
        "Какой твой самый большой страх?",
        "Что ты никогда не расскажешь родителям?",
        "Кого в этом чате ты считаешь самым странным?",
        "Какая твоя самая неловкая история?",
        "Ты когда-нибудь врал лучшему другу?",
        "Кого в этом чате ты бы позвал на свидание?",
    ]
    await update.message.reply_text(f"🤔 Правда: {random.choice(truths)}")

async def dare(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dares = [
        "Напиши комплимент следующему кто напишет в чат!",
        "Отправь голосовое и спой 10 секунд любой песни!",
        "Напиши что-нибудь смешное капслоком!",
        "Напиши признание в любви чату!",
        "Напиши стих про кого-нибудь из чата!",
    ]
    await update.message.reply_text(f"😈 Действие: {random.choice(dares)}")

async def ascii_art(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Использование: /ascii привет")
        return
    text = " ".join(context.args).upper()[:8]
    result = ""
    for char in text:
        result += char + " "
    big = ""
    for char in text:
        big += f"[{char}]"
    await update.message.reply_text(f"🔤 *{big}*", parse_mode="Markdown")

async def news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        response = requests.get(
            "https://news.google.com/rss?hl=ru&gl=RU&ceid=RU:ru",
            timeout=10,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        import xml.etree.ElementTree as ET
        root = ET.fromstring(response.content)
        items = root.findall(".//item")[:5]
        text = "📰 *Последние новости:*\n\n"
        for item in items:
            title = item.find("title").text
            link = item.find("link").text
            text += f"• [{title}]({link})\n\n"
        await update.message.reply_text(text, parse_mode="Markdown", disable_web_page_preview=True)
    except Exception:
        await update.message.reply_text("❌ Не могу получить новости!")

async def currency(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        response = requests.get("https://api.exchangerate-api.com/v4/latest/USD", timeout=5)
        data = response.json()
        rates = data["rates"]
        uah = rates.get("UAH", "?")
        eur = rates.get("EUR", "?")
        rub = rates.get("RUB", "?")
        gbp = rates.get("GBP", "?")
        text = (
            f"💱 *Курс валют (к USD):*\n\n"
            f"🇺🇦 UAH: {uah:.2f} грн\n"
            f"🇪🇺 EUR: {eur:.4f}\n"
            f"🇷🇺 RUB: {rub:.2f}\n"
            f"🇬🇧 GBP: {gbp:.4f}\n"
        )
        await update.message.reply_text(text, parse_mode="Markdown")
    except Exception:
        await update.message.reply_text("❌ Не могу получить курс валют!")

async def daily(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    now = datetime.now(timezone.utc)
    last = last_daily.get(user_id)
    if last and (now - last).total_seconds() < 86400:
        remaining = 86400 - (now - last).total_seconds()
        hours = int(remaining // 3600)
        minutes = int((remaining % 3600) // 60)
        await update.message.reply_text(f"⏰ Следующая награда через {hours}ч {minutes}м!")
        return
    coins = random.randint(5, 20)
    user_coins[user_id] = user_coins.get(user_id, 0) + coins
    last_daily[user_id] = now
    await update.message.reply_text(
        f"🎁 Ты получил *{coins}* монет!\n"
        f"💰 Баланс: *{user_coins[user_id]}* монет",
        parse_mode="Markdown"
    )

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.reply_to_message.from_user if update.message.reply_to_message else update.effective_user
    coins = user_coins.get(user.id, 0)
    await update.message.reply_text(f"💰 Баланс {user.first_name}: *{coins}* монет", parse_mode="Markdown")

async def top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not user_coins:
        await update.message.reply_text("Никто ещё не получал монеты!")
        return
    sorted_users = sorted(user_coins.items(), key=lambda x: x[1], reverse=True)[:10]
    text = "🏆 *Топ богачей:*\n\n"
    medals = ["🥇", "🥈", "🥉"] + ["4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    for i, (uid, coins) in enumerate(sorted_users):
        text += f"{medals[i]} ID{uid}: *{coins}* монет\n"
    await update.message.reply_text(text, parse_mode="Markdown")

async def transfer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message.reply_to_message:
        await message.reply_text("Ответь на сообщение получателя! Пример: /transfer 50")
        return
    if not context.args:
        await message.reply_text("Укажи сумму! Пример: /transfer 50")
        return
    try:
        amount = int(context.args[0])
        if amount <= 0:
            await message.reply_text("❌ Сумма должна быть больше 0!")
            return
        sender_id = update.effective_user.id
        receiver = message.reply_to_message.from_user
        if user_coins.get(sender_id, 0) < amount:
            await message.reply_text("❌ Недостаточно монет!")
            return
        user_coins[sender_id] = user_coins.get(sender_id, 0) - amount
        user_coins[receiver.id] = user_coins.get(receiver.id, 0) + amount
        await message.reply_text(
            f"✅ Переведено *{amount}* монет для {receiver.first_name}!\n"
            f"💰 Твой баланс: *{user_coins[sender_id]}* монет",
            parse_mode="Markdown"
        )
    except ValueError:
        await message.reply_text("❌ Укажи число!")

async def casino(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not context.args:
        await update.message.reply_text("Использование: /casino 10")
        return
    try:
        bet = int(context.args[0])
        if bet <= 0:
            await update.message.reply_text("❌ Ставка должна быть больше 0!")
            return
        if user_coins.get(user_id, 0) < bet:
            await update.message.reply_text(f"❌ Недостаточно монет! У тебя {user_coins.get(user_id, 0)} монет")
            return
        result = random.random()
        if result < 0.45:
            user_coins[user_id] = user_coins.get(user_id, 0) + bet
            await update.message.reply_text(
                f"🎰 Ты выиграл *{bet}* монет! 🎉\n💰 Баланс: *{user_coins[user_id]}* монет",
                parse_mode="Markdown"
            )
        elif result < 0.9:
            user_coins[user_id] = user_coins.get(user_id, 0) - bet
            await update.message.reply_text(
                f"🎰 Ты проиграл *{bet}* монет 😢\n💰 Баланс: *{user_coins[user_id]}* монет",
                parse_mode="Markdown"
            )
        else:
            jackpot = bet * 3
            user_coins[user_id] = user_coins.get(user_id, 0) + jackpot
            await update.message.reply_text(
                f"🎰 ДЖЕКПОТ! Ты выиграл *{jackpot}* монет! 🤑\n💰 Баланс: *{user_coins[user_id]}* монет",
                parse_mode="Markdown"
            )
    except ValueError:
        await update.message.reply_text("❌ Укажи число!")

async def shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🛒 *Магазин команд:*\n\n"
        "За 100 монет можешь заказать кастомную команду у автора бота!\n\n"
        "📝 Что можно заказать:\n"
        "• Кастомное приветствие для группы\n"
        "• Персональная команда с твоим именем\n"
        "• Любая другая идея!\n\n"
        "💬 Напиши автору бота и покажи свой баланс (/balance)",
        parse_mode="Markdown"
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
app.add_handler(CommandHandler("slowmode", slowmode))
app.add_handler(CommandHandler("adminlist", adminlist))
app.add_handler(CommandHandler("everyone", everyone))
app.add_handler(CommandHandler("choose", choose))
app.add_handler(CommandHandler("cube", cube))
app.add_handler(CommandHandler("weather", weather))
app.add_handler(CommandHandler("roll", roll))
app.add_handler(CommandHandler("flip", flip))
app.add_handler(CommandHandler("joke", joke))
app.add_handler(CommandHandler("poll", poll))
app.add_handler(CommandHandler("info", info))
app.add_handler(CommandHandler("iq", iq))
app.add_handler(CommandHandler("rate", rate))
app.add_handler(CommandHandler("slap", slap))
app.add_handler(CommandHandler("hug", hug))
app.add_handler(CommandHandler("rps", rps))
app.add_handler(CommandHandler("music", music))
app.add_handler(CommandHandler("checklist", checklist))
app.add_handler(CommandHandler("8ball", eightball))
app.add_handler(CommandHandler("compliment", compliment))
app.add_handler(CommandHandler("roast", roast))
app.add_handler(CommandHandler("truth", truth))
app.add_handler(CommandHandler("dare", dare))
app.add_handler(CommandHandler("ascii", ascii_art))
app.add_handler(CommandHandler("news", news))
app.add_handler(CommandHandler("currency", currency))
app.add_handler(CommandHandler("daily", daily))
app.add_handler(CommandHandler("balance", balance))
app.add_handler(CommandHandler("top", top))
app.add_handler(CommandHandler("transfer", transfer))
app.add_handler(CommandHandler("casino", casino))
app.add_handler(CommandHandler("shop", shop))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("Миханя запущен...")
app.run_polling()
