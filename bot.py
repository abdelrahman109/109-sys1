import os
import logging
import sqlite3
from dotenv import load_dotenv
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not TOKEN:
    logger.error("TELEGRAM_BOT_TOKEN not found")
    exit(1)

bot = telebot.TeleBot(TOKEN)
DB_PATH = os.path.join(os.path.dirname(__file__), 'instance', 'app.db')
user_registration_state = {}

def main_menu(user_id=None):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    is_registered = False
    if user_id:
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("SELECT id FROM users WHERE telegram_id = ?", (user_id,))
            is_registered = c.fetchone() is not None
            conn.close()
        except:
            pass
    
    if is_registered:
        btn1 = KeyboardButton("💰 تبرع")
        btn2 = KeyboardButton("📊 تقاريري")
        btn3 = KeyboardButton("👤 ملفي الشخصي")
        btn4 = KeyboardButton("📜 شهاداتي")
        btn5 = KeyboardButton("🔗 ربط التيليجرام")
        markup.add(btn1, btn2, btn3, btn4, btn5)
    else:
        markup.add(KeyboardButton("📝 تسجيل حساب"))
    return markup

def cancel_markup():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("❌ إلغاء"))
    return markup

@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.chat.id
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT full_name FROM users WHERE telegram_id = ?", (user_id,))
        user = c.fetchone()
        conn.close()
        
        if user:
            bot.send_message(user_id, f"👋 مرحباً بعودتك {user[0]}!", reply_markup=main_menu(user_id))
        else:
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("📝 تسجيل حساب جديد", callback_data="register"))
            bot.send_message(user_id, "👋 مرحباً بك في نظام الدفعة 109\n\nاضغط الزر للتسجيل:", reply_markup=markup)
    except Exception as e:
        logger.error(f"Start error: {e}")
        bot.send_message(user_id, "حدث خطأ، يرجى المحاولة لاحقاً")

@bot.message_handler(func=lambda m: m.text == "📝 تسجيل حساب")
def register_start(message):
    user_id = message.chat.id
    msg = bot.send_message(user_id, "📝 أدخل رقم هاتفك:", reply_markup=cancel_markup())
    bot.register_next_step_handler(msg, register_phone)

def register_phone(message):
    user_id = message.chat.id
    if message.text == "❌ إلغاء":
        bot.send_message(user_id, "تم الإلغاء", reply_markup=main_menu(user_id))
        return
    phone = message.text.strip()
    if not phone.isdigit() or len(phone) < 10:
        msg = bot.send_message(user_id, "⚠️ رقم غير صالح، حاول مرة أخرى:", reply_markup=cancel_markup())
        bot.register_next_step_handler(msg, register_phone)
        return
    user_registration_state[user_id] = {'phone': phone}
    msg = bot.send_message(user_id, "🔐 أدخل كلمة المرور (6 أحرف على الأقل):", reply_markup=cancel_markup())
    bot.register_next_step_handler(msg, register_password)

def register_password(message):
    user_id = message.chat.id
    if message.text == "❌ إلغاء":
        bot.send_message(user_id, "تم الإلغاء", reply_markup=main_menu(user_id))
        return
    password = message.text.strip()
    if len(password) < 6:
        msg = bot.send_message(user_id, "⚠️ كلمة المرور قصيرة، حاول مرة أخرى:", reply_markup=cancel_markup())
        bot.register_next_step_handler(msg, register_password)
        return
    user_registration_state[user_id]['password'] = password
    msg = bot.send_message(user_id, "👤 أدخل اسمك الكامل:", reply_markup=cancel_markup())
    bot.register_next_step_handler(msg, register_fullname)

