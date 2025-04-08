# constants.py
import datetime

# --- Емодзі ---
EMOJI_VIP = "🏆"
EMOJI_BOOTCAMP = "🎯"
EMOJI_STANDART = "💻"
EMOJI_PS5 = "🎮"
EMOJI_CALENDAR = "📅"
EMOJI_CLOCK = "🕒"
EMOJI_BACK = "⬅️"
EMOJI_NEXT = "➡️"
EMOJI_CONFIRM = "✅"
EMOJI_CANCEL = "❌"
EMOJI_RESTART = "🔄"
EMOJI_USER = "👤"
EMOJI_PHONE = "📞"
EMOJI_LOCATION = "📍"
EMOJI_PC = "💻"
EMOJI_QTY = "🔢"
EMOJI_LINK = "🔗"
EMOJI_INFO = "📢"
EMOJI_IGNORE = " "
EMOJI_PRICE = "💰"
EMOJI_CONTACT = "🧑‍💼"
EMOJI_BOOK = "📝"
EMOJI_DAY = "☀️"
EMOJI_NIGHT = "🌙"
EMOJI_MAP = "🗺️"
EMOJI_COFFEE = "☕"

# --- Зони та ПК ---
ZONES = {
    "VIP": {"name": f"VIP {EMOJI_VIP}", "range": list(range(1, 11))},
    "BOOTCAMP": {"name": f"BOOTCAMP {EMOJI_BOOTCAMP}", "range": list(range(21, 31))},
    "STANDART": {"name": f"STANDART {EMOJI_STANDART}", "range": list(range(11, 21)) + list(range(31, 62))}, # Оновлено: до 61 включно
    "PS5": {"name": f"PS5 {EMOJI_PS5}", "range": []} # PS5 не має номерів
}

# --- Стани для ConversationHandler ---
# Додали WAITING_MAIN_CHOICE замість SELECTING_MAIN_OPTION
(WAITING_MAIN_CHOICE, SHOWING_INFO, SELECTING_BOOKING_TYPE, SELECTING_ZONE,
 SELECTING_PC_OR_QTY, SELECTING_PC, ENTERING_QUANTITY, ENTERING_NAME,
 SELECTING_DATE, SELECTING_START_TIME, SELECTING_END_TIME, SHARING_PHONE,
 CONFIRMATION) = range(13)

# --- Тексти повідомлень ---
MSG_START_MENU = "Вітаю! Оберіть опцію:"
MSG_CHOOSE_BOOKING_TYPE = f"Оберіть тип бронювання:"
MSG_CHOOSE_ZONE = "Чудово! Тепер оберіть зону:"
MSG_CHOOSE_OPTION = "Оберіть конкретний комп'ютер чи бажану кількість місць?"
MSG_CHOOSE_PC = f"Оберіть один або декілька ПК зі списку нижче.\nНатискайте на номер, щоб додати/видалити.\nНатисніть {EMOJI_CONFIRM} для підтвердження."
MSG_ENTER_QUANTITY = f"{EMOJI_QTY} Введіть бажану кількість комп'ютерів (цифрою):"
MSG_INVALID_QUANTITY = f"{EMOJI_CANCEL} Будь ласка, введіть дійсне число більше нуля."
MSG_ENTER_NAME = f"{EMOJI_USER} Введіть ваше ім'я:"
MSG_CHOOSE_DATE = f"{EMOJI_CALENDAR} Оберіть дату бронювання:"
MSG_CHOOSE_START_TIME = f"{EMOJI_CLOCK} Оберіть час початку (з 10:00 до 21:30):"
MSG_CHOOSE_END_TIME = f"{EMOJI_CLOCK} Оберіть час завершення (має бути пізніше часу початку):"
MSG_INVALID_END_TIME = f"{EMOJI_CANCEL} Час завершення має бути пізнішим за час початку. Спробуйте ще раз."
MSG_REQUEST_PHONE = f"{EMOJI_PHONE} Майже готово! Натисніть кнопку нижче, щоб поділитися контактом для зв'язку."
MSG_THANKS_REQUEST_SENT = f"{EMOJI_CONFIRM} Дякую! Вашу заявку на бронювання надіслано адміністратору. Незабаром з вами зв'яжуться для підтвердження {EMOJI_COFFEE}"
MSG_BOOKING_DETAILS = "Перевірте деталі бронювання:"
MSG_CONFIRM_BOOKING = "Все вірно?"
MSG_BOOKING_CANCELLED = f"{EMOJI_RESTART} Дія скасована. Щоб почати знову, натисніть /start."
MSG_FALLBACK = "Щось пішло не так або я не зрозумів команду.\n\nЩоб почати знову, натисніть /start."
MSG_ERROR_SENDING = f"{EMOJI_CANCEL} Виникла помилка під час надсилання заявки адміністратору.\nСпробуйте пізніше або зв'яжіться з клубом напряму."
MSG_CONTACT_NOT_YOURS = f"{EMOJI_CANCEL} Будь ласка, поділіться своїм власним номером телефону."
MSG_PLEASE_PRESS_BUTTON = f"{EMOJI_CANCEL} Будь ласка, натисніть кнопку 'Поділитися номером телефону'."
MSG_CHOOSE_AT_LEAST_ONE_PC = f"{EMOJI_CANCEL} Будь ласка, оберіть хоча б один ПК перед підтвердженням."
MSG_TIME_SLOTS_ERROR = f"{EMOJI_CANCEL} Не вдалося розрахувати доступні слоти часу. Спробуйте пізніше."


