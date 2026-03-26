from flask import Blueprint, current_app, flash, redirect, request, session, url_for
from .bot_service import send_telegram_message
from .db import audit
from .helpers import login_required

bp = Blueprint('notifications', __name__, url_prefix='/notifications')


@bp.route('/test', methods=['POST'])
@login_required
def send_test_message():
    chat_id = request.form.get('chat_id') or request.form.get('telegram_chat_id')
    ok, err = send_telegram_message(current_app, chat_id, 'رسالة اختبار من منصة صندوق الدفعة 109', session['user_id'], 'test_message')
    if ok:
        audit(current_app, session['user_id'], 'telegram_test', 'notification', session['user_id'], chat_id, request.remote_addr)
        flash('تم إرسال رسالة الاختبار بنجاح', 'success')
    else:
        flash(f'تعذر إرسال الرسالة: {err}', 'danger')
    return redirect(url_for('users.notification_settings'))
