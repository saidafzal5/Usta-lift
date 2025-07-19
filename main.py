import logging
from aiogram import Bot, Dispatcher, types, executor
import gspread
from oauth2client.service_account import ServiceAccountCredentials

import os
from dotenv import load_dotenv
load_dotenv()
API_TOKEN = os.getenv("TELEGRAM_TOKEN")
# Update this line with your bot token

# Google Sheets settings
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive"
]
creds = ServiceAccountCredentials.from_json_keyfile_name("carbon-sight-455100-t3-5417d7a17900.json", scope)
client = gspread.authorize(creds)

# File names or IDs
sheet = client.open("LiftServiceDB")
sh_lifts = sheet.worksheet("Lifts")
sh_xodim = sheet.worksheet("Xodimlar")
sh_buyurtma = sheet.worksheet("Buyurtmalar")

# Logger
logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# === START command ===
@dp.message_handler(commands=['start'])
async def start_cmd(message: types.Message):
    telegram_id = str(message.from_user.id)
    user_rows = sh_xodim.get_all_records()
    for row in user_rows:
        if str(row['Telegram ID']) == telegram_id:
            await message.answer(f"Salom, {row['Ism']}! Siz tizimga ulandingiz.")
            return
    await message.answer("Siz tizimda ro‘yxatdan o‘tmagansiz. Iltimos, admin bilan bog‘laning.")

# === TASKS command ===
@dp.message_handler(commands=['vazifalar'])
async def vazifalar_cmd(message: types.Message):
    telegram_id = str(message.from_user.id)
    user_rows = sh_xodim.get_all_records()
    ism = None
    for row in user_rows:
        if str(row['Telegram ID']) == telegram_id:
            ism = row['Ism']
            break
    if not ism:
        await message.answer("Siz ro‘yxatda yo‘qsiz.")
        return

    vazifalar = sh_buyurtma.get_all_records()
    matn = "\u270D Sizga biriktirilgan xizmatlar:\n"
    for v in vazifalar:
        if v['Xodim'] == ism and v['Status'].lower() != "bajarilgan":
            matn += f"\nLift ID: {v['Lift ID']}\nSana: {v['Sana']}\nStatus: {v['Status']}\n---"
    await message.answer(matn)

# === HANDLE PHOTO submission ===
@dp.message_handler(content_types=['photo'])
async def handle_photo(message: types.Message):
    caption = message.caption  # Format: LiftID;Vaqt;Lokatsiya
    telegram_id = str(message.from_user.id)
    user_rows = sh_xodim.get_all_records()
    ism = None
    for row in user_rows:
        if str(row['Telegram ID']) == telegram_id:
            ism = row['Ism']
            break
    if not ism:
        await message.answer("Siz ro‘yxatda yo‘qsiz.")
        return

    try:
        lift_id, vaqt, lok = caption.split(";")
        cell = sh_buyurtma.find(lift_id)
        row = cell.row
        sh_buyurtma.update_cell(row, 4, ism)          # Xodim ustuni
        sh_buyurtma.update_cell(row, 5, vaqt)         # Vaqt ustuni
        sh_buyurtma.update_cell(row, 6, "Bajarilgan") # Status ustuni
        sh_buyurtma.update_cell(row, 7, lok)          # Lokatsiya ustuni (agar mavjud bo‘lsa)
        await message.answer("Hisobot qabul qilindi, rahmat!")
    except Exception as e:
        logging.error(f"Error processing photo: {str(e)}")
        await message.answer("Hisobot yuborishda xatolik. Iltimos, format: LiftID;Vaqt;Lokatsiya.")

# Start the bot
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
