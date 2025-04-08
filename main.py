# main.py
import logging
from telegram import Update # Імпорт класу Update
from telegram.ext import (
    Application,
    CommandHandler,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)
from telegram.warnings import PTBUserWarning
import warnings

# Імпортуємо конфігурацію, константи та обробники
# Переконуємось, що імпортуємо саме змінні, а не весь модуль, якщо потрібна перевірка
from config import BOT_TOKEN, GROUP_CHAT_ID
import handlers
import constants as C # Використовуємо аліас C для констант

# Налаштування логування
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

def main() -> None:
    """Запускає бота."""
    logger.info("Запуск бота...")

    # --- ПЕРЕВІРКА КОНФІГУРАЦІЇ ---
    # Перевіряємо, чи завантажився токен з config.py (який читає .env або змінні оточення)
    if not BOT_TOKEN or BOT_TOKEN == "ЗАМІНИ_МЕНЕ_ЯКЩО_НЕМАЄ_ENV":
        logger.critical("ПОМИЛКА: BOT_TOKEN не знайдено або не встановлено! Перевірте змінні оточення або файл .env.")
        return # Не запускати бота без токена

    # Перевіряємо ID групи (в config.py він вже має бути int або викличе помилку)
    if not GROUP_CHAT_ID:
        logger.critical("ПОМИЛКА: GROUP_CHAT_ID не знайдено або не встановлено! Перевірте змінні оточення або файл .env.")
        return
    logger.info(f"Токен знайдено. ID групи для повідомлень: {GROUP_CHAT_ID}")
    # --- Кінець перевірки ---

    # Створення Application
    application = Application.builder().token(BOT_TOKEN).build()

    # --- Визначення ConversationHandler для процесу БРОНЮВАННЯ ---
    booking_conv_handler = ConversationHandler(
        # Точка входу: текстове повідомлення з текстом кнопки "Бронювання"
        entry_points=[MessageHandler(filters.Text([C.BTN_BOOKING]) & ~filters.COMMAND, handlers.start_booking_conversation)],
        states={
            # --- Стани процесу бронювання ---
            C.SELECTING_BOOKING_TYPE: [
                CallbackQueryHandler(handlers.handle_booking_type, pattern="^booktype_"),
            ],
            C.SELECTING_ZONE: [
                CallbackQueryHandler(handlers.handle_zone_selection, pattern="^zone_"),
                CallbackQueryHandler(handlers.handle_back_button, pattern="^back_to_booking_type$")
            ],
            C.SELECTING_PC_OR_QTY: [
                CallbackQueryHandler(handlers.handle_pc_or_quantity, pattern="^option_"),
                CallbackQueryHandler(handlers.handle_back_button, pattern="^back_to_zone_selection$")
            ],
            C.SELECTING_PC: [
                CallbackQueryHandler(handlers.handle_pc_selection, pattern="^pcselect_"),
                CallbackQueryHandler(handlers.handle_back_button, pattern="^back_to_pc_or_qty$")
            ],
            C.ENTERING_QUANTITY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.handle_quantity_input),
            ],
            C.ENTERING_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.handle_name_input),
            ],
            C.SELECTING_DATE: [
                CallbackQueryHandler(handlers.handle_date_selection, pattern=f"^{C.CALENDAR_CALLBACK_PREFIX}_"),
            ],
            C.SELECTING_START_TIME: [
                CallbackQueryHandler(handlers.handle_start_time_selection, pattern="^starttime_"),
                CallbackQueryHandler(handlers.handle_back_button, pattern="^back_to_date_selection$")
            ],
            C.SELECTING_END_TIME: [
                CallbackQueryHandler(handlers.handle_end_time_selection, pattern="^endtime_"),
                CallbackQueryHandler(handlers.handle_back_button, pattern="^back_to_start_time$")
            ],
            C.SHARING_PHONE: [
                 MessageHandler(filters.CONTACT, handlers.handle_phone_input),
                 MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.handle_phone_input), # Обробка помилки
                 CallbackQueryHandler(handlers.handle_back_button, pattern="^back_to_") # Кнопка Назад
            ],
            C.CONFIRMATION: [
                CallbackQueryHandler(handlers.handle_confirmation, pattern="^confirm_YES$"),
            ]
        },
        fallbacks=[
            # Команди для скасування/перезапуску розмови бронювання
            CommandHandler("start", handlers.start),
            CommandHandler("cancel", handlers.cancel_command_handler),
            # Загальна кнопка скасування/перезапуску
            CallbackQueryHandler(handlers.cancel_callback_handler, pattern="^cancel_booking$"),
            # Обробка кнопок "Назад"
            CallbackQueryHandler(handlers.handle_back_button, pattern="^back_to_"),
            # Обробка будь-якого іншого повідомлення/дії як помилки В МЕЖАХ РОЗМОВИ
            MessageHandler(filters.ALL, handlers.fallback_handler),
        ],
        allow_reentry=True,
        per_message=False # Важливо для роботи з callback'ами та повідомленнями
    )

    # --- Реєстрація обробників ---
    # 1. Обробник команди /start (показує клавіатуру, не входить у розмову)
    application.add_handler(CommandHandler("start", handlers.start))

    # 2. Обробники для кнопок "Ціни" та "Зв'язок" (працюють завжди, поза розмовою)
    application.add_handler(MessageHandler(filters.Text([C.BTN_PRICES]) & ~filters.COMMAND, handlers.show_prices))
    application.add_handler(MessageHandler(filters.Text([C.BTN_CONTACT_ADMIN]) & ~filters.COMMAND, handlers.show_admin_contact))

    # 3. Додавання ConversationHandler для процесу бронювання (запускається кнопкою "Бронювання")
    application.add_handler(booking_conv_handler)

    # 4. Глобальний обробник команди /cancel (на випадок, якщо користувач поза розмовою)
    # Можна додати окремо, хоча він є і у fallbacks
    application.add_handler(CommandHandler("cancel", handlers.cancel_command_handler))

    # Можна додати тут обробники невідомих команд/повідомлень, якщо потрібно

    logger.info("Бот готовий до роботи. Починаю опитування...")
    # Запуск бота
    application.run_polling(allowed_updates=Update.ALL_TYPES)

    logger.info("Бот зупинено.")

if __name__ == "__main__":
    main()