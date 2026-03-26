import os
import logging
import sqlite3
from dotenv import load_dotenv
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# تحميل المتغيرات البيئية
load_dotenv()

# إعداد التسجيل
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# توكن البوت
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not TOKEN:
    logger.error("TELEGRAM_BOT_TOKEN not found in environment variables")
    exit(1)

bot = telebot.TeleBot(TOKEN)

# مسار قاعدة البيانات
DB_PATH = os.path.join(os.path.dirname(__file__), 'instance', 'app.db')

# قاموس لتتبع حالة المستخدمين أثناء التسجيل
user_registration_state = {}

# التأكد من وجود مجلد instance
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

# ==================== لوحات المفاتيح (الأزرار) ====================

def main_menu(user_id=None):
    """القائمة الرئيسية مع أزرار ثابتة"""
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    
    # التحقق إذا كان المستخدم مسجلاً
    is_registered = False
    if user_id:
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            # التحقق من وجود جدول users
            c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
            if c.fetchone():
                c.execute("SELECT id FROM users WHERE telegram_id = ?", (user_id,))
                is_registered = c.fetchone() is not None
            conn.close()
        except Exception as e:
            logger.error(f"Database error in main_menu: {e}")
    
    if is_registered:
        # قائمة المستخدم المسجل
        btn1 = KeyboardButton("💰 تبرع")
        btn2 = KeyboardButton("📊 تقاريري")
        btn3 = KeyboardButton("👤 ملفي الشخصي")
        btn4 = KeyboardButton("📜 شهاداتي")
        btn5 = KeyboardButton("🔗 ربط التيليجرام")
        markup.add(btn1, btn2, btn3, btn4, btn5)
    else:
        # قائمة الزائر
        btn1 = KeyboardButton("📝 تسجيل حساب")
        markup.add(btn1)
    
    return markup

def cancel_markup():
    """لوحة تحتوي زر إلغاء فقط"""
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("❌ إلغاء"))
    return markup

# ==================== أوامر البوت ====================

