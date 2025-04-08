# calendar_logic.py
import calendar
import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from constants import (MONTH_NAMES_UK, WDAY_NAMES_UK, EMOJI_BACK, EMOJI_NEXT,
                     EMOJI_CALENDAR, EMOJI_IGNORE, CALENDAR_CALLBACK_PREFIX,
                     BTN_CANCEL_BOOKING) # Використовуємо загальну кнопку скасування

def create_calendar(year=None, month=None):
    """
    Створює інлайн-клавіатуру календаря для вказаного місяця та року.
    Якщо рік та місяць не вказані, використовує поточні.
    Дозволяє навігацію та вибір на 3 місяці вперед (поточний + 2 наступних).
    """
    now = datetime.datetime.now()
    # Встановлюємо сьогоднішню дату на початок дня для коректних порівнянь
    today = datetime.date(now.year, now.month, now.day)

    if year is None:
        year = today.year
    if month is None:
        month = today.month

    # Розраховуємо індекси місяців (0-based для зручності розрахунків)
    # Наприклад, квітень 2025 -> 2025 * 12 + 4 - 1 = 24300 + 3 = 24303
    current_year_month_index = today.year * 12 + today.month - 1
    target_year_month_index = year * 12 + month - 1

    # Обмеження: календар на 3 місяці вперед від поточного
    months_ahead = 3
    # Індекс останнього місяця, який ми дозволяємо показувати/обирати
    max_allowed_year_month_index = current_year_month_index + months_ahead - 1

    # Перевірка можливості навігації
    # Чи можна повернутись до попереднього місяця (не раніше поточного)
    can_go_back = target_year_month_index > current_year_month_index
    # Чи можна перейти до наступного місяця (не далі дозволеного максимуму)
    can_go_forward = target_year_month_index < max_allowed_year_month_index

    # --- Верхній рядок: Назва місяця та рік ---
    month_name = MONTH_NAMES_UK[month - 1]
    ignore_callback = f"{CALENDAR_CALLBACK_PREFIX}_IGNORE"
    header_row = [InlineKeyboardButton(f"{month_name} {year}", callback_data=ignore_callback)]
    keyboard = [header_row]

    # --- Другий рядок: Дні тижня ---
    week_days_row = [InlineKeyboardButton(day, callback_data=ignore_callback) for day in WDAY_NAMES_UK]
    keyboard.append(week_days_row)

    # --- Основна сітка календаря ---
    month_calendar = calendar.monthcalendar(year, month)
    for week in month_calendar:
        row = []
        for day in week:
            if day == 0:
                row.append(InlineKeyboardButton(EMOJI_IGNORE, callback_data=ignore_callback)) # Порожня клітинка
            else:
                try:
                    current_date = datetime.date(year, month, day)
                    # Дозволити вибір тільки сьогоднішньої дати та дат в межах дозволеного діапазону місяців
                    if current_date >= today and target_year_month_index <= max_allowed_year_month_index :
                        callback_data = f"{CALENDAR_CALLBACK_PREFIX}_SELECT_{current_date.strftime('%Y-%m-%d')}"
                        row.append(InlineKeyboardButton(str(day), callback_data=callback_data))
                    else:
                        # Минулі дати або дати за межами діапазону - неактивні (сірі)
                        # Просто текст без callback_data або з ignore_callback
                        row.append(InlineKeyboardButton(f"•{day}•", callback_data=ignore_callback)) # Візуально відрізняємо неактивні
                except ValueError:
                     # На випадок неможливих дат (напр. 31 лютого) - хоча monthcalendar не має їх генерувати
                      row.append(InlineKeyboardButton(EMOJI_IGNORE, callback_data=ignore_callback))
        keyboard.append(row)

    # --- Нижній рядок: Навігація ---
    nav_row = []
    if can_go_back:
        prev_month, prev_year = (month - 1, year) if month > 1 else (12, year - 1)
        nav_row.append(InlineKeyboardButton(EMOJI_BACK, callback_data=f"{CALENDAR_CALLBACK_PREFIX}_PREV_{prev_year}_{prev_month}"))
    else:
        nav_row.append(InlineKeyboardButton(EMOJI_IGNORE, callback_data=ignore_callback)) # Пустий елемент для вирівнювання

    nav_row.append(InlineKeyboardButton(EMOJI_CALENDAR, callback_data=ignore_callback)) # Центральна кнопка

    if can_go_forward:
        next_month, next_year = (month + 1, year) if month < 12 else (1, year + 1)
        nav_row.append(InlineKeyboardButton(EMOJI_NEXT, callback_data=f"{CALENDAR_CALLBACK_PREFIX}_NEXT_{next_year}_{next_month}"))
    else:
         nav_row.append(InlineKeyboardButton(EMOJI_IGNORE, callback_data=ignore_callback))

    keyboard.append(nav_row)

    # Додати кнопку скасування всього процесу бронювання
    keyboard.append([InlineKeyboardButton(BTN_CANCEL_BOOKING, callback_data="cancel_booking")])

    return InlineKeyboardMarkup(keyboard)

# Функція для обробки callback'ів календаря
async def process_calendar_selection(update, context):
    """
    Обробляє натискання на кнопки календаря (вибір дати, навігація).
    Повертає tuple: (було_обрано_дату: bool | None, текст_для_повідомлення: str | None)
    Якщо дату обрано -> (True, "📅 Обрана дата: YYYY-MM-DD")
    Якщо навігація -> (False, None)
    Якщо помилка/ігнор -> (None, None)
    """
    query = update.callback_query
    # Відповідаємо на запит одразу, щоб кнопка перестала "крутитися"
    await query.answer()

    callback_data = query.data

    # Перевіряємо, чи дані починаються з префіксу календаря
    if not callback_data or not callback_data.startswith(f"{CALENDAR_CALLBACK_PREFIX}_"):
        return None, None # Це не callback календаря

    data = callback_data.split('_')
    action = data[1] # Другий елемент: IGNORE, SELECT, PREV, NEXT

    if action == "IGNORE":
        return None, None

    elif action == "SELECT":
        try:
            selected_date_str = data[2]
            # Перевірка формату дати
            datetime.datetime.strptime(selected_date_str, '%Y-%m-%d').date()
            # Зберігаємо обрану дату
            context.user_data['selected_date'] = selected_date_str
            message_text = f"{EMOJI_CALENDAR} Обрана дата: {selected_date_str}"
            # Редагуємо текст повідомлення, щоб показати обрану дату
            await query.edit_message_text(message_text, reply_markup=None) # Забираємо клавіатуру
            return True, message_text
        except (IndexError, ValueError) as e:
             print(f"Помилка розбору дати календаря: {e}, data: {callback_data}") # Логування помилки
             return None, None

    elif action in ["PREV", "NEXT"]:
        try:
            year, month = int(data[2]), int(data[3])
            # Оновлюємо клавіатуру календаря, залишаючи текст запиту той самий
            await query.edit_message_text(
                text=query.message.text,
                reply_markup=create_calendar(year, month)
            )
            return False, None # Сигналізуємо, що це була навігація
        except (IndexError, ValueError) as e:
            print(f"Помилка розбору навігації календаря: {e}, data: {callback_data}")
            return None, None

    return None, None # Невідома дія