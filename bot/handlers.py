from telegram import Update
from telegram.ext import ContextTypes
from app import create_app
from app.db import link_user_by_code
from .messages import WELCOME

app = create_app()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = context.args[0] if context.args else None
    if code:
        with app.app_context():
            user = link_user_by_code(app, code, update.effective_chat.id)
        if user:
            await update.message.reply_text(f'تم ربط حسابك بنجاح يا {user["full_name"]}.')
            return
        await update.message.reply_text('رمز الربط غير صحيح أو منتهي.')
        return
    await update.message.reply_text(WELCOME)


async def link_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = context.args[0] if context.args else None
    if not code:
        await update.message.reply_text('استخدم الأمر بالشكل التالي: /link CODE')
        return
    with app.app_context():
        user = link_user_by_code(app, code, update.effective_chat.id)
    if user:
        await update.message.reply_text(f'تم ربط حسابك بنجاح يا {user["full_name"]}.')
    else:
        await update.message.reply_text('رمز الربط غير صحيح أو منتهي.')


async def get_chat_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f'Chat ID: {update.effective_chat.id}')
