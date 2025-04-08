# handlers.py
import logging
from telegram import (Update, User, ReplyKeyboardRemove, ReplyKeyboardMarkup,
                    KeyboardButton, InlineKeyboardMarkup)
from telegram.constants import ParseMode
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)
import datetime
import re # На майбутнє, для перевірки телефону

# Імпортуємо константи, клавіатури та логіку календаря
from constants import * # Імпортуємо все з констант
import keyboards
import calendar_logic
from config import GROUP_CHAT_ID # Імпортуємо ID групи

# Налаштування логування
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


# --- Допоміжні функції ---
def get_user_info(user: User | None) -> str:
    """Отримує інформацію про користувача для логів."""
    if not user: return "Невідомий користувач"
    info = f"ID: {user.id}"
    if user.full_name: info += f" | Ім'я: {user.full_name}"
    if user.username: info += f" | @{user.username}"
    return info

async def clear_user_data(context: ContextTypes.DEFAULT_TYPE):
    """Очищує дані користувача, зібрані під час бронювання."""
    keys_to_remove = [
        'zone_key', 'zone_name', 'booking_type', 'selected_pcs', 'quantity',
        'user_name', 'selected_date', 'start_time', 'end_time', 'user_phone',
        'current_state', 'message_to_edit', 'booking_time_type'
    ]
    for key in keys_to_remove:
        context.user_data.pop(key, None)
    logger.debug("Дані користувача для бронювання очищено.")

async def send_or_edit_message(context: ContextTypes.DEFAULT_TYPE, chat_id: int, text: str, reply_markup: InlineKeyboardMarkup | None = None, parse_mode: str | None = None):
    """Намагається відредагувати останнє *інлайн* повідомлення, якщо не виходить - надсилає нове."""
    message_id = context.user_data.get('message_to_edit')
    success = False
    if not isinstance(reply_markup, (InlineKeyboardMarkup, type(None))):
        logger.error("send_or_edit_message отримав невірний тип reply_markup.")
        reply_markup = None

    if message_id:
        try:
            await context.bot.edit_message_text(
                chat_id=chat_id, message_id=message_id, text=text,
                reply_markup=reply_markup, parse_mode=parse_mode
            )
            logger.debug(f"Інлайн-повідомлення {message_id} відредаговано.")
            success = True
        except Exception as e:
             success = False

    if not success:
        try:
            context.user_data.pop('message_to_edit', None) # Видаляємо старий ID
            sent_message = await context.bot.send_message(
                chat_id=chat_id, text=text, reply_markup=reply_markup, parse_mode=parse_mode
            )
            context.user_data['message_to_edit'] = sent_message.message_id # Зберігаємо ID нового
            logger.debug(f"Надіслано нове інлайн-повідомлення {sent_message.message_id}.")
        except Exception as e:
            logger.error(f"Не вдалося надіслати повідомлення в чат {chat_id}: {e}")

