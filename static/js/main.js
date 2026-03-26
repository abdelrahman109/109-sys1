// ==================== نظام دعم الدفعة 109 ====================

// إخفاء التنبيهات تلقائياً بعد 5 ثواني
document.addEventListener('DOMContentLoaded', function() {
    // إخفاء التنبيهات
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            alert.style.transition = 'opacity 0.5s ease';
            alert.style.opacity = '0';
            setTimeout(function() {
                if (alert.parentNode) {
                    alert.remove();
                }
            }, 500);
        }, 5000);
    });
    
    // تفعيل التلميحات (tooltips)
    const tooltips = document.querySelectorAll('[data-toggle="tooltip"]');
    if (tooltips.length > 0 && typeof bootstrap !== 'undefined') {
        tooltips.forEach(function(tooltip) {
            new bootstrap.Tooltip(tooltip);
        });
    }
    
    // تفعيل القوائم المنسدلة
    const dropdowns = document.querySelectorAll('.dropdown-toggle');
    if (dropdowns.length > 0 && typeof bootstrap !== 'undefined') {
        dropdowns.forEach(function(dropdown) {
            new bootstrap.Dropdown(dropdown);
        });
    }
});

// ==================== دوال مساعدة ====================

// تأكيد الحذف
function confirmDelete(message) {
    return confirm(message || '⚠️ هل أنت متأكد من الحذف؟ هذا الإجراء لا يمكن التراجع عنه.');
}

// تأكيد العملية
function confirmAction(message) {
    return confirm(message || '⚠️ هل أنت متأكد من تنفيذ هذا الإجراء؟');
}

// تنسيق الأرقام كعملة (جنيه مصري)
function formatCurrency(amount) {
    if (!amount && amount !== 0) return '0 ج.م';
    return new Intl.NumberFormat('ar-EG', {
        style: 'currency',
        currency: 'EGP',
        minimumFractionDigits: 2
    }).format(amount);
}

