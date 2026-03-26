# منصة صندوق الدفعة 109 - نسخة تشغيل جاهزة وموسعة

نسخة Flask جاهزة للتشغيل على Ubuntu 22.04 مع:
- تسجيل ودخول المستخدمين
- تبرعات + مهلة 10 دقائق + رفع إيصال + مراجعة أدمن
- أدوار أدمن متعددة
- إدارة المصاريف مع اعتماد/رفض وربط اختياري بحالات الأسر
- إدارة الشهداء والأسر من لوحة الأدمن
- صورة لكل شهيد + بيانات الأسرة + سجل دعم
- صفحة شفافية عامة
- ربط تيليجرام للمستخدمين
- رسائل Broadcast للأعضاء
- Audit logs و Notification logs
- تقارير CSV / Excel / PDF
- شهادات تبرع PDF
- scheduler للمهام الدورية
- systemd + nginx + gunicorn + backup timer

## 1) التهيئة السريعة
```bash
cd /home/ubuntu
unzip 109-sys-final-ready.zip -d 109-sys
cd 109-sys
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
nano .env
python scripts/init_db.py
```

## 2) التشغيل المحلي
```bash
source .venv/bin/activate
python webapp.py
```
ثم افتح:
- http://127.0.0.1:8000

## 3) استيراد بيانات الشهداء من Excel
```bash
source .venv/bin/activate
python scripts/import_martyrs.py "/path/to/الشهداء.xlsx"
```

## 4) التشغيل كخدمات
```bash
sudo cp deploy/systemd/109-web.service /etc/systemd/system/
sudo cp deploy/systemd/109-bot.service /etc/systemd/system/
sudo cp deploy/systemd/109-scheduler.service /etc/systemd/system/
sudo cp deploy/systemd/109-backup.service /etc/systemd/system/
sudo cp deploy/systemd/109-backup.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable 109-web 109-bot 109-scheduler 109-backup.timer
sudo systemctl start 109-web 109-bot 109-scheduler 109-backup.timer
```

## 5) إعداد nginx
```bash
sudo cp deploy/nginx/109-sys.conf /etc/nginx/sites-available/109-sys
sudo ln -s /etc/nginx/sites-available/109-sys /etc/nginx/sites-enabled/109-sys
sudo nginx -t
sudo systemctl reload nginx
```

## 6) بيانات الأدمن
يتم إنشاء حساب الأدمن تلقائيًا من القيم الموجودة في `.env`:
- `ADMIN_PHONE`
- `ADMIN_PASSWORD`

## 7) تيليجرام
ضع القيم التالية في `.env`:
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_BOT_USERNAME`
- `TELEGRAM_ADMIN_CHAT_IDS`

المستخدم يمكنه ربط حسابه من صفحة الملف الشخصي.

## 8) النسخ الاحتياطي
- يدوي: من لوحة الأدمن `/admin/system` أو عبر `scripts/backup_db.sh`
- تلقائي: `109-backup.timer`
- الاسترجاع: `scripts/restore_db.sh /path/to/backup.db`

## 9) التقارير
- `/reports/donations.csv`
- `/reports/donations.xlsx`
- `/reports/expenses.csv`
- `/reports/expenses.xlsx`
- `/reports/martyrs.csv`
- `/reports/martyrs.xlsx`
- `/reports/summary.pdf`

## 10) ملاحظات مهمة
- غيّر `SECRET_KEY` و `ADMIN_PASSWORD` قبل التشغيل الحقيقي.
- لا تضع توكن البوت داخل الكود.
- لو التوكن انكشف، اعمل له Rotate من BotFather فورًا.
- صور الشهداء تحفظ في `uploads/martyrs/`.
- لا يوجد تبرع باسم شهيد بعينه من واجهة المستخدم؛ الدعم يتم إداريًا من داخل النظام.