# --- Функція форматування фінального повідомлення --- (Без змін)
def format_booking_details(data):
    """Форматує зібрані дані для повідомлення підтвердження та пуша."""
    details = []
    user_name = data.get('user_name', '-')
    booking_time_type = data.get('booking_time_type', 'day') # 'day' or 'night'

    details.append(f"{EMOJI_INFO} Нове бронювання!")
    details.append(f"{EMOJI_USER} Ім’я: {user_name}")
    details.append(f"{EMOJI_PHONE} Телефон: {data.get('user_phone', '-')}")
    details.append(f"{EMOJI_LOCATION} Зона: {data.get('zone_name', '-')}")

    booking_type = data.get('booking_type')
    if booking_type == 'specific':
        if data.get('zone_key') == 'PS5':
             details.append(f"{EMOJI_PC} Комп’ютери: PS5")
             details.append(f"{EMOJI_QTY} Кількість: 1")
        elif data.get('selected_pcs'):
             pcs_str = ", ".join(map(str, sorted(data['selected_pcs'])))
             details.append(f"{EMOJI_PC} Комп’ютери: {pcs_str}")
             details.append(f"{EMOJI_QTY} Кількість: {len(data['selected_pcs'])}")
        else:
             details.append(f"{EMOJI_PC} Комп’ютери: -")
             details.append(f"{EMOJI_QTY} Кількість: -")
    elif booking_type == 'quantity' and data.get('quantity'):
        details.append(f"{EMOJI_PC} Комп’ютери: -")
        details.append(f"{EMOJI_QTY} Кількість: {data['quantity']}")
    else:
         details.append(f"{EMOJI_PC} Комп’ютери: -")
         details.append(f"{EMOJI_QTY} Кількість: -")

    details.append(f"{EMOJI_CALENDAR} Дата: {data.get('selected_date', '-')}")

    if booking_time_type == 'night':
        details.append(f"{EMOJI_CLOCK} Час: Нічна")
    else: # 'day'
        details.append(f"{EMOJI_CLOCK} Час: {data.get('start_time', '-')} - {data.get('end_time', '-')}")

    user_id = data.get('user_id')
    if user_id:
        link_text = "Перейти до чату"
        details.append(f'{EMOJI_LINK} Звʼязок: <a href="tg://user?id={user_id}">{link_text}</a>')
    else:
        details.append(f'{EMOJI_LINK} Звʼязок: Недоступний')

    return "\n".join(details), ParseMode.HTML


# --- Обробники команд та Глобальні Обробники Повідомлень ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Надсилає вітальне повідомлення та показує головне меню (ReplyKeyboard)."""
    user = update.effective_user
    chat_id = update.effective_chat.id
    logger.info(f"Користувач {get_user_info(user)} запустив /start.")
    # Очищаємо дані на випадок, якщо користувач був у процесі бронювання
    await clear_user_data(context)
    context.user_data['user_id'] = user.id # Зберігаємо ID користувача

    # Надсилаємо вітальне повідомлення та показуємо статичну клавіатуру
    await update.message.reply_text(
        MSG_START_MENU,
        reply_markup=keyboards.get_persistent_main_keyboard()
    )
    # Ця функція більше не повертає стан для ConversationHandler

async def show_prices(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Надсилає повідомлення з цінами."""
    user = update.effective_user
    chat_id = update.effective_chat.id
    logger.info(f"Користувач {get_user_info(user)} запитав ціни.")
    await context.bot.send_message(
        chat_id=chat_id,
        text=PRICE_LIST_TEXT,
        parse_mode=ParseMode.HTML
    )

async def show_admin_contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Надсилає повідомлення з контактами адміністратора."""
    user = update.effective_user
    chat_id = update.effective_chat.id
    logger.info(f"Користувач {get_user_info(user)} запитав контакти адміна.")
    await context.bot.send_message(
        chat_id=chat_id,
        text=ADMIN_CONTACT_TEXT,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True
    )

async def cancel_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE, message: str = MSG_BOOKING_CANCELLED) -> int:
    """Завершує розмову бронювання, очищує дані, інформує користувача."""
    user = update.effective_user
    chat_id = update.effective_chat.id
    log_msg = f"Користувач {get_user_info(user)} скасував/завершив розмову бронювання."

    # Не потрібно прибирати ReplyKeyboard, вона постійна
    # # await context.bot.send_message(chat_id=chat_id, text="...", reply_markup=ReplyKeyboardRemove(), disable_notification=True)

    if update.callback_query:
        log_msg += " (через кнопку)"
        query = update.callback_query
        await query.answer()
        # Редагуємо текст повідомлення, де була інлайн-кнопка, прибираючи її
        await send_or_edit_message(context, chat_id, message, reply_markup=None)
    elif update.message:
         log_msg += " (через команду або повідомлення)"
         # Надсилаємо нове повідомлення про скасування
         await context.bot.send_message(chat_id=chat_id, text=message)

    logger.info(log_msg)
    await clear_user_data(context) # Очищаємо дані бронювання
    return ConversationHandler.END # Завершуємо ConversationHandler

async def cancel_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обробляє команду /cancel."""
    # Перевіряємо, чи є активна розмова, яку можна скасувати
    # (Це складно перевірити надійно без зберігання стану поза ConversationHandler)
    # Просто викликаємо функцію скасування
    return await cancel_conversation(update, context)

async def cancel_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обробляє натискання загальної кнопки скасування 'cancel_booking'."""
    return await cancel_conversation(update, context)


