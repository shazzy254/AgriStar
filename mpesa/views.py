import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from marketplace.models import Order

@csrf_exempt
def mpesa_callback(request):
    data = json.loads(request.body.decode('utf-8'))
    callback_data = data.get("Body", {}).get("stkCallback", {})
    result_code = callback_data.get("ResultCode")
    
    checkout_request_id = callback_data.get("CheckoutRequestID")
    mpesa_receipt_number = callback_data.get("CallbackMetadata", {}).get("Item", [])
    
    # Extract receipt number if successful
    receipt_number = ""
    if result_code == 0:
        for item in mpesa_receipt_number:
            if item.get("Name") == "MpesaReceiptNumber":
                receipt_number = item.get("Value")
                break
    
    if checkout_request_id:
        try:
            order = Order.objects.get(checkout_request_id=checkout_request_id)
            if result_code == 0:
                order.status = "ESCROW"
                order.mpesa_receipt_number = receipt_number
                order.save()
            else:
                # Handle failure (optional)
                pass
        except Order.DoesNotExist:
            pass
            
    return JsonResponse({"status": "ok"})

@csrf_exempt
def b2c_result(request):
    data = json.loads(request.body.decode('utf-8'))
    # Handle B2C result
    # You might want to update order status here if you track B2C conversation IDs
    print("B2C result:", data)
    return JsonResponse({"status": "ok"})

@csrf_exempt
def b2c_timeout(request):
    data = json.loads(request.body.decode('utf-8'))
    # Handle timeout scenario
    print("B2C timeout:", data)
    return JsonResponse({"status": "ok"})