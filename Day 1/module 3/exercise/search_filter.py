# search_filter.py

def search_products(products, keyword):
    """Search products by keyword"""
    results = []
    for product in products:
        if keyword.lower() in product["name"].lower():
            results.append(product)
    return results

def filter_by_price(products, min_price, max_price):
    """Filter products by price range"""
    filtered = []
    for product in products:
        if min_price <= product["price"] <= max_price:
            filtered.append(product)
    return filtered

def filter_by_category(products, category):
    """Filter products by category"""
    filtered = []
    for product in products:
        if product["category"] == category:
            filtered.append(product)
    return filtered

def sort_products(products, sort_by):
    """Sort products by price or name"""
    if sort_by == "price":
        return sorted(products, key=lambda x: x["price"])
    elif sort_by == "name":
        return sorted(products, key=lambda x: x["name"])
    return products