# --- Точка Входу та Обробники станів для ConversationHandler Бронювання ---

async def start_booking_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Починає процес бронювання після натискання кнопки 'Бронювання'."""
    user = update.effective_user
    chat_id = update.effective_chat.id
    logger.info(f"Користувач {get_user_info(user)} почав процес бронювання.")
    await clear_user_data(context) # Очищаємо попередні спроби
    context.user_data['user_id'] = user.id # Зберігаємо ID

    # Надсилаємо запит типу бронювання (День/Ніч) з інлайн кнопками
    sent_message = await update.message.reply_text( # Відповідаємо на повідомлення з текстом кнопки
        MSG_CHOOSE_BOOKING_TYPE,
        reply_markup=keyboards.get_booking_type_keyboard()
    )
    context.user_data['message_to_edit'] = sent_message.message_id
    context.user_data['current_state'] = SELECTING_BOOKING_TYPE
    return SELECTING_BOOKING_TYPE

# State 2: SELECTING_BOOKING_TYPE
async def handle_booking_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обробляє вибір День/Ніч."""
    query = update.callback_query
    await query.answer()
    choice = query.data # booktype_day або booktype_night
    user = update.effective_user
    chat_id = query.message.chat_id
    next_state = SELECTING_BOOKING_TYPE # Залишитись у разі помилки

    message_text = MSG_CHOOSE_ZONE
    reply_markup = keyboards.get_zone_keyboard()
    parse_mode = None # За замовчуванням HTML/Markdown не потрібен

    # Використовуємо текст з constants.py
    if choice == "booktype_day":
        context.user_data['booking_time_type'] = 'day'
        logger.info(f"Користувач {get_user_info(user)} обрав тип: День.")
        next_state = SELECTING_ZONE
    elif choice == "booktype_night":
        context.user_data['booking_time_type'] = 'night'
        logger.info(f"Користувач {get_user_info(user)} обрав тип: Ніч.")
        message_text += MSG_NIGHT_BOOKING_INFO # Додаємо інфо (тепер з HTML)
        parse_mode = ParseMode.HTML # Вказуємо HTML
        next_state = SELECTING_ZONE
    else:
        logger.warning(f"Невідомий callback у виборі типу бронювання: {choice}")
        await send_or_edit_message(context, chat_id, MSG_FALLBACK, reply_markup=keyboards.get_booking_type_keyboard())
        return next_state

    await send_or_edit_message(
        context, chat_id, message_text, reply_markup=reply_markup, parse_mode=parse_mode
    )
    context.user_data['current_state'] = next_state
    return next_state

# State 3: SELECTING_ZONE (Без змін)
async def handle_zone_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    zone_key = query.data.split('_')[1]
    user = update.effective_user
    chat_id = query.message.chat_id

    if zone_key not in ZONES:
        logger.warning(f"Отримано невірний ключ зони: {zone_key}")
        await send_or_edit_message(context, chat_id, "Сталася помилка. Спробуйте /start ще раз.")
        return await cancel_conversation(update, context)

    zone_name = ZONES[zone_key]['name']
    context.user_data['zone_key'] = zone_key
    context.user_data['zone_name'] = zone_name
    context.user_data['selected_pcs'] = []

    logger.info(f"Користувач {get_user_info(user)} обрав зону: {zone_name}")

    next_state = ENTERING_NAME

    if zone_key == "PS5":
        context.user_data['booking_type'] = 'specific'
        logger.debug("Обрано PS5, перехід до введення імені.")
        await send_or_edit_message(
             context, chat_id, f"Ви обрали зону: {zone_name}.\n{MSG_ENTER_NAME}", reply_markup=None
        )
    else:
        logger.debug("Обрано PC зону, перехід до вибору ПК/Кількість.")
        await send_or_edit_message(
            context, chat_id, f"Ви обрали зону: {zone_name}. {MSG_CHOOSE_OPTION}",
            reply_markup=keyboards.get_pc_or_quantity_keyboard()
        )
        next_state = SELECTING_PC_OR_QTY

    context.user_data['current_state'] = next_state
    return next_state