# --- Тексти для цін ---
PRICE_LIST_TEXT = f"""
{EMOJI_PRICE} <b>Наші Ціни</b> {EMOJI_PRICE}

🖥️ <b>PC Zone (Standart)</b>
1 година - 90 грн
3 години - 255 грн
5 годин - 400 грн
{EMOJI_DAY} День (11:00-22:00) - 630 грн
{EMOJI_NIGHT} Ніч (22:00-7:00) - 450 грн

😎 <b>VIP Zone</b>
1 година - 130 грн
3 години - 350 грн
5 годин - 585 грн
{EMOJI_DAY} День (11:00-22:00) - 900 грн
{EMOJI_NIGHT} Ніч (22:00-7:00) - 850 грн

🚀 <b>Bootcamp Zone</b>
1 година - 160 грн
3 години - 430 грн
5 годин - 700 грн
{EMOJI_DAY} День (11:00-22:00) - 1100 грн
{EMOJI_NIGHT} Ніч (22:00-7:00) - 1050 грн

🎮 <b>PS 5 Zone</b>
1 година - 250 грн
3 години - 675 грн
Додаткові джойстіки — 125 грн/год за один
{EMOJI_NIGHT} Ніч (22:00-7:00) - 1450 грн

👨‍💻 <b>Коворкінг</b>
1 година - 90 грн
{EMOJI_DAY} День (11:00-22:00) - 550 грн + безлімітна кава {EMOJI_COFFEE}

**<i>Ціну вказано за 1 ігрову станцію</i>
"""

# --- Тексти для контактів ---
ADMIN_USERNAME = "@checkpointarsnl"
ADMIN_PHONE = "+380678686865"
ADMIN_MAP_URL = "https://maps.app.goo.gl/9qcB5qBwQmebUx5z9" 

ADMIN_CONTACT_TEXT = f"""
{EMOJI_CONTACT} **Зв'язок з адміністратором:**

Telegram: {ADMIN_USERNAME}
Телефон: {ADMIN_PHONE}
{EMOJI_MAP} Адреса на карті: {ADMIN_MAP_URL}
"""

# --- Тексти для кнопок ---
BTN_BOOKING = f"{EMOJI_BOOK} Бронювання"
BTN_PRICES = f"{EMOJI_PRICE} Ціни"
BTN_CONTACT_ADMIN = f"{EMOJI_CONTACT} Зв'язок з адміном"
BTN_DAY_BOOKING = f"{EMOJI_DAY} День"
BTN_NIGHT_BOOKING = f"{EMOJI_NIGHT} Ніч"
BTN_BACK_TO_MAIN_MENU = f"{EMOJI_BACK} Головне меню"

BTN_SPECIFIC_PC = f"{EMOJI_PC} Обрати конкретні ПК"
BTN_BY_QUANTITY = f"{EMOJI_QTY} Ввести кількість"
BTN_CONFIRM_SELECTION = f"{EMOJI_CONFIRM} Підтвердити вибір"
BTN_CANCEL_BOOKING = f"{EMOJI_RESTART} Скасувати / Почати заново" # Використовується в процесі
BTN_SHARE_PHONE = f"{EMOJI_PHONE} Поділитися номером телефону" # Текст для Reply кнопки
BTN_YES_CONFIRM = f"{EMOJI_CONFIRM} Так, відправити заявку"
BTN_NO_RESTART = f"{EMOJI_RESTART} Ні, почати заново"
BTN_CANCEL_DATE = f"{EMOJI_CANCEL} Скасувати вибір дати" # Не використовується зараз, але можна додати

# --- Формат часу ---
TIME_FORMAT = "%H:%M"
DATE_FORMAT = "%Y-%m-%d"

# --- Генерація часових слотів ---
def generate_time_slots(start_hour=10, end_hour=22, minute_step=30):
    slots = []
    try:
        start_dt = datetime.datetime.combine(datetime.date.today(), datetime.time(start_hour, 0))
        end_dt = datetime.datetime.combine(datetime.date.today(), datetime.time(end_hour, 0))
        current_dt = start_dt
        while current_dt < end_dt:
            slots.append(current_dt.strftime(TIME_FORMAT))
            current_dt += datetime.timedelta(minutes=minute_step)
    except Exception as e:
        print(f"Помилка генерації слотів часу: {e}") # Логування помилки
    return slots

START_TIME_SLOTS = generate_time_slots(10, 22, 30)
END_TIME_SLOTS = generate_time_slots(10, 22, 30)[1:] + ["22:00"]

# --- Для календаря ---
MONTH_NAMES_UK = ["Січень", "Лютий", "Березень", "Квітень", "Травень", "Червень",
                "Липень", "Серпень", "Вересень", "Жовтень", "Листопад", "Грудень"]
WDAY_NAMES_UK = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Нд"]
CALENDAR_CALLBACK_PREFIX = "calendar" # Префікс для callback даних календаря

MSG_NIGHT_BOOKING_INFO = (
    "\n\n❗️ <b>Інформація про нічні 🎮:</b>\n"  
    "Зазвичай проводяться у ночі з Пт-Сб та Сб-Нд (22:00 - 07:00).\n"
    "Щодо інших днів - уточніть можливість у адміністратора."
)
