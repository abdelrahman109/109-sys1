from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for
from .bot_service import notify_admins
from .constants import DONATION_TYPES, PAYMENT_METHODS
from .db import attach_donation_proof, audit, cancel_donation, create_donation, get_donation
from .helpers import donation_expiry, login_required, secure_image_upload

bp = Blueprint('donations', __name__)


@bp.route('/donate', methods=['GET', 'POST'])
@login_required
def donate():
    if request.method == 'POST':
        amount = int(request.form['amount'])
        donation_id, code = create_donation(
            current_app,
            user_id=session['user_id'],
            amount=amount,
            donation_type=request.form['donation_type'],
            payment_method=request.form['payment_method'],
            expires_at=donation_expiry(current_app.config['DONATION_EXPIRY_MINUTES']),
        )
        audit(current_app, session['user_id'], 'create_donation', 'donation', code, f'Amount={amount}', request.remote_addr)
        flash(f'تم إنشاء التبرع بنجاح. رقم العملية: {code}', 'success')
        return redirect(url_for('users.donation_history'))
    return render_template(
        'user/donate.html',
        donation_types=DONATION_TYPES,
        payment_methods=PAYMENT_METHODS,
        instapay_number=current_app.config['INSTAPAY_NUMBER'],
        instapay_link=current_app.config['INSTAPAY_LINK'],
        bank_account=current_app.config['BANK_ACCOUNT'],
        expiry_minutes=current_app.config['DONATION_EXPIRY_MINUTES'],
    )


@bp.route('/donations/<int:donation_id>/upload-proof', methods=['POST'])
@login_required
def upload_proof(donation_id):
    filename, error = secure_image_upload(request.files.get('payment_proof'), current_app.config['UPLOAD_FOLDER'])
    if error:
        flash(error, 'warning')
        return redirect(url_for('users.donation_history'))
    attach_donation_proof(current_app, donation_id, session['user_id'], f'uploads/payment_proofs/{filename}')
    donation = get_donation(current_app, donation_id)
    notify_admins(current_app, f"تبرع جديد بانتظار المراجعة\nالكود: {donation['donation_code']}\nالاسم: {donation['full_name']}\nالمبلغ: {donation['amount']} جنيه", 'new_donation')
    audit(current_app, session['user_id'], 'upload_proof', 'donation', donation_id, filename, request.remote_addr)
    flash('تم رفع الإيصال وبانتظار مراجعة الأدمن', 'success')
    return redirect(url_for('users.donation_history'))


@bp.route('/donations/<int:donation_id>/cancel', methods=['POST'])
@login_required
def cancel(donation_id):
    reason = request.form.get('reason') or 'إلغاء من المستخدم'
    cancel_donation(current_app, donation_id, session['user_id'], reason)
    audit(current_app, session['user_id'], 'cancel_donation', 'donation', donation_id, reason, request.remote_addr)
    flash('تم إلغاء التبرع', 'info')
    return redirect(url_for('users.donation_history'))
