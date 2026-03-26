from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import create_app
from app.db import create_donation, create_user
from app.helpers import donation_expiry

app = create_app()
with app.app_context():
    try:
        user_id = create_user(app, '01011111111', 'Password123!', 'مستخدم تجريبي', 1)
    except Exception:
        user_id = 2
    create_donation(app, user_id, 500, 'تبرع عام', 'InstaPay', donation_expiry(10))
print('Seed completed')
