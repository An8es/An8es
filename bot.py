import requests
import logging
import json
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from config import TELEGRAM_BOT_TOKEN, AI_API_KEY

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# URL для API нейронки
AI_API_URL = "https://api.intelligence.io.solutions/api/v1/chat/completions"

# Предзагруженные статьи
LAWS_DATA = {
    "Трудовой кодекс": [
        {"title": "Статья 21. Основные права и обязанности работника", "link": "http://tk-rf.ru/21"},
        {"title": "Статья 22. Основные права и обязанности работодателя", "link": "http://tk-rf.ru/22"},
        {"title": "Статья 56. Понятие трудового договора", "link": "http://tk-rf.ru/56"},
        {"title": "Статья 57. Содержание трудового договора", "link": "http://tk-rf.ru/57"},
        {"title": "Статья 91. Понятие рабочего времени", "link": "http://tk-rf.ru/91"},
        {"title": "Статья 92. Нормальная продолжительность рабочего времени", "link": "http://tk-rf.ru/92"},
        {"title": "Статья 106. Понятие времени отдыха", "link": "http://tk-rf.ru/106"},
        {"title": "Статья 107. Виды времени отдыха", "link": "http://tk-rf.ru/107"},
        {"title": "Статья 129. Основные понятия и определения", "link": "http://tk-rf.ru/129"},
        {"title": "Статья 136. Порядок, место и сроки выплаты заработной платы", "link": "http://tk-rf.ru/136"}
    ],
    "Административные правонарушения": [
        {"title": "Статья 12.8. Управление транспортным средством в состоянии опьянения", "link": "http://koap-rf.ru/12.8"},
        {"title": "Статья 12.9. Превышение установленной скорости движения", "link": "http://koap-rf.ru/12.9"},
        {"title": "Статья 12.26. Невыполнение требования о прохождении медицинского освидетельствования", "link": "http://koap-rf.ru/12.26"},
        {"title": "Статья 20.1. Мелкое хулиганство", "link": "http://koap-rf.ru/20.1"},
        {"title": "Статья 20.20. Распитие алкогольной продукции в запрещенных местах", "link": "http://koap-rf.ru/20.20"},
        {"title": "Статья 20.25. Уклонение от исполнения административного наказания", "link": "http://koap-rf.ru/20.25"},
        {"title": "Статья 6.24. Нарушение запрета курения табака", "link": "http://koap-rf.ru/6.24"},
        {"title": "Статья 7.27. Мелкое хищение", "link": "http://koap-rf.ru/7.27"},
        {"title": "Статья 19.3. Неповиновение законному распоряжению сотрудника полиции", "link": "http://koap-rf.ru/19.3"},
        {"title": "Статья 19.5. Невыполнение в срок законного предписания", "link": "http://koap-rf.ru/19.5"}
    ],
    "Федеральные законы": [
        {"title": "ФЗ-59. О порядке рассмотрения обращений граждан", "link": "http://fz-rf.ru/59"},
        {"title": "ФЗ-152. О персональных данных", "link": "http://fz-rf.ru/152"},
        {"title": "ФЗ-44. О контрактной системе в сфере закупок", "link": "http://fz-rf.ru/44"},
        {"title": "ФЗ-223. О закупках товаров, работ, услуг отдельными видами юридических лиц", "link": "http://fz-rf.ru/223"},
        {"title": "ФЗ-135. О защите конкуренции", "link": "http://fz-rf.ru/135"},
        {"title": "ФЗ-38. О рекламе", "link": "http://fz-rf.ru/38"},
        {"title": "ФЗ-2300-1. О защите прав потребителей", "link": "http://fz-rf.ru/2300-1"},
        {"title": "ФЗ-400. О страховых пенсиях", "link": "http://fz-rf.ru/400"},
        {"title": "ФЗ-326. Об обязательном медицинском страховании", "link": "http://fz-rf.ru/326"},
        {"title": "ФЗ-127. О несостоятельности (банкротстве)", "link": "http://fz-rf.ru/127"}
    ],
    "Уголовный кодекс": [
        {"title": "Статья 105. Убийство", "link": "http://uk-rf.ru/105"},
        {"title": "Статья 111. Умышленное причинение тяжкого вреда здоровью", "link": "http://uk-rf.ru/111"},
        {"title": "Статья 158. Кража", "link": "http://uk-rf.ru/158"},
        {"title": "Статья 159. Мошенничество", "link": "http://uk-rf.ru/159"},
        {"title": "Статья 161. Грабеж", "link": "http://uk-rf.ru/161"},
        {"title": "Статья 162. Разбой", "link": "http://uk-rf.ru/162"},
        {"title": "Статья 163. Вымогательство", "link": "http://uk-rf.ru/163"},
        {"title": "Статья 228. Незаконные приобретение, хранение, перевозка наркотических средств", "link": "http://uk-rf.ru/228"},
        {"title": "Статья 264. Нарушение правил дорожного движения", "link": "http://uk-rf.ru/264"},
        {"title": "Статья 291. Дача взятки", "link": "http://uk-rf.ru/291"}
    ]
}

