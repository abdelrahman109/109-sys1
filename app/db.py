import os
import shutil
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Optional
from werkzeug.security import check_password_hash, generate_password_hash
from .constants import ADMIN_ROLES, COLLEGES, EXPENSE_STATUSES, WEAPONS
from .helpers import ensure_dir, now_str

SCHEMA = """
CREATE TABLE IF NOT EXISTS colleges (
    id INTEGER PRIMARY KEY,
    name_ar TEXT NOT NULL,
    name_en TEXT NOT NULL,
    display_order INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS weapons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name_ar TEXT NOT NULL,
    college_id INTEGER NOT NULL,
    FOREIGN KEY (college_id) REFERENCES colleges(id)
);
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    phone TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    full_name TEXT NOT NULL,
    college_id INTEGER,
    weapon_id INTEGER,
    custom_weapon TEXT,
    is_verified INTEGER DEFAULT 0,
    monthly_subscription INTEGER DEFAULT 0,
    monthly_amount INTEGER DEFAULT 0,
    telegram_chat_id TEXT,
    telegram_link_code TEXT,
    role TEXT NOT NULL DEFAULT 'donor',
    is_active INTEGER DEFAULT 1,
    created_at TEXT NOT NULL,
    last_login TEXT,
    FOREIGN KEY (college_id) REFERENCES colleges(id),
    FOREIGN KEY (weapon_id) REFERENCES weapons(id)
);
CREATE TABLE IF NOT EXISTS donations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    donation_code TEXT UNIQUE NOT NULL,
    user_id INTEGER NOT NULL,
    amount INTEGER NOT NULL CHECK (amount > 0),
    donation_type TEXT NOT NULL,
    payment_method TEXT NOT NULL,
    payment_proof_path TEXT,
    status TEXT NOT NULL,
    expires_at TEXT,
    cancel_reason TEXT,
    admin_notes TEXT,
    created_at TEXT NOT NULL,
    proof_uploaded_at TEXT,
    reviewed_at TEXT,
    reviewed_by INTEGER,
    paid_at TEXT,
    certificate_path TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (reviewed_by) REFERENCES users(id)
);
CREATE TABLE IF NOT EXISTS martyrs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    military_rank TEXT,
    college_id INTEGER,
    weapon_id INTEGER,
    custom_weapon TEXT,
    governorate TEXT,
    birth_date TEXT,
    martyrdom_date TEXT,
    age_at_martyrdom REAL,
    marital_status TEXT,
    brothers_count INTEGER DEFAULT 0,
    sisters_count INTEGER DEFAULT 0,
    sons_count INTEGER DEFAULT 0,
    daughters_count INTEGER DEFAULT 0,
    children_count INTEGER DEFAULT 0,
    father_phone TEXT,
    mother_phone TEXT,
    alternate_phone TEXT,
    alternate_phone_owner TEXT,
    family_guardian_name TEXT,
    family_phone TEXT,
    family_address TEXT,
    monthly_support_needed INTEGER DEFAULT 0,
    urgent_need INTEGER DEFAULT 0,
    support_priority TEXT DEFAULT 'normal',
    family_status TEXT,
    notes TEXT,
    image_path TEXT,
    is_active INTEGER DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT,
    FOREIGN KEY (college_id) REFERENCES colleges(id),
    FOREIGN KEY (weapon_id) REFERENCES weapons(id)
);
CREATE TABLE IF NOT EXISTS martyr_support_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    martyr_id INTEGER NOT NULL,
    support_type TEXT NOT NULL,
    amount INTEGER NOT NULL DEFAULT 0,
    support_date TEXT NOT NULL,
    description TEXT,
    added_by INTEGER,
    created_at TEXT NOT NULL,
    FOREIGN KEY (martyr_id) REFERENCES martyrs(id),
    FOREIGN KEY (added_by) REFERENCES users(id)
);
CREATE TABLE IF NOT EXISTS martyr_documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    martyr_id INTEGER NOT NULL,
    document_type TEXT,
    file_path TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (martyr_id) REFERENCES martyrs(id)
);
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    expense_date TEXT NOT NULL,
    category TEXT NOT NULL,
    amount INTEGER NOT NULL CHECK (amount > 0),
    description TEXT,
    payment_method TEXT NOT NULL,
    receipt_path TEXT,
    martyr_id INTEGER,
    status TEXT NOT NULL DEFAULT 'pending',
    rejection_reason TEXT,
    added_by INTEGER,
    approved_by INTEGER,
    approved_at TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (martyr_id) REFERENCES martyrs(id),
    FOREIGN KEY (added_by) REFERENCES users(id),
    FOREIGN KEY (approved_by) REFERENCES users(id)
);
CREATE TABLE IF NOT EXISTS notification_preferences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER UNIQUE NOT NULL,
    telegram_chat_id TEXT,
    notify_confirm INTEGER DEFAULT 1,
    notify_monthly INTEGER DEFAULT 1,
    notify_new_content INTEGER DEFAULT 1,
    notify_ramadan INTEGER DEFAULT 1,
    notify_admin INTEGER DEFAULT 1,
    quiet_start TEXT DEFAULT '23:00',
    quiet_end TEXT DEFAULT '06:00',
    FOREIGN KEY (user_id) REFERENCES users(id)
);
CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    actor_user_id INTEGER,
    action TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id TEXT,
    details TEXT,
    ip_address TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (actor_user_id) REFERENCES users(id)
);
CREATE TABLE IF NOT EXISTS notification_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    channel TEXT NOT NULL,
    subject TEXT,
    message TEXT NOT NULL,
    status TEXT NOT NULL,
    error_message TEXT,
    created_at TEXT NOT NULL,
    sent_at TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
CREATE TABLE IF NOT EXISTS login_attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    phone TEXT NOT NULL,
    ip_address TEXT,
    success INTEGER NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS broadcast_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    sent_by INTEGER,
    sent_at TEXT NOT NULL,
    recipient_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    FOREIGN KEY (sent_by) REFERENCES users(id)
);
CREATE TABLE IF NOT EXISTS backup_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    backup_path TEXT NOT NULL,
    size_bytes INTEGER DEFAULT 0,
    status TEXT NOT NULL,
    notes TEXT,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_users_phone ON users(phone);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_donations_user_id ON donations(user_id);
CREATE INDEX IF NOT EXISTS idx_donations_status ON donations(status);
CREATE INDEX IF NOT EXISTS idx_donations_created_at ON donations(created_at);
CREATE INDEX IF NOT EXISTS idx_expenses_date ON expenses(expense_date);
CREATE INDEX IF NOT EXISTS idx_expenses_status ON expenses(status);
CREATE INDEX IF NOT EXISTS idx_martyrs_name ON martyrs(full_name);
CREATE INDEX IF NOT EXISTS idx_martyrs_priority ON martyrs(support_priority, urgent_need, is_active);
CREATE INDEX IF NOT EXISTS idx_support_logs_martyr ON martyr_support_logs(martyr_id, support_date);
"""


