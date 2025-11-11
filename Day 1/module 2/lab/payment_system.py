# payment_system.py

def process_payment(amount, card_number, cvv):
    """
    Process payment transaction
    Rules:
    - Amount must be positive
    - Card number must be 16 digits
    - CVV must be 3 digits
    """
    if amount <= 0:
        return "Invalid amount"
    if len(card_number) != 16:
        return "Invalid card"
    if len(cvv) != 3:
        return "Invalid CVV"
    return "Payment successful"


def calculate_tax(amount, country):
    """
    Calculate tax based on country
    US: 10%
    UK: 20%
    Other: 5%
    """
    if country == "US":
        return amount * 0.10
    elif country == "UK":
        return amount * 0.20
    else:
        return amount * 0.05