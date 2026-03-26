from datetime import datetime
from flask_login import UserMixin

class User(UserMixin):
    """نموذج المستخدم لـ Flask-Login"""
    def __init__(self, user_data):
        self.id = user_data['id']
        self.full_name = user_data['full_name']
        self.phone = user_data['phone']
        self.password = user_data['password']
        self.role = user_data.get('role', 'user')
        self.telegram_id = user_data.get('telegram_id')
        self.email = user_data.get('email')
        self.college = user_data.get('college')
        self.specialization = user_data.get('specialization')
        self.monthly_donation = user_data.get('monthly_donation', 0)
        self.is_active = user_data.get('is_active', 1)
        self.created_at = user_data.get('created_at', datetime.now())
    
    def get_id(self):
        return str(self.id)
    
    def is_admin(self):
        return self.role == 'admin'
    
    def is_authenticated(self):
        return True
    
    def is_active(self):
        return bool(self.is_active)
    
    def is_anonymous(self):
        return False
    
    @staticmethod
    def get(user_id, db):
        """الحصول على المستخدم من قاعدة البيانات"""
        user_data = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        if user_data:
            return User(user_data)
        return None
    
    @staticmethod
    def get_by_phone(phone, db):
        """الحصول على المستخدم برقم الهاتف"""
        user_data = db.execute('SELECT * FROM users WHERE phone = ?', (phone,)).fetchone()
        if user_data:
            return User(user_data)
        return None


class Donation:
    """نموذج التبرع"""
    def __init__(self, data):
        self.id = data['id']
        self.user_id = data['user_id']
        self.amount = data['amount']
        self.receipt_path = data.get('receipt_path')
        self.status = data.get('status', 'pending')
        self.notes = data.get('notes')
        self.is_monthly = data.get('is_monthly', False)
        self.created_at = data.get('created_at', datetime.now())
        self.reviewed_at = data.get('reviewed_at')
        self.reviewed_by = data.get('reviewed_by')


class Martyr:
    """نموذج الشهيد"""
    def __init__(self, data):
        self.id = data['id']
        self.full_name = data['full_name']
        self.birth_date = data.get('birth_date')
        self.martyrdom_date = data.get('martyrdom_date')
        self.rank = data.get('rank')
        self.unit = data.get('unit')
        self.bio = data.get('bio')
        self.image_path = data.get('image_path')
        self.family_id = data.get('family_id')
        self.created_at = data.get('created_at', datetime.now())


class ResetCode:
    """نموذج كود استرجاع كلمة السر"""
    def __init__(self, code_data):
        self.id = code_data['id']
        self.user_id = code_data['user_id']
        self.code = code_data['code']
        self.created_at = code_data.get('created_at', datetime.now())
        self.expires_at = code_data['expires_at']
