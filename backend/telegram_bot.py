import os
import logging
import asyncio
from typing import Dict, Any
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, PhotoSize
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, 
    MessageHandler, filters, ContextTypes
)
from pymongo import MongoClient
from datetime import datetime
import uuid
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "test_database")

# Подключение к MongoDB
mongo_client = MongoClient(MONGO_URL)
db = mongo_client[DB_NAME]
users_collection = db.users
test_results_collection = db.test_results

# Канал для проверки подписки
CHANNEL_USERNAME = "@anna_gertssss"
CHANNEL_URL = "https://t.me/anna_gertssss"

# ID админа
ADMIN_ID = 7470811680

# Вопросы теста с баллами
TEST_QUESTIONS = [
    {
        "question": "Твой возраст",
        "options": [
            ("до 30", 20),
            ("30–35", 30),
            ("36–40", 40),
            ("41–45", 50),
            ("46+", 60)
        ]
    },
    {
        "question": "Как у тебя с гормонами?",
        "options": [
            ("Всё стабильно", 20),
            ("ПМС усилился, отёки, раздражение", 40),
            ("Начались сбои, прыгает цикл", 50),
            ("Уже менопауза / близко", 60)
        ]
    },
    {
        "question": "Как ты сейчас питаешься?",
        "options": [
            ("ЗОЖ, но вес не уходит", 40),
            ("Часто срывы", 30),
            ("Постоянно голодная", 50),
            ("Ем нормально, но тяжесть", 50)
        ]
    },
    {
        "question": "Что больше всего бесит?",
        "options": [
            ("Лицо стало \"пухлым\"", 40),
            ("Вес держится на животе", 50),
            ("Сил нет", 50),
            ("Постоянные перепады в настроении", 50),
            ("Падает либидо", 40),
            ("Всё вместе 😩", 60)
        ]
    },
    {
        "question": "Пробовала ли ты кето раньше?",
        "options": [
            ("Да, но не зашло", 20),
            ("Никогда", 30),
            ("Хочу, но боюсь", 40),
            ("Пробовала — понравилось", 60)
        ]
    }
]

# Результаты теста
TEST_RESULTS = {
    (100, 130): {
        "percentage": 60,
        "title": "Кето может стать отличным способом сохранить баланс",
        "description": """Ты на том этапе, когда тело работает стабильно, и это прекрасно.
Но если ты хочешь:
— дольше сохранить гормональный ресурс
— предотвратить "качели" с весом и энергией
— помочь организму пережить гормональные изменения без стресса

Кето в мягкой форме может быть профилактикой и способом заботы о себе на глубоком уровне.

📩 Забери рацион на 3 дня — начни с легкого входа и посмотри, как тебе."""
    },
    (131, 170): {
        "percentage": 70,
        "title": "Твоё тело может реагировать на кето очень хорошо",
        "description": """По твоим ответам видно: ты внимательно следишь за собой и уже знаешь, что работает, а что нет.

Но, возможно, ты чувствуешь, что:
— привычные схемы больше не дают результата
— тело "тормозит"
— хочется больше лёгкости и энергии

Кето — это не просто "есть жир". Это система, которая:
✅ учит тело не зависеть от сахара
✅ даёт питание гормонам
✅ помогает стабилизировать метаболизм

📩 Забери адаптированный рацион на 3 дня и попробуй без стресса и экспериментов над собой."""
    },
    (171, 200): {
        "percentage": 80,
        "title": "У тебя может быть высокая чувствительность к углеводам",
        "description": """Ты уже многое знаешь о себе — и, похоже, пришла к моменту, когда хочется изменений, но не через "жесткач".

Кето может тебе подойти, потому что:
✅ оно помогает сохранять мышечную массу
✅ регулирует тягу к сладкому
✅ даёт ощущение насыщения и ясности

Главное — начать грамотно: не с бекона и масла, а с продуманного женского подхода.

📩 Получи рацион на 3 дня — ты почувствуешь первые перемены уже после завтрака."""
    },
    (201, 230): {
        "percentage": 90,
        "title": "Кето может стать для тебя новым уровнем энергии и комфорта",
        "description": """Ты точно готова к более глубокому уровню заботы о себе.

Кето помогает женщинам:
✅ улучшать питание кожи и волос
✅ мягко убирать "застои" в теле
✅ питать гормональную систему жирами, а не углеводами

Возможно, ты уже пробовала "есть правильно", считать калории, убирать сладкое.
Но кето работает не за счёт ограничений, а за счёт грамотной перестройки топлива.

📩 Получи кеторацион на 3 дня — это вкусно, легко и даст тебе сразу ощущение "я снова в ресурсе"."""
    },
    (231, 500): {
        "percentage": 100,
        "title": "У тебя отличные шансы на результаты с женским кето",
        "description": """Всё, что ты прошла, даёт тебе опыт.
А кето может стать твоей новой точкой опоры — не диетой, а стилем жизни, где:
✅ тело сжигает жир эффективно
✅ гормоны работают в балансе
✅ настроение, энергия и либидо восстанавливаются

Твоя система уже готова к переменам — важно просто дать ей поддержку, а не стресс.

📩 Получи 3-дневный рацион, чтобы попробовать этот путь грамотно и бережно к себе."""
    }
}