def get_db(app=None):
    from flask import current_app
    flask_app = app or current_app
    db_path = flask_app.config['DATABASE_PATH']
    ensure_dir(os.path.dirname(db_path))
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON;')
    conn.execute('PRAGMA journal_mode = WAL;')
    return conn


def init_db(app):
    with closing(get_db(app)) as conn:
        conn.executescript(SCHEMA)
        _run_migrations(conn)
        conn.commit()


def _run_migrations(conn):
    # Lightweight compatibility migrations for existing SQLite files.
    migrations = {
        'users': {'role': "ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'donor'", 'is_active': "ALTER TABLE users ADD COLUMN is_active INTEGER DEFAULT 1", 'telegram_link_code': "ALTER TABLE users ADD COLUMN telegram_link_code TEXT"},
        'donations': {'admin_notes': "ALTER TABLE donations ADD COLUMN admin_notes TEXT", 'reviewed_at': "ALTER TABLE donations ADD COLUMN reviewed_at TEXT", 'reviewed_by': "ALTER TABLE donations ADD COLUMN reviewed_by INTEGER", 'paid_at': "ALTER TABLE donations ADD COLUMN paid_at TEXT", 'certificate_path': "ALTER TABLE donations ADD COLUMN certificate_path TEXT"},
        'expenses': {'martyr_id': "ALTER TABLE expenses ADD COLUMN martyr_id INTEGER", 'status': "ALTER TABLE expenses ADD COLUMN status TEXT NOT NULL DEFAULT 'pending'", 'rejection_reason': "ALTER TABLE expenses ADD COLUMN rejection_reason TEXT", 'approved_by': "ALTER TABLE expenses ADD COLUMN approved_by INTEGER", 'approved_at': "ALTER TABLE expenses ADD COLUMN approved_at TEXT"},
        'martyrs': {'image_path': "ALTER TABLE martyrs ADD COLUMN image_path TEXT", 'family_phone': "ALTER TABLE martyrs ADD COLUMN family_phone TEXT", 'monthly_support_needed': "ALTER TABLE martyrs ADD COLUMN monthly_support_needed INTEGER DEFAULT 0", 'urgent_need': "ALTER TABLE martyrs ADD COLUMN urgent_need INTEGER DEFAULT 0", 'support_priority': "ALTER TABLE martyrs ADD COLUMN support_priority TEXT DEFAULT 'normal'", 'is_active': "ALTER TABLE martyrs ADD COLUMN is_active INTEGER DEFAULT 1"},
    }
    for table, cols in migrations.items():
        existing = {row['name'] for row in conn.execute(f'PRAGMA table_info({table})').fetchall()}
        for col, stmt in cols.items():
            if existing and col not in existing:
                conn.execute(stmt)