# State 4: SELECTING_PC_OR_QTY (Без змін)
async def handle_pc_or_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    choice = query.data.split('_')[1]
    zone_key = context.user_data.get('zone_key')
    user = update.effective_user
    chat_id = query.message.chat_id
    next_state = ConversationHandler.END

    if not zone_key or zone_key == 'PS5':
        logger.error("Помилка стану: Немає zone_key або це PS5 у handle_pc_or_quantity.")
        return await cancel_conversation(update, context, MSG_FALLBACK)

    if choice == "specific":
        logger.info(f"Користувач {get_user_info(user)} обрав: конкретні ПК")
        context.user_data['booking_type'] = 'specific'
        context.user_data['selected_pcs'] = []
        pc_keyboard = keyboards.get_pc_selection_keyboard(zone_key, [])
        if pc_keyboard:
            await send_or_edit_message(
                context, chat_id, MSG_CHOOSE_PC, reply_markup=pc_keyboard
            )
            next_state = SELECTING_PC
        else:
             logger.error(f"Для зони {zone_key} не вдалося створити клавіатуру ПК.")
             return await cancel_conversation(update, context, MSG_FALLBACK)

    elif choice == "quantity":
        logger.info(f"Користувач {get_user_info(user)} обрав: за кількістю")
        context.user_data['booking_type'] = 'quantity'
        await send_or_edit_message(context, chat_id, MSG_ENTER_QUANTITY, reply_markup=None)
        next_state = ENTERING_QUANTITY
    else:
        logger.warning(f"Невідомий callback у виборі ПК/Кількість: {choice}")
        await send_or_edit_message(context, chat_id, MSG_FALLBACK, reply_markup=keyboards.get_pc_or_quantity_keyboard())
        next_state = SELECTING_PC_OR_QTY

    context.user_data['current_state'] = next_state
    return next_state

# State 5: SELECTING_PC (Без змін)
async def handle_pc_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    data = query.data.split('_')
    action = data[1]
    zone_key = context.user_data.get('zone_key')
    selected_pcs = context.user_data.get('selected_pcs', [])
    user = update.effective_user
    chat_id = query.message.chat_id
    next_state = SELECTING_PC

    if not zone_key:
        logger.error("Помилка стану: Немає zone_key у handle_pc_selection.")
        return await cancel_conversation(update, context)

    if action == "TOGGLE":
        try:
            pc_number = int(data[2])
            if pc_number in selected_pcs:
                selected_pcs.remove(pc_number)
                logger.debug(f"ПК {pc_number} вилучено.")
            else:
                selected_pcs.append(pc_number)
                logger.debug(f"ПК {pc_number} додано.")
            context.user_data['selected_pcs'] = selected_pcs
            await query.edit_message_reply_markup(
                reply_markup=keyboards.get_pc_selection_keyboard(zone_key, selected_pcs)
            )
        except (IndexError, ValueError) as e:
             logger.warning(f"Помилка обробки TOGGLE ПК: {e}, data: {query.data}")

    elif action == "CONFIRM":
        if not selected_pcs:
            await context.bot.answer_callback_query(query.id, text=MSG_CHOOSE_AT_LEAST_ONE_PC, show_alert=True)
        else:
            pcs_str = ", ".join(map(str, sorted(selected_pcs)))
            logger.info(f"Користувач {get_user_info(user)} підтвердив вибір ПК: {pcs_str}")
            await send_or_edit_message(
                context, chat_id, f"Ви обрали ПК: {pcs_str}.\n{MSG_ENTER_NAME}", reply_markup=None
            )
            next_state = ENTERING_NAME

    context.user_data['current_state'] = next_state
    return next_state

