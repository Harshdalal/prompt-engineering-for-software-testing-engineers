
"""
USER STORY:
As a commerce manager, I want prices to reflect promotions, taxes, and membership rules
so that customers see accurate totals and the business avoids revenue leaks.

REQUIREMENTS:
- Functions to compute base subtotal, apply coupons, membership perks, and taxes
- Coupons: percentage (PCT10), fixed (FLAT5), and BOGO-like for selected SKUs
- Membership: GOLD (5% extra off, free shipping), SILVER (2% extra off if subtotal >= $50)
- Taxes: regional rates; food items taxed differently; tax-exempt SKUs
- Hidden conditions: stacking rules (max 2 discounts), rounding at each stage, min payable $1
- Guardrails: max discount 60% of subtotal; shipping fees vary by region and waived if threshold met
- Output: itemized breakdown and final total; include reason flags for applied rules
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional

# Configuration
CFG = {
    "tax_by_region": {"CA": 0.0825, "NY": 0.088, "TX": 0.0625, "INTL": 0.0},
    "food_tax": 0.0,
    "shipping_by_region": {"CA": 6.99, "NY": 7.99, "TX": 5.99, "INTL": 12.99},
    "free_ship_threshold": 75.0,
    "max_discount_pct": 0.60,
    "stacking_limit": 2,
}

@dataclass
class Item:
    sku: str
    price: float
    qty: int = 1
    category: str = "general"  # "general" | "food"
    tax_exempt: bool = False

@dataclass
class Quote:
    region: str
    membership: Optional[str] = None  # "GOLD" | "SILVER" | None
    coupon_codes: List[str] = field(default_factory=list)

@dataclass
class Breakdown:
    subtotal: float
    discounts: List[Dict] = field(default_factory=list)
    shipping: float = 0.0
    tax: float = 0.0
    total: float = 0.0
    reason_flags: List[str] = field(default_factory=list)

def round_money(x: float) -> float:
    return float(f"{x:.2f}")

def _apply_bogo(items: List[Item], code: str) -> float:
    if code.upper() != "BOGO1":
        return 0.0
    discount = 0.0
    for it in items:
        if it.sku.startswith("B1"):
            free_units = it.qty // 2
            discount += free_units * it.price
    return round_money(discount)

def _apply_coupon(subtotal: float, items: List[Item], code: str) -> float:
    code = code.upper()
    if code.startswith("PCT"):
        try:
            pct = int(code.replace("PCT", "")) / 100.0
        except ValueError:
            return 0.0
        return round_money(subtotal * pct)
    if code.startswith("FLAT"):
        try:
            amt = float(code.replace("FLAT", ""))
        except ValueError:
            return 0.0
        return round_money(min(amt, subtotal))
    if code == "BOGO1":
        return _apply_bogo(items, code)
    return 0.0

def _membership_discount(subtotal: float, membership: Optional[str]) -> float:
    if membership == "GOLD":
        return round_money(subtotal * 0.05)
    if membership == "SILVER" and subtotal >= 50.0:
        return round_money(subtotal * 0.02)
    return 0.0

def _shipping_fee(region: str, membership: Optional[str], subtotal_after_discounts: float) -> float:
    if membership == "GOLD" or subtotal_after_discounts >= CFG["free_ship_threshold"]:
        return 0.0
    return CFG["shipping_by_region"].get(region, CFG["shipping_by_region"]["INTL"])

def _tax_for_item(it: Item, region: str) -> float:
    if it.tax_exempt:
        return 0.0
    if it.category == "food":
        return CFG["food_tax"]
    return CFG["tax_by_region"].get(region, 0.0)

def price_quote(items: List[Item], quote: Quote) -> Breakdown:
    subtotal = round_money(sum(it.price * it.qty for it in items))
    discounts: List[Dict] = []
    reason_flags: List[str] = []

    remaining_stacks = CFG["stacking_limit"]
    total_discount = 0.0

    memb_disc = _membership_discount(subtotal, quote.membership)
    if memb_disc > 0:
        total_discount += memb_disc
        discounts.append({"type": "membership", "amount": memb_disc})
        reason_flags.append(f"membership_{quote.membership.lower()}")
        remaining_stacks -= 1

    for code in quote.coupon_codes:
        if remaining_stacks <= 0:
            reason_flags.append("stacking_limit_reached")
            break
        disc = _apply_coupon(subtotal, items, code)
        if disc <= 0:
            continue
        discounts.append({"type": f"coupon:{code.upper()}", "amount": disc})
        total_discount += disc
        remaining_stacks -= 1

    max_allowed = round_money(subtotal * CFG["max_discount_pct"])
    if total_discount > max_allowed:
        reason_flags.append("discount_cap_applied")
        total_discount = max_allowed

    subtotal_after_discounts = max(0.0, round_money(subtotal - total_discount))

    shipping = round_money(_shipping_fee(quote.region, quote.membership, subtotal_after_discounts))
    if shipping == 0.0:
        reason_flags.append("free_shipping")

    tax_total = 0.0
    for it in items:
        rate = _tax_for_item(it, quote.region)
        tax_total += round_money(it.price * it.qty * rate)
    tax_total = round_money(tax_total)

    total = round_money(subtotal_after_discounts + shipping + tax_total)
    if total < 1.0 and subtotal > 0:
        reason_flags.append("min_payable_enforced")
        total = 1.0

    return Breakdown(
        subtotal=subtotal,
        discounts=discounts,
        shipping=shipping,
        tax=tax_total,
        total=total,
        reason_flags=reason_flags
    )

def quote_from_dict(items: List[Dict], region: str, membership: Optional[str]=None, codes: Optional[List[str]]=None) -> Breakdown:
    it_objs = [Item(**i) for i in items]
    q = Quote(region=region, membership=membership, coupon_codes=(codes or []))
    return price_quote(it_objs, q)
