from telegram import Update, BotCommand
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes
from openai import OpenAI

TELEGRAM_TOKEN = "8675206328:AAHfyiHA0Q1x-Z_scFhr5cwpHRUwWB5vTgk"
OPENROUTER_API_KEY = "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"

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

user_histories = {}

async def set_commands(app):
    await app.bot.set_my_commands([
        BotCommand("start", "Начать разговор"),
        BotCommand("clear", "Очистить историю чата"),
        BotCommand("members", "Количество участников группы"),
        BotCommand("kick", "Кикнуть участника (ответь на его сообщение)"),
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

    # В группе отвечаем только если упомянули бота
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
        model="nvidia/nemotron-3-super-120b-a12b:free",
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



app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
app.post_init = set_commands
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("clear", clear))
app.add_handler(CommandHandler("members", members))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.add_handler(CommandHandler("kick", kick))

print("Миханя запущен...")
app.run_polling()