# State 6: ENTERING_QUANTITY (Без змін)
async def handle_quantity_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_input = update.message.text
    user = update.effective_user
    chat_id = update.effective_chat.id
    next_state = ENTERING_QUANTITY

    try:
        quantity = int(user_input)
        if quantity <= 0:
            raise ValueError("Кількість має бути більше нуля")
        context.user_data['quantity'] = quantity
        logger.info(f"Користувач {get_user_info(user)} ввів кількість: {quantity}")
        sent_message = await update.message.reply_text(text=MSG_ENTER_NAME)
        context.user_data['message_to_edit'] = sent_message.message_id
        next_state = ENTERING_NAME
    except (ValueError, TypeError):
        logger.warning(f"Користувач {get_user_info(user)} ввів невірну кількість: {user_input}")
        await update.message.reply_text(MSG_INVALID_QUANTITY)

    context.user_data['current_state'] = next_state
    return next_state

# State 7: ENTERING_NAME (Без змін)
async def handle_name_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_name = update.message.text.strip()
    user = update.effective_user
    chat_id = update.effective_chat.id
    next_state = ENTERING_NAME

    if not user_name:
        logger.warning(f"Користувач {get_user_info(user)} надіслав порожнє ім'я.")
        await update.message.reply_text("Будь ласка, введіть ваше ім'я.")
        return next_state

    context.user_data['user_name'] = user_name
    logger.info(f"Користувач {get_user_info(user)} ввів ім'я: {user_name}")

    sent_message = await update.message.reply_text(
        MSG_CHOOSE_DATE,
        reply_markup=keyboards.get_calendar_keyboard()
    )
    context.user_data['message_to_edit'] = sent_message.message_id
    next_state = SELECTING_DATE

    context.user_data['current_state'] = next_state
    return next_state

# State 8: SELECTING_DATE (Без змін)
async def handle_date_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    user = update.effective_user
    chat_id = query.message.chat_id
    next_state = SELECTING_DATE

    date_selected, message_text = await calendar_logic.process_calendar_selection(update, context)

    if date_selected is True:
        selected_date = context.user_data['selected_date']
        logger.info(f"Користувач {get_user_info(user)} обрав дату: {selected_date}")
        booking_time_type = context.user_data.get('booking_time_type', 'day')
        context.user_data.pop('message_to_edit', None) # Скидаємо ID відредагованого повідомлення

        if booking_time_type == 'day':
            logger.debug("Тип 'День', перехід до вибору часу початку.")
            sent_message = await context.bot.send_message(
                chat_id=chat_id, text=MSG_CHOOSE_START_TIME,
                reply_markup=keyboards.get_start_time_keyboard()
            )
            context.user_data['message_to_edit'] = sent_message.message_id
            next_state = SELECTING_START_TIME
        else: # 'night'
             logger.debug("Тип 'Ніч', перехід до запиту телефону.")
             reply_keyboard = [[KeyboardButton(BTN_SHARE_PHONE, request_contact=True)]]
             reply_markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
             await context.bot.send_message(
                 chat_id=chat_id, text=MSG_REQUEST_PHONE, reply_markup=reply_markup
             )
             inline_markup = keyboards.get_phone_step_inline_keyboard(booking_time_type)
             sent_inline_msg = await context.bot.send_message(
                 chat_id=chat_id, text="Або:", reply_markup=inline_markup
             )
             context.user_data['message_to_edit'] = sent_inline_msg.message_id
             next_state = SHARING_PHONE

    elif date_selected is False:
        logger.debug(f"Користувач {get_user_info(user)} перейшов по календарю.")
    else:
        logger.warning(f"Помилка обробки календаря для {get_user_info(user)}.")

    context.user_data['current_state'] = next_state
    return next_state

# State 9: SELECTING_START_TIME (Без змін)
async def handle_start_time_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    start_time = query.data.split('_')[1]
    context.user_data['start_time'] = start_time
    user = update.effective_user
    chat_id = query.message.chat_id
    next_state = SELECTING_START_TIME

    logger.info(f"Користувач {get_user_info(user)} обрав час початку: {start_time}")
    end_time_keyboard = keyboards.get_end_time_keyboard(start_time)

    if end_time_keyboard:
        await send_or_edit_message(
            context, chat_id, f"Час початку: {start_time}. {MSG_CHOOSE_END_TIME}",
            reply_markup=end_time_keyboard
        )
        next_state = SELECTING_END_TIME
    else:
        logger.warning(f"Немає доступних слотів часу завершення після {start_time}")
        await send_or_edit_message(
            context, chat_id, f"{MSG_INVALID_END_TIME} Немає слотів завершення для {start_time}.",
            reply_markup=keyboards.get_start_time_keyboard()
        )

    context.user_data['current_state'] = next_state
    return next_state

