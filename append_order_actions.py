
code_to_append = """

@login_required
def accept_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, product__seller=request.user)
    if order.status == 'PENDING':
        order.status = 'ACCEPTED'
        order.save()
        
        # Notify buyer
        Notification.objects.create(
            user=order.buyer,
            notification_type='ORDER_ACCEPTED',
            order=order,
            message=f"Your order for {order.product.name} has been accepted! You can now proceed to payment."
        )
        messages.success(request, f"Order #{order.id} accepted.")
    return redirect('dashboard')

@login_required
def reject_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, product__seller=request.user)
    if order.status == 'PENDING':
        order.status = 'REJECTED'
        order.save()
        
        # Notify buyer
        Notification.objects.create(
            user=order.buyer,
            notification_type='ORDER_REJECTED',
            order=order,
            message=f"Your order for {order.product.name} has been rejected."
        )
        messages.warning(request, f"Order #{order.id} rejected.")
    return redirect('dashboard')
"""

with open(r'c:\Users\Admin\Desktop\Monicah - Copy\marketplace\views.py', 'a') as f:
    f.write(code_to_append)
