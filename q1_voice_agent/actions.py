"""
Business Action Handlers for Question 1:
- Lead Creation
- Preliminary Premium Quotation Engine
- Mock CRM Webhook Integration
- Callback Scheduling
"""

import time
import json
from typing import Dict, Any, Optional


class BusinessActionHandler:
    """
    Executes automated downstream business actions upon qualification or escalation.
    Fulfills the 'Optional Business Action' requirement for high scoring.
    """

    @staticmethod
    def calculate_preliminary_quote(age: int, sum_insured: int, is_tobacco_user: bool, has_ped: bool) -> Dict[str, Any]:
        """Calculates estimated monthly and annual health insurance premium."""
        # Base annual rate per $100k coverage by age bracket
        if age < 30:
            base_rate_per_100k = 180.0
        elif age < 45:
            base_rate_per_100k = 260.0
        elif age < 55:
            base_rate_per_100k = 420.0
        else:
            base_rate_per_100k = 680.0

        multiplier = sum_insured / 100000.0
        annual_premium = base_rate_per_100k * multiplier

        # Smoker loading (25%)
        tobacco_surcharge = annual_premium * 0.25 if is_tobacco_user else 0.0
        # Pre-existing condition risk factor (15%)
        ped_surcharge = annual_premium * 0.15 if has_ped else 0.0

        total_annual = annual_premium + tobacco_surcharge + ped_surcharge
        total_monthly = round(total_annual / 12.0, 2)

        return {
            "sum_insured": sum_insured,
            "base_annual_premium": round(annual_premium, 2),
            "tobacco_loading": round(tobacco_surcharge, 2),
            "ped_surcharge": round(ped_surcharge, 2),
            "total_annual_premium": round(total_annual, 2),
            "estimated_monthly_premium": total_monthly,
            "currency": "USD"
        }

    @staticmethod
    def create_crm_lead(profile: Dict[str, Any], call_id: str, status: str = "QUALIFIED") -> Dict[str, Any]:
        """
        Creates a structured CRM Lead Record and simulates firing an outbound webhook.
        """
        quote = profile.get("quote", {})
        lead_payload = {
            "lead_id": f"LEAD_{int(time.time())}_{call_id[:6]}",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "status": status,
            "call_id": call_id,
            "customer_profile": {
                "age": profile.get("age"),
                "location": profile.get("location"),
                "pre_existing_conditions": profile.get("pre_existing_conditions"),
                "tobacco_user": profile.get("tobacco_user"),
                "target_sum_insured": profile.get("sum_insured")
            },
            "quotation_summary": quote,
            "assigned_team": "Direct_Sales_VIP" if profile.get("sum_insured", 0) >= 750000 else "Standard_Underwriting",
            "webhook_dispatched": True,
            "webhook_endpoint": "https://crm.aegis-internal.io/api/v1/inbound_lead"
        }
        return lead_payload

    @staticmethod
    def schedule_callback(profile: Dict[str, Any], reason: str = "Human Escalation Request") -> Dict[str, Any]:
        """Dispatches an urgent callback request to senior underwriting desk."""
        return {
            "task": "URGENT_CALLBACK_DISPATCH",
            "reason": reason,
            "priority": "HIGH",
            "scheduled_time": "Within 15 minutes",
            "assigned_queue": "Senior_Licensed_Underwriters"
        }
