import requests
from .db import log_notification


def send_telegram_message(app, chat_id, message, user_id=None, subject=None):
    token = app.config.get('TELEGRAM_BOT_TOKEN')
    if not token or not chat_id:
        log_notification(app, user_id, 'telegram', subject, message, 'skipped', 'Missing token or chat id')
        return False, 'Missing token or chat id'
    url = f'https://api.telegram.org/bot{token}/sendMessage'
    try:
        resp = requests.post(url, json={'chat_id': str(chat_id), 'text': message}, timeout=15)
        if resp.ok and resp.json().get('ok'):
            log_notification(app, user_id, 'telegram', subject, message, 'sent')
            return True, None
        err = resp.text[:500]
        log_notification(app, user_id, 'telegram', subject, message, 'failed', err)
        return False, err
    except Exception as exc:
        log_notification(app, user_id, 'telegram', subject, message, 'failed', str(exc))
        return False, str(exc)


def notify_admins(app, message, subject='admin_notification'):
    sent = 0
    for chat_id in app.config.get('TELEGRAM_ADMIN_CHAT_IDS', []):
        ok, _ = send_telegram_message(app, chat_id, message, subject=subject)
        if ok:
            sent += 1
    return sent
