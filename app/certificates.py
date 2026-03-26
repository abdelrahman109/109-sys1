from pathlib import Path
from flask import Blueprint, abort, current_app, g, session
from .db import get_donation, set_donation_certificate_path
from .helpers import admin_required, ensure_dir, file_download_response, login_required
from .pdf_utils import build_certificate_pdf

bp = Blueprint('certificates', __name__, url_prefix='/certificates')


@bp.route('/donation/<int:donation_id>.pdf')
@login_required
def donation_certificate(donation_id):
    donation = get_donation(current_app, donation_id)
    if not donation:
        abort(404)
    if not session.get('is_admin') and donation['user_id'] != session['user_id']:
        abort(403)
    if donation['status'] != 'paid':
        abort(400, 'Certificate is available only for paid donations')
    ensure_dir(current_app.config['CERTIFICATES_FOLDER'])
    path = Path(current_app.config['CERTIFICATES_FOLDER']) / f"certificate-{donation['donation_code']}.pdf"
    if not path.exists():
        build_certificate_pdf(path, donation, current_app.config['APP_NAME'])
        set_donation_certificate_path(current_app, donation_id, str(path))
    return file_download_response(path, f"certificate-{donation['donation_code']}.pdf", 'application/pdf')
