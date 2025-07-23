from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from pymongo import MongoClient
import os
from dotenv import load_dotenv
import asyncio
import threading
import logging

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Настройка MongoDB
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "test_database")

client = MongoClient(MONGO_URL)
db = client[DB_NAME]

# Создание FastAPI приложения
app = FastAPI(title="Anna Hertz Telegram Bot API", version="1.0.0")

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Глобальная переменная для статуса бота
bot_status = {"running": False, "message": "Бот не запущен"}

class BotStatus(BaseModel):
    status: str
    message: str

@app.on_event("startup")
async def startup_event():
    """Событие запуска приложения"""
    global bot_status
    
    logger.info("Запуск FastAPI сервера...")
    
    # Импортируем и запускаем бота в отдельном процессе
    def run_bot():
        try:
            from telegram_bot import TelegramBot
            import asyncio
            
            # Создаем новый event loop для бота
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            bot = TelegramBot()
            
            # Запускаем бота в бесконечном цикле
            while True:
                try:
                    loop.run_until_complete(bot.run())
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    logger.error(f"Ошибка в боте: {e}")
                    asyncio.sleep(5)  # Пауза перед перезапуском
            
        except Exception as e:
            logger.error(f"Ошибка при запуске Telegram бота: {e}")
            bot_status["running"] = False
            bot_status["message"] = f"Ошибка: {str(e)}"
    
    # Запускаем бота в отдельном потоке
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    bot_status["running"] = True
    bot_status["message"] = "Telegram бот запущен"
    
    logger.info("Telegram бот запущен в фоновом режиме")

@app.on_event("shutdown")
async def shutdown_event():
    """Событие остановки приложения"""
    logger.info("Остановка приложения...")
    global bot_status
    bot_status["running"] = False
    bot_status["message"] = "Бот остановлен"

@app.get("/")
async def root():
    """Корневой эндпоинт"""
    return {"message": "Anna Hertz Telegram Bot API is running"}

@app.get("/api/bot/status", response_model=BotStatus)
async def get_bot_status():
    """Получение статуса бота"""
    global bot_status
    
    status = "running" if bot_status["running"] else "stopped"
    message = bot_status["message"]
    
    return BotStatus(status=status, message=message)

@app.get("/api/users/count")
async def get_users_count():
    """Получение количества пользователей"""
    try:
        count = db.users.count_documents({})
        return {"total_users": count}
    except Exception as e:
        logger.error(f"Ошибка при получении количества пользователей: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при получении данных")

@app.get("/api/test-results/count")
async def get_test_results_count():
    """Получение количества завершенных тестов"""
    try:
        count = db.test_results.count_documents({})
        return {"total_tests": count}
    except Exception as e:
        logger.error(f"Ошибка при получении количества тестов: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при получении данных")

@app.get("/api/users")
async def get_users():
    """Получение списка пользователей"""
    try:
        users = list(db.users.find({}, {"_id": 0}).limit(50))
        return {"users": users}
    except Exception as e:
        logger.error(f"Ошибка при получении пользователей: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при получении данных")

@app.get("/api/test-results")
async def get_test_results():
    """Получение результатов тестов"""
    try:
        results = list(db.test_results.find({}, {"_id": 0}).limit(50))
        return {"test_results": results}
    except Exception as e:
        logger.error(f"Ошибка при получении результатов тестов: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при получении данных")

@app.get("/api/health")
async def health_check():
    """Проверка здоровья приложения"""
    try:
        # Проверяем подключение к MongoDB
        db.command('ping')
        mongo_status = "connected"
    except Exception:
        mongo_status = "disconnected"
    
    # Проверяем статус бота
    global bot_status
    telegram_bot_status = "running" if bot_status["running"] else "stopped"
    
    return {
        "status": "healthy",
        "mongodb": mongo_status,
        "telegram_bot": telegram_bot_status,
        "message": "API is working properly"
    }

# Обработчик ошибок
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"message": "Endpoint not found"}
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"message": "Internal server error"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)