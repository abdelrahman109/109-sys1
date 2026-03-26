from pathlib import Path
from flask import Blueprint, current_app
from openpyxl import Workbook
from openpyxl.styles import Font
from .db import dashboard_stats, list_donations, list_expenses, list_martyrs, list_martyr_support_logs
from .helpers import admin_required, csv_response, ensure_dir, file_download_response, login_required, now_str
from .pdf_utils import build_summary_pdf

bp = Blueprint('reports', __name__, url_prefix='/reports')


def _write_xlsx(path, headers, rows):
    wb = Workbook()
    ws = wb.active
    ws.append(headers)
    for cell in ws[1]:
        cell.font = Font(bold=True)
    for row in rows:
        ws.append([row.get(h, '') for h in headers])
    for col in ws.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        ws.column_dimensions[col[0].column_letter].width = min(max(max_len + 2, 12), 35)
    wb.save(path)


@bp.route('/donations.csv')
@login_required
@admin_required
def donations_csv():
    rows = list_donations(current_app)
    headers = ['id', 'donation_code', 'full_name', 'phone', 'college_name', 'amount', 'donation_type', 'payment_method', 'status', 'created_at', 'paid_at', 'cancel_reason']
    return csv_response('donations_report.csv', rows, headers)


@bp.route('/expenses.csv')
@login_required
@admin_required
def expenses_csv():
    rows = list_expenses(current_app)
    headers = ['id', 'expense_date', 'category', 'martyr_name', 'amount', 'description', 'payment_method', 'status', 'added_by_name', 'approved_by_name', 'created_at']
    return csv_response('expenses_report.csv', rows, headers)


@bp.route('/martyrs.csv')
@login_required
@admin_required
def martyrs_csv():
    rows = list_martyrs(current_app)
    headers = ['id', 'full_name', 'college_name', 'weapon_name', 'family_phone', 'monthly_support_needed', 'support_priority', 'urgent_need', 'support_total', 'last_support_date', 'is_active']
    return csv_response('martyrs_report.csv', rows, headers)


@bp.route('/donations.xlsx')
@login_required
@admin_required
def donations_xlsx():
    rows = list_donations(current_app)
    headers = ['id', 'donation_code', 'full_name', 'phone', 'college_name', 'amount', 'donation_type', 'payment_method', 'status', 'created_at', 'paid_at', 'cancel_reason']
    ensure_dir(current_app.config['REPORTS_FOLDER'])
    path = Path(current_app.config['REPORTS_FOLDER']) / 'donations_report.xlsx'
    _write_xlsx(path, headers, rows)
    return file_download_response(path, 'donations_report.xlsx', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')


@bp.route('/expenses.xlsx')
@login_required
@admin_required
def expenses_xlsx():
    rows = list_expenses(current_app)
    headers = ['id', 'expense_date', 'category', 'martyr_name', 'amount', 'description', 'payment_method', 'status', 'added_by_name', 'approved_by_name', 'created_at']
    ensure_dir(current_app.config['REPORTS_FOLDER'])
    path = Path(current_app.config['REPORTS_FOLDER']) / 'expenses_report.xlsx'
    _write_xlsx(path, headers, rows)
    return file_download_response(path, 'expenses_report.xlsx', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')


@bp.route('/martyrs.xlsx')
@login_required
@admin_required
def martyrs_xlsx():
    rows = list_martyrs(current_app)
    headers = ['id', 'full_name', 'college_name', 'weapon_name', 'family_phone', 'monthly_support_needed', 'support_priority', 'urgent_need', 'support_total', 'last_support_date', 'is_active']
    ensure_dir(current_app.config['REPORTS_FOLDER'])
    path = Path(current_app.config['REPORTS_FOLDER']) / 'martyrs_report.xlsx'
    _write_xlsx(path, headers, rows)
    return file_download_response(path, 'martyrs_report.xlsx', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')


@bp.route('/martyr/<int:martyr_id>/support.xlsx')
@login_required
@admin_required
def martyr_support_xlsx(martyr_id):
    rows = list_martyr_support_logs(current_app, martyr_id)
    headers = ['id', 'support_date', 'support_type', 'amount', 'description', 'added_by_name', 'created_at']
    ensure_dir(current_app.config['REPORTS_FOLDER'])
    path = Path(current_app.config['REPORTS_FOLDER']) / f'martyr-support-{martyr_id}.xlsx'
    _write_xlsx(path, headers, rows)
    return file_download_response(path, f'martyr-support-{martyr_id}.xlsx', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')


@bp.route('/summary.pdf')
@login_required
@admin_required
def summary_pdf():
    ensure_dir(current_app.config['REPORTS_FOLDER'])
    path = Path(current_app.config['REPORTS_FOLDER']) / 'summary_report.pdf'
    build_summary_pdf(path, dashboard_stats(current_app), now_str())
    return file_download_response(path, 'summary_report.pdf', 'application/pdf')
