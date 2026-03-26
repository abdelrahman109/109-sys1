import time
from datetime import datetime
from app import create_app
from app.tasks import run_daily_backup_job, run_expiry_job, run_monthly_reminder_job

app = create_app()
last_backup_day = None
last_monthly_day = None

if __name__ == '__main__':
    while True:
        now = datetime.utcnow()
        with app.app_context():
            run_expiry_job(app)
            if last_backup_day != now.date().isoformat() and now.hour == 1:
                run_daily_backup_job(app)
                last_backup_day = now.date().isoformat()
            if last_monthly_day != now.date().isoformat() and now.day == app.config['MONTHLY_REMINDER_DAY'] and now.hour == 9:
                run_monthly_reminder_job(app)
                last_monthly_day = now.date().isoformat()
        time.sleep(60)
