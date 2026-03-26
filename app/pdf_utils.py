from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from bidi.algorithm import get_display
import arabic_reshaper

FONT_CANDIDATES = [
    '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
    '/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf',
]


def register_arabic_font():
    for candidate in FONT_CANDIDATES:
        if Path(candidate).exists():
            pdfmetrics.registerFont(TTFont('ArabicUI', candidate))
            return 'ArabicUI'
    return 'Helvetica'


def ar(text):
    text = str(text or '')
    try:
        return get_display(arabic_reshaper.reshape(text))
    except Exception:
        return text


def build_certificate_pdf(path, donation, app_name):
    font_name = register_arabic_font()
    c = canvas.Canvas(str(path), pagesize=A4)
    width, height = A4
    c.setTitle('Donation Certificate')
    c.setFont(font_name, 24)
    c.drawCentredString(width / 2, height - 3 * cm, ar(app_name))
    c.setFont(font_name, 18)
    c.drawCentredString(width / 2, height - 5 * cm, ar('شهادة شكر وتقدير'))
    c.setFont(font_name, 14)
    lines = [
        f"نشهد نحن إدارة صندوق الدفعة 109 بأن السيد/ {donation['full_name']}",
        f"قد تبرع بمبلغ {donation['amount']} جنيه", 
        f"لصالح: {donation['donation_type']}",
        f"كود العملية: {donation['donation_code']}",
        f"تاريخ القبول: {donation.get('paid_at') or donation.get('reviewed_at') or donation.get('created_at')}",
    ]
    y = height - 8 * cm
    for line in lines:
        c.drawRightString(width - 2.5 * cm, y, ar(line))
        y -= 1.2 * cm
    c.setFont(font_name, 12)
    c.drawRightString(width - 2.5 * cm, y - 0.8 * cm, ar('مع خالص الشكر والتقدير'))
    c.rect(1.8 * cm, 1.8 * cm, width - 3.6 * cm, height - 3.6 * cm)
    c.showPage()
    c.save()


def build_summary_pdf(path, stats, generated_at):
    font_name = register_arabic_font()
    c = canvas.Canvas(str(path), pagesize=A4)
    width, height = A4
    c.setTitle('Fund Summary Report')
    c.setFont(font_name, 24)
    c.drawCentredString(width / 2, height - 3 * cm, ar('تقرير ملخص صندوق الدفعة 109'))
    c.setFont(font_name, 13)
    lines = [
        f"تاريخ الإنشاء: {generated_at}",
        f"إجمالي التبرعات: {stats['donations_total']} جنيه",
        f"إجمالي المصاريف: {stats['expenses_total']} جنيه",
        f"صافي الصندوق: {stats['net_total']} جنيه",
        f"الهدف: {stats['goal_amount']} جنيه",
        f"نسبة الإنجاز: {stats['goal_percent']}%",
        f"عدد المتبرعين: {stats['donors_count']}",
        f"متوسط التبرع: {stats['avg_donation']} جنيه",
        f"تبرعات تنتظر مراجعة: {stats['pending_review']}",
        f"مصروفات تنتظر اعتماد: {stats['pending_expenses']}",
    ]
    y = height - 5.5 * cm
    for line in lines:
        c.drawRightString(width - 2.5 * cm, y, ar(line))
        y -= 0.9 * cm
    y -= 0.4 * cm
    c.setFont(font_name, 15)
    c.drawRightString(width - 2.5 * cm, y, ar('التوزيع حسب نوع التبرع'))
    c.setFont(font_name, 11)
    y -= 0.9 * cm
    for item in stats['by_type'][:8]:
        c.drawRightString(width - 2.5 * cm, y, ar(f"{item['donation_type']}: {item['amount']} جنيه ({item['count']} عملية)"))
        y -= 0.7 * cm
        if y < 4 * cm:
            c.showPage()
            c.setFont(font_name, 11)
            y = height - 3 * cm
    c.showPage()
    c.save()
