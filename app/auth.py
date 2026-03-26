from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for
from .db import audit, authenticate_user, create_user, get_colleges, get_weapons_by_college, public_stats, record_login_attempt, too_many_recent_failures
from .helpers import json_ok

bp = Blueprint('auth', __name__)


@bp.route('/')
def home():
    return render_template('public/home.html', stats=public_stats(current_app))


@bp.route('/transparency')
def transparency():
    return render_template('public/transparency.html', stats=public_stats(current_app))


@bp.route('/api/weapons/<int:college_id>')
def weapons_api(college_id):
    return json_ok(weapons=get_weapons_by_college(current_app, college_id))


@bp.route('/register', methods=['GET', 'POST'])
def register():
    colleges = get_colleges(current_app)
    selected_college = int(request.form.get('college_id') or colleges[0]['id']) if colleges else None
    weapons = get_weapons_by_college(current_app, selected_college) if selected_college else []
    if request.method == 'POST':
        try:
            user_id = create_user(
                current_app,
                phone=request.form['phone'].strip(),
                password=request.form['password'],
                full_name=request.form['full_name'].strip(),
                college_id=int(request.form['college_id']),
                weapon_id=int(request.form['weapon_id']) if request.form.get('weapon_id') else None,
                custom_weapon=request.form.get('custom_weapon', '').strip() or None,
                monthly_subscription=1 if request.form.get('monthly_subscription') else 0,
                monthly_amount=int(request.form.get('monthly_amount') or 0),
            )
            audit(current_app, user_id, 'register', 'user', user_id, 'New user registration', request.remote_addr)
            flash('تم إنشاء الحساب بنجاح. يمكنك تسجيل الدخول الآن.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as exc:
            flash(f'تعذر إنشاء الحساب: {exc}', 'danger')
    return render_template('public/register.html', colleges=colleges, weapons=weapons, selected_college=selected_college)


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        phone = request.form['phone'].strip()
        ip_address = request.remote_addr or '-'
        if too_many_recent_failures(current_app, phone, ip_address):
            flash('تم تجاوز عدد المحاولات المسموح. حاول لاحقًا.', 'danger')
            return render_template('public/login.html')
        user = authenticate_user(current_app, phone, request.form['password'])
        record_login_attempt(current_app, phone, ip_address, bool(user))
        if user:
            session['user_id'] = user['id']
            session['full_name'] = user['full_name']
            session['role'] = user.get('role', 'donor')
            session['is_admin'] = user.get('role') != 'donor'
            audit(current_app, user['id'], 'login', 'user', user['id'], 'Successful login', ip_address)
            flash('تم تسجيل الدخول بنجاح', 'success')
            if session['is_admin']:
                return redirect(url_for('admin.dashboard'))
            return redirect(url_for('users.dashboard'))
        flash('بيانات الدخول غير صحيحة', 'danger')
    return render_template('public/login.html')


@bp.route('/logout')
def logout():
    if session.get('user_id'):
        audit(current_app, session.get('user_id'), 'logout', 'user', session.get('user_id'), 'User logged out', request.remote_addr)
    session.clear()
    flash('تم تسجيل الخروج', 'info')
    return redirect(url_for('auth.home'))
