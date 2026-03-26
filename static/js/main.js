// ==================== نظام دعم الدفعة 109 ====================
// تفاعلات متقدمة وتجاوب كامل

document.addEventListener('DOMContentLoaded', function() {
    // ==================== شريط التنقل للموبايل ====================
    const navbarToggler = document.querySelector('.navbar-toggler');
    const navLinks = document.querySelector('.nav-links');
    
    if (navbarToggler && navLinks) {
        navbarToggler.addEventListener('click', function() {
            navLinks.classList.toggle('active');
        });
    }
    
    // ==================== إغلاق القائمة عند النقر على رابط ====================
    const navItems = document.querySelectorAll('.nav-links a');
    navItems.forEach(function(item) {
        item.addEventListener('click', function() {
            if (window.innerWidth <= 768 && navLinks) {
                navLinks.classList.remove('active');
            }
        });
    });
    
    // ==================== إخفاء التنبيهات تلقائياً ====================
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
    
    // ==================== التحقق من صحة النماذج ====================
    const forms = document.querySelectorAll('form[data-validate="true"]');
    forms.forEach(function(form) {
        form.addEventListener('submit', function(event) {
            let isValid = true;
            const requiredFields = form.querySelectorAll('[required]');
            
            requiredFields.forEach(function(field) {
                if (!field.value.trim()) {
                    isValid = false;
                    field.classList.add('is-invalid');
                    
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
                showMessage('يرجى تعبئة جميع الحقول المطلوبة', 'danger');
            }
        });
        
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
    });
    
    // ==================== تحريك الأرقام في الإحصائيات ====================
    const statNumbers = document.querySelectorAll('.stat-card h3');
    statNumbers.forEach(function(stat) {
        const target = parseInt(stat.textContent.replace(/[^0-9]/g, ''));
        if (target && target > 0) {
            const originalText = stat.textContent;
            stat.textContent = '0';
            animateNumber(stat, 0, target, 1000, originalText);
        }
    });
    
    // ==================== تفعيل التلميحات ====================
    const tooltips = document.querySelectorAll('[data-toggle="tooltip"]');
    if (tooltips.length > 0 && typeof bootstrap !== 'undefined') {
        tooltips.forEach(function(tooltip) {
            new bootstrap.Tooltip(tooltip);
        });
    }
    
    console.log('✅ نظام دعم الدفعة 109 جاهز');
});

// ==================== دوال مساعدة ====================

// تحريك الأرقام
function animateNumber(element, start, end, duration, originalText) {
    if (!element) return;
    let startTimestamp = null;
    const isCurrency = originalText ? originalText.includes('ج') : false;
    
    const step = (timestamp) => {
        if (!startTimestamp) startTimestamp = timestamp;
        const progress = Math.min((timestamp - startTimestamp) / duration, 1);
        const value = Math.floor(progress * (end - start) + start);
        
        if (isCurrency) {
            element.textContent = formatCurrency(value);
        } else {
            element.textContent = value.toLocaleString();
        }
        
        if (progress < 1) {
            window.requestAnimationFrame(step);
        }
    };
    window.requestAnimationFrame(step);
}

// عرض رسالة
function showMessage(message, type = 'info', containerId = 'message-container') {
    const container = document.getElementById(containerId);
    if (container) {
        const alert = document.createElement('div');
        alert.className = `alert alert-${type} fade-in-up`;
        alert.innerHTML = `
            <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'danger' ? 'exclamation-circle' : 'info-circle'}"></i>
            <span>${message}</span>
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

// التحقق من رقم الهاتف المصري
function isValidPhone(phone) {
    return /^(010|011|012|015)[0-9]{8}$/.test(phone);
}

// التحقق من البريد الإلكتروني
function isValidEmail(email) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

// تأكيد الحذف
function confirmDelete(message) {
    return confirm(`⚠️ ${message || 'هل أنت متأكد من الحذف؟ هذا الإجراء لا يمكن التراجع عنه.'}`);
}

// تأكيد العملية
function confirmAction(message) {
    return confirm(`❓ ${message || 'هل أنت متأكد من تنفيذ هذا الإجراء؟'}`);
}

// التحقق من رقم الهاتف (API)
async function checkPhoneExists(phone) {
    try {
        const response = await fetch(`/api/check-phone?phone=${encodeURIComponent(phone)}`);
        const data = await response.json();
        return data.exists;
    } catch (error) {
        console.error('Error checking phone:', error);
        return false;
    }
}

// إرسال كود استرجاع كلمة السر
async function sendResetCode(phone) {
    try {
        const response = await fetch('/api/send-reset-code', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ phone })
        });
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error sending reset code:', error);
        return { success: false, message: 'حدث خطأ في الاتصال' };
    }
}

// إعادة تعيين كلمة السر
async function resetPassword(phone, code, newPassword) {
    try {
        const response = await fetch('/api/reset-password', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ phone, code, new_password: newPassword })
        });
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error resetting password:', error);
        return { success: false, message: 'حدث خطأ في الاتصال' };
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
        const originalContent = container.innerHTML;
        container.setAttribute('data-original', originalContent);
        container.innerHTML = `
            <div class="text-center p-5">
                <div class="loader"></div>
                <p class="mt-3 text-gradient">${message}</p>
            </div>
        `;
    }
}

function hideLoading(containerId) {
    const container = document.getElementById(containerId);
    if (container && container.getAttribute('data-original')) {
        container.innerHTML = container.getAttribute('data-original');
        container.removeAttribute('data-original');
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

// ==================== تغيير وضع الأدمن ====================
function enableAdminMode() {
    document.body.classList.add('admin-mode');
}

function disableAdminMode() {
    document.body.classList.remove('admin-mode');
}
