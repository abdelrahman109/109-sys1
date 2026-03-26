from app import create_app
from app.db import init_db, seed_admin, seed_reference_data
from app.helpers import ensure_dir

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        ensure_dir(app.config['UPLOAD_FOLDER'])
        ensure_dir(app.config['EXPENSE_UPLOAD_FOLDER'])
        ensure_dir(app.config['MARTYR_UPLOAD_FOLDER'])
        ensure_dir(app.config['GENERATED_FOLDER'])
        ensure_dir(app.config['CERTIFICATES_FOLDER'])
        ensure_dir(app.config['REPORTS_FOLDER'])
        ensure_dir(app.config['BACKUPS_FOLDER'])
        init_db(app)
        seed_reference_data(app)
        seed_admin(app)
        print('Database initialized successfully')
