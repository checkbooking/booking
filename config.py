# config.py
import os
from dotenv import load_dotenv # Додаємо для локального тестування (опціонально)

# Завантажити змінні з .env файлу для локальної розробки (опціонально)
# Створіть файл .env поруч з config.py і додайте туди:
# BOT_TOKEN=ВАШ_БОТ_ТОКЕН
# GROUP_CHAT_ID=ВАШ_ID_ГРУПИ
load_dotenv()

# Читаємо змінні оточення
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_CHAT_ID_STR = os.getenv("GROUP_CHAT_ID") # Читаємо як рядок

# Перевірка, чи змінні завантажено (для надійності)
if BOT_TOKEN is None:
    print("!!! ПОМИЛКА: Змінна оточення BOT_TOKEN не встановлена!")
    # Можна або викликати виняток, або встановити значення за замовчуванням для локального тестування
    # raise ValueError("Змінна оточення BOT_TOKEN не встановлена!")
    BOT_TOKEN = "ЗАМІНИ_МЕНЕ_ЯКЩО_НЕМАЄ_ENV" # Тільки для тестування!

if GROUP_CHAT_ID_STR is None:
    print("!!! ПОМИЛКА: Змінна оточення GROUP_CHAT_ID не встановлена!")
    # raise ValueError("Змінна оточення GROUP_CHAT_ID не встановлена!")
    GROUP_CHAT_ID = -1002259140468 # Встановіть якесь тестове значення або ID вашої тестової групи
else:
     try:
         # Перетворюємо рядок на ціле число
         GROUP_CHAT_ID = int(GROUP_CHAT_ID_STR)
     except ValueError:
          print(f"!!! ПОМИЛКА: GROUP_CHAT_ID ('{GROUP_CHAT_ID_STR}') не є дійсним числом!")
          raise ValueError(f"GROUP_CHAT_ID ('{GROUP_CHAT_ID_STR}') не є дійсним числом!")