@bot.message_handler(commands=['start'])
def start_command(message):
    """معالجة أمر /start"""
    user_id = message.chat.id
    username = message.from_user.username or "لا يوجد"
    
    logger.info(f"User {user_id} (@{username}) started the bot")
    
    try:
        # التأكد من وجود قاعدة البيانات والجدول
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # إنشاء جدول users إذا لم يكن موجوداً
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phone TEXT UNIQUE,
                password TEXT,
                full_name TEXT,
                email TEXT,
                telegram_id INTEGER,
                role TEXT DEFAULT 'user',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active INTEGER DEFAULT 1
            )
        ''')
        conn.commit()
        
        # التحقق من وجود المستخدم
        c.execute("SELECT full_name, phone FROM users WHERE telegram_id = ?", (user_id,))
        user = c.fetchone()
        conn.close()
        
        if user:
            # مستخدم مسجل مسبقاً
            welcome_msg = (
                f"👋 *مرحباً بعودتك {user[0]}!*\n\n"
                f"📞 رقم هاتفك المسجل: `{user[1]}`\n\n"
                "يمكنك استخدام الأزرار أدناه للتنقل في النظام."
            )
            bot.send_message(
                user_id,
                welcome_msg,
                parse_mode='Markdown',
                reply_markup=main_menu(user_id)
            )
        else:
            # مستخدم غير مسجل
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("📝 تسجيل حساب جديد", callback_data="register"))
            bot.send_message(
                user_id,
                "👋 *مرحباً بك في نظام دعم الدفعة 109*\n\n"
                "هذا البوت يساعدك في:\n"
                "• تقديم التبرعات\n"
                "• متابعة تقاريرك\n"
                "• استلام الشهادات\n\n"
                "يبدو أنك غير مسجل بعد. اضغط الزر أدناه لتسجيل حسابك.",
                parse_mode='Markdown',
                reply_markup=markup
            )
    except Exception as e:
        logger.error(f"Error in start_command: {e}")
        bot.send_message(user_id, f"❌ حدث خطأ: {e}")

@bot.message_handler(commands=['help'])
def help_command(message):
    """معالجة أمر /help"""
    help_text = (
        "📋 *قائمة الأوامر المتاحة:*\n\n"
        "/start - بدء البوت والقائمة الرئيسية\n"
        "/help - عرض هذه المساعدة\n"
        "/id - عرض معرفك في التيليجرام\n"
        "/cancel - إلغاء العملية الحالية\n\n"
        "*الخدمات المتاحة:*\n"
        "• تسجيل حساب جديد\n"
        "• تقديم تبرعات\n"
        "• عرض التقارير\n"
        "• تحميل شهادات التبرع\n"
        "• ربط حساب التيليجرام"
    )
    bot.send_message(message.chat.id, help_text, parse_mode='Markdown')

@bot.message_handler(commands=['id'])
def id_command(message):
    """معالجة أمر /id"""
    user_id = message.chat.id
    bot.send_message(
        user_id,
        f"🆔 *معرفك في التيليجرام:*\n`{user_id}`",
        parse_mode='Markdown'
    )

@bot.message_handler(commands=['cancel'])
def cancel_command(message):
    """إلغاء العملية الحالية"""
    user_id = message.chat.id
    if user_id in user_registration_state:
        del user_registration_state[user_id]
    bot.send_message(
        user_id,
        "❌ تم إلغاء العملية.",
        reply_markup=main_menu(user_id)
    )

# ==================== معالجة الأزرار والرسائل ====================

@bot.message_handler(func=lambda message: message.text == "📝 تسجيل حساب")
def register_button(message):
    """بدء عملية التسجيل"""
    register_start(message)

@bot.message_handler(func=lambda message: message.text == "💰 تبرع")
def donate_button(message):
    """بدء عملية التبرع"""
    user_id = message.chat.id
    bot.send_message(
        user_id,
        "💰 *تقديم تبرع*\n\n"
        "للتبرع، يرجى الدخول إلى رابط الويب:\n"
        "http://34.205.237.226/donate\n\n"
        "أو يمكنك التبرع عبر تحويل بنكي ثم رفع الإيصال من الموقع.",
        parse_mode='Markdown'
    )

@bot.message_handler(func=lambda message: message.text == "📊 تقاريري")
def reports_button(message):
    """عرض التقارير"""
    user_id = message.chat.id
    bot.send_message(
        user_id,
        "📊 *تقاريري*\n\n"
        "لعرض تقاريرك، يرجى الدخول إلى:\n"
        "http://34.205.237.226/reports\n\n"
        "يمكنك هناك تحميل تقارير CSV, Excel, PDF.",
        parse_mode='Markdown'
    )

@bot.message_handler(func=lambda message: message.text == "👤 ملفي الشخصي")
def profile_button(message):
    """عرض الملف الشخصي"""
    user_id = message.chat.id
    
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""
            SELECT full_name, phone, email, created_at 
            FROM users 
            WHERE telegram_id = ?
        """, (user_id,))
        user = c.fetchone()
        conn.close()
        
        if user:
            profile_text = (
                f"👤 *ملفي الشخصي*\n\n"
                f"📛 الاسم: {user[0]}\n"
                f"📞 الهاتف: {user[1]}\n"
                f"📧 البريد: {user[2] or 'غير مضاف'}\n"
                f"📅 تاريخ التسجيل: {user[3]}\n\n"
                "يمكنك تعديل بياناتك من الموقع الإلكتروني."
            )
            bot.send_message(user_id, profile_text, parse_mode='Markdown')
        else:
            bot.send_message(user_id, "❌ لم يتم العثور على بياناتك.")
    except Exception as e:
        logger.error(f"Profile error: {e}")
        bot.send_message(user_id, f"❌ حدث خطأ: {e}")

@bot.message_handler(func=lambda message: message.text == "📜 شهاداتي")
def certificates_button(message):
    """عرض شهادات التبرع"""
    user_id = message.chat.id
    bot.send_message(
        user_id,
        "📜 *شهادات التبرع*\n\n"
        "لتحميل شهادات التبرع، يرجى الدخول إلى:\n"
        "http://34.205.237.226/certificates\n\n"
        "جميع الشهادات متاحة بصيغة PDF.",
        parse_mode='Markdown'
    )

@bot.message_handler(func=lambda message: message.text == "🔗 ربط التيليجرام")
def link_telegram_button(message):
    """ربط حساب التيليجرام (إذا كان مسجلاً من الويب)"""
    user_id = message.chat.id
    
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # تحقق إذا كان المستخدم لديه حساب في النظام
        c.execute("SELECT id FROM users WHERE telegram_id = ?", (user_id,))
        existing = c.fetchone()
        
        if existing:
            bot.send_message(user_id, "✅ حسابك مرتبط بالفعل!")
        else:
            # طلب رقم الهاتف للربط
            msg = bot.send_message(
                user_id,
                "🔗 *ربط حساب التيليجرام*\n\n"
                "أدخل رقم هاتفك المسجل في الموقع لربط حسابك:",
                parse_mode='Markdown',
                reply_markup=cancel_markup()
            )
            bot.register_next_step_handler(msg, link_telegram_phone)
        
        conn.close()
    except Exception as e:
        logger.error(f"Link button error: {e}")
        bot.send_message(user_id, f"❌ حدث خطأ: {e}")

def link_telegram_phone(message):
    """معالجة رقم الهاتف لربط الحساب"""
    user_id = message.chat.id
    
    if message.text == "❌ إلغاء":
        bot.send_message(user_id, "❌ تم إلغاء العملية.", reply_markup=main_menu(user_id))
        return
    
    phone = message.text.strip()
    
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT id, full_name FROM users WHERE phone = ?", (phone,))
        user = c.fetchone()
        
        if user:
            # تحديث telegram_id للمستخدم
            c.execute("UPDATE users SET telegram_id = ? WHERE id = ?", (user_id, user[0]))
            conn.commit()
            bot.send_message(
                user_id,
                f"✅ *تم ربط حسابك بنجاح!*\n\n"
                f"👤 مرحباً {user[1]}، أصبح بإمكانك الآن استخدام البوت بالكامل.",
                parse_mode='Markdown',
                reply_markup=main_menu(user_id)
            )
        else:
            bot.send_message(
                user_id,
                "❌ لم يتم العثور على مستخدم بهذا الرقم.\n"
                "يرجى التأكد من الرقم أو تسجيل حساب جديد عبر الموقع.",
                reply_markup=main_menu(user_id)
            )
        
        conn.close()
    except Exception as e:
        logger.error(f"Link phone error: {e}")
        bot.send_message(user_id, f"❌ حدث خطأ: {e}", reply_markup=main_menu(user_id))

@bot.message_handler(func=lambda message: message.text == "❌ إلغاء")
def cancel_button(message):
    """إلغاء العملية الحالية"""
    user_id = message.chat.id
    if user_id in user_registration_state:
        del user_registration_state[user_id]
    bot.send_message(user_id, "❌ تم الإلغاء.", reply_markup=main_menu(user_id))

# ==================== عملية التسجيل الكاملة ====================

def register_start(message):
    """بدء عملية التسجيل من البوت"""
    user_id = message.chat.id
    
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        # إنشاء جدول users إذا لم يكن موجوداً
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phone TEXT UNIQUE,
                password TEXT,
                full_name TEXT,
                email TEXT,
                telegram_id INTEGER,
                role TEXT DEFAULT 'user',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active INTEGER DEFAULT 1
            )
        ''')
        conn.commit()
        
        # تحقق إذا كان المستخدم مسجلاً مسبقاً
        c.execute("SELECT id FROM users WHERE telegram_id = ?", (user_id,))
        if c.fetchone():
            bot.send_message(user_id, "✅ أنت مسجل مسبقاً في النظام!", reply_markup=main_menu(user_id))
            conn.close()
            return
        conn.close()
        
        msg = bot.send_message(
            user_id,
            "📝 *تسجيل حساب جديد*\n\n"
            "أدخل رقم هاتفك (مثال: 0123456789):",
            parse_mode='Markdown',
            reply_markup=cancel_markup()
        )
        bot.register_next_step_handler(msg, register_phone)
    except Exception as e:
        logger.error(f"Register start error: {e}")
        bot.send_message(user_id, f"❌ حدث خطأ: {e}")

