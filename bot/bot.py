from telegram.ext import ApplicationBuilder, CommandHandler
from app import create_app
from bot.handlers import get_chat_id, link_account, start

app = create_app()


def main():
    token = app.config.get('TELEGRAM_BOT_TOKEN')
    if not token:
        raise RuntimeError('TELEGRAM_BOT_TOKEN is not configured')
    application = ApplicationBuilder().token(token).build()
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('id', get_chat_id))
    application.add_handler(CommandHandler('link', link_account))
    application.run_polling()


if __name__ == '__main__':
    main()