# State 10: SELECTING_END_TIME (Без змін)
async def handle_end_time_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    end_time = query.data.split('_')[1]
    start_time = context.user_data.get('start_time')
    user = update.effective_user
    chat_id = query.message.chat_id
    next_state = SELECTING_END_TIME

    if not start_time or end_time <= start_time:
        logger.warning(f"Користувач {get_user_info(user)} обрав невірний час завершення: {end_time} (початок {start_time})")
        await send_or_edit_message(
             context, chat_id, MSG_INVALID_END_TIME,
             reply_markup=keyboards.get_end_time_keyboard(start_time)
        )
        return next_state

    context.user_data['end_time'] = end_time
    logger.info(f"Користувач {get_user_info(user)} обрав час завершення: {end_time}")

    logger.debug("Перехід до запиту телефону.")
    reply_keyboard = [[KeyboardButton(BTN_SHARE_PHONE, request_contact=True)]]
    reply_markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
    await query.edit_message_reply_markup(reply_markup=None)
    await query.edit_message_text(f"Час обрано: {start_time} - {end_time}")
    await context.bot.send_message(chat_id=chat_id, text=MSG_REQUEST_PHONE, reply_markup=reply_markup)
    booking_time_type = context.user_data.get('booking_time_type', 'day')
    inline_markup = keyboards.get_phone_step_inline_keyboard(booking_time_type)
    sent_inline_msg = await context.bot.send_message(chat_id=chat_id, text="Або:", reply_markup=inline_markup)
    context.user_data['message_to_edit'] = sent_inline_msg.message_id

    next_state = SHARING_PHONE
    context.user_data['current_state'] = next_state
    return next_state

# State 11: SHARING_PHONE (Змінено: використовуємо reply_text для відновлення клавіатури)
async def handle_phone_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    chat_id = update.effective_chat.id
    contact = update.message.contact
    text_input = update.message.text
    phone_number = None
    next_state = SHARING_PHONE

    context.user_data.pop('message_to_edit', None) # Скидаємо ID інлайн-повідомлення "Або:"

    if contact:
        if contact.user_id != user.id:
            logger.warning(f"Користувач {get_user_info(user)} надіслав чужий контакт.")
            await update.message.reply_text(MSG_CONTACT_NOT_YOURS, reply_markup=ReplyKeyboardRemove())
            return await cancel_conversation(update, context, "Сталася помилка з контактом. Спробуйте /start ще раз.")

        phone_number = contact.phone_number
        context.user_data['user_phone'] = phone_number
        logger.info(f"Користувач {get_user_info(user)} поділився контактом: {phone_number}")

        # Замість ReplyKeyboardRemove() надсилаємо текст і нашу постійну клавіатуру
        await update.message.reply_text(
            "Телефон отримано!",
            reply_markup=keyboards.get_persistent_main_keyboard() # <-- Показуємо головне меню
        )

    elif text_input and text_input != BTN_SHARE_PHONE:
         logger.warning(f"Користувач {get_user_info(user)} ввів текст замість кнопки: {text_input}")
         await update.message.reply_text(MSG_PLEASE_PRESS_BUTTON)
         # Повторно надсилаємо запит контакту
         reply_keyboard = [[KeyboardButton(BTN_SHARE_PHONE, request_contact=True)]]
         reply_markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
         await context.bot.send_message(chat_id=chat_id, text=MSG_REQUEST_PHONE, reply_markup=reply_markup)
         booking_time_type = context.user_data.get('booking_time_type', 'day')
         inline_markup = keyboards.get_phone_step_inline_keyboard(booking_time_type)
         sent_inline_msg = await context.bot.send_message(chat_id=chat_id, text="Або:", reply_markup=inline_markup)
         context.user_data['message_to_edit'] = sent_inline_msg.message_id
         return SHARING_PHONE

    else: # Не контакт і не очікуваний текст
        logger.warning(f"Отримано неочікуване повідомлення замість контакту від {get_user_info(user)}")
        await update.message.reply_text(MSG_PLEASE_PRESS_BUTTON)
         # Повторно надсилаємо запит контакту
        reply_keyboard = [[KeyboardButton(BTN_SHARE_PHONE, request_contact=True)]]
        reply_markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
        await context.bot.send_message(chat_id=chat_id, text=MSG_REQUEST_PHONE, reply_markup=reply_markup)
        booking_time_type = context.user_data.get('booking_time_type', 'day')
        inline_markup = keyboards.get_phone_step_inline_keyboard(booking_time_type)
        sent_inline_msg = await context.bot.send_message(chat_id=chat_id, text="Або:", reply_markup=inline_markup)
        context.user_data['message_to_edit'] = sent_inline_msg.message_id
        return SHARING_PHONE

    # Якщо отримали номер телефону
    if phone_number:
        logger.debug("Перехід до фінального підтвердження.")
        details_text, parse_mode = format_booking_details(context.user_data)
        # Надсилаємо нове повідомлення з деталями та кнопками підтвердження (Inline)
        sent_message = await context.bot.send_message(
            chat_id=chat_id,
            text=f"{MSG_BOOKING_DETAILS}\n\n{details_text}\n\n{MSG_CONFIRM_BOOKING}",
            reply_markup=keyboards.get_confirmation_keyboard(),
            parse_mode=parse_mode
        )
        context.user_data['message_to_edit'] = sent_message.message_id
        next_state = CONFIRMATION

    context.user_data['current_state'] = next_state
    return next_state

