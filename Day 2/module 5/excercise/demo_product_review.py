# demo_product_review.py

"""
USER STORY:
As a customer, I want to rate and review products so that other customers can make informed decisions.

REQUIREMENTS:
- Customers can rate products from 1 to 5 stars
- Review text is optional but limited to 500 characters
- Customers can only review products they purchased
- Average rating should be calculated from all reviews
"""

# Review storage
reviews_db = {}
review_counter = 2000
purchase_history = {}


def submit_review(product_id, user_id, rating, review_text):
    """Submit product review with rating"""
    global review_counter
    
    if not product_id or not user_id:
        return {"error": "Product ID and User ID required"}
    
    if rating < 1 or rating > 5:
        return {"error": "Rating must be between 1 and 5"}
    
    if len(review_text) > 500:
        return {"error": "Review text must be 500 characters or less"}
    
    # Check purchase eligibility
    if not check_purchase_eligibility(user_id, product_id):
        return {"error": "You must purchase this product before reviewing"}
    
    # Check if user already reviewed this product
    for review in reviews_db.values():
        if review["user_id"] == user_id and review["product_id"] == product_id:
            return {"error": "You have already reviewed this product"}
    
    # Create review
    review_counter += 1
    review_id = f"REV{review_counter}"
    
    review = {
        "review_id": review_id,
        "product_id": product_id,
        "user_id": user_id,
        "rating": rating,
        "review_text": review_text,
        "helpful_count": 0,
        "created_at": "2024-01-01"
    }
    
    reviews_db[review_id] = review
    
    return {"review_id": review_id, "status": "Review submitted successfully"}


def calculate_average_rating(product_id):
    """Calculate average rating from all reviews"""
    if not product_id:
        return {"error": "Product ID required"}
    
    product_reviews = [r for r in reviews_db.values() if r["product_id"] == product_id]
    
    if not product_reviews:
        return {"average_rating": 0, "review_count": 0}
    
    ratings_list = [r["rating"] for r in product_reviews]
    average = sum(ratings_list) / len(ratings_list)
    
    return {
        "product_id": product_id,
        "average_rating": round(average, 1),
        "review_count": len(product_reviews)
    }


def check_purchase_eligibility(user_id, product_id):
    """Check if user purchased the product"""
    if user_id not in purchase_history:
        return False
    
    purchased_products = purchase_history.get(user_id, [])
    return product_id in purchased_products


def filter_reviews(product_id, min_rating):
    """Filter reviews by minimum rating"""
    if not product_id:
        return {"error": "Product ID required"}
    
    if min_rating < 1 or min_rating > 5:
        return {"error": "Minimum rating must be between 1 and 5"}
    
    product_reviews = [r for r in reviews_db.values() if r["product_id"] == product_id]
    
    filtered = []
    for review in product_reviews:
        if review["rating"] >= min_rating:
            filtered.append(review)
    
    return {
        "product_id": product_id,
        "min_rating": min_rating,
        "reviews": filtered,
        "count": len(filtered)
    }


def mark_review_helpful(review_id, user_id):
    """Mark a review as helpful"""
    if not review_id or not user_id:
        return {"error": "Review ID and User ID required"}
    
    if review_id not in reviews_db:
        return {"error": "Review not found"}
    
    review = reviews_db[review_id]
    
    # Increment helpful count
    review["helpful_count"] += 1
    
    return {
        "review_id": review_id,
        "helpful_count": review["helpful_count"],
        "message": "Review marked as helpful"
    }