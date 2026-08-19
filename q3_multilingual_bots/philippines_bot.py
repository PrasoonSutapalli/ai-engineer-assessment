"""
Philippines Native-Language Voice Agent (Bancassurance & Life Insurance).
Specialized for natural Taglish code-switching, local financial terminology,
cultural politeness markers ('po'/'opo'), and human escalation.
"""

import re
import uuid
from typing import Dict, Any, List, Optional


class PhilippinesBancassuranceBot:
    """
    Taglish Life Insurance & Bancassurance Conversational Voice Agent.
    Handles English, Tagalog, and natural Taglish code-switching for Philippine bank customers.
    """

    def __init__(self, customer_name: str = "Mr. Santos", bank_name: str = "BDO"):
        self.call_id = str(uuid.uuid4())
        self.customer_name = customer_name
        self.bank_name = bank_name
        self.state = "GREETING"
        self.history: List[Dict[str, str]] = []
        self.escalated = False

    def process_turn(self, user_input: str) -> Dict[str, Any]:
        """Processes conversational turns in Taglish/English/Tagalog."""
        self.history.append({"speaker": "CUSTOMER", "text": user_input})
        text = user_input.lower()
        action_executed = None

        # 1. Escalation check (Taglish & English triggers)
        escalate_triggers = ['human', 'agent', 'supervisor', 'kausap na tao', 'tawag sa tao', 'manager', 'ayaw ko ng bot']
        if any(trig in text for trig in escalate_triggers):
            self.escalated = True
            self.state = "ESCALATED"
            speech = (
                "Opo, nauunawaan ko po. I-transfer ko na po kayo ngayon sa ating Senior Bancassurance Specialist "
                "para mas maasikaso po kayo nang maayos. Please stay on the line po."
            )
            action_executed = {"task": "ESCALATE_TO_PH_BANCASSURANCE_DESK", "market": "PH", "language": "Taglish"}
            self.history.append({"speaker": "AGENT", "text": speech})
            return {"speech_text": speech, "state": self.state, "escalated": True, "action": action_executed}

        # 2. Inquiries on Beneficiary, Policy Lapse, and Riders
        if any(w in text for w in ['lapse', 'mag-lapse', 'hindi makabayad', 'delay', 'overdue']):
            speech = (
                "Wag po kayong mag-alala! May 31-day grace period po tayo bago mag-lapse ang inyong life insurance policy. "
                "Pwede po tayong mag-set up ng auto-debit arrangement sa inyong bank account para tuloy-tuloy ang inyong family coverage."
            )
            self.state = "OFFERED_GRACE_PERIOD"
        elif any(w in text for w in ['beneficiary', 'benepisyaryo', 'pamilya', 'anak', 'asawa']):
            speech = (
                "Yes po, pwede niyo pong i-designate ang inyong spouse o mga anak as primary beneficiaries. "
                "100% tax-free po ang death and critical illness benefit payout directly deposited sa kanilang bank account."
            )
            self.state = "EXPLAINED_BENEFICIARY"
        elif any(w in text for w in ['rider', 'critical illness', 'dagdag cover', 'aksidente']):
            speech = (
                "Available po ang ating Comprehensive Critical Illness and Accidental Death Rider. "
                "Dagdag proteksyon po ito para covered ang 56 major illnesses with cash payout upon diagnosis."
            )
            self.state = "EXPLAINED_RIDERS"
        elif any(w in text for w in ['magkano', 'premium', 'hulog', 'presyo', 'how much', 'cost']):
            speech = (
                f"Para po sa premium, nagsisimula po ito sa kasing-baba ng ₱1,850 per month para sa ₱1.5 Million guaranteed life cover, "
                f"diretsong debit po sa inyong {self.bank_name} Savings account with zero hassle."
            )
            self.state = "QUOTED_PREMIUM"
        elif self.state == "GREETING":
            if any(w in text for w in ['oo', 'sige', 'yes', 'okay', 'pwede', 'ano yun', 'sure']):
                speech = (
                    f"Maraming salamat po, {self.customer_name}! As a valued {self.bank_name} depositor, qualified po kayo "
                    f"sa exclusive Bancassurance Life & Health Protection plan with guaranteed cash endowment. "
                    f"Gusto niyo po bang malaman kung magkano ang monthly premium at benefits para sa inyong pamilya?"
                )
                self.state = "DISCOVERY"
            else:
                speech = "Salamat po sa inyong oras! Pwede po kayong mag-inquire anytime sa nearest bank branch. Ingat po kayo palagi!"
                self.state = "COMPLETED"
        elif self.state == "DISCOVERY" or self.state == "QUOTED_PREMIUM":
            if any(w in text for w in ['sige', 'apply', 'interesado', 'gusto ko', 'yes', 'ok', 'proceed']):
                speech = (
                    "Napakagandang desisyon po niyan! Na-lock in ko na po ang preliminary pre-approval sa inyong bank profile. "
                    "Magpapadala po ako ng SMS confirmation link para ma-review niyo ang full policy endorsement. Maraming salamat po!"
                )
                self.state = "ENROLLED"
                action_executed = {"task": "LOG_PH_BANCASSURANCE_LEAD", "status": "APPROVED", "premium_php": 1850}
            else:
                speech = "May iba pa po ba kayong katanungan tungkol sa inyong policy coverage or beneficiaries?"
        else:
            speech = "Salamat po! Nandito po ako lagi para tumulong sa inyong bancassurance concerns."

        self.history.append({"speaker": "AGENT", "text": speech})
        return {
            "speech_text": speech,
            "state": self.state,
            "escalated": self.escalated,
            "action": action_executed
        }
