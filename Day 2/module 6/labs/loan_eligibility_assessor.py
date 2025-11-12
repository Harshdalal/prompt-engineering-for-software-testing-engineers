
"""
USER STORY:
As a loan officer, I want to automatically assess loan applications so that I can quickly
identify eligible borrowers and risky cases requiring manual review.

REQUIREMENTS:
- Validate applicant inputs (age, income, credit score, employment months, requested amount)
- Compute Debt-to-Income (DTI) and flag high-risk thresholds
- Region-specific rules (e.g., restricted regions, minimum income floors)
- Hidden conditions: inconsistent income sources, sudden employment gap, prior defaults
- Overlays: allow soft-approval with collateral or co-signer if close to thresholds
- Output decision: approved, soft_approved, manual_review, declined with reasons
- Traceability: retain rule hits and risk flags for QA review
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional

# Risk configuration (tuned by policy team)
RISK_CFG = {
    "min_age": 18,
    "max_age": 70,
    "min_income": 18000,          # annual
    "min_credit": 600,
    "max_dti": 0.43,              # common mortgage-like heuristic
    "soft_approve_dti": 0.48,     # allow with co-signer/collateral
    "max_amount_multiplier": 6,   # 6x monthly income ceiling
    "restricted_regions": {"OFAC-BLK", "ZZ-999"},
    "income_floor_by_region": {"US-CA": 24000, "US-NY": 26000, "IN-MH": 300000},
    "recent_gap_months": 3,
    "prior_default_cooldown_years": 5,
}

@dataclass
class Applicant:
    applicant_id: str
    age: int
    annual_income: float
    monthly_debt: float
    credit_score: int
    employment_months: int
    region: str
    requested_amount: float
    has_collateral: bool = False
    has_cosigner: bool = False
    prior_default_years_ago: Optional[int] = None
    income_sources: List[Dict] = field(default_factory=list)  # [{"type": "salary", "amount": 1000, "stable": True}, ...]

@dataclass
class Decision:
    status: str                  # approved | soft_approved | manual_review | declined
    max_amount: float
    apr: float
    reasons: List[str] = field(default_factory=list)
    risk_flags: List[str] = field(default_factory=list)
    rule_hits: List[str] = field(default_factory=list)

def _cap_amount_by_income(app: Applicant, rule_hits: List[str]) -> float:
    monthly_income = app.annual_income / 12.0
    cap = max(0.0, monthly_income * RISK_CFG["max_amount_multiplier"])
    rule_hits.append("max_amount_multiplier")
    return min(app.requested_amount, cap)

def _regional_income_floor(app: Applicant, reasons: List[str], rule_hits: List[str]) -> bool:
    floor = RISK_CFG["income_floor_by_region"].get(app.region, RISK_CFG["min_income"])
    rule_hits.append(f"income_floor_region:{app.region}")
    if app.annual_income < floor:
        reasons.append(f"income below regional floor ({floor})")
        return False
    return True

def _validate_inputs(app: Applicant, reasons: List[str], rule_hits: List[str]) -> bool:
    ok = True
    if app.age < RISK_CFG["min_age"] or app.age > RISK_CFG["max_age"]:
        reasons.append("age out of bounds")
        ok = False
    if app.credit_score < 300 or app.credit_score > 850:
        reasons.append("invalid credit score")
        ok = False
    if app.employment_months < 0:
        reasons.append("employment months negative")
        ok = False
    if app.requested_amount <= 0:
        reasons.append("requested amount must be positive")
        ok = False
    rule_hits.append("input_validation")
    return ok

def _hidden_conditions(app: Applicant, risk_flags: List[str], rule_hits: List[str]) -> None:
    # Inconsistent income (e.g., >40% from unstable sources)
    if app.income_sources:
        total = sum(src.get("amount", 0) for src in app.income_sources)
        unstable = sum(src.get("amount", 0) for src in app.income_sources if not src.get("stable", True))
        if total > 0 and (unstable / total) > 0.4:
            risk_flags.append("income_instability_high")
    # Employment gap
    if app.employment_months < 12 and app.employment_months <= RISK_CFG["recent_gap_months"]:
        risk_flags.append("recent_employment_gap")
    # Prior default
    if app.prior_default_years_ago is not None and app.prior_default_years_ago < RISK_CFG["prior_default_cooldown_years"]:
        risk_flags.append("recent_prior_default")
    rule_hits.append("hidden_conditions_scan")

def _region_blocklist(app: Applicant, reasons: List[str], rule_hits: List[str]) -> bool:
    if app.region in RISK_CFG["restricted_regions"]:
        reasons.append("region restricted")
        rule_hits.append("region_blocked")
        return False
    rule_hits.append("region_allowed")
    return True

def _compute_dti(app: Applicant, rule_hits: List[str]) -> float:
    gross_monthly = max(1.0, app.annual_income / 12.0)  # avoid div-by-zero
    dti = app.monthly_debt / gross_monthly
    rule_hits.append("dti_computed")
    return dti

def assess_application(app: Applicant) -> Decision:
    reasons: List[str] = []
    risk_flags: List[str] = []
    rule_hits: List[str] = []

    if not _validate_inputs(app, reasons, rule_hits):
        return Decision(status="declined", max_amount=0.0, apr=0.0, reasons=reasons, risk_flags=risk_flags, rule_hits=rule_hits)

    if not _region_blocklist(app, reasons, rule_hits):
        return Decision(status="declined", max_amount=0.0, apr=0.0, reasons=reasons, risk_flags=risk_flags, rule_hits=rule_hits)

    if not _regional_income_floor(app, reasons, rule_hits):
        return Decision(status="declined", max_amount=0.0, apr=0.0, reasons=reasons, risk_flags=risk_flags, rule_hits=rule_hits)

    dti = _compute_dti(app, rule_hits)
    if dti > 0.8:
        reasons.append("DTI extreme")
    elif dti > RISK_CFG["soft_approve_dti"]:
        risk_flags.append("dti_high_soft")
    elif dti > RISK_CFG["max_dti"]:
        risk_flags.append("dti_above_max")

    if app.credit_score < RISK_CFG["min_credit"]:
        risk_flags.append("credit_below_min")

    _hidden_conditions(app, risk_flags, rule_hits)

    # Determine max lendable amount and APR tiers
    max_amount = _cap_amount_by_income(app, rule_hits)
    apr_base = 0.12 if app.credit_score >= 720 else (0.18 if app.credit_score >= 650 else 0.24)
    apr_penalty = 0.03 if dti > 0.4 else 0.0
    apr = round(apr_base + apr_penalty, 3)

    # Decision logic layering
    if "DTI extreme" in reasons:
        return Decision(status="declined", max_amount=0.0, apr=0.0, reasons=reasons, risk_flags=risk_flags, rule_hits=rule_hits)

    # Hard declines
    if "region restricted" in reasons:
        return Decision(status="declined", max_amount=0.0, apr=0.0, reasons=reasons, risk_flags=risk_flags, rule_hits=rule_hits)

    # Soft approval path if close to thresholds and mitigants exist
    near_threshold = ("dti_above_max" in risk_flags) or ("credit_below_min" in risk_flags)
    mitigants = app.has_collateral or app.has_cosigner
    if near_threshold and mitigants and max_amount > 0:
        return Decision(status="soft_approved", max_amount=max_amount * 0.8, apr=apr + 0.02,
                        reasons=["soft approval with mitigants"], risk_flags=risk_flags, rule_hits=rule_hits)

    # Manual review if hidden risks present
    if {"income_instability_high", "recent_employment_gap", "recent_prior_default"} & set(risk_flags):
        return Decision(status="manual_review", max_amount=max_amount * 0.6, apr=apr + 0.01,
                        reasons=["hidden risks detected"], risk_flags=risk_flags, rule_hits=rule_hits)

    # Approve if all core checks pass
    if dti <= RISK_CFG["max_dti"] and app.credit_score >= RISK_CFG["min_credit"] and max_amount > 0:
        return Decision(status="approved", max_amount=max_amount, apr=apr,
                        reasons=["meets policy thresholds"], risk_flags=risk_flags, rule_hits=rule_hits)

    # Fallback: manual review for ambiguous cases
    return Decision(status="manual_review", max_amount=max_amount * 0.5, apr=apr + 0.01,
                    reasons=["policy edge case"], risk_flags=risk_flags, rule_hits=rule_hits)
