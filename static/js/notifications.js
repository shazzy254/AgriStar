// Notifications functionality with AJAX support

document.addEventListener('DOMContentLoaded', function () {
    // Update notification count on page load
    updateNotificationCount();

    // Mark notification as read on click
    document.querySelectorAll('.notification-item').forEach(item => {
        item.addEventListener('click', function () {
            const notificationId = this.dataset.notificationId;
            const isRead = this.dataset.isRead === 'true';

            if (!isRead) {
                markNotificationAsRead(notificationId);
            }
        });
    });

    // Mark all as read button
    const markAllReadBtn = document.querySelector('#mark-all-read-btn');
    if (markAllReadBtn) {
        markAllReadBtn.addEventListener('click', function (e) {
            e.preventDefault();
            markAllNotificationsAsRead();
        });
    }

    // Auto-refresh notification count every 30 seconds
    setInterval(updateNotificationCount, 30000);
});

// Mark single notification as read
function markNotificationAsRead(notificationId) {
    const csrfToken = getCsrfToken();

    fetch(`/marketplace/notifications/${notificationId}/read/`, {
        method: 'POST',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': csrfToken
        }
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Update notification item styling
                const notificationItem = document.querySelector(`[data-notification-id="${notificationId}"]`);
                if (notificationItem) {
                    notificationItem.classList.remove('unread');
                    notificationItem.dataset.isRead = 'true';
                }

                // Update badge
                updateNotificationBadge(data.unread_count);
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
}

// Mark all notifications as read
function markAllNotificationsAsRead() {
    const csrfToken = getCsrfToken();

    fetch('/marketplace/notifications/read-all/', {
        method: 'POST',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': csrfToken
        }
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Update all notification items
                document.querySelectorAll('.notification-item.unread').forEach(item => {
                    item.classList.remove('unread');
                    item.dataset.isRead = 'true';
                });

                // Update badge
                updateNotificationBadge(0);

                showToast('All notifications marked as read', 'success');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showToast('An error occurred', 'error');
        });
}

// Update notification count (could be called periodically)
function updateNotificationCount() {
    const notificationBadge = document.querySelector('.notification-badge .badge');
    if (notificationBadge) {
        // Badge is already rendered by Django template
        return;
    }
}

// Update notification badge
function updateNotificationBadge(count) {
    const notificationBadge = document.querySelector('.notification-badge .badge');
    if (notificationBadge) {
        notificationBadge.textContent = count;

        if (count === 0) {
            notificationBadge.style.display = 'none';
        } else {
            notificationBadge.style.display = 'inline-block';
        }
    }
}

// Get CSRF token
function getCsrfToken() {
    const cookieValue = document.cookie
        .split('; ')
        .find(row => row.startsWith('csrftoken='))
        ?.split('=')[1];
    return cookieValue;
}

// Show toast notification
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast-notification alert alert-${type === 'success' ? 'success' : type === 'error' ? 'danger' : 'info'}`;
    toast.innerHTML = `
        <div class="d-flex align-items-center">
            <i class="bi bi-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'} me-2"></i>
            <span>${message}</span>
        </div>
    `;

    document.body.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'slideOutRight 0.3s ease';
        setTimeout(() => {
            toast.remove();
        }, 300);
    }, 3000);
}

// Favorite toggle functionality
document.addEventListener('click', function (e) {
    if (e.target.closest('.favorite-btn')) {
        e.preventDefault();
        const button = e.target.closest('.favorite-btn');
        const productId = button.dataset.productId;

        toggleFavorite(productId, button);
    }
});

// Toggle favorite
function toggleFavorite(productId, button) {
    const csrfToken = getCsrfToken();

    fetch(`/marketplace/favorites/toggle/${productId}/`, {
        method: 'POST',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': csrfToken
        }
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Toggle active class
                if (data.is_favorited) {
                    button.classList.add('active');
                } else {
                    button.classList.remove('active');
                }

                showToast(data.message, 'success');
            } else {
                showToast('Failed to update favorite', 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showToast('An error occurred', 'error');
        });
}
