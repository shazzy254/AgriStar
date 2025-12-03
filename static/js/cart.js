// Cart functionality with AJAX support

document.addEventListener('DOMContentLoaded', function () {
    // Update cart count on page load
    updateCartCount();

    // Add to cart buttons
    document.querySelectorAll('.add-to-cart-btn').forEach(button => {
        button.addEventListener('click', function (e) {
            e.preventDefault();
            const productId = this.dataset.productId;
            const quantityInput = document.querySelector(`#quantity-${productId}`);
            const quantity = quantityInput ? quantityInput.value : 1;

            addToCart(productId, quantity);
        });
    });

    // Quantity update buttons
    document.querySelectorAll('.update-quantity-btn').forEach(button => {
        button.addEventListener('click', function (e) {
            e.preventDefault();
            const itemId = this.dataset.itemId;
            const quantity = this.dataset.quantity;

            updateCartItemQuantity(itemId, quantity);
        });
    });

    // Remove from cart buttons
    document.querySelectorAll('.remove-cart-item-btn').forEach(button => {
        button.addEventListener('click', function (e) {
            e.preventDefault();
            const itemId = this.dataset.itemId;

            if (confirm('Remove this item from cart?')) {
                removeFromCart(itemId);
            }
        });
    });
});

// Add product to cart
function addToCart(productId, quantity = 1) {
    const csrfToken = getCsrfToken();

    fetch(`/marketplace/cart/add/${productId}/`, {
        method: 'POST',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': csrfToken
        },
        body: `quantity=${quantity}`
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showToast(data.message, 'success');
                updateCartBadge(data.cart_count);
            } else {
                showToast(data.error || 'Failed to add to cart', 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showToast('An error occurred', 'error');
        });
}

// Update cart item quantity
function updateCartItemQuantity(itemId, quantity) {
    const csrfToken = getCsrfToken();

    fetch(`/marketplace/cart/update/${itemId}/`, {
        method: 'POST',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': csrfToken
        },
        body: `quantity=${quantity}`
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Update item total
                const itemTotalElement = document.querySelector(`#item-total-${itemId}`);
                if (itemTotalElement) {
                    itemTotalElement.textContent = `$${data.item_total.toFixed(2)}`;
                }

                // Update cart total
                const cartTotalElement = document.querySelector('#cart-total');
                if (cartTotalElement) {
                    cartTotalElement.textContent = `$${data.cart_total.toFixed(2)}`;
                }

                // Update quantity display
                const quantityElement = document.querySelector(`#quantity-${itemId}`);
                if (quantityElement) {
                    quantityElement.value = quantity;
                }
            } else {
                showToast(data.error || 'Failed to update quantity', 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showToast('An error occurred', 'error');
        });
}

// Remove item from cart
function removeFromCart(itemId) {
    const csrfToken = getCsrfToken();

    fetch(`/marketplace/cart/remove/${itemId}/`, {
        method: 'POST',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': csrfToken
        }
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showToast(data.message, 'success');
                updateCartBadge(data.cart_count);

                // Remove item from DOM
                const itemElement = document.querySelector(`#cart-item-${itemId}`);
                if (itemElement) {
                    itemElement.style.transition = 'opacity 0.3s ease';
                    itemElement.style.opacity = '0';
                    setTimeout(() => {
                        itemElement.remove();

                        // Check if cart is empty
                        const cartItems = document.querySelectorAll('.cart-item-card');
                        if (cartItems.length === 0) {
                            location.reload();
                        }
                    }, 300);
                }
            } else {
                showToast(data.error || 'Failed to remove item', 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showToast('An error occurred', 'error');
        });
}

// Update cart count
function updateCartCount() {
    const cartBadge = document.querySelector('.cart-badge .badge');
    if (cartBadge) {
        // Badge is already rendered by Django template
        return;
    }
}

// Update cart badge
function updateCartBadge(count) {
    const cartBadge = document.querySelector('.cart-badge .badge');
    if (cartBadge) {
        cartBadge.textContent = count;

        if (count === 0) {
            cartBadge.style.display = 'none';
        } else {
            cartBadge.style.display = 'inline-block';
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

// Quantity increment/decrement
document.addEventListener('click', function (e) {
    if (e.target.classList.contains('qty-increment')) {
        const input = e.target.parentElement.querySelector('.quantity-input');
        input.value = parseInt(input.value) + 1;

        const itemId = e.target.dataset.itemId;
        if (itemId) {
            updateCartItemQuantity(itemId, input.value);
        }
    }

    if (e.target.classList.contains('qty-decrement')) {
        const input = e.target.parentElement.querySelector('.quantity-input');
        if (parseInt(input.value) > 1) {
            input.value = parseInt(input.value) - 1;

            const itemId = e.target.dataset.itemId;
            if (itemId) {
                updateCartItemQuantity(itemId, input.value);
            }
        }
    }
});
