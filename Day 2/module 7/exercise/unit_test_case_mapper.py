
"""
This script simulates mapping of Copilot-generated unit test outputs into manual test cases.
It provides templates that participants can refine using prompt engineering.
"""

def example_copilot_unit_test_output():
    return {
        "test_name": "test_gold_member_with_pct10_coupon",
        "setup": {
            "items": [{"sku": "A1", "price": 20.0, "qty": 3}],
            "region": "CA",
            "membership": "GOLD",
            "coupons": ["PCT10"]
        },
        "asserts": {
            "subtotal": 60.00,
            "discount_total": 9.00,
            "shipping": 0.00,
            "tax": 4.95,
            "total": 55.95,
            "flags": ["membership_gold", "free_shipping"]
        }
    }

def convert_to_manual_test(unit_test):
    setup = unit_test["setup"]
    asserts = unit_test["asserts"]
    print("Manual Test Case:")
    print(f"Input items: {setup['items']}")
    print(f"Region: {setup['region']} | Membership: {setup['membership']} | Coupons: {setup['coupons']}")
    print("Expected Results:")
    for k, v in asserts.items():
        print(f"  - {k}: {v}")
    print("This mirrors the Copilot unit test, expressed as a manual case.")

if __name__ == "__main__":
    convert_to_manual_test(example_copilot_unit_test_output())
