import csv
import io
import os
import secrets
import uuid
from datetime import datetime, timedelta
from functools import wraps
from pathlib import Path
from PIL import Image, UnidentifiedImageError
from flask import Response, abort, flash, g, jsonify, redirect, request, send_file, session, url_for
from .constants import ADMIN_ROLES, ALLOWED_IMAGE_EXTENSIONS, MAX_IMAGE_COUNT

DATETIME_FMT = '%Y-%m-%d %H:%M:%S'


def now():
    return datetime.utcnow()


def now_str():
    return now().strftime(DATETIME_FMT)


def parse_dt(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, DATETIME_FMT)
    except Exception:
        return None


def donation_expiry(minutes):
    return (now() + timedelta(minutes=minutes)).strftime(DATETIME_FMT)


def format_currency(value):
    return f"{int(value or 0):,} جنيه"


def ensure_dir(path):
    Path(path).mkdir(parents=True, exist_ok=True)


def ensure_csrf_token():
    if '_csrf_token' not in session:
        session['_csrf_token'] = secrets.token_hex(16)


def validate_csrf():
    if request.method in ('POST', 'PUT', 'PATCH', 'DELETE'):
        token = request.form.get('csrf_token') or request.headers.get('X-CSRFToken')
        if not token or token != session.get('_csrf_token'):
            abort(400, 'Invalid CSRF token')


def load_current_user(app):
    from .db import get_user_by_id
    validate_csrf()
    g.current_user = get_user_by_id(app, session.get('user_id')) if session.get('user_id') else None


def login_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not session.get('user_id'):
            flash('سجل الدخول أولاً', 'warning')
            return redirect(url_for('auth.login'))
        return view(*args, **kwargs)
    return wrapper


def role_required(*roles):
    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            user_role = session.get('role')
            if not session.get('user_id'):
                flash('سجل الدخول أولاً', 'warning')
                return redirect(url_for('auth.login'))
            if user_role not in roles:
                flash('غير مصرح لك بهذه الصفحة', 'danger')
                if user_role in ADMIN_ROLES:
                    return redirect(url_for('admin.dashboard'))
                return redirect(url_for('users.dashboard'))
            return view(*args, **kwargs)
        return wrapper
    return decorator


def admin_required(view):
    return role_required(*ADMIN_ROLES)(view)


def is_admin_role(role):
    return role in ADMIN_ROLES


def secure_image_upload(file_storage, upload_folder):
    if not file_storage or not file_storage.filename:
        return None, 'يرجى اختيار صورة أولاً'
    ext = Path(file_storage.filename).suffix.lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        return None, 'نوع الملف غير مسموح'
    ensure_dir(upload_folder)
    filename = f"{uuid.uuid4().hex}{ext}"
    abs_path = Path(upload_folder) / filename
    try:
        image = Image.open(file_storage.stream)
        image.verify()
        file_storage.stream.seek(0)
        file_storage.save(abs_path)
    except (UnidentifiedImageError, OSError):
        return None, 'الملف ليس صورة صالحة'
    return filename, None


def secure_multiple_images(files, upload_folder):
    files = [f for f in files if getattr(f, 'filename', '')]
    if not files:
        return [], 'يرجى اختيار صورة واحدة على الأقل'
    if len(files) > MAX_IMAGE_COUNT:
        return [], f'الحد الأقصى {MAX_IMAGE_COUNT} صور'
    saved = []
    for item in files:
        filename, error = secure_image_upload(item, upload_folder)
        if error:
            for path in saved:
                try:
                    os.remove(Path(upload_folder) / path)
                except OSError:
                    pass
            return [], error
        saved.append(filename)
    return saved, None


def csv_response(filename, rows, headers):
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=headers)
    writer.writeheader()
    for row in rows:
        writer.writerow({k: row.get(k, '') for k in headers})
    return Response(output.getvalue(), mimetype='text/csv; charset=utf-8', headers={'Content-Disposition': f'attachment; filename={filename}'})


def file_download_response(path, download_name, mimetype=None):
    return send_file(path, as_attachment=True, download_name=download_name, mimetype=mimetype)


def json_ok(**kwargs):
    return jsonify({'ok': True, **kwargs})


def remaining_seconds(expires_at):
    dt = parse_dt(expires_at)
    if not dt:
        return 0
    return max(int((dt - now()).total_seconds()), 0)
