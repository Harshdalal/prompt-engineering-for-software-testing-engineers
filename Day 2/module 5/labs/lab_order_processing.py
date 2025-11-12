# lab_order_processing.py

"""
USER STORY:
As a customer, I want to place and track orders so that I can receive my purchased items.

REQUIREMENTS:
- Customers can place orders with multiple items
- Order total must be greater than $10
- Free shipping for orders above $50
- Orders can be cancelled within 24 hours
- Order status: pending, confirmed, shipped, delivered, cancelled
"""

# Order storage and tracking
orders_db = {}
order_counter = 5000


def create_order(customer_id, items, total_amount):
    """Create new order"""
    global order_counter
    
    if not customer_id:
        return {"error": "Customer ID required"}
    
    if total_amount < 10:
        return {"error": "Order minimum is $10"}
    
    if not items or len(items) == 0:
        return {"error": "Order must have items"}
    
    # Validate items structure
    for item in items:
        if "name" not in item or "quantity" not in item or "price" not in item:
            return {"error": "Invalid item format"}
        if item["quantity"] <= 0:
            return {"error": "Item quantity must be positive"}
    
    # Calculate shipping
    shipping_cost = calculate_shipping(total_amount)
    final_total = total_amount + shipping_cost
    
    # Create order
    order_counter += 1
    order_id = f"ORD{order_counter}"
    
    import datetime
    order = {
        "order_id": order_id,
        "customer_id": customer_id,
        "items": items,
        "subtotal": total_amount,
        "shipping": shipping_cost,
        "total": final_total,
        "status": "pending",
        "created_at": datetime.datetime.now()
    }
    
    orders_db[order_id] = order
    
    return {"order_id": order_id, "status": "pending", "total": final_total}


def calculate_shipping(total_amount):
    """Calculate shipping cost"""
    if total_amount >= 50:
        return 0
    elif total_amount >= 30:
        return 3.99
    else:
        return 5.99


def cancel_order(order_id, hours_since_order):
    """Cancel order if within 24 hours"""
    if not order_id:
        return {"error": "Order ID required"}
    
    if order_id not in orders_db:
        return {"error": "Order not found"}
    
    order = orders_db[order_id]
    
    if order["status"] == "cancelled":
        return {"error": "Order already cancelled"}
    
    if order["status"] in ["shipped", "delivered"]:
        return {"error": f"Cannot cancel {order['status']} order"}
    
    if hours_since_order > 24:
        return {"error": "Cannot cancel after 24 hours"}
    
    # Calculate refund
    if hours_since_order <= 24:
        refund_amount = order["total"]
    else:
        refund_amount = 0
    
    # Update order
    order["status"] = "cancelled"
    order["refund_amount"] = refund_amount
    
    return {
        "order_id": order_id,
        "status": "cancelled",
        "refund_amount": refund_amount
    }


def update_order_status(order_id, new_status):
    """Update order status"""
    valid_statuses = ["pending", "confirmed", "shipped", "delivered", "cancelled"]
    
    if not order_id:
        return {"error": "Order ID required"}
    
    if new_status not in valid_statuses:
        return {"error": "Invalid status"}
    
    if order_id not in orders_db:
        return {"error": "Order not found"}
    
    order = orders_db[order_id]
    current_status = order["status"]
    
    # Validate status transitions
    if current_status == "cancelled":
        return {"error": "Cannot update cancelled order"}
    
    if current_status == "delivered":
        return {"error": "Cannot update delivered order"}
    
    # Update status
    order["status"] = new_status
    
    return {
        "order_id": order_id,
        "status": new_status,
        "message": f"Status updated to {new_status}"
    }


def apply_discount_code(total_amount, discount_code):
    """Apply discount code to order"""
    if not discount_code:
        return total_amount
    
    discount_code = discount_code.upper()
    
    if discount_code == "SAVE10":
        discounted = total_amount * 0.9
    elif discount_code == "SAVE20":
        discounted = total_amount * 0.8
    elif discount_code == "SAVE30":
        discounted = total_amount * 0.7
    else:
        return {"error": "Invalid discount code"}
    
    # Minimum order after discount
    if discounted < 10:
        return {"error": "Order total after discount must be at least $10"}
    
    return discounted