def calculate_discount(price, discount_percent):
    """Calculate final price after discount"""
    return price - (price * discount_percent / 100)

def is_eligible_for_free_shipping(total_amount, user_type):
    """Check if order qualifies for free shipping"""
    if user_type == "premium":
        return True
    if total_amount > 50:
        return True
    return False