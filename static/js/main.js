// ==================== نظام دعم الدفعة 109 ====================
// تأثيرات حركية متقدمة وتفاعلات عصرية

// تشغيل عند تحميل الصفحة
document.addEventListener('DOMContentLoaded', function() {
    // إضافة كلاس للـ navbar عند التمرير
    const navbar = document.querySelector('.navbar');
    if (navbar) {
        window.addEventListener('scroll', function() {
            if (window.scrollY > 50) {
                navbar.classList.add('scrolled');
            } else {
                navbar.classList.remove('scrolled');
            }
        });
    }
    
    // إخفاء التنبيهات بتأثير حركي
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            alert.style.transition = 'all 0.5s ease';
            alert.style.opacity = '0';
            alert.style.transform = 'translateX(30px)';
            setTimeout(function() {
                if (alert.parentNode) alert.remove();
            }, 500);
        }, 5000);
    });
    
    // تفعيل الـ tooltips
    const tooltips = document.querySelectorAll('[data-toggle="tooltip"]');
    if (tooltips.length > 0 && typeof bootstrap !== 'undefined') {
        tooltips.forEach(function(tooltip) {
            new bootstrap.Tooltip(tooltip);
        });
    }
    
    // إضافة تأثير ظهور تدريجي للعناصر
    const elements = document.querySelectorAll('.card, .stat-card, .hero');
    elements.forEach(function(el, index) {
        el.style.opacity = '0';
        el.style.transform = 'translateY(30px)';
        setTimeout(function() {
            el.style.transition = 'all 0.6s ease';
            el.style.opacity = '1';
            el.style.transform = 'translateY(0)';
        }, index * 100);
    });
});

// ==================== دوال مساعدة ====================

// تأكيد الحذف مع تأثير
function confirmDelete(message) {
    return confirm(`⚠️ ${message || 'هل أنت متأكد من الحذف؟ هذا الإجراء لا يمكن التراجع عنه.'}`);
}

// تأكيد العملية
function confirmAction(message) {
    return confirm(`❓ ${message || 'هل أنت متأكد من تنفيذ هذا الإجراء؟'}`);
}

// تنسيق العملة
function formatCurrency(amount) {
    if (!amount && amount !== 0) return '0 ج.م';
    return new Intl.NumberFormat('ar-EG', {
        style: 'currency',
        currency: 'EGP',
        minimumFractionDigits: 2
    }).format(amount);
}

// تنسيق التاريخ
function formatDate(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return dateString;
    return date.toLocaleDateString('ar-EG', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
}

// تنسيق التاريخ والوقت
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

// التحقق من رقم الهاتف المصري
function isValidPhone(phone) {
    return /^(010|011|012|015)[0-9]{8}$/.test(phone);
}

// التحقق من البريد الإلكتروني
function isValidEmail(email) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

// عرض رسالة نجاح
function showSuccess(message, containerId = 'message-container') {
    showMessage(message, 'success', containerId);
}

// عرض رسالة خطأ
function showError(message, containerId = 'message-container') {
    showMessage(message, 'danger', containerId);
}

// عرض رسالة
function showMessage(message, type, containerId) {
    const container = document.getElementById(containerId);
    if (container) {
        const alert = document.createElement('div');
        alert.className = `alert alert-${type} fade-in-up`;
        alert.innerHTML = `
            <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'danger' ? 'exclamation-circle' : 'info-circle'}"></i>
            ${message}
            <button type="button" class="close" onclick="this.parentElement.remove()">&times;</button>
        `;
        container.appendChild(alert);
        
        setTimeout(() => {
            alert.style.opacity = '0';
            alert.style.transform = 'translateX(30px)';
            setTimeout(() => alert.remove(), 500);
        }, 5000);
    } else {
        alert(message);
    }
}

// ==================== دوال الجداول ====================

function initDataTable(tableId, options = {}) {
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
        return $(table).DataTable({ ...defaultOptions, ...options });
    }
    return null;
}

// ==================== دوال البحث ====================

function filterTable(searchId, tableId, columnIndex = 0) {
    const searchInput = document.getElementById(searchId);
    const table = document.getElementById(tableId);
    if (!searchInput || !table) return;
    
    searchInput.addEventListener('keyup', function() {
        const value = this.value.toLowerCase();
        const rows = table.getElementsByTagName('tr');
        
        for (let i = 1; i < rows.length; i++) {
            const cell = rows[i].getElementsByTagName('td')[columnIndex];
            if (cell) {
                rows[i].style.display = cell.textContent.toLowerCase().includes(value) ? '' : 'none';
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
                <div class="loader"></div>
                <p class="mt-3 text-gradient">${message}</p>
            </div>
        `;
    }
}

function hideLoading(containerId, content) {
    const container = document.getElementById(containerId);
    if (container && content) {
        container.innerHTML = content;
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

// ==================== دوال الإحصائيات ====================

function animateNumber(element, start, end, duration = 1000) {
    if (!element) return;
    let startTimestamp = null;
    const step = (timestamp) => {
        if (!startTimestamp) startTimestamp = timestamp;
        const progress = Math.min((timestamp - startTimestamp) / duration, 1);
        const value = Math.floor(progress * (end - start) + start);
        element.textContent = value.toLocaleString();
        if (progress < 1) {
            window.requestAnimationFrame(step);
        }
    };
    window.requestAnimationFrame(step);
}

// تشغيل عند تحميل الصفحة
document.addEventListener('DOMContentLoaded', function() {
    // تحريك الأرقام في الإحصائيات
    const statNumbers = document.querySelectorAll('.stat-card h3');
    statNumbers.forEach(function(stat) {
        const target = parseInt(stat.textContent.replace(/[^0-9]/g, ''));
        if (target) {
            stat.textContent = '0';
            animateNumber(stat, 0, target, 1000);
        }
    });
    
    console.log('✅ نظام دعم الدفعة 109 - التصميم العصاري جاهز');
});
