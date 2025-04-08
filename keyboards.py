# keyboards.py
from telegram import (InlineKeyboardButton, InlineKeyboardMarkup,
                    ReplyKeyboardMarkup, KeyboardButton)
from constants import (ZONES, EMOJI_VIP, EMOJI_BOOTCAMP, EMOJI_STANDART, EMOJI_PS5,
                     BTN_SPECIFIC_PC, BTN_BY_QUANTITY, BTN_CONFIRM_SELECTION,
                     EMOJI_CONFIRM, EMOJI_BACK, START_TIME_SLOTS, END_TIME_SLOTS,
                     BTN_YES_CONFIRM, BTN_NO_RESTART, BTN_BOOKING, BTN_PRICES, # Тексти для ReplyKeyboard
                     BTN_CONTACT_ADMIN, BTN_DAY_BOOKING, BTN_NIGHT_BOOKING,
                     BTN_CANCEL_BOOKING) # Імпортували потрібні тексти кнопок
import calendar_logic
import datetime

# --- Клавіатура Головного Меню (Статична) ---
def get_persistent_main_keyboard():
    """Створює статичну клавіатуру головного меню."""
    keyboard = [
        [KeyboardButton(BTN_BOOKING)],
        [KeyboardButton(BTN_PRICES), KeyboardButton(BTN_CONTACT_ADMIN)],
    ]
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=False,
        input_field_placeholder="Оберіть опцію..."
        )

# --- Клавіатура Вибору Типу Бронювання (День/Ніч) ---
def get_booking_type_keyboard():
    """Створює інлайн-клавіатуру для вибору День/Ніч."""
    keyboard = [
        [
            InlineKeyboardButton(BTN_DAY_BOOKING, callback_data="booktype_day"),
            InlineKeyboardButton(BTN_NIGHT_BOOKING, callback_data="booktype_night"),
        ],
        # Кнопка "Скасувати" завершить розмову
        [InlineKeyboardButton(BTN_CANCEL_BOOKING, callback_data="cancel_booking")]
    ]
    return InlineKeyboardMarkup(keyboard)

# --- Клавіатура вибору зони ---
def get_zone_keyboard():
    """Створює інлайн-клавіатуру для вибору Зони."""
    keyboard = [
        [InlineKeyboardButton(ZONES["VIP"]["name"], callback_data="zone_VIP")],
        [InlineKeyboardButton(ZONES["BOOTCAMP"]["name"], callback_data="zone_BOOTCAMP")],
        [InlineKeyboardButton(ZONES["STANDART"]["name"], callback_data="zone_STANDART")],
        [InlineKeyboardButton(ZONES["PS5"]["name"], callback_data="zone_PS5")],
        # Кнопка "Назад" до вибору типу бронювання
        [InlineKeyboardButton(f"{EMOJI_BACK} Назад до вибору День/Ніч", callback_data="back_to_booking_type")]
    ]
    return InlineKeyboardMarkup(keyboard)

# --- Клавіатура вибору опції (ПК чи кількість) ---
def get_pc_or_quantity_keyboard():
    """Створює інлайн-клавіатуру для вибору 'Конкретні ПК' / 'Кількість'."""
    keyboard = [
        [InlineKeyboardButton(BTN_SPECIFIC_PC, callback_data="option_specific")],
        [InlineKeyboardButton(BTN_BY_QUANTITY, callback_data="option_quantity")],
        # Кнопка "Назад" до вибору зони
        [InlineKeyboardButton(f"{EMOJI_BACK} Назад до вибору зони", callback_data="back_to_zone_selection")]
    ]
    return InlineKeyboardMarkup(keyboard)