def seed_reference_data(app):
    with closing(get_db(app)) as conn:
        if conn.execute('SELECT COUNT(*) c FROM colleges').fetchone()['c'] == 0:
            conn.executemany('INSERT INTO colleges (id, name_ar, name_en, display_order) VALUES (:id, :name_ar, :name_en, :display_order)', COLLEGES)
        if conn.execute('SELECT COUNT(*) c FROM weapons').fetchone()['c'] == 0:
            for college_id, items in WEAPONS.items():
                conn.executemany('INSERT INTO weapons (name_ar, college_id) VALUES (?, ?)', [(item, college_id) for item in items])
        conn.commit()


def seed_admin(app):
    with closing(get_db(app)) as conn:
        exists = conn.execute('SELECT id FROM users WHERE phone = ?', (app.config['ADMIN_PHONE'],)).fetchone()
        if not exists:
            conn.execute(
                'INSERT INTO users (phone, password, full_name, is_verified, role, telegram_link_code, created_at) VALUES (?, ?, ?, 1, ?, lower(hex(randomblob(8))), ?)',
                (app.config['ADMIN_PHONE'], generate_password_hash(app.config['ADMIN_PASSWORD']), app.config['ADMIN_NAME'], 'super_admin', now_str()),
            )
            admin_id = conn.execute('SELECT last_insert_rowid() id').fetchone()['id']
            conn.execute('INSERT INTO notification_preferences (user_id) VALUES (?)', (admin_id,))
            conn.commit()


def audit(app, actor_user_id, action, entity_type, entity_id=None, details=None, ip_address=None):
    with closing(get_db(app)) as conn:
        conn.execute(
            'INSERT INTO audit_logs (actor_user_id, action, entity_type, entity_id, details, ip_address, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)',
            (actor_user_id, action, entity_type, entity_id, details, ip_address, now_str()),
        )
        conn.commit()


def log_notification(app, user_id, channel, subject, message, status, error_message=None):
    sent_at = now_str() if status == 'sent' else None
    with closing(get_db(app)) as conn:
        conn.execute(
            'INSERT INTO notification_logs (user_id, channel, subject, message, status, error_message, created_at, sent_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
            (user_id, channel, subject, message, status, error_message, now_str(), sent_at),
        )
        conn.commit()


def record_login_attempt(app, phone, ip_address, success):
    with closing(get_db(app)) as conn:
        conn.execute('INSERT INTO login_attempts (phone, ip_address, success, created_at) VALUES (?, ?, ?, ?)', (phone, ip_address, int(success), now_str()))
        conn.commit()


def too_many_recent_failures(app, phone, ip_address):
    with closing(get_db(app)) as conn:
        row = conn.execute(
            "SELECT COUNT(*) c FROM login_attempts WHERE phone = ? AND ip_address = ? AND success = 0 AND datetime(created_at) >= datetime('now', ?)",
            (phone, ip_address, f"-{app.config['LOGIN_RATE_LIMIT_MINUTES']} minutes"),
        ).fetchone()
        return row['c'] >= app.config['LOGIN_RATE_LIMIT_COUNT']


def create_user(app, phone, password, full_name, college_id, weapon_id=None, custom_weapon=None, monthly_subscription=0, monthly_amount=0):
    with closing(get_db(app)) as conn:
        conn.execute(
            'INSERT INTO users (phone, password, full_name, college_id, weapon_id, custom_weapon, monthly_subscription, monthly_amount, telegram_link_code, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, lower(hex(randomblob(8))), ?)',
            (phone, generate_password_hash(password), full_name, college_id, weapon_id, custom_weapon, int(bool(monthly_subscription)), int(monthly_amount or 0), now_str()),
        )
        user_id = conn.execute('SELECT last_insert_rowid() id').fetchone()['id']
        conn.execute('INSERT INTO notification_preferences (user_id) VALUES (?)', (user_id,))
        conn.commit()
        return user_id


def authenticate_user(app, phone, password):
    with closing(get_db(app)) as conn:
        user = conn.execute('SELECT * FROM users WHERE phone = ? AND is_active = 1', (phone,)).fetchone()
        if user and check_password_hash(user['password'], password):
            conn.execute('UPDATE users SET last_login = ? WHERE id = ?', (now_str(), user['id']))
            conn.commit()
            return dict(user)
    return None


