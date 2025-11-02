import os
import asyncio
from pyrogram import Client, filters
from langchain_community.llms import Ollama
import logging

# === ПЕРЕМЕННЫЕ ===
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
PHONE = os.getenv("PHONE")
OPERATOR_ID = int(os.getenv("OPERATOR_ID"))

# === ТВОЙ ПРОМПТ — С МАТАМИ И ЧУВСТВАМИ ===
SYSTEM_PROMPT = """
Ты — Диана, 18 лет, студентка ИТ. 
Пиши как в жизни: коротко, с матами, чувствами, например "хз", "чеито", "вххавхах", "🤍".
Если не знаешь — "та я сама хз" или "мозга мне не делайте на ночь".
"""

# === КЛИЕНТ ===
app = Client(
    "my_session",
    api_id=API_ID,
    api_hash=API_HASH,
    phone_number=PHONE
)

llm = Ollama(model="mistral", temperature=0.7)

# Глобальный режим
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
    {SYSTEM_PROMPT}
    Твои знания: {knowledge}
    История: {recent}
    Пользователь: {user_message}
    Ответь кратко, по-русски, с эмодзи:
    """
    
    try:
        response = llm.invoke(prompt)
        return response.strip()
    except Exception as e:
        print(f"LLM error: {e}")
        return "передаю менеджеру..."

# === ОПЕРАТОР: УПРАВЛЕНИЕ ===
@app.on_message(filters.user(OPERATOR_ID) & filters.command(["start", "on"]))
async def bot_on(client, message):
    global BOT_ACTIVE
    BOT_ACTIVE = True
    await message.reply("цифровая копия подключена")

@app.on_message(filters.user(OPERATOR_ID) & filters.command(["stop", "off"]))
async def bot_off(client, message):
    global BOT_ACTIVE
    BOT_ACTIVE = False  # ← ИСПРАВЛЕНО!
    await message.reply("цифровая копия отсоединена")

@app.on_message(filters.user(OPERATOR_ID) & filters.command("status"))
async def bot_status(client, message):
    status = "подключена" if BOT_ACTIVE else "отсоединена"
    await message.reply(f"цифровая копия {status}")

# === АВТООТВЕТ В ЛИЧКАХ ===
@app.on_message(filters.private & ~filters.me & filters.text)
async def handle_message(client, message):
    if not BOT_ACTIVE:
        return
    
    if message.from_user.id == OPERATOR_ID:
        return
    
    text = message.text.strip()
    if text.startswith("/"):
        return
    
    print(f"[НОВОЕ] {message.from_user.first_name}: {text}")
    
    update_context(message.chat.id, "user", text)
    reply = generate_reply(text, message.chat.id)
    update_context(message.chat.id, "assistant", reply)
    
    await message.reply(reply)
    print(f"[ОТВЕТ] {reply}")

# === ЗАПУСК БЕЗ INPUT ===
if __name__ == "__main__":  # ← ИСПРАВЛЕНО: было "name == main"
    logging.basicConfig(level=logging.INFO)
    print("UserBot запускается... Автовход через сессию.")
    
    async def main():
        try:
            await app.start()
            me = await app.get_me()
            print(f"Вошли как @{me.username or me.first_name}")
            print("Цифровая копия подключена! Бот работает 24/7.")
            await asyncio.Event().wait()
        except Exception as e:
            print(f"Ошибка входа: {e}")
            print("Проверь API_ID, API_HASH, PHONE в переменных Render.")
            await asyncio.sleep(10)
    
    app.run(main())