class TelegramBot:
    def __init__(self):
        self.application = None
        self.user_states = {}  # Хранение состояний пользователей
        
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        user_id = update.effective_user.id
        username = update.effective_user.username or update.effective_user.first_name
        
        # Сохраняем пользователя в БД
        user_data = {
            "user_id": str(user_id),
            "username": username,
            "first_name": update.effective_user.first_name,
            "last_name": update.effective_user.last_name,
            "created_at": datetime.utcnow(),
            "test_completed": False
        }
        
        users_collection.update_one(
            {"user_id": str(user_id)},
            {"$set": user_data},
            upsert=True
        )
        
        # Приветственное сообщение
        welcome_text = """Привет! 
Ты попала в мой бот

Меня зовут Анна Герц
Я - натуропат , помогаю тысячам женщин становиться здоровыми и стройными и влюбляться в свое тело вновь , и вновь. 

В этом боте будет много полезных гайдов и уроков 😍 
Присоединяйся ✨"""
        
        # Отправляем приветственное сообщение с фото Анны Герц
        photo_path = "/root/app/telegram_bot_images/anna_photo.jpg"
        
        try:
            with open(photo_path, 'rb') as photo_file:
                await update.message.reply_photo(
                    photo=photo_file,
                    caption=welcome_text
                )
        except Exception as e:
            logger.error(f"Ошибка при отправке фото: {e}")
            # Если фото не загрузилось, отправляем текст
            await update.message.reply_text(welcome_text)
        
        # Ждем 5 секунд перед отправкой второго сообщения
        await asyncio.sleep(5)
        await self.send_subscription_check(update, context)
        
    async def send_subscription_check(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Отправка сообщения о проверке подписки"""
        subscription_text = """Для начала  тебе нужно подписаться на мой телеграм-канал, в котором я делюсь очень полезной информацией о чистоте питания, тела и сознания. Показываю реальную жизнь без перекосов, категоричности и вылизанной картинки идеальной жизни !

Где и ты, и я имеем право на ошибки в питании, в спорте, в мыслях, в отношениях - но в этой не идеальности и есть жизнь👍

А также ты найдешь там полезные посты и подкасты про питание и не только  — материал, который не знает гугл, так как это мой опыт и опыт 1000 женщин, прошедших путь очищения со мной . 

Подписывайся и жми кнопку ниже ⬇️"""
        
        keyboard = [
            [InlineKeyboardButton("Подписаться на канал", url=CHANNEL_URL)],
            [InlineKeyboardButton("Проверка подписки", callback_data="check_subscription")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(subscription_text, reply_markup=reply_markup)
        
    async def check_subscription(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Проверка подписки на канал"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        username = query.from_user.username or query.from_user.first_name
        
        try:
            # Проверяем подписку пользователя на канал
            member = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
            
            # Проверяем статус участника
            if member.status in ['member', 'administrator', 'creator']:
                logger.info(f"Пользователь {username} (ID: {user_id}) подписан на канал")
                await query.edit_message_text("Вижу подписку 💗")
                await self.send_test_invitation(query, context)
            else:
                logger.info(f"Пользователь {username} (ID: {user_id}) НЕ подписан на канал")
                await query.edit_message_text(
                    "Кажется, ты еще не подписалась на канал 🤔\n\n"
                    "Подпишись на канал и нажми кнопку еще раз ⬇️",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("Подписаться на канал", url=CHANNEL_URL)],
                        [InlineKeyboardButton("Проверка подписки", callback_data="check_subscription")]
                    ])
                )
                
        except Exception as e:
            logger.error(f"Ошибка при проверке подписки для пользователя {username} (ID: {user_id}): {e}")
            # В случае ошибки (например, бот не администратор канала) - считаем что подписки нет
            logger.info(f"Пользователь {username} (ID: {user_id}) - подписка не найдена (ошибка проверки)")
            await query.edit_message_text(
                "Не увидел подписку на канал 🤔\n\n"
                "Подпишись на канал и попробуй еще раз ⬇️",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Подписаться на канал", url=CHANNEL_URL)],
                    [InlineKeyboardButton("Проверка подписки", callback_data="check_subscription")]
                ])
            )
            
    async def send_test_invitation(self, query_or_update, context: ContextTypes.DEFAULT_TYPE):
        """Отправка приглашения к тесту"""
        test_invitation = """Если тебе 30+, а вес стоит, цикл скачет, отеки, лицо "плывёт".

Это может быть следствием 
недостаточного потребления белка, отсутствием полезных жиров , застоем лимфы, признаками состояния непроходящего стресса и высокого уровня кортизола, невниманием к себе и своему телу, и  пр.

Я сделала короткий тест (5 вопросов) чтобы показать:
🌟как сейчас работают твои гормоны
🌟подойдёт ли тебе кето
🌟и что будет, если ты попробуешь вычистить свое тело 👍

После теста , я выдам тебе результат и рацион , адаптированный под твою ситуацию"""
        
        keyboard = [[InlineKeyboardButton("Пройти тест →", callback_data="start_test")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if hasattr(query_or_update, 'message'):
            # Это callback query
            await query_or_update.message.reply_text(test_invitation, reply_markup=reply_markup)
        else:
            # Это обычное update
            await query_or_update.message.reply_text(test_invitation, reply_markup=reply_markup)
            
    async def start_test(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Начало теста"""
        query = update.callback_query
        await query.answer()
        
        user_id = str(query.from_user.id)
        
        # Инициализируем тест для пользователя
        self.user_states[user_id] = {
            "test_active": True,
            "current_question": 0,
            "answers": [],
            "total_score": 0
        }
        
        await self.send_question(query, context, 0)
        
    async def send_question(self, query, context: ContextTypes.DEFAULT_TYPE, question_index: int):
        """Отправка вопроса теста"""
        if question_index >= len(TEST_QUESTIONS):
            # Тест завершен
            await self.finish_test(query, context)
            return
            
        question_data = TEST_QUESTIONS[question_index]
        
        # Заголовок теста
        if question_index == 0:
            header = "Ответь на 5 вопросов — и я пришлю твой результат + адаптированный рацион на 3 дня\n\n"
        else:
            header = ""
            
        question_text = f"{header}Вопрос {question_index + 1}: {question_data['question']}"
        
        # Создаем кнопки для ответов
        keyboard = []
        for i, (option_text, score) in enumerate(question_data['options']):
            callback_data = f"answer_{question_index}_{i}"
            keyboard.append([InlineKeyboardButton(option_text, callback_data=callback_data)])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(question_text, reply_markup=reply_markup)
        
    async def handle_answer(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка ответа на вопрос теста"""
        query = update.callback_query
        await query.answer()
        
        user_id = str(query.from_user.id)
        
        if user_id not in self.user_states or not self.user_states[user_id].get("test_active"):
            await query.edit_message_text("Тест не найден. Начните заново с команды /start")
            return
            
        # Парсим ответ
        callback_data = query.data
        parts = callback_data.split('_')
        question_index = int(parts[1])
        answer_index = int(parts[2])
        
        # Получаем баллы за ответ
        question_data = TEST_QUESTIONS[question_index]
        option_text, score = question_data['options'][answer_index]
        
        # Сохраняем ответ
        user_state = self.user_states[user_id]
        user_state['answers'].append({
            'question_index': question_index,
            'answer_index': answer_index,
            'answer_text': option_text,
            'score': score
        })
        user_state['total_score'] += score
        user_state['current_question'] = question_index + 1
        
        # Переходим к следующему вопросу
        await self.send_question(query, context, question_index + 1)
        
    async def finish_test(self, query, context: ContextTypes.DEFAULT_TYPE):
        """Завершение теста и показ результата"""
        user_id = str(query.from_user.id)
        user_state = self.user_states[user_id]
        total_score = user_state['total_score']
        
        # Определяем результат
        result = None
        for score_range, result_data in TEST_RESULTS.items():
            if score_range[0] <= total_score <= score_range[1]:
                result = result_data
                break
                
        if not result:
            result = TEST_RESULTS[(231, 500)]  # По умолчанию максимальный результат
            
        # Сохраняем результат в БД
        test_result = {
            "user_id": user_id,
            "test_id": str(uuid.uuid4()),
            "answers": user_state['answers'],
            "total_score": total_score,
            "result_percentage": result['percentage'],
            "result_title": result['title'],
            "completed_at": datetime.utcnow()
        }
        
        test_results_collection.insert_one(test_result)
        
        # Обновляем статус пользователя
        users_collection.update_one(
            {"user_id": user_id},
            {"$set": {"test_completed": True, "last_test_score": total_score}}
        )
        
        # Формируем сообщение с результатом
        result_text = f"{result['percentage']}% — {result['title']}\n\n{result['description']}"
        
        # Добавляем кнопку для получения рациона
        keyboard = [[InlineKeyboardButton("Получить рацион", callback_data="get_diet")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(result_text, reply_markup=reply_markup)
        
        # Сохраняем состояние пользователя для использования в send_diet
        self.user_states[user_id] = {
            "total_score": total_score,
            "result": result
        }
            
    async def send_diet(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Отправка PDF рациона"""
        query = update.callback_query
        await query.answer()
        
        user_id = str(query.from_user.id)
        user_state = self.user_states.get(user_id, {})
        total_score = user_state.get('total_score', 0)
        
        # Определяем результат для отображения без кнопки
        result = None
        for score_range, result_data in TEST_RESULTS.items():
            if score_range[0] <= total_score <= score_range[1]:
                result = result_data
                break
                
        if not result:
            result = TEST_RESULTS[(231, 500)]  # По умолчанию максимальный результат
        
        # Формируем сообщение с результатом БЕЗ кнопки
        result_text = f"{result['percentage']}% — {result['title']}\n\n{result['description']}"
        
        # Убираем кнопку, оставляя только результат теста
        await query.edit_message_text(result_text)
        
        # Отправляем PDF файл
        pdf_path = "/root/app/telegram_bot_pdfs/Кето Анна Герц.pdf"
        
        try:
            with open(pdf_path, 'rb') as pdf_file:
                await context.bot.send_document(
                    chat_id=query.message.chat_id,
                    document=pdf_file,
                    filename="Кето-Начало_рацион.pdf",
                    caption="Кето-Начало: лёгкий вход в мир низких углеводов"
                )
        except Exception as e:
            logger.error(f"Ошибка при отправке PDF: {e}")
            await query.message.reply_text("Извини, произошла ошибка при отправке файла. Попробуй позже.")

    async def admin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /admin"""
        user_id = update.effective_user.id
        
        # Проверяем, что команду вызвал админ
        if user_id != ADMIN_ID:
            await update.message.reply_text("❌ У вас нет доступа к админ-панели.")
            return
        
        admin_text = "🔧 **Админ-панель**\n\nВыберите действие:"
        
        keyboard = [
            [InlineKeyboardButton("📢 Массовая рассылка", callback_data="admin_broadcast")],
            [InlineKeyboardButton("👥 Список пользователей", callback_data="admin_users")],
            [InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(admin_text, reply_markup=reply_markup, parse_mode='Markdown')

    async def admin_broadcast_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Начало массовой рассылки"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        if user_id != ADMIN_ID:
            await query.edit_message_text("❌ У вас нет доступа к админ-панели.")
            return
        
        # Устанавливаем состояние ожидания сообщения для рассылки
        self.user_states[str(user_id)] = {
            "admin_mode": "broadcast_waiting",
            "message_id": query.message.message_id
        }
        
        await query.edit_message_text(
            "📢 **Массовая рассылка**\n\n"
            "Отправьте сообщение, которое нужно разослать всем пользователям бота.\n\n"
            "_Поддерживаются текст, фото, видео и другие типы сообщений._",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Отмена", callback_data="admin_cancel")]])
        )

    async def admin_users_list(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показ списка пользователей"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        if user_id != ADMIN_ID:
            await query.edit_message_text("❌ У вас нет доступа к админ-панели.")
            return
        
        try:
            # Получаем всех пользователей из базы данных
            users = list(users_collection.find({}, {
                "user_id": 1, 
                "username": 1, 
                "first_name": 1, 
                "last_name": 1,
                "created_at": 1,
                "test_completed": 1
            }).sort("created_at", 1))
            
            if not users:
                await query.edit_message_text("👥 Пользователи не найдены.")
                return
            
            # Формируем список пользователей
            users_text = "👥 **Список пользователей:**\n\n"
            for i, user in enumerate(users, 1):
                username = user.get('username', 'Нет username')
                first_name = user.get('first_name', 'Нет имени')
                last_name = user.get('last_name', '')
                full_name = f"{first_name} {last_name}".strip()
                test_status = "✅" if user.get('test_completed', False) else "❌"
                
                users_text += f"{i}. @{username} ({full_name}) {test_status}\n"
                
                # Ограничиваем длину сообщения Telegram (макс. 4096 символов)
                if len(users_text) > 3500:
                    users_text += f"\n... и еще {len(users) - i} пользователей"
                    break
            
            users_text += f"\n📊 **Всего пользователей:** {len(users)}"
            users_text += "\n✅ - прошел тест, ❌ - не проходил тест"
            
            keyboard = [[InlineKeyboardButton("🔄 Обновить", callback_data="admin_users")],
                       [InlineKeyboardButton("◀️ Назад", callback_data="admin_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(users_text, reply_markup=reply_markup, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Ошибка при получении списка пользователей: {e}")
            await query.edit_message_text("❌ Ошибка при получении списка пользователей.")

    async def admin_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показ статистики"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        if user_id != ADMIN_ID:
            await query.edit_message_text("❌ У вас нет доступа к админ-панели.")
            return
        
        try:
            # Получаем статистику
            total_users = users_collection.count_documents({})
            total_tests = test_results_collection.count_documents({})
            users_with_tests = users_collection.count_documents({"test_completed": True})
            
            # Статистика по датам (пользователи за последние 7 дней)
            from datetime import datetime, timedelta
            week_ago = datetime.utcnow() - timedelta(days=7)
            new_users_week = users_collection.count_documents({"created_at": {"$gte": week_ago}})
            
            stats_text = f"""📊 **Статистика бота:**

👥 **Пользователи:**
• Всего: {total_users}
• За неделю: {new_users_week}
• Прошли тест: {users_with_tests}

📝 **Тесты:**
• Всего пройдено: {total_tests}
• Конверсия: {round((users_with_tests / total_users * 100) if total_users > 0 else 0, 1)}%

📅 **Дата:** {datetime.now().strftime('%d.%m.%Y %H:%M')}"""

            keyboard = [[InlineKeyboardButton("🔄 Обновить", callback_data="admin_stats")],
                       [InlineKeyboardButton("◀️ Назад", callback_data="admin_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(stats_text, reply_markup=reply_markup, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Ошибка при получении статистики: {e}")
            await query.edit_message_text("❌ Ошибка при получении статистики.")

    async def admin_cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Отмена админ-действия"""
        query = update.callback_query
        await query.answer()
        
        user_id = str(query.from_user.id)
        if user_id in self.user_states:
            del self.user_states[user_id]
        
        await self.show_admin_menu(query, context)

    async def show_admin_menu(self, query, context: ContextTypes.DEFAULT_TYPE):
        """Показ главного админ-меню"""
        admin_text = "🔧 **Админ-панель**\n\nВыберите действие:"
        
        keyboard = [
            [InlineKeyboardButton("📢 Массовая рассылка", callback_data="admin_broadcast")],
            [InlineKeyboardButton("👥 Список пользователей", callback_data="admin_users")],
            [InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(admin_text, reply_markup=reply_markup, parse_mode='Markdown')

    async def handle_admin_broadcast_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка сообщения для массовой рассылки"""
        user_id = str(update.effective_user.id)
        
        # Проверяем, что пользователь в режиме ожидания рассылки
        if (user_id not in self.user_states or 
            self.user_states[user_id].get('admin_mode') != 'broadcast_waiting'):
            return
        
        if int(user_id) != ADMIN_ID:
            return
        
        # Получаем всех пользователей
        try:
            users = list(users_collection.find({}, {"user_id": 1}))
            total_users = len(users)
            
            if total_users == 0:
                await update.message.reply_text("❌ Нет пользователей для рассылки.")
                return
            
            # Подтверждение рассылки
            confirm_text = f"📢 **Подтверждение рассылки**\n\n"
            confirm_text += f"Сообщение будет отправлено **{total_users}** пользователям.\n\n"
            confirm_text += "Подтвердите отправку:"
            
            # Сохраняем сообщение для рассылки
            self.user_states[user_id]['broadcast_message'] = update.message
            self.user_states[user_id]['admin_mode'] = 'broadcast_confirm'
            
            keyboard = [
                [InlineKeyboardButton("✅ Отправить", callback_data="admin_broadcast_confirm")],
                [InlineKeyboardButton("❌ Отмена", callback_data="admin_cancel")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(confirm_text, reply_markup=reply_markup, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Ошибка при подготовке рассылки: {e}")
            await update.message.reply_text("❌ Ошибка при подготовке рассылки.")

    async def admin_broadcast_confirm(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Подтверждение и выполнение массовой рассылки"""
        query = update.callback_query
        await query.answer()
        
        user_id = str(query.from_user.id)
        
        if int(user_id) != ADMIN_ID:
            await query.edit_message_text("❌ У вас нет доступа к админ-панели.")
            return
        
        if (user_id not in self.user_states or 
            self.user_states[user_id].get('admin_mode') != 'broadcast_confirm'):
            await query.edit_message_text("❌ Сообщение для рассылки не найдено.")
            return
        
        broadcast_message = self.user_states[user_id].get('broadcast_message')
        if not broadcast_message:
            await query.edit_message_text("❌ Сообщение для рассылки не найдено.")
            return
        
        try:
            # Получаем всех пользователей
            users = list(users_collection.find({}, {"user_id": 1}))
            total_users = len(users)
            
            await query.edit_message_text(
                f"📢 **Рассылка запущена...**\n\n"
                f"Отправка сообщения {total_users} пользователям.\n"
                f"Это может занять несколько минут.",
                parse_mode='Markdown'
            )
            
            # Счетчики для статистики
            sent_count = 0
            error_count = 0
            
            # Отправляем сообщения всем пользователям
            for user in users:
                try:
                    user_chat_id = int(user['user_id'])
                    
                    # Определяем тип сообщения и отправляем соответствующим образом
                    if broadcast_message.text:
                        await context.bot.send_message(
                            chat_id=user_chat_id,
                            text=broadcast_message.text,
                            parse_mode='Markdown' if any(char in broadcast_message.text for char in ['*', '_', '`']) else None
                        )
                    elif broadcast_message.photo:
                        await context.bot.send_photo(
                            chat_id=user_chat_id,
                            photo=broadcast_message.photo[-1].file_id,
                            caption=broadcast_message.caption
                        )
                    elif broadcast_message.video:
                        await context.bot.send_video(
                            chat_id=user_chat_id,
                            video=broadcast_message.video.file_id,
                            caption=broadcast_message.caption
                        )
                    elif broadcast_message.document:
                        await context.bot.send_document(
                            chat_id=user_chat_id,
                            document=broadcast_message.document.file_id,
                            caption=broadcast_message.caption
                        )
                    
                    sent_count += 1
                    
                    # Небольшая пауза между отправками, чтобы не превысить лимиты Telegram
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    logger.error(f"Ошибка при отправке сообщения пользователю {user['user_id']}: {e}")
                    error_count += 1
            
            # Отчет о рассылке
            report_text = f"📢 **Рассылка завершена!**\n\n"
            report_text += f"✅ Отправлено: {sent_count}\n"
            report_text += f"❌ Ошибок: {error_count}\n"
            report_text += f"📊 Всего пользователей: {total_users}"
            
            keyboard = [[InlineKeyboardButton("◀️ В админ-панель", callback_data="admin_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(report_text, reply_markup=reply_markup, parse_mode='Markdown')
            
            # Очищаем состояние
            if user_id in self.user_states:
                del self.user_states[user_id]
                
        except Exception as e:
            logger.error(f"Ошибка при выполнении рассылки: {e}")
            await query.edit_message_text("❌ Ошибка при выполнении рассылки.")
            
    async def callback_query_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик всех callback запросов"""
        query = update.callback_query
        
        if query.data == "check_subscription":
            await self.check_subscription(update, context)
        elif query.data == "start_test":
            await self.start_test(update, context)
        elif query.data.startswith("answer_"):
            await self.handle_answer(update, context)
        elif query.data == "get_diet":
            await self.send_diet(update, context)
        # Админ функции
        elif query.data == "admin_broadcast":
            await self.admin_broadcast_start(update, context)
        elif query.data == "admin_users":
            await self.admin_users_list(update, context)
        elif query.data == "admin_stats":
            await self.admin_stats(update, context)
        elif query.data == "admin_cancel":
            await self.admin_cancel(update, context)
        elif query.data == "admin_menu":
            await self.show_admin_menu(query, context)
        elif query.data == "admin_broadcast_confirm":
            await self.admin_broadcast_confirm(update, context)
            
    def setup_handlers(self):
        """Настройка обработчиков"""
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CallbackQueryHandler(self.callback_query_handler))
        
    async def run(self):
        """Запуск бота"""
        try:
            # Создаем приложение
            self.application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
            
            # Настраиваем обработчики
            self.setup_handlers()
            
            # Запускаем бота
            logger.info("Запуск Telegram бота...")
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling(drop_pending_updates=True)
            
            # Бесконечный цикл
            import asyncio
            while True:
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"Ошибка при работе бота: {e}")
            raise e


def main():
    """Главная функция"""
    bot = TelegramBot()
    asyncio.run(bot.run())


if __name__ == "__main__":
    main()
