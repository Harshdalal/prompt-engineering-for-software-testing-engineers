
"""
USER STORY:
As a dispatch coordinator, I want to assign couriers to delivery orders so that food arrives
on time while balancing courier load and minimizing melt/spoil risks.

REQUIREMENTS:
- Orders include prep_time, temperature class (hot/cold), distance, and priority
- Couriers have capacity, vehicle type, and current load with ETA
- Hidden conditions: weather penalty, stacked orders exceeding thermal window, kitchen delays
- Business rules: max distance by vehicle, cap stacked hot items, reassign if ETA slips
- Outcomes: assigned, queued, escalate with reasons and audit trail
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional

CFG = {
    "max_distance_by_vehicle": {"car": 25.0, "bike": 10.0, "scooter": 15.0},
    "hot_stack_cap": 3,
    "cold_stack_cap": 4,
    "thermal_window_min": 12,  # minutes from pickup to dropoff for hot
    "weather_penalty": 1.25,   # increase ETA multiplier
    "reassign_threshold_min": 8,
}

@dataclass
class Order:
    order_id: str
    prep_time_min: int
    temp_class: str  # "hot" | "cold"
    distance_km: float
    priority: int = 0  # 0 normal, 1 vip
    kitchen_delayed: bool = False

@dataclass
class Courier:
    courier_id: str
    vehicle: str
    capacity: int
    current_load: int = 0
    eta_min: int = 0
    hot_stack: int = 0
    cold_stack: int = 0
    risk_flags: List[str] = field(default_factory=list)

@dataclass
class Assignment:
    status: str
    courier_id: Optional[str]
    reasons: List[str] = field(default_factory=list)
    rule_hits: List[str] = field(default_factory=list)

class Dispatcher:
    def __init__(self, weather_bad: bool = False):
        self.weather_bad = weather_bad
        self.queue: List[Order] = []

    def _eligible(self, c: Courier, o: Order, reasons: List[str], rule_hits: List[str]) -> bool:
        maxd = CFG["max_distance_by_vehicle"].get(c.vehicle, 12.0)
        if o.distance_km > maxd:
            reasons.append("distance_exceeds_vehicle_limit")
            return False
        if c.current_load >= c.capacity:
            reasons.append("courier_at_capacity")
            return False
        if o.temp_class == "hot" and c.hot_stack >= CFG["hot_stack_cap"]:
            reasons.append("hot_stack_cap_reached")
            return False
        if o.temp_class == "cold" and c.cold_stack >= CFG["cold_stack_cap"]:
            reasons.append("cold_stack_cap_reached")
            return False
        rule_hits.append("eligibility_ok")
        return True

    def _eta(self, c: Courier, o: Order, rule_hits: List[str]) -> int:
        prep = o.prep_time_min
        travel = int(round(o.distance_km / 0.5))  # 0.5 km/min baseline
        eta = prep + travel + c.eta_min + c.current_load * 2
        if self.weather_bad:
            eta = int(eta * CFG["weather_penalty"])
        if o.kitchen_delayed:
            eta += 5
        rule_hits.append("eta_computed")
        return eta

    def _thermal_violation(self, eta: int, o: Order, rule_hits: List[str]) -> bool:
        if o.temp_class == "hot" and eta > CFG["thermal_window_min"]:
            rule_hits.append("thermal_violation")
            return True
        return False

    def _update_courier(self, c: Courier, o: Order):
        c.current_load += 1
        if o.temp_class == "hot":
            c.hot_stack += 1
        else:
            c.cold_stack += 1
        c.eta_min += max(2, int(o.distance_km / 1.0))

    def assign(self, couriers: List[Courier], order: Order) -> Assignment:
        reasons: List[str] = []
        rule_hits: List[str] = []

        if order.distance_km <= 0 or order.prep_time_min < 0 or order.temp_class not in {"hot", "cold"}:
            return Assignment(status="escalate", courier_id=None, reasons=["invalid_order"], rule_hits=rule_hits)

        ranked: List[Dict] = []
        for c in couriers:
            local_reasons: List[str] = []
            if not self._eligible(c, order, local_reasons, rule_hits):
                continue
            eta = self._eta(c, order, rule_hits)
            ranked.append({"courier": c, "eta": eta, "reasons": local_reasons})

        if not ranked:
            self.queue.append(order)
            return Assignment(status="queued", courier_id=None, reasons=["no_eligible_courier"], rule_hits=rule_hits)

        ranked.sort(key=lambda x: (x["eta"] - order.priority * 3, x["courier"].current_load))

        # Choose best feasible option avoiding thermal violation
        for option in ranked:
            if not self._thermal_violation(option["eta"], order, rule_hits):
                chosen = option["courier"]
                self._update_courier(chosen, order)
                return Assignment(status="assigned", courier_id=chosen.courier_id, reasons=option["reasons"], rule_hits=rule_hits)

        # All options violate thermal window -> escalate
        return Assignment(status="escalate", courier_id=None, reasons=["thermal_window_risk"], rule_hits=rule_hits)

    def reassign_if_slip(self, c: Courier, order: Order, new_eta_min: int) -> Assignment:
        reasons: List[str] = []
        rule_hits: List[str] = ["reassign_check"]
        if new_eta_min - c.eta_min >= CFG["reassign_threshold_min"]:
            reasons.append("eta_slip_detected")
            # naive reassign to queue
            self.queue.append(order)
            c.current_load = max(0, c.current_load - 1)
            return Assignment(status="queued", courier_id=None, reasons=reasons, rule_hits=rule_hits)
        return Assignment(status="retained", courier_id=c.courier_id, reasons=["within_eta_tolerance"], rule_hits=rule_hits)
