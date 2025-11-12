# shopping_cart.py

def add_item(cart, item, price, quantity):
    """Add item to shopping cart"""
    if quantity <= 0:
        return "Invalid quantity"
    cart[item] = {"price": price, "quantity": quantity}
    return "Item added"

def remove_item(cart, item):
    """Remove item from cart"""
    if item in cart:
        del cart[item]
        return "Item removed"
    return "Item not found"

def calculate_total(cart):
    """Calculate total cart value"""
    total = 0
    for item in cart:
        total += cart[item]["price"] * cart[item]["quantity"]
    return total

def apply_coupon(total, coupon_code):
    """Apply discount coupon"""
    if coupon_code == "SAVE10":
        return total * 0.9
    elif coupon_code == "SAVE20":
        return total * 0.8
    return total