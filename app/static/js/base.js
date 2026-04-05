/* 基础 JavaScript - 通用工具函数 */

function showFlashMessage(message, category = 'info') {
    const container = document.querySelector('.flash-messages') || createFlashContainer();
    const alert = document.createElement('div');
    alert.className = `alert alert-${category}`;
    alert.innerHTML = `
        <span>${message}</span>
        <button type="button" class="close-btn" onclick="this.parentElement.remove()">&times;</button>
    `;
    container.appendChild(alert);
    
    setTimeout(() => {
        alert.remove();
    }, 5000);
}

function createFlashContainer() {
    const container = document.createElement('div');
    container.className = 'flash-messages';
    document.body.appendChild(container);
    return container;
}

function formatDateTime(dateStr) {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

document.addEventListener('DOMContentLoaded', function() {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.remove();
        }, 5000);
    });
});