def _decorate_user_row(row):
    data = dict(row)
    data['is_admin'] = int(data.get('role') in ADMIN_ROLES)
    return data


def get_colleges(app):
    with closing(get_db(app)) as conn:
        return [dict(r) for r in conn.execute('SELECT * FROM colleges ORDER BY display_order, id').fetchall()]


def get_weapons_by_college(app, college_id):
    with closing(get_db(app)) as conn:
        return [dict(r) for r in conn.execute('SELECT * FROM weapons WHERE college_id = ? ORDER BY name_ar', (college_id,)).fetchall()]


def get_user_by_id(app, user_id):
    if not user_id:
        return None
    with closing(get_db(app)) as conn:
        row = conn.execute(
            'SELECT u.*, c.name_ar AS college_name, w.name_ar AS weapon_name FROM users u LEFT JOIN colleges c ON c.id = u.college_id LEFT JOIN weapons w ON w.id = u.weapon_id WHERE u.id = ?',
            (user_id,),
        ).fetchone()
        return _decorate_user_row(row) if row else None


def list_users(app, search=''):
    sql = 'SELECT u.*, c.name_ar AS college_name, w.name_ar AS weapon_name FROM users u LEFT JOIN colleges c ON c.id = u.college_id LEFT JOIN weapons w ON w.id = u.weapon_id WHERE 1=1'
    params = []
    if search:
        sql += ' AND (u.full_name LIKE ? OR u.phone LIKE ? OR u.role LIKE ?)'
        params.extend([f'%{search}%', f'%{search}%', f'%{search}%'])
    sql += ' ORDER BY u.created_at DESC'
    with closing(get_db(app)) as conn:
        return [_decorate_user_row(r) for r in conn.execute(sql, params).fetchall()]


def update_user_profile(app, user_id, full_name, college_id, weapon_id, custom_weapon, monthly_subscription, monthly_amount):
    with closing(get_db(app)) as conn:
        conn.execute(
            'UPDATE users SET full_name = ?, college_id = ?, weapon_id = ?, custom_weapon = ?, monthly_subscription = ?, monthly_amount = ? WHERE id = ?',
            (full_name, college_id, weapon_id, custom_weapon, int(bool(monthly_subscription)), int(monthly_amount or 0), user_id),
        )
        conn.commit()


def update_user_admin(app, user_id, role, is_active, is_verified):
    with closing(get_db(app)) as conn:
        conn.execute('UPDATE users SET role = ?, is_active = ?, is_verified = ? WHERE id = ?', (role, int(bool(is_active)), int(bool(is_verified)), user_id))
        conn.commit()


def regenerate_telegram_link_code(app, user_id):
    with closing(get_db(app)) as conn:
        conn.execute('UPDATE users SET telegram_link_code = lower(hex(randomblob(8))) WHERE id = ?', (user_id,))
        conn.commit()


def link_user_by_code(app, code, chat_id):
    with closing(get_db(app)) as conn:
        user = conn.execute('SELECT * FROM users WHERE telegram_link_code = ? AND is_active = 1', (code,)).fetchone()
        if not user:
            return None
        conn.execute('UPDATE users SET telegram_chat_id = ?, telegram_link_code = lower(hex(randomblob(8))) WHERE id = ?', (str(chat_id), user['id']))
        conn.execute('UPDATE notification_preferences SET telegram_chat_id = ? WHERE user_id = ?', (str(chat_id), user['id']))
        conn.commit()
        return dict(user)


def get_notification_preferences(app, user_id):
    with closing(get_db(app)) as conn:
        row = conn.execute('SELECT * FROM notification_preferences WHERE user_id = ?', (user_id,)).fetchone()
        return dict(row) if row else None


def update_notification_preferences(app, user_id, data):
    with closing(get_db(app)) as conn:
        conn.execute(
            'UPDATE notification_preferences SET notify_confirm = ?, notify_monthly = ?, notify_new_content = ?, notify_ramadan = ?, notify_admin = ?, quiet_start = ?, quiet_end = ?, telegram_chat_id = ? WHERE user_id = ?',
            (int(bool(data.get('notify_confirm'))), int(bool(data.get('notify_monthly'))), int(bool(data.get('notify_new_content'))), int(bool(data.get('notify_ramadan'))), int(bool(data.get('notify_admin'))), data.get('quiet_start', '23:00'), data.get('quiet_end', '06:00'), data.get('telegram_chat_id') or None, user_id),
        )
        conn.commit()


