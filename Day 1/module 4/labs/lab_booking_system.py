# lab_booking_system.py

# Room data and storage
ROOM_PRICES = {"standard": 100, "deluxe": 200, "suite": 350}
available_rooms = {"standard": 10, "deluxe": 5, "suite": 3}
bookings_db = {}
booking_counter = 1000


def check_availability(date, room_type):
    """Check if room is available on given date"""
    if not date or not room_type:
        return {"available": False, "error": "Date and room type required"}
    
    if room_type not in ROOM_PRICES:
        return {"available": False, "error": "Invalid room type"}
    
    rooms_left = available_rooms.get(room_type, 0)
    
    if rooms_left <= 0:
        return {"available": False, "error": "No rooms available"}
    
    return {
        "available": True,
        "rooms": rooms_left,
        "room_type": room_type,
        "price_per_night": ROOM_PRICES[room_type]
    }


def create_booking(guest_name, room_type, checkin, checkout):
    """Create new room booking"""
    global booking_counter
    
    if not guest_name or not room_type:
        return {"error": "Guest name and room type required"}
    
    if not checkin or not checkout:
        return {"error": "Check-in and check-out dates required"}
    
    if checkin >= checkout:
        return {"error": "Check-out must be after check-in"}
    
    # Check availability
    availability = check_availability(checkin, room_type)
    if not availability.get("available"):
        return {"error": availability.get("error")}
    
    # Calculate cost
    nights = (checkout - checkin).days
    if nights > 30:
        return {"error": "Maximum 30 nights allowed"}
    
    total_cost = ROOM_PRICES[room_type] * nights
    tax = total_cost * 0.10
    final_cost = total_cost + tax
    
    # Create booking
    booking_counter += 1
    booking_id = f"BK{booking_counter}"
    
    booking = {
        "booking_id": booking_id,
        "guest_name": guest_name,
        "room_type": room_type,
        "checkin": checkin,
        "checkout": checkout,
        "nights": nights,
        "total_cost": final_cost,
        "status": "confirmed"
    }
    
    bookings_db[booking_id] = booking
    available_rooms[room_type] -= 1
    
    return {"booking_id": booking_id, "status": "confirmed", "total_cost": final_cost}


def cancel_booking(booking_id):
    """Cancel existing booking"""
    if not booking_id:
        return {"error": "Booking ID required"}
    
    if booking_id not in bookings_db:
        return {"error": "Booking not found"}
    
    booking = bookings_db[booking_id]
    
    if booking["status"] == "cancelled":
        return {"error": "Booking already cancelled"}
    
    # Calculate refund (100% if more than 48 hours before checkin)
    import datetime
    hours_until = (booking["checkin"] - datetime.datetime.now()).total_seconds() / 3600
    
    if hours_until > 48:
        refund_amount = booking["total_cost"]
    elif hours_until > 24:
        refund_amount = booking["total_cost"] * 0.5
    else:
        refund_amount = 0
    
    # Update booking
    booking["status"] = "cancelled"
    booking["refund_amount"] = refund_amount
    
    # Restore room availability
    available_rooms[booking["room_type"]] += 1
    
    return {
        "booking_id": booking_id,
        "status": "cancelled",
        "refund_amount": refund_amount
    }


def get_booking_details(booking_id):
    """Get booking information"""
    if not booking_id:
        return {"error": "Booking ID required"}
    
    if booking_id not in bookings_db:
        return {"error": "Booking not found"}
    
    booking = bookings_db[booking_id]
    
    return {
        "booking_id": booking["booking_id"],
        "guest": booking["guest_name"],
        "room": booking["room_type"],
        "checkin": booking["checkin"],
        "checkout": booking["checkout"],
        "nights": booking["nights"],
        "total_cost": booking["total_cost"],
        "status": booking["status"]
    }