def register_phone(message):
    """استقبال رقم الهاتف"""
    user_id = message.chat.id
    
    if message.text == "❌ إلغاء":
        bot.send_message(user_id, "❌ تم إلغاء التسجيل.", reply_markup=main_menu(user_id))
        return
    
    phone = message.text.strip()
    
    # تحقق من صحة الرقم
    if len(phone) < 10 or not phone.isdigit():
        msg = bot.send_message(
            user_id,
            "⚠️ رقم هاتف غير صالح. أدخل رقم صحيح (أرقام فقط):",
            reply_markup=cancel_markup()
        )
        bot.register_next_step_handler(msg, register_phone)
        return
    
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT id FROM users WHERE phone = ?", (phone,))
        if c.fetchone():
            conn.close()
            msg = bot.send_message(
                user_id,
                "⚠️ هذا الرقم مسجل مسبقاً. إذا كان حسابك، استخدم خيار 'ربط التيليجرام'.\n\n"
                "أدخل رقم آخر:",
                reply_markup=cancel_markup()
            )
            bot.register_next_step_handler(msg, register_phone)
            return
        conn.close()
    except Exception as e:
        logger.error(f"Phone check error: {e}")
    
    user_registration_state[user_id] = {'phone': phone}
    
    msg = bot.send_message(
        user_id,
        "🔐 أدخل كلمة المرور (6 أحرف على الأقل):",
        reply_markup=cancel_markup()
    )
    bot.register_next_step_handler(msg, register_password)

