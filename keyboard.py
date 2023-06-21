from pyrogram.types import ReplyKeyboardMarkup, KeyboardButton

start = ReplyKeyboardMarkup([
    [KeyboardButton("ارسال شماره", request_contact=True)]
])
start_keyboard = ReplyKeyboardMarkup([
    ["👤حساب کاربری"],
    ["📎لینک های تولید شده"],
    ["💰خرید ترافیک", '👥دعوت از دوستان'],
    ["⚠قوانین", "❓راهنما"],
], resize_keyboard=True)

admin_keyboard = ReplyKeyboardMarkup([
    ['تغییر رمز عبور', 'شارژ حساب', 'لیست کاربران'],
    ['بازگشت']
], resize_keyboard=True)