def _next_donation_code(conn):
    last = conn.execute("SELECT id FROM donations ORDER BY id DESC LIMIT 1").fetchone()
    next_id = (last['id'] if last else 0) + 1
    return f"DON-{next_id:06d}"


def create_donation(app, user_id, amount, donation_type, payment_method, expires_at):
    with closing(get_db(app)) as conn:
        code = _next_donation_code(conn)
        conn.execute(
            "INSERT INTO donations (donation_code, user_id, amount, donation_type, payment_method, status, expires_at, created_at) VALUES (?, ?, ?, ?, ?, 'pending_proof', ?, ?)",
            (code, user_id, int(amount), donation_type, payment_method, expires_at, now_str()),
        )
        donation_id = conn.execute('SELECT last_insert_rowid() id').fetchone()['id']
        conn.commit()
        return donation_id, code


def list_user_donations(app, user_id):
    with closing(get_db(app)) as conn:
        rows = conn.execute('SELECT * FROM donations WHERE user_id = ? ORDER BY id DESC', (user_id,)).fetchall()
        return [dict(r) for r in rows]


def get_donation(app, donation_id):
    with closing(get_db(app)) as conn:
        row = conn.execute(
            'SELECT d.*, u.full_name, u.phone, u.telegram_chat_id FROM donations d JOIN users u ON u.id = d.user_id WHERE d.id = ?',
            (donation_id,),
        ).fetchone()
        return dict(row) if row else None


def attach_donation_proof(app, donation_id, user_id, proof_path):
    with closing(get_db(app)) as conn:
        conn.execute("UPDATE donations SET payment_proof_path = ?, status = 'pending_review', proof_uploaded_at = ? WHERE id = ? AND user_id = ? AND status = 'pending_proof'", (proof_path, now_str(), donation_id, user_id))
        conn.commit()


def cancel_donation(app, donation_id, user_id, reason):
    with closing(get_db(app)) as conn:
        conn.execute("UPDATE donations SET status = 'cancelled', cancel_reason = ? WHERE id = ? AND user_id = ? AND status IN ('pending_proof', 'pending_review')", (reason, donation_id, user_id))
        conn.commit()


def set_donation_certificate_path(app, donation_id, certificate_path):
    with closing(get_db(app)) as conn:
        conn.execute('UPDATE donations SET certificate_path = ? WHERE id = ?', (certificate_path, donation_id))
        conn.commit()


def review_donation(app, donation_id, reviewer_id, status, reason=None, admin_notes=None):
    paid_at = now_str() if status == 'paid' else None
    with closing(get_db(app)) as conn:
        conn.execute('UPDATE donations SET status = ?, cancel_reason = ?, admin_notes = ?, reviewed_at = ?, reviewed_by = ?, paid_at = ? WHERE id = ?', (status, reason, admin_notes, now_str(), reviewer_id, paid_at, donation_id))
        conn.commit()


def list_donations(app, status=None, donation_type=None, payment_method=None, college_id=None, q=None):
    sql = 'SELECT d.*, u.full_name, u.phone, u.college_id, c.name_ar AS college_name FROM donations d JOIN users u ON u.id = d.user_id LEFT JOIN colleges c ON c.id = u.college_id WHERE 1=1'
    params = []
    if status:
        sql += ' AND d.status = ?'
        params.append(status)
    if donation_type:
        sql += ' AND d.donation_type = ?'
        params.append(donation_type)
    if payment_method:
        sql += ' AND d.payment_method = ?'
        params.append(payment_method)
    if college_id:
        sql += ' AND u.college_id = ?'
        params.append(college_id)
    if q:
        sql += ' AND (u.full_name LIKE ? OR u.phone LIKE ? OR d.donation_code LIKE ?)'
        params.extend([f'%{q}%', f'%{q}%', f'%{q}%'])
    sql += ' ORDER BY d.id DESC'
    with closing(get_db(app)) as conn:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]


def expire_old_donations(app):
    with closing(get_db(app)) as conn:
        rows = conn.execute("SELECT d.*, u.id AS user_id, u.full_name, u.telegram_chat_id FROM donations d JOIN users u ON u.id = d.user_id WHERE d.status = 'pending_proof' AND datetime(d.expires_at) < datetime('now')").fetchall()
        conn.execute("UPDATE donations SET status = 'expired', cancel_reason = 'انتهت مهلة رفع الإيصال' WHERE status = 'pending_proof' AND datetime(expires_at) < datetime('now')")
        conn.commit()
        return [dict(r) for r in rows]


def add_expense(app, expense_date, category, amount, description, payment_method, added_by, receipt_path=None, martyr_id=None):
    with closing(get_db(app)) as conn:
        conn.execute('INSERT INTO expenses (expense_date, category, amount, description, payment_method, receipt_path, martyr_id, added_by, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)', (expense_date, category, int(amount), description, payment_method, receipt_path, martyr_id, added_by, now_str()))
        conn.commit()


