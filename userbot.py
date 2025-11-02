import os
import asyncio
from pyrogram import Client, filters
from langchain_ollama import OllamaLLM  # ← НОВЫЙ ИМПОРТ
import logging

# === ПЕРЕМЕННЫЕ ===
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
PHONE = os.getenv("PHONE")
OPERATOR_ID = int(os.getenv("OPERATOR_ID"))
PASSWORD = os.getenv("PASSWORD")  # ← ПАРОЛЬ

# === КЛИЕНТ ===
app = Client(
    "my_session",
    api_id=API_ID,
    api_hash=API_HASH,
    phone_number=PHONE,
    password=PASSWORD  # ← АВТОВХОД С ПАРОЛЕМ
)

llm = OllamaLLM(model="mistral", temperature=0.7)  # ← НОВЫЙ КЛАСС

BOT_ACTIVE = True
context_cache = {}

def get_context(chat_id):
    if chat_id not in context_cache:
        context_cache[chat_id] = []
    return context_cache[chat_id]

def update_context(chat_id, role, content):
    ctx = get_context(chat_id)
    ctx.append({"role": role, "content": content})
    if len(ctx) > 10:
        ctx = ctx[-10:]
    context_cache[chat_id] = ctx

def generate_reply(user_message, chat_id):
    ctx = get_context(chat_id)
    recent = " | ".join([m['content'] for m in ctx[-3:]])
    
    knowledge = ""
    try:
        with open("knowledge.txt", "r", encoding="utf-8") as f:
            knowledge = f.read()[:1000]
    except:
        pass

    prompt = f"""
    Ты — Диана, 18 лет, студентка ИТ. 
    Пиши как в жизни: коротко, с матами, чувствами, например "хз", "чеито", "вххавхах", "🤍".
    Если не знаешь — "та я сама хз" или "мозга мне не делайте на ночь".
    Твои знания: {knowledge}
    История: {recent}
    Пользователь: {user_message}
    Ответь кратко, по-русски, с эмодзи:
    """
    
    try:
        return llm.invoke(prompt).strip()
    except Exception as e:
        print(f"LLM error: {e}")
        return "передаю менеджеру..."

# === ОПЕРАТОР ===
@app.on_message(filters.user(OPERATOR_ID) & filters.command(["start", "on"]))
async def bot_on(client, message):
    global BOT_ACTIVE
    BOT_ACTIVE = True
    await message.reply("цифровая копия подключена")

@app.on_message(filters.user(OPERATOR_ID) & filters.command(["stop", "off"]))
async def bot_off(client, message):
    global BOT_ACTIVE
    BOT_ACTIVE = False
    await message.reply("цифровая копия отсоединена")

@app.on_message(filters.user(OPERATOR_ID) & filters.command("status"))
async def bot_status(client, message):
    status = "подключена" if BOT_ACTIVE else "отсоединена"
    await message.reply(f"цифровая копия {status}")

# === АВТООТВЕТ ===
@app.on_message(filters.private & ~filters.me & filters.text)
async def handle_message(client, message):
    if not BOT_ACTIVE or message.from_user.id == OPERATOR_ID:
        return
    if message.text.startswith("/"):
        return
    
    print(f"[НОВОЕ] {message.from_user.first_name}: {message.text}")
    update_context(message.chat.id, "user", message.text)
    reply = generate_reply(message.text, message.chat.id)
    update_context(message.chat.id, "assistant", reply)
    await message.reply(reply)

# === ЗАПУСК ===
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("UserBot запускается... Автовход с паролем.")
    
    async def main():
        try:
            await app.start()
            me = await app.get_me()
            print(f"Успешно вошли как @{me.username or me.first_name}")
            print("Цифровая копия подключена! Бот работает 24/7.")
            await asyncio.Event().wait()
        except Exception as e:
            print(f"Ошибка: {e}")
            await asyncio.sleep(10)
    
    app.run(main())