# --- Клавіатура вибору конкретних ПК ---
def get_pc_selection_keyboard(zone_key, selected_pcs=None):
    """Створює інлайн-клавіатуру для вибору конкретних ПК."""
    if selected_pcs is None:
        selected_pcs = []

    zone_info = ZONES.get(zone_key)
    if not zone_info or not zone_info.get("range"):
        return None # Повернути None, якщо немає ПК

    pc_numbers = zone_info["range"]
    keyboard = []
    row = []
    pcs_per_row = 5 # Кількість кнопок ПК в рядку

    for pc_num in pc_numbers:
        pc_str = str(pc_num)
        text = f"ПК {pc_str}"
        if pc_num in selected_pcs:
            text += f" {EMOJI_CONFIRM}" # Позначка обраного

        callback_data = f"pcselect_TOGGLE_{pc_str}"
        row.append(InlineKeyboardButton(text, callback_data=callback_data))

        if len(row) == pcs_per_row:
            keyboard.append(row)
            row = []

    if row: # Додати останній неповний рядок
        keyboard.append(row)

    # Кнопки керування
    control_row = []
    if selected_pcs: # Кнопка підтвердження, якщо є обрані
       control_row.append(InlineKeyboardButton(BTN_CONFIRM_SELECTION, callback_data="pcselect_CONFIRM"))
    # Кнопка "Назад" до вибору "ПК/Кількість"
    control_row.append(InlineKeyboardButton(f"{EMOJI_BACK} Назад", callback_data="back_to_pc_or_qty"))
    keyboard.append(control_row)

    return InlineKeyboardMarkup(keyboard)

# --- Клавіатура вибору дати (використовує calendar_logic) ---
def get_calendar_keyboard(year=None, month=None):
    """Викликає генератор календаря."""
    # Кнопка скасування процесу додається всередині calendar_logic.create_calendar
    return calendar_logic.create_calendar(year, month)


# --- Клавіатура вибору часу ---
def get_time_keyboard(time_slots, callback_prefix, back_callback_data="back_to_date_selection"):
    """Створює інлайн-клавіатуру для вибору часового слоту."""
    keyboard = []
    row = []
    slots_per_row = 4
    for i, time_slot in enumerate(time_slots):
        row.append(InlineKeyboardButton(time_slot, callback_data=f"{callback_prefix}_{time_slot}"))
        if (i + 1) % slots_per_row == 0:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    # Додаємо кнопку "Назад" до вибору дати
    keyboard.append([InlineKeyboardButton(f"{EMOJI_BACK} Назад до вибору дати", callback_data=back_callback_data)])
    return InlineKeyboardMarkup(keyboard)

def get_start_time_keyboard():
    """Клавіатура для вибору часу початку."""
    # Повертаємось до вибору дати
    return get_time_keyboard(START_TIME_SLOTS, "starttime", "back_to_date_selection")

def get_end_time_keyboard(start_time_str):
    """Клавіатура для вибору часу завершення (фільтрує слоти)."""
    try:
        start_dt = datetime.datetime.strptime(start_time_str, '%H:%M')
        valid_end_slots = [
            t for t in END_TIME_SLOTS
            if datetime.datetime.strptime(t, '%H:%M') > start_dt
        ]
    except (ValueError, TypeError): # Якщо start_time_str None або невірний формат
        valid_end_slots = [] # Не показувати слоти, якщо час початку невірний

    if not valid_end_slots:
       return None # Немає доступних слотів

    # Повертаємось до вибору часу початку
    return get_time_keyboard(valid_end_slots, "endtime", "back_to_start_time")

# --- Клавіатура для кроку запиту номера телефону ---
def get_phone_step_inline_keyboard(booking_type):
    """Створює інлайн-клавіатуру з кнопкою 'Назад' для етапу запиту телефону."""
    # Визначаємо, куди повертатися: до вибору часу (День) чи до вибору дати (Ніч)
    if booking_type == 'day':
        back_callback = "back_to_end_time"
        back_text = f"{EMOJI_BACK} Назад до часу завершення"
    else: # 'night'
        back_callback = "back_to_date_selection"
        back_text = f"{EMOJI_BACK} Назад до вибору дати"

    keyboard = [
        [InlineKeyboardButton(back_text, callback_data=back_callback)],
        # Додаємо загальну кнопку скасування сюди теж
        [InlineKeyboardButton(BTN_CANCEL_BOOKING, callback_data="cancel_booking")]
    ]
    return InlineKeyboardMarkup(keyboard)


# --- Клавіатура підтвердження бронювання ---
def get_confirmation_keyboard():
     """Створює інлайн-клавіатуру для фінального підтвердження."""
     keyboard = [
        [InlineKeyboardButton(BTN_YES_CONFIRM, callback_data="confirm_YES")],
        # Кнопка "Ні" тепер скасовує весь процес
        [InlineKeyboardButton(BTN_NO_RESTART, callback_data="cancel_booking")]
    ]
     return InlineKeyboardMarkup(keyboard)

# Функція get_info_section_keyboard() видалена, бо більше не потрібна.