# State 12: CONFIRMATION (Без змін)
async def handle_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    choice = query.data.split('_')[1] # 'YES'
    user = update.effective_user
    chat_id = query.message.chat_id

    if choice == "YES":
        logger.info(f"Користувач {get_user_info(user)} підтвердив бронювання.")
        final_message, parse_mode = format_booking_details(context.user_data)
        message_id_to_edit = context.user_data.get('message_to_edit')

        try:
            await context.bot.send_message(
                chat_id=GROUP_CHAT_ID, text=final_message, parse_mode=parse_mode,
                disable_web_page_preview=True
            )
            logger.info(f"Повідомлення про бронювання надіслано в групу {GROUP_CHAT_ID}")

            if message_id_to_edit: # Прибираємо кнопки Так/Ні
                try:
                    await context.bot.edit_message_reply_markup(
                        chat_id=chat_id, message_id=message_id_to_edit, reply_markup=None
                    )
                except Exception as e:
                    logger.warning(f"Не вдалося прибрати кнопки з повідомлення {message_id_to_edit}: {e}")

            await context.bot.send_message(chat_id=chat_id, text=MSG_THANKS_REQUEST_SENT)

        except Exception as e:
            logger.error(f"Не вдалося надіслати повідомлення в групу {GROUP_CHAT_ID}: {e}")
            await send_or_edit_message(context, chat_id, MSG_ERROR_SENDING, reply_markup=None)

        await clear_user_data(context)
        return ConversationHandler.END

    # "NO" обробляється fallback'ом cancel_booking

