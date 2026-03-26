import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
BASE_DIR = Path(__file__).resolve().parent.parent


class Config:
    BASE_DIR = BASE_DIR
    APP_NAME = os.getenv('APP_NAME', 'منصة صندوق الدفعة 109')
    SECRET_KEY = os.getenv('SECRET_KEY', 'change-me-immediately')
    SITE_URL = os.getenv('SITE_URL', 'http://127.0.0.1:8000')
    
    # إعدادات قاعدة البيانات
    DATABASE_PATH = os.getenv('DATABASE_PATH', str(BASE_DIR / 'instance' / 'donations.db'))
    SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI', f'sqlite:///{DATABASE_PATH}')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # إعدادات رفع الملفات
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', str(BASE_DIR / 'uploads' / 'payment_proofs'))
    EXPENSE_UPLOAD_FOLDER = os.getenv('EXPENSE_UPLOAD_FOLDER', str(BASE_DIR / 'uploads' / 'expense_receipts'))
    MARTYR_UPLOAD_FOLDER = os.getenv('MARTYR_UPLOAD_FOLDER', str(BASE_DIR / 'uploads' / 'martyrs'))
    GENERATED_FOLDER = os.getenv('GENERATED_FOLDER', str(BASE_DIR / 'generated'))
    CERTIFICATES_FOLDER = os.getenv('CERTIFICATES_FOLDER', str(BASE_DIR / 'generated' / 'certificates'))
    REPORTS_FOLDER = os.getenv('REPORTS_FOLDER', str(BASE_DIR / 'generated' / 'reports'))
    BACKUPS_FOLDER = os.getenv('BACKUPS_FOLDER', str(BASE_DIR / 'backups'))
    
    # إعدادات التطبيق
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH_MB', '8')) * 1024 * 1024
    GOAL_AMOUNT = int(os.getenv('GOAL_AMOUNT', '50000'))
    DONATION_EXPIRY_MINUTES = int(os.getenv('DONATION_EXPIRY_MINUTES', '10'))
    LOGIN_RATE_LIMIT_COUNT = int(os.getenv('LOGIN_RATE_LIMIT_COUNT', '5'))
    LOGIN_RATE_LIMIT_MINUTES = int(os.getenv('LOGIN_RATE_LIMIT_MINUTES', '15'))
    EXPENSE_RECEIPT_REQUIRED_OVER = int(os.getenv('EXPENSE_RECEIPT_REQUIRED_OVER', '1000'))
    
    # إعدادات الأدمن
    ADMIN_PHONE = os.getenv('ADMIN_PHONE', '01000000000')
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'ChangeMe123!')
    ADMIN_NAME = os.getenv('ADMIN_NAME', 'مسؤول النظام')
    
    # إعدادات الدفع
    INSTAPAY_NUMBER = os.getenv('INSTAPAY_NUMBER', '01020877259')
    INSTAPAY_LINK = os.getenv('INSTAPAY_LINK', 'https://ipn.eg/S/gawish92/instapay/2dPqBf')
    BANK_ACCOUNT = os.getenv('BANK_ACCOUNT', 'حساب صندوق الدفعة 109 - بنك مصر')
    
    # إعدادات التيليجرام
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
    TELEGRAM_BOT_USERNAME = os.getenv('TELEGRAM_BOT_USERNAME', '')
    TELEGRAM_ADMIN_CHAT_IDS = [i.strip() for i in os.getenv('TELEGRAM_ADMIN_CHAT_IDS', '').split(',') if i.strip()]
    
    # إعدادات الوقت
    QUIET_HOURS_DEFAULT_START = os.getenv('QUIET_HOURS_DEFAULT_START', '23:00')
    QUIET_HOURS_DEFAULT_END = os.getenv('QUIET_HOURS_DEFAULT_END', '06:00')
    MONTHLY_REMINDER_DAY = int(os.getenv('MONTHLY_REMINDER_DAY', '16'))
    MONTH_CLOSE_DAY = int(os.getenv('MONTH_CLOSE_DAY', '17'))