// تنسيق التاريخ
function formatDate(dateString, format = 'arabic') {
    if (!dateString) return '-';
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return dateString;
    
    if (format === 'arabic') {
        return date.toLocaleDateString('ar-EG', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    }
    
    return date.toLocaleDateString('ar-EG');
}

// تنسيق الوقت
function formatDateTime(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return dateString;
    
    return date.toLocaleDateString('ar-EG', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// التحقق من صحة رقم الهاتف المصري
function isValidEgyptianPhone(phone) {
    const phoneRegex = /^(010|011|012|015)[0-9]{8}$/;
    return phoneRegex.test(phone);
}

// التحقق من صحة البريد الإلكتروني
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

// عرض رسالة خطأ
function showError(message, containerId = 'error-container') {
    const container = document.getElementById(containerId);
    if (container) {
        const alert = document.createElement('div');
        alert.className = 'alert alert-danger';
        alert.innerHTML = `
            <i class="fas fa-exclamation-circle"></i>
            ${message}
            <button type="button" class="close" onclick="this.parentElement.remove()">&times;</button>
        `;
        container.appendChild(alert);
        
        // إخفاء تلقائي بعد 5 ثواني
        setTimeout(() => alert.remove(), 5000);
    } else {
        alert(message);
    }
}

// عرض رسالة نجاح
function showSuccess(message, containerId = 'success-container') {
    const container = document.getElementById(containerId);
    if (container) {
        const alert = document.createElement('div');
        alert.className = 'alert alert-success';
        alert.innerHTML = `
            <i class="fas fa-check-circle"></i>
            ${message}
            <button type="button" class="close" onclick="this.parentElement.remove()">&times;</button>
        `;
        container.appendChild(alert);
        
        // إخفاء تلقائي بعد 5 ثواني
        setTimeout(() => alert.remove(), 5000);
    } else {
        alert(message);
    }
}

// ==================== دوال الجداول ====================

// تفعيل DataTables إذا كانت موجودة
function initDataTables(tableId, options = {}) {
    const table = document.getElementById(tableId);
    if (table && typeof $ !== 'undefined' && $.fn.DataTable) {
        const defaultOptions = {
            language: {
                url: '//cdn.datatables.net/plug-ins/1.13.6/i18n/ar.json'
            },
            pageLength: 10,
            responsive: true,
            order: [[0, 'desc']]
        };
        
        const mergedOptions = { ...defaultOptions, ...options };
        return $(table).DataTable(mergedOptions);
    }
    return null;
}

// ==================== دوال النماذج ====================

// تفعيل التحقق من النماذج
function initFormValidation(formId) {
    const form = document.getElementById(formId);
    if (!form) return;
    
    form.addEventListener('submit', function(event) {
        let isValid = true;
        const requiredFields = form.querySelectorAll('[required]');
        
        requiredFields.forEach(function(field) {
            if (!field.value.trim()) {
                isValid = false;
                field.classList.add('is-invalid');
                
                // إضافة رسالة خطأ إذا لم تكن موجودة
                let errorDiv = field.nextElementSibling;
                if (!errorDiv || !errorDiv.classList.contains('invalid-feedback')) {
                    errorDiv = document.createElement('div');
                    errorDiv.className = 'invalid-feedback';
                    errorDiv.textContent = 'هذا الحقل مطلوب';
                    field.parentNode.insertBefore(errorDiv, field.nextSibling);
                }
            } else {
                field.classList.remove('is-invalid');
                const errorDiv = field.nextElementSibling;
                if (errorDiv && errorDiv.classList.contains('invalid-feedback')) {
                    errorDiv.remove();
                }
            }
        });
        
        if (!isValid) {
            event.preventDefault();
            showError('يرجى تعبئة جميع الحقول المطلوبة');
        }
    });
    
    // إزالة التحذير عند الكتابة
    form.querySelectorAll('[required]').forEach(function(field) {
        field.addEventListener('input', function() {
            if (this.value.trim()) {
                this.classList.remove('is-invalid');
                const errorDiv = this.nextElementSibling;
                if (errorDiv && errorDiv.classList.contains('invalid-feedback')) {
                    errorDiv.remove();
                }
            }
        });
    });
}

// ==================== دوال البحث والفلترة ====================

function filterTable(searchInputId, tableId, columnIndex = 0) {
    const searchInput = document.getElementById(searchInputId);
    const table = document.getElementById(tableId);
    
    if (!searchInput || !table) return;
    
    searchInput.addEventListener('keyup', function() {
        const searchValue = this.value.toLowerCase();
        const rows = table.getElementsByTagName('tr');
        
        for (let i = 1; i < rows.length; i++) {
            const cell = rows[i].getElementsByTagName('td')[columnIndex];
            if (cell) {
                const cellValue = cell.textContent.toLowerCase();
                rows[i].style.display = cellValue.includes(searchValue) ? '' : 'none';
            }
        }
    });
}

// ==================== دوال التحميل ====================

function showLoading(containerId, message = 'جاري التحميل...') {
    const container = document.getElementById(containerId);
    if (container) {
        container.innerHTML = `
            <div class="text-center p-5">
                <div class="spinner"></div>
                <p class="mt-3">${message}</p>
            </div>
        `;
    }
}

function hideLoading(containerId, originalContent) {
    const container = document.getElementById(containerId);
    if (container && originalContent) {
        container.innerHTML = originalContent;
    }
}

// ==================== دوال التقارير ====================

function downloadReport(url, filename) {
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// ==================== تشغيل عند تحميل الصفحة ====================

document.addEventListener('DOMContentLoaded', function() {
    // تفعيل جميع النماذج
    const forms = document.querySelectorAll('form[data-validate="true"]');
    forms.forEach(function(form) {
        initFormValidation(form.id);
    });
    
    // تفعيل الجداول
    const tables = document.querySelectorAll('table[data-datatable="true"]');
    tables.forEach(function(table) {
        initDataTables(table.id);
    });
    
    console.log('✅ نظام دعم الدفعة 109 جاهز');
});
