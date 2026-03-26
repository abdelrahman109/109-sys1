from .bot_service import notify_admins, send_telegram_message
from .db import create_backup, expire_old_donations, register_backup_log, telegram_recipients


def run_expiry_job(app):
    expired = expire_old_donations(app)
    for donation in expired:
        if donation.get('telegram_chat_id'):
            send_telegram_message(app, donation['telegram_chat_id'], f"انتهت مهلة رفع الإيصال للتبرع {donation['donation_code']}", donation['user_id'], 'donation_expired')
    if expired:
        notify_admins(app, f'تم إغلاق {len(expired)} تبرعات لانتهاء المهلة', 'expiry_summary')
    return len(expired)


def run_monthly_reminder_job(app):
    success = 0
    for recipient in telegram_recipients(app):
        ok, _ = send_telegram_message(app, recipient['telegram_chat_id'], 'تذكير شهري: لا تنس مساهمتك في صندوق الدفعة 109.', recipient['id'], 'monthly_reminder')
        if ok:
            success += 1
    return success


def run_daily_backup_job(app):
    try:
        return create_backup(app)
    except Exception as exc:
        register_backup_log(app, '', 0, 'failed', str(exc))
        raise