# --- Обробники кнопок "Назад" --- (Без змін)
async def handle_back_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обробляє різні кнопки 'Назад'."""
    query = update.callback_query
    await query.answer()
    action = query.data
    user = update.effective_user
    chat_id = query.message.chat_id
    logger.debug(f"Натиснуто кнопку 'Назад': {action}")
    next_state = ConversationHandler.END

    if action == "back_to_booking_type":
         await send_or_edit_message(
            context, chat_id, MSG_CHOOSE_BOOKING_TYPE, keyboards.get_booking_type_keyboard()
         )
         next_state = SELECTING_BOOKING_TYPE
    elif action == "back_to_zone_selection":
         message_text = MSG_CHOOSE_ZONE
         parse_mode = None
         if context.user_data.get('booking_time_type') == 'night':
             message_text += MSG_NIGHT_BOOKING_INFO
             parse_mode = ParseMode.HTML
         await send_or_edit_message(
             context, chat_id, message_text, keyboards.get_zone_keyboard(), parse_mode=parse_mode
         )
         next_state = SELECTING_ZONE
    elif action == "back_to_pc_or_qty":
         zone_name = context.user_data.get('zone_name', 'обраній зоні')
         await send_or_edit_message(
             context, chat_id, f"Ви знаходитесь у зоні: {zone_name}. {MSG_CHOOSE_OPTION}",
             reply_markup=keyboards.get_pc_or_quantity_keyboard()
         )
         next_state = SELECTING_PC_OR_QTY
    elif action == "back_to_date_selection":
         context.user_data.pop('message_to_edit', None)
         # Потрібно відправити нове повідомлення, оскільки ми не знаємо, яке редагувати
         sent_message = await context.bot.send_message(
             chat_id=chat_id, text=MSG_CHOOSE_DATE, reply_markup=keyboards.get_calendar_keyboard()
         )
         context.user_data['message_to_edit'] = sent_message.message_id
         next_state = SELECTING_DATE
    elif action == "back_to_start_time":
         await send_or_edit_message(
             context, chat_id, MSG_CHOOSE_START_TIME, keyboards.get_start_time_keyboard()
         )
         next_state = SELECTING_START_TIME
    elif action == "back_to_end_time":
         start_time = context.user_data.get('start_time')
         end_time_keyboard = keyboards.get_end_time_keyboard(start_time)
         if end_time_keyboard:
             await send_or_edit_message(
                 context, chat_id, f"Час початку: {start_time}. {MSG_CHOOSE_END_TIME}",
                 reply_markup=end_time_keyboard
             )
             next_state = SELECTING_END_TIME
         else:
              await send_or_edit_message(
                 context, chat_id, MSG_CHOOSE_START_TIME, keyboards.get_start_time_keyboard()
             )
              next_state = SELECTING_START_TIME
    else:
        logger.warning(f"Невідома дія для кнопки 'Назад': {action}. Завершую розмову.")
        await send_or_edit_message(context, chat_id, MSG_FALLBACK, reply_markup=None)
        return await cancel_conversation(update, context)

    context.user_data['current_state'] = next_state
    logger.debug(f"Перехід у стан {next_state} після кнопки 'Назад'")
    return next_state


# --- Обробник для непередбачених відповідей --- (Без змін)
async def fallback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обробляє повідомлення, які не відповідають очікуваному стану розмови."""
    user = update.effective_user
    current_state = context.user_data.get('current_state', 'Невідомий')
    log_msg = f"Fallback handler спрацював для {get_user_info(user)} у стані {current_state}."

    # Якщо це текстове повідомлення, яке *не є* кнопкою головного меню,
    # і бот *не очікує* текст (тобто не в станах ENTERING_QUANTITY, ENTERING_NAME)
    if (update.message and update.message.text and
        update.message.text not in [BTN_BOOKING, BTN_PRICES, BTN_CONTACT_ADMIN] and
        current_state not in [ENTERING_QUANTITY, ENTERING_NAME]):
         log_msg += f" Текст: {update.message.text} (неочікуваний)"
         logger.warning(log_msg)
         await update.message.reply_text("Будь ласка, використовуйте кнопки для навігації.")
         return current_state # Залишаємо поточний стан розмови

    # Інші неочікувані дії (не текст, не колбек)
    if update.message:
        log_msg += f" Тип: {update.message.effective_attachment_type or 'Text'}, Текст: {update.message.text}"
    elif update.callback_query:
         # Неочікуваний колбек (не кнопка "Назад", не "Скасувати")
         log_msg += f" Неочікуваний Callback data: {update.callback_query.data}"
         await update.callback_query.answer("Неочікувана дія.", show_alert=True)
    else:
        log_msg += " Невідомий тип оновлення."

    logger.warning(log_msg)
    # Завершуємо розмову при незрозумілих діях
    await context.bot.send_message(chat_id=update.effective_chat.id, text=MSG_FALLBACK)
    return await cancel_conversation(update, context) # Завершуємо розмову