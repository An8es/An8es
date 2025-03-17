# bot.py

import requests
import logging
import json
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from config import TELEGRAM_BOT_TOKEN, AI_API_KEY

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,  # Уровень логирования (INFO, DEBUG, WARNING, ERROR, CRITICAL)
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # Формат логов
    handlers=[
        logging.FileHandler("bot.log"),  # Логи будут записываться в файл bot.log
        logging.StreamHandler()  # Логи также будут выводиться в консоль
    ]
)
logger = logging.getLogger(__name__)

# URL для API нейронки
AI_API_URL = "https://api.intelligence.io.solutions/api/v1/chat/completions"

# Функция для запроса к нейронке
async def ask_ai(question: str) -> str:
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {AI_API_KEY}",
    }

    data = {
        "model": "deepseek-ai/DeepSeek-R1",
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful assistant. Respond in Russian."
            },
            {
                "role": "user",
                "content": question
            }
        ],
    }

    try:
        logger.info(f"Отправка запроса к нейронке: {question}")
        response = requests.post(AI_API_URL, headers=headers, json=data)
        response.raise_for_status()
        data = response.json()
        logger.info(f"Ответ от нейронки: {data}")

        # Извлекаем финальный ответ
        ai_response = data['choices'][0]['message']['content']

        # Убираем <think> и внутренние размышления
        if "<think>" in ai_response:
            ai_response = ai_response.split("</think>")[-1].strip()

        # Убираем лишние элементы (### и **)
        ai_response = ai_response.replace("###", "").replace("**", "")

        return ai_response
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при запросе к нейронке: {e}")
        return f"Ошибка при выполнении запроса: {e}"

# Функция для поиска законов по ключевому слову
def search_laws(query: str) -> list:
    try:
        with open("laws.json", "r", encoding="utf-8") as f:
            laws = json.load(f)
    except FileNotFoundError:
        from parser import parse_laws
        laws = parse_laws()  # Если файл не найден, парсим законы заново

    results = []
    for law in laws:
        if query.lower() in law["title"].lower():
            results.append(law)
    return results

# Функция для получения краткого описания статьи
async def get_article_summary(link: str) -> str:
    # Запрашиваем у нейронки краткое описание статьи
    prompt = f"Кратко опиши, что содержится по этой ссылке: {link}"
    return await ask_ai(prompt)

# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Пользователь {update.message.from_user.username} запустил бота.")
    await update.message.reply_text("Привет! Я ваш помощник с ИИ. Задайте мне вопрос или используйте команду /laws для поиска законов.")

# Обработчик команды /laws
async def laws(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = " ".join(context.args)  # Получаем аргументы команды
    if not user_message:
        await update.message.reply_text("Пожалуйста, укажите ключевое слово для поиска. Например: /laws кража")
        return

    logger.info(f"Поиск законов по запросу: {user_message}")
    results = search_laws(user_message)

    if results:
        response = "Вот что я нашёл:\n\n"
        for law in results:
            summary = await get_article_summary(law["link"])  # Получаем краткое описание
            response += f"📖 {law['title']}\n🔗 {law['link']}\nℹ️ {summary}\n\n"
    else:
        response = "По вашему запросу ничего не найдено."

    await update.message.reply_text(response)

# Обработчик текстовых сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    logger.info(f"Получено сообщение от пользователя {update.message.from_user.username}: {user_message}")

    # Отправляем сообщение "Думаю..."
    thinking_message = await update.message.reply_text("Думаю...")

    # Запрашиваем ответ у нейронки
    ai_response = await ask_ai(user_message)

    # Редактируем сообщение "Думаю..." и добавляем финальный ответ
    await thinking_message.edit_text(ai_response)

# Основная функция для запуска бота
def main():
    logger.info("Запуск бота...")
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # Регистрация обработчиков
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("laws", laws))  # Добавляем обработчик команды /laws
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Запуск бота
    application.run_polling()

if __name__ == "__main__":
    main()