def register_password(message):
    """استقبال كلمة المرور"""
    user_id = message.chat.id
    
    if message.text == "❌ إلغاء":
        if user_id in user_registration_state:
            del user_registration_state[user_id]
        bot.send_message(user_id, "❌ تم إلغاء التسجيل.", reply_markup=main_menu(user_id))
        return
    
    password = message.text.strip()
    
    if len(password) < 6:
        msg = bot.send_message(
            user_id,
            "⚠️ كلمة المرور يجب أن تكون 6 أحرف على الأقل. حاول مرة أخرى:",
            reply_markup=cancel_markup()
        )
        bot.register_next_step_handler(msg, register_password)
        return
    
    user_registration_state[user_id]['password'] = password
    
    msg = bot.send_message(
        user_id,
        "👤 أدخل اسمك الكامل (الاسم الثلاثي):",
        reply_markup=cancel_markup()
    )
    bot.register_next_step_handler(msg, register_fullname)

def register_fullname(message):
    """استكمال التسجيل وحفظ البيانات"""
    user_id = message.chat.id
    
    if message.text == "❌ إلغاء":
        if user_id in user_registration_state:
            del user_registration_state[user_id]
        bot.send_message(user_id, "❌ تم إلغاء التسجيل.", reply_markup=main_menu(user_id))
        return
    
    fullname = message.text.strip()
    
    if len(fullname) < 3:
        msg = bot.send_message(
            user_id,
            "⚠️ الاسم قصير جداً. أدخل اسمك الكامل:",
            reply_markup=cancel_markup()
        )
        bot.register_next_step_handler(msg, register_fullname)
        return
    
    phone = user_registration_state[user_id]['phone']
    password = user_registration_state[user_id]['password']
    
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # إدراج المستخدم الجديد
        c.execute("""
            INSERT INTO users (phone, password, full_name, telegram_id, role, created_at)
            VALUES (?, ?, ?, ?, 'user', datetime('now'))
        """, (phone, password, fullname, user_id))
        
        conn.commit()
        conn.close()
        
        bot.send_message(
            user_id,
            "✅ *تم تسجيل حسابك بنجاح!*\n\n"
            f"📞 الهاتف: {phone}\n"
            f"👤 الاسم: {fullname}\n\n"
            "يمكنك الآن:\n"
            "• تقديم التبرعات\n"
            "• متابعة تقاريرك\n"
            "• استلام الشهادات\n\n"
            "استخدم الأزرار أدناه للتنقل.",
            parse_mode='Markdown',
            reply_markup=main_menu(user_id)
        )
        
        # تنظيف حالة المستخدم
        if user_id in user_registration_state:
            del user_registration_state[user_id]
        
    except Exception as e:
        logger.error(f"Error registering user: {e}")
        bot.send_message(
            user_id,
            f"❌ حدث خطأ أثناء التسجيل: {str(e)}\n"
            "يرجى المحاولة مرة أخرى لاحقاً.",
            reply_markup=main_menu(user_id)
        )
        if user_id in user_registration_state:
            del user_registration_state[user_id]

# ==================== معالجة الأزرار التفاعلية (Inline) ====================

@bot.callback_query_handler(func=lambda call: call.data == "register")
def handle_register_callback(call):
    """معالجة الضغط على زر التسجيل"""
    register_start(call.message)
    bot.answer_callback_query(call.id)

# ==================== تشغيل البوت ====================

if __name__ == '__main__':
    logger.info("Starting Telegram bot...")
    try:
        bot_info = bot.get_me()
        logger.info(f"Bot username: {bot_info.username}")
    except Exception as e:
        logger.error(f"Failed to get bot info: {e}")
    
    # تشغيل البوت مع إعادة محاولة تلقائية
    while True:
        try:
            bot.infinity_polling(timeout=60, skip_pending=True)
        except Exception as e:
            logger.error(f"Bot polling error: {e}")
            import time
            time.sleep(5)