# Примеры запросов для каждой категории
CATEGORY_EXAMPLES = {
    "Трудовой кодекс": "Например: 'Какая статья регулирует продолжительность рабочего дня?'",
    "Административные правонарушения": "Например: 'Какая статья предусматривает наказание за управление автомобилем в состоянии опьянения?'",
    "Федеральные законы": "Например: 'Какая статья регулирует защиту персональных данных?'",
    "Уголовный кодекс": "Например: 'Какая статья предусматривает наказание за кражу?'"
}

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
                "content": "You are a helpful assistant. Respond in Russian and provide information only related to Russian laws. Always include links to relevant articles if applicable."
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

        ai_response = data['choices'][0]['message']['content']
        if "<think>" in ai_response:
            ai_response = ai_response.split("</think>")[-1].strip()
        ai_response = ai_response.replace("###", "").replace("**", "")
        return ai_response
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при запросе к нейронке: {e}")
        return f"Ошибка при выполнении запроса: {e}"

# Функция для поиска законов по ключевому слову
def search_laws(query: str, category: str) -> list:
    results = []
    if category in LAWS_DATA:
        for law in LAWS_DATA[category]:
            if query.lower() in law["title"].lower():
                results.append(law)
    return results

# Функция для получения краткого описания статьи
async def get_article_summary(link: str) -> str:
    prompt = f"Кратко опиши, что содержится по этой ссылке: {link}"
    return await ask_ai(prompt)

# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Пользователь {update.message.from_user.username} запустил бота.")
    keyboard = [["Трудовой кодекс", "Административные правонарушения"], ["Федеральные законы", "Уголовный кодекс"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text(
        "Привет! Я ваш помощник с ИИ. Выберите категорию законов:",
        reply_markup=reply_markup
    )

# Обработчик команды /restart
async def restart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Пользователь {update.message.from_user.username} перезапустил бота.")
    
    # Сбрасываем состояние пользователя
    if "category" in context.user_data:
        del context.user_data["category"]
    
    # Показываем кнопки с категориями
    keyboard = [["Трудовой кодекс", "Административные правонарушения"], ["Федеральные законы", "Уголовный кодекс"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    
    await update.message.reply_text(
        "Бот перезапущен. Выберите категорию законов:",
        reply_markup=reply_markup
    )

# Обработчик выбора категории
async def handle_category_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    logger.info(f"Пользователь {update.message.from_user.username} выбрал категорию: {user_message}")

    if user_message in LAWS_DATA:
        context.user_data["category"] = user_message
        
        # Создаем кнопки для статей
        articles = [law["title"] for law in LAWS_DATA[user_message]]
        articles.append("Другое")
        keyboard = [articles[i:i + 2] for i in range(0, len(articles), 2)]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        
        await update.message.reply_text(
            f"Вы выбрали категорию: {user_message}. Выберите статью или нажмите 'Другое' для поиска:",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text("Пожалуйста, выберите категорию из списка.")

# Обработчик выбора статьи
async def handle_article_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    logger.info(f"Пользователь {update.message.from_user.username} выбрал статью: {user_message}")

    if "category" in context.user_data:
        category = context.user_data["category"]
        
        if user_message == "Другое":
            example = CATEGORY_EXAMPLES.get(category, "Введите ваш запрос.")
            await update.message.reply_text(
                f"Введите ваш запрос. {example}",
                reply_markup=ReplyKeyboardRemove()
            )
        else:
            # Ищем выбранную статью
            results = search_laws(user_message, category)
            
            if results:
                law = results[0]  # Берем первую найденную статью
                summary = await get_article_summary(law["link"])
                response = f"📖 {law['title']}\n🔗 {law['link']}\nℹ️ {summary}"
            else:
                response = f"Статья '{user_message}' не найдена в категории '{category}'."
            
            await update.message.reply_text(response)
    else:
        await update.message.reply_text("Пожалуйста, сначала выберите категорию законов.")

# Обработчик текстовых сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    logger.info(f"Получено сообщение от пользователя {update.message.from_user.username}: {user_message}")

    if user_message in LAWS_DATA:
        await handle_category_selection(update, context)
    elif "category" in context.user_data:
        await handle_article_selection(update, context)
    else:
        await update.message.reply_text("Пожалуйста, сначала выберите категорию законов.")

# Основная функция для запуска бота
def main():
    logger.info("Запуск бота...")
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("restart", restart))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    application.run_polling()

if __name__ == "__main__":
    main()