def register_fullname(message):
    user_id = message.chat.id
    if message.text == "❌ إلغاء":
        bot.send_message(user_id, "تم الإلغاء", reply_markup=main_menu(user_id))
        return
    fullname = message.text.strip()
    if len(fullname) < 3:
        msg = bot.send_message(user_id, "⚠️ الاسم قصير، حاول مرة أخرى:", reply_markup=cancel_markup())
        bot.register_next_step_handler(msg, register_fullname)
        return
    
    phone = user_registration_state[user_id]['phone']
    password = user_registration_state[user_id]['password']
    
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, phone TEXT UNIQUE, password TEXT, full_name TEXT, telegram_id INTEGER, role TEXT DEFAULT 'user', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
        c.execute("INSERT INTO users (phone, password, full_name, telegram_id) VALUES (?, ?, ?, ?)", (phone, password, fullname, user_id))
        conn.commit()
        conn.close()
        bot.send_message(user_id, f"✅ تم التسجيل بنجاح!\n\nالاسم: {fullname}\nالهاتف: {phone}", reply_markup=main_menu(user_id))
        del user_registration_state[user_id]
    except Exception as e:
        bot.send_message(user_id, f"❌ خطأ: {e}", reply_markup=main_menu(user_id))

@bot.message_handler(func=lambda m: m.text == "💰 تبرع")
def donate_button(message):
    bot.send_message(message.chat.id, "💰 للتبرع، يرجى زيارة:\nhttp://34.205.237.226/donate")

@bot.message_handler(func=lambda m: m.text == "📊 تقاريري")
def reports_button(message):
    bot.send_message(message.chat.id, "📊 تقاريرك:\nhttp://34.205.237.226/reports")

@bot.message_handler(func=lambda m: m.text == "👤 ملفي الشخصي")
def profile_button(message):
    user_id = message.chat.id
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT full_name, phone FROM users WHERE telegram_id = ?", (user_id,))
        user = c.fetchone()
        conn.close()
        if user:
            bot.send_message(user_id, f"👤 ملفي الشخصي\n\nالاسم: {user[0]}\nالهاتف: {user[1]}")
        else:
            bot.send_message(user_id, "❌ لم يتم العثور على بياناتك")
    except:
        bot.send_message(user_id, "حدث خطأ")

@bot.message_handler(func=lambda m: m.text == "📜 شهاداتي")
def certificates_button(message):
    bot.send_message(message.chat.id, "📜 شهادات التبرع:\nhttp://34.205.237.226/certificates")

@bot.message_handler(func=lambda m: m.text == "🔗 ربط التيليجرام")
def link_button(message):
    user_id = message.chat.id
    msg = bot.send_message(user_id, "🔗 أدخل رقم هاتفك المسجل في الموقع:", reply_markup=cancel_markup())
    bot.register_next_step_handler(msg, link_phone)

def link_phone(message):
    user_id = message.chat.id
    if message.text == "❌ إلغاء":
        bot.send_message(user_id, "تم الإلغاء", reply_markup=main_menu(user_id))
        return
    phone = message.text.strip()
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("UPDATE users SET telegram_id = ? WHERE phone = ?", (user_id, phone))
        conn.commit()
        if c.rowcount > 0:
            bot.send_message(user_id, "✅ تم ربط حسابك بنجاح!", reply_markup=main_menu(user_id))
        else:
            bot.send_message(user_id, "❌ لم يتم العثور على هذا الرقم", reply_markup=main_menu(user_id))
        conn.close()
    except:
        bot.send_message(user_id, "حدث خطأ", reply_markup=main_menu(user_id))

@bot.message_handler(func=lambda m: m.text == "❌ إلغاء")
def cancel_button(message):
    user_id = message.chat.id
    if user_id in user_registration_state:
        del user_registration_state[user_id]
    bot.send_message(user_id, "❌ تم الإلغاء", reply_markup=main_menu(user_id))

@bot.callback_query_handler(func=lambda call: call.data == "register")
def handle_register(call):
    register_start(call.message)
    bot.answer_callback_query(call.id)

if __name__ == '__main__':
    logger.info("Bot started...")
    bot.infinity_polling()
