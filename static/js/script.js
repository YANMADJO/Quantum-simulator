// static/js/script.js
document.addEventListener('DOMContentLoaded', () => {
    const notifications = document.querySelectorAll('.notification');
    if (notifications.length > 0) {
        notifications.forEach(notification => {
            if (notification.textContent.trim().length > 0) {
                notification.classList.add('show');
            }
        });
    }
});