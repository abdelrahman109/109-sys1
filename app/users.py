from flask import Blueprint, current_app, flash, g, redirect, render_template, request, session, url_for
from .db import dashboard_stats, get_colleges, get_notification_preferences, get_weapons_by_college, list_user_donations, regenerate_telegram_link_code, update_notification_preferences, update_user_profile
from .helpers import login_required

bp = Blueprint('users', __name__)


@bp.route('/dashboard')
@login_required
def dashboard():
    if session.get('is_admin'):
        return redirect(url_for('admin.dashboard'))
    stats = dashboard_stats(current_app)
    donations = list_user_donations(current_app, session['user_id'])[:5]
    return render_template('user/dashboard.html', user=g.current_user, donations=donations, stats=stats)


@bp.route('/donations')
@login_required
def donation_history():
    donations = list_user_donations(current_app, session['user_id'])
    return render_template('user/donations.html', donations=donations)


@bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    colleges = get_colleges(current_app)
    if request.method == 'POST':
        college_id = int(request.form['college_id']) if request.form.get('college_id') else None
        weapon_id = int(request.form['weapon_id']) if request.form.get('weapon_id') else None
        update_user_profile(
            current_app,
            session['user_id'],
            request.form['full_name'].strip(),
            college_id,
            weapon_id,
            request.form.get('custom_weapon', '').strip(),
            1 if request.form.get('monthly_subscription') else 0,
            int(request.form.get('monthly_amount') or 0),
        )
        flash('تم تحديث الملف الشخصي', 'success')
        return redirect(url_for('users.profile'))
    selected_college = g.current_user.get('college_id') or (colleges[0]['id'] if colleges else None)
    weapons = get_weapons_by_college(current_app, selected_college) if selected_college else []
    return render_template('user/profile.html', user=g.current_user, colleges=colleges, weapons=weapons, selected_college=selected_college)


@bp.route('/profile/regenerate-link', methods=['POST'])
@login_required
def regenerate_link():
    regenerate_telegram_link_code(current_app, session['user_id'])
    flash('تم إنشاء كود ربط جديد لتليجرام', 'success')
    return redirect(url_for('users.profile'))


@bp.route('/notifications', methods=['GET', 'POST'])
@login_required
def notification_settings():
    prefs = get_notification_preferences(current_app, session['user_id'])
    if request.method == 'POST':
        update_notification_preferences(current_app, session['user_id'], request.form)
        flash('تم حفظ إعدادات الإشعارات', 'success')
        return redirect(url_for('users.notification_settings'))
    return render_template('user/notifications.html', prefs=prefs)
