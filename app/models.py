from datetime import datetime
from flask_login import UserMixin

class User(UserMixin):
    """نموذج المستخدم لـ Flask-Login"""
    def __init__(self, user_data):
        self.id = user_data['id']
        self.full_name = user_data['full_name']
        self.phone = user_data['phone']
        self.password = user_data['password']
        self.role = user_data['role'] if 'role' in user_data.keys() else 'user'
        self.telegram_id = user_data['telegram_id'] if 'telegram_id' in user_data.keys() else None
        self.email = user_data['email'] if 'email' in user_data.keys() else None
        self.college = user_data['college'] if 'college' in user_data.keys() else None
        self.specialization = user_data['specialization'] if 'specialization' in user_data.keys() else None
        self.monthly_donation = user_data['monthly_donation'] if 'monthly_donation' in user_data.keys() else 0
        self.is_active = user_data['is_active'] if 'is_active' in user_data.keys() else 1
        self.created_at = user_data['created_at'] if 'created_at' in user_data.keys() else datetime.now()
    
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
        self.receipt_path = data['receipt_path'] if 'receipt_path' in data.keys() else None
        self.status = data['status'] if 'status' in data.keys() else 'pending'
        self.notes = data['notes'] if 'notes' in data.keys() else None
        self.is_monthly = data['is_monthly'] if 'is_monthly' in data.keys() else False
        self.created_at = data['created_at'] if 'created_at' in data.keys() else datetime.now()
        self.reviewed_at = data['reviewed_at'] if 'reviewed_at' in data.keys() else None
        self.reviewed_by = data['reviewed_by'] if 'reviewed_by' in data.keys() else None


class Martyr:
    """نموذج الشهيد"""
    def __init__(self, data):
        self.id = data['id']
        self.full_name = data['full_name']
        self.birth_date = data['birth_date'] if 'birth_date' in data.keys() else None
        self.martyrdom_date = data['martyrdom_date'] if 'martyrdom_date' in data.keys() else None
        self.rank = data['rank'] if 'rank' in data.keys() else None
        self.unit = data['unit'] if 'unit' in data.keys() else None
        self.bio = data['bio'] if 'bio' in data.keys() else None
        self.image_path = data['image_path'] if 'image_path' in data.keys() else None
        self.family_id = data['family_id'] if 'family_id' in data.keys() else None
        self.created_at = data['created_at'] if 'created_at' in data.keys() else datetime.now()


class ResetCode:
    """نموذج كود استرجاع كلمة السر"""
    def __init__(self, code_data):
        self.id = code_data['id']
        self.user_id = code_data['user_id']
        self.code = code_data['code']
        self.created_at = code_data['created_at'] if 'created_at' in code_data.keys() else datetime.now()
        self.expires_at = code_data['expires_at']
