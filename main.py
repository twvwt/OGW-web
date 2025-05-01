import logging
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.enums import ParseMode

# Загрузка переменных окружения
load_dotenv()

# Конфигурация
TOKEN = os.getenv("TOKEN")
WEBAPP_URL = "https://yourdomain.com/index_1.html"  # Замените на ваш URL
DB_LITE = os.getenv("DB_LITE")

# Инициализация бота и диспетчера
bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

# Настройка логгирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

async def set_main_menu():
    """Установка команд меню бота"""
    main_menu_commands = [
        types.BotCommand(command='/start', description='🚀 Начать работу'),
        types.BotCommand(command='/menu', description='📱 Главное меню'),
        types.BotCommand(command='/help', description='❓ Помощь'),
        types.BotCommand(command='/contacts', description='📞 Контакты'),
    ]
    await bot.set_my_commands(main_menu_commands)

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """Обработчик команды /start"""
    keyboard = InlineKeyboardBuilder()
    keyboard.row(
        InlineKeyboardButton(
            text="📱 Перейти в приложение", 
            web_app=WebAppInfo(url=WEBAPP_URL)
        )
    )
    keyboard.row(
        InlineKeyboardButton(
            text="📢 Наш канал", 
            url="https://t.me/OGWPLUS")
        )
    
    await message.answer(
        f"👋 <b>Привет, {message.from_user.full_name}!</b>\n\n"
        "✨ Добро пожаловать в <b>OGWPLUS</b> - официальный магазин техники Apple и ремонта.\n\n"
        "Нажмите кнопку ниже, чтобы перейти в приложение:",
        reply_markup=keyboard.as_markup()
    )

@dp.message(Command("menu"))
async def cmd_menu(message: types.Message):
    """Обработчик команды /menu"""
    keyboard = InlineKeyboardBuilder()
    keyboard.row(
        InlineKeyboardButton(
            text="📱 Перейти в приложение", 
            web_app=WebAppInfo(url=WEBAPP_URL)
        )
    )
    keyboard.row(
        InlineKeyboardButton(text="📢 Наш канал", url="https://t.me/OGWPLUS"),
        InlineKeyboardButton(text="📞 Контакты", callback_data="contacts")
    )
    keyboard.row(
        InlineKeyboardButton(text="❓ Помощь", callback_data="help"),
        InlineKeyboardButton(text="🛒 Корзина", callback_data="basket")
    )
    
    await message.answer(
        "📋 <b>Главное меню:</b>",
        reply_markup=keyboard.as_markup()
    )

@dp.callback_query(lambda c: c.data == "contacts")
async def process_contacts(callback: types.CallbackQuery):
    """Обработчик кнопки Контакты"""
    keyboard = InlineKeyboardBuilder()
    keyboard.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")
    )
    
    await callback.message.edit_text(
        "📞 <b>Наши контакты:</b>\n\n"
        "📍 <u>Адреса магазинов:</u>\n"
        "• Москва, Багратионовский проезд 7к2, БЦ Рубин\n"
        "• Москва, Сущевский вал 5с1, 5 подъезд, 2 этаж\n\n"
        "📱 <u>Телефон:</u> +7 (910) 447-79-78\n"
        "✉️ <u>Telegram:</u> @OGWPLUS\n\n"
        "🕒 <u>Часы работы:</u> ежедневно 11:00-20:00",
        reply_markup=keyboard.as_markup()
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data == "help")
async def process_help(callback: types.CallbackQuery):
    """Обработчик кнопки Помощь"""
    keyboard = InlineKeyboardBuilder()
    keyboard.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")
    )
    
    await callback.message.edit_text(
        "❓ <b>Помощь:</b>\n\n"
        "1. Нажмите <b>'Перейти в приложение'</b> для входа\n"
        "2. В приложении доступно:\n"
        "   • Просмотр товаров 🛍️\n"
        "   • Добавление в корзину 🛒\n"
        "   • Оформление заказов 💳\n"
        "   • Запись на ремонт 🛠️\n\n"
        "🆘 По вопросам пишите в @OGWPLUS",
        reply_markup=keyboard.as_markup()
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data == "back_to_menu")
async def process_back_to_menu(callback: types.CallbackQuery):
    """Обработчик кнопки Назад"""
    await cmd_menu(callback.message)
    await callback.answer()

async def main():
    """Запуск бота"""
    await set_main_menu()
    logger.info("Бот запущен")
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен")