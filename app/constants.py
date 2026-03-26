COLLEGES = [
    {'id': 1, 'name_ar': 'الكلية الحربية', 'name_en': 'Military Academy', 'display_order': 1},
    {'id': 2, 'name_ar': 'الكلية الفنية العسكرية', 'name_en': 'Military Technical College', 'display_order': 2},
    {'id': 3, 'name_ar': 'الكلية الجوية', 'name_en': 'Air Force College', 'display_order': 3},
    {'id': 4, 'name_ar': 'الكلية البحرية', 'name_en': 'Naval College', 'display_order': 4},
    {'id': 5, 'name_ar': 'كلية الدفاع الجوي', 'name_en': 'Air Defense College', 'display_order': 5},
    {'id': 6, 'name_ar': 'الكلية التكنولوجية العسكرية', 'name_en': 'Military Technological College', 'display_order': 6},
]

WEAPONS = {
    1: ['المشاة', 'المدرعات', 'المدفعية', 'الإشارة', 'الصاعقة', 'الحرس الجمهوري', 'الاستطلاع', 'الإمداد والتموين', 'الشرطة العسكرية', 'الأسلحة والذخيرة', 'المركبات', 'الحرب الإلكترونية', 'الشؤون المعنوية'],
    2: [f'تخصص {i}' for i in range(1, 29)],
    3: ['طيارين', 'مراقبة جوية', 'دفاع جوي', 'توجيه', 'فنيين', 'إدارة جوية'],
    4: ['ملاحة', 'إشارة بحرية', 'مدفعية بحرية', 'إمداد بحري', 'ضفادع بشرية'],
    5: ['رادار', 'صواريخ', 'مدفعية', 'قيادة وسيطرة'],
    6: ['ميكاترونكس', 'اتصالات', 'حواسب', 'كهرباء', 'ميكانيكا'],
}

DONATION_TYPES = ['تبرع عام', 'رمضان 2027', 'مساعدة أسر', 'تطوير الدفعة']
PAYMENT_METHODS = ['InstaPay', 'محفظة إلكترونية', 'تحويل بنكي']
DONATION_STATUSES = ['draft', 'pending_proof', 'pending_review', 'paid', 'rejected', 'expired', 'cancelled']
EXPENSE_CATEGORIES = ['دعم أسر شهداء', 'علاج', 'تعليم', 'مطاعم', 'هدايا', 'إيجار', 'مطبوعات', 'إعلانات', 'إدارة', 'أخرى']
EXPENSE_PAYMENT_METHODS = ['كاش', 'بنك', 'محفظة']
EXPENSE_STATUSES = ['pending', 'approved', 'rejected']
ADMIN_ROLES = ['super_admin', 'finance_admin', 'reviewer', 'content_admin', 'family_admin']
MARTYR_PRIORITIES = ['normal', 'high', 'critical']
SUPPORT_TYPES = ['دعم مالي', 'علاج', 'تعليم', 'مساعدة عينية', 'مصاريف عاجلة', 'أخرى']
ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp'}
MAX_IMAGE_COUNT = 3