def review_expense(app, expense_id, status, reviewer_id, rejection_reason=None):
    if status not in EXPENSE_STATUSES:
        raise ValueError('Invalid expense status')
    approved_at = now_str() if status == 'approved' else None
    with closing(get_db(app)) as conn:
        conn.execute('UPDATE expenses SET status = ?, rejection_reason = ?, approved_by = ?, approved_at = ? WHERE id = ?', (status, rejection_reason, reviewer_id, approved_at, expense_id))
        conn.commit()


def list_expenses(app, status=None):
    sql = 'SELECT e.*, u.full_name AS added_by_name, au.full_name AS approved_by_name, m.full_name AS martyr_name FROM expenses e LEFT JOIN users u ON u.id = e.added_by LEFT JOIN users au ON au.id = e.approved_by LEFT JOIN martyrs m ON m.id = e.martyr_id WHERE 1=1'
    params = []
    if status:
        sql += ' AND e.status = ?'
        params.append(status)
    sql += ' ORDER BY e.expense_date DESC, e.id DESC'
    with closing(get_db(app)) as conn:
        rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]


def list_audit_logs(app, limit=300):
    with closing(get_db(app)) as conn:
        rows = conn.execute('SELECT a.*, u.full_name AS actor_name FROM audit_logs a LEFT JOIN users u ON u.id = a.actor_user_id ORDER BY a.id DESC LIMIT ?', (limit,)).fetchall()
        return [dict(r) for r in rows]


def list_notification_logs(app, limit=300):
    with closing(get_db(app)) as conn:
        rows = conn.execute('SELECT n.*, u.full_name FROM notification_logs n LEFT JOIN users u ON u.id = n.user_id ORDER BY n.id DESC LIMIT ?', (limit,)).fetchall()
        return [dict(r) for r in rows]


def create_broadcast_log(app, title, body, sent_by, recipient_count, success_count):
    with closing(get_db(app)) as conn:
        conn.execute('INSERT INTO broadcast_messages (title, body, sent_by, sent_at, recipient_count, success_count) VALUES (?, ?, ?, ?, ?, ?)', (title, body, sent_by, now_str(), recipient_count, success_count))
        conn.commit()


def list_broadcast_messages(app):
    with closing(get_db(app)) as conn:
        rows = conn.execute('SELECT b.*, u.full_name AS sender_name FROM broadcast_messages b LEFT JOIN users u ON u.id = b.sent_by ORDER BY b.id DESC LIMIT 100').fetchall()
        return [dict(r) for r in rows]


def telegram_recipients(app):
    with closing(get_db(app)) as conn:
        rows = conn.execute('SELECT u.id, u.full_name, COALESCE(np.telegram_chat_id, u.telegram_chat_id) AS telegram_chat_id FROM users u LEFT JOIN notification_preferences np ON np.user_id = u.id WHERE u.is_active = 1 AND COALESCE(np.telegram_chat_id, u.telegram_chat_id) IS NOT NULL').fetchall()
        return [dict(r) for r in rows]


def _martyr_base_select():
    return """
        SELECT m.*, c.name_ar AS college_name, w.name_ar AS weapon_name,
               COALESCE((SELECT SUM(amount) FROM martyr_support_logs s WHERE s.martyr_id = m.id), 0) AS support_total,
               COALESCE((SELECT MAX(support_date) FROM martyr_support_logs s WHERE s.martyr_id = m.id), '') AS last_support_date,
               COALESCE((SELECT COUNT(*) FROM martyr_support_logs s WHERE s.martyr_id = m.id), 0) AS support_count
        FROM martyrs m
        LEFT JOIN colleges c ON c.id = m.college_id
        LEFT JOIN weapons w ON w.id = m.weapon_id
    """


def list_martyrs(app, q=None, college_id=None, priority=None, is_active: Optional[int] = None):
    sql = _martyr_base_select() + ' WHERE 1=1'
    params = []
    if q:
        sql += ' AND (m.full_name LIKE ? OR m.family_phone LIKE ? OR m.notes LIKE ?)'
        params.extend([f'%{q}%', f'%{q}%', f'%{q}%'])
    if college_id:
        sql += ' AND m.college_id = ?'
        params.append(college_id)
    if priority:
        sql += ' AND m.support_priority = ?'
        params.append(priority)
    if is_active is not None and str(is_active) != '':
        sql += ' AND m.is_active = ?'
        params.append(int(is_active))
    sql += ' ORDER BY m.urgent_need DESC, m.is_active DESC, m.full_name ASC'
    with closing(get_db(app)) as conn:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]


