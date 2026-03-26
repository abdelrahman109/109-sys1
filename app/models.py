from datetime import datetime
from flask_login import UserMixin
from app import db

class User(UserMixin, db.Model):
    """نموذج المستخدم"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(15), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(100))
    telegram_id = db.Column(db.Integer, unique=True)
    role = db.Column(db.String(20), default='user')  # user, admin, super_admin
    college = db.Column(db.String(100))
    specialization = db.Column(db.String(100))
    monthly_donation = db.Column(db.Float, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # العلاقات
    donations = db.relationship('Donation', backref='user', lazy=True)
    
    def __repr__(self):
        return f'<User {self.full_name}>'


class Donation(db.Model):
    """نموذج التبرع"""
    __tablename__ = 'donations'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    receipt_path = db.Column(db.String(200))
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    notes = db.Column(db.Text)
    is_monthly = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime)
    reviewed_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    def __repr__(self):
        return f'<Donation {self.amount} by user {self.user_id}>'


class Expense(db.Model):
    """نموذج المصروفات"""
    __tablename__ = 'expenses'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50))
    description = db.Column(db.Text)
    receipt_path = db.Column(db.String(200))
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    family_id = db.Column(db.Integer, db.ForeignKey('families.id'))  # اختياري للربط بالأسر
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    approved_at = db.Column(db.DateTime)
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    def __repr__(self):
        return f'<Expense {self.title} - {self.amount}>'


class Martyr(db.Model):
    """نموذج الشهيد"""
    __tablename__ = 'martyrs'
    
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    birth_date = db.Column(db.Date)
    martyrdom_date = db.Column(db.Date)
    rank = db.Column(db.String(50))
    unit = db.Column(db.String(100))
    bio = db.Column(db.Text)
    image_path = db.Column(db.String(200))
    family_id = db.Column(db.Integer, db.ForeignKey('families.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # العلاقات
    family = db.relationship('Family', backref='martyr', uselist=False)
    
    def __repr__(self):
        return f'<Martyr {self.full_name}>'


class Family(db.Model):
    """نموذج أسرة الشهيد"""
    __tablename__ = 'families'
    
    id = db.Column(db.Integer, primary_key=True)
    martyr_id = db.Column(db.Integer, db.ForeignKey('martyrs.id'))
    father_name = db.Column(db.String(100))
    mother_name = db.Column(db.String(100))
    address = db.Column(db.String(200))
    phone = db.Column(db.String(15))
    children_count = db.Column(db.Integer, default=0)
    monthly_support = db.Column(db.Float, default=0)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # العلاقات
    support_history = db.relationship('FamilySupport', backref='family', lazy=True)
    
    def __repr__(self):
        return f'<Family of martyr {self.martyr_id}>'


class FamilySupport(db.Model):
    """نموذج سجل دعم الأسر"""
    __tablename__ = 'family_supports'
    
    id = db.Column(db.Integer, primary_key=True)
    family_id = db.Column(db.Integer, db.ForeignKey('families.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    type = db.Column(db.String(50))  # monthly, one_time, emergency
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))


class ResetCode(db.Model):
    """نموذج كود استرجاع كلمة السر"""
    __tablename__ = 'reset_codes'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    code = db.Column(db.String(6), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    
    def __repr__(self):
        return f'<ResetCode for user {self.user_id}>'


class Notification(db.Model):
    """نموذج الإشعارات"""
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50))  # donation, expense, system, broadcast
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Notification {self.title}>'


class AuditLog(db.Model):
    """نموذج سجل التدقيق"""
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    action = db.Column(db.String(100), nullable=False)
    target_type = db.Column(db.String(50))
    target_id = db.Column(db.Integer)
    details = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<AuditLog {self.action} by user {self.user_id}>'