def get_martyr(app, martyr_id):
    with closing(get_db(app)) as conn:
        row = conn.execute(_martyr_base_select() + ' WHERE m.id = ?', (martyr_id,)).fetchone()
        return dict(row) if row else None


def create_martyr(app, data):
    fields = ['full_name','military_rank','college_id','weapon_id','custom_weapon','governorate','birth_date','martyrdom_date','age_at_martyrdom','marital_status','brothers_count','sisters_count','sons_count','daughters_count','children_count','father_phone','mother_phone','alternate_phone','alternate_phone_owner','family_guardian_name','family_phone','family_address','monthly_support_needed','urgent_need','support_priority','family_status','notes','image_path','is_active']
    values = [data.get(f) for f in fields]
    with closing(get_db(app)) as conn:
        conn.execute(f"INSERT INTO martyrs ({','.join(fields)}, created_at, updated_at) VALUES ({','.join(['?']*len(fields))}, ?, ?)", values + [now_str(), now_str()])
        martyr_id = conn.execute('SELECT last_insert_rowid() id').fetchone()['id']
        conn.commit()
        return martyr_id


def update_martyr(app, martyr_id, data):
    fields = ['full_name','military_rank','college_id','weapon_id','custom_weapon','governorate','birth_date','martyrdom_date','age_at_martyrdom','marital_status','brothers_count','sisters_count','sons_count','daughters_count','children_count','father_phone','mother_phone','alternate_phone','alternate_phone_owner','family_guardian_name','family_phone','family_address','monthly_support_needed','urgent_need','support_priority','family_status','notes','is_active']
    values = [data.get(f) for f in fields]
    with closing(get_db(app)) as conn:
        conn.execute(f"UPDATE martyrs SET {','.join([f'{f} = ?' for f in fields])}, updated_at = ? WHERE id = ?", values + [now_str(), martyr_id])
        conn.commit()


def update_martyr_image(app, martyr_id, image_path):
    with closing(get_db(app)) as conn:
        conn.execute('UPDATE martyrs SET image_path = ?, updated_at = ? WHERE id = ?', (image_path, now_str(), martyr_id))
        conn.commit()


def add_martyr_support(app, martyr_id, support_type, amount, support_date, description, added_by):
    with closing(get_db(app)) as conn:
        conn.execute('INSERT INTO martyr_support_logs (martyr_id, support_type, amount, support_date, description, added_by, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)', (martyr_id, support_type, int(amount or 0), support_date, description, added_by, now_str()))
        conn.commit()


def list_martyr_support_logs(app, martyr_id):
    with closing(get_db(app)) as conn:
        rows = conn.execute('SELECT s.*, u.full_name AS added_by_name FROM martyr_support_logs s LEFT JOIN users u ON u.id = s.added_by WHERE martyr_id = ? ORDER BY support_date DESC, s.id DESC', (martyr_id,)).fetchall()
        return [dict(r) for r in rows]


def dashboard_stats(app):
    with closing(get_db(app)) as conn:
        donations_total = conn.execute("SELECT COALESCE(SUM(amount),0) total FROM donations WHERE status = 'paid'").fetchone()['total']
        expenses_total = conn.execute("SELECT COALESCE(SUM(amount),0) total FROM expenses WHERE status = 'approved'").fetchone()['total']
        donors_count = conn.execute("SELECT COUNT(DISTINCT user_id) total FROM donations WHERE status = 'paid'").fetchone()['total']
        avg_donation = conn.execute("SELECT COALESCE(AVG(amount),0) avgv FROM donations WHERE status = 'paid'").fetchone()['avgv']
        pending_review = conn.execute("SELECT COUNT(*) c FROM donations WHERE status = 'pending_review'").fetchone()['c']
        pending_expenses = conn.execute("SELECT COUNT(*) c FROM expenses WHERE status = 'pending'").fetchone()['c']
        expiring = conn.execute("SELECT COUNT(*) c FROM donations WHERE status = 'pending_proof'").fetchone()['c']
        total_users = conn.execute('SELECT COUNT(*) c FROM users').fetchone()['c']
        martyrs_count = conn.execute('SELECT COUNT(*) c FROM martyrs WHERE is_active = 1').fetchone()['c']
        urgent_cases = conn.execute('SELECT COUNT(*) c FROM martyrs WHERE is_active = 1 AND urgent_need = 1').fetchone()['c']
        support_total = conn.execute('SELECT COALESCE(SUM(amount),0) total FROM martyr_support_logs').fetchone()['total']
        by_type = [dict(r) for r in conn.execute("SELECT donation_type, COUNT(*) count, COALESCE(SUM(amount),0) amount FROM donations WHERE status='paid' GROUP BY donation_type ORDER BY amount DESC").fetchall()]
        by_payment = [dict(r) for r in conn.execute("SELECT payment_method, COUNT(*) count, COALESCE(SUM(amount),0) amount FROM donations WHERE status='paid' GROUP BY payment_method ORDER BY amount DESC").fetchall()]
        by_college = [dict(r) for r in conn.execute("SELECT c.name_ar AS college_name, COUNT(*) count, COALESCE(SUM(d.amount),0) amount FROM donations d JOIN users u ON u.id = d.user_id LEFT JOIN colleges c ON c.id = u.college_id WHERE d.status='paid' GROUP BY u.college_id ORDER BY amount DESC").fetchall()]
        return {
            'donations_total': donations_total,
            'expenses_total': expenses_total,
            'net_total': donations_total - expenses_total,
            'goal_amount': app.config['GOAL_AMOUNT'],
            'goal_percent': round((donations_total / app.config['GOAL_AMOUNT']) * 100, 2) if app.config['GOAL_AMOUNT'] else 0,
            'donors_count': donors_count,
            'avg_donation': round(avg_donation or 0, 2),
            'pending_review': pending_review,
            'pending_expenses': pending_expenses,
            'expiring': expiring,
            'total_users': total_users,
            'martyrs_count': martyrs_count,
            'urgent_cases': urgent_cases,
            'support_total': support_total,
            'by_type': by_type,
            'by_payment': by_payment,
            'by_college': by_college,
        }


def public_stats(app):
    stats = dashboard_stats(app)
    return {
        'donations_total': stats['donations_total'],
        'expenses_total': stats['expenses_total'],
        'net_total': stats['net_total'],
        'goal_amount': stats['goal_amount'],
        'goal_percent': stats['goal_percent'],
        'donors_count': stats['donors_count'],
        'last_updated': now_str(),
    }


def register_backup_log(app, backup_path, size_bytes, status, notes=None):
    with closing(get_db(app)) as conn:
        conn.execute('INSERT INTO backup_logs (backup_path, size_bytes, status, notes, created_at) VALUES (?, ?, ?, ?, ?)', (backup_path, size_bytes, status, notes, now_str()))
        conn.commit()


def create_backup(app, backup_name=None):
    ensure_dir(app.config['BACKUPS_FOLDER'])
    src = Path(app.config['DATABASE_PATH'])
    if not src.exists():
        raise FileNotFoundError(str(src))
    name = backup_name or f"donations-{now_str().replace(':', '-').replace(' ', '_')}.db"
    dest = Path(app.config['BACKUPS_FOLDER']) / name
    shutil.copy2(src, dest)
    size_bytes = dest.stat().st_size if dest.exists() else 0
    register_backup_log(app, str(dest), size_bytes, 'success')
    return str(dest)


def get_system_health(app):
    db_path = Path(app.config['DATABASE_PATH'])
    backups = []
    with closing(get_db(app)) as conn:
        backups = [dict(r) for r in conn.execute('SELECT * FROM backup_logs ORDER BY id DESC LIMIT 1').fetchall()]
        counts = {
            'failed_notifications': conn.execute("SELECT COUNT(*) c FROM notification_logs WHERE status = 'failed'").fetchone()['c'],
            'failed_backups': conn.execute("SELECT COUNT(*) c FROM backup_logs WHERE status = 'failed'").fetchone()['c'],
            'martyrs': conn.execute('SELECT COUNT(*) c FROM martyrs').fetchone()['c'],
            'support_logs': conn.execute('SELECT COUNT(*) c FROM martyr_support_logs').fetchone()['c'],
        }
    stat = shutil.disk_usage(db_path.parent if db_path.parent.exists() else Path('.'))
    return {
        'db_exists': db_path.exists(),
        'db_path': str(db_path),
        'telegram_enabled': bool(app.config.get('TELEGRAM_BOT_TOKEN')),
        'disk_free_gb': round(stat.free / (1024**3), 2),
        'latest_backup': backups[0] if backups else None,
        'failed_notifications': counts['failed_notifications'],
        'failed_backups': counts['failed_backups'],
        'martyrs': counts['martyrs'],
        'support_logs': counts['support_logs'],
    }

def init_reset_codes_table(app):
    """إنشاء جدول reset_codes إذا لم يكن موجوداً"""
    db = get_db(app)
    db.execute('''
        CREATE TABLE IF NOT EXISTS reset_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            code TEXT NOT NULL,
            expires_at TIMESTAMP NOT NULL
        )
    ''')
