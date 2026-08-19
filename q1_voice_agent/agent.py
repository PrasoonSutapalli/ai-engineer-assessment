"""
Aegis Health Shield Knowledge-Grounded Voice Agent.
Implements dynamic RAG retrieval, conversational qualification flow,
safe fallback guardrails, human escalation, and CRM business actions.
"""

import re
import uuid
from typing import Dict, Any, List, Optional
from q2_knowledge_base.kb_store import default_kb
from .actions import BusinessActionHandler
from .prompts import QUALIFICATION_SCRIPT_STEPS


class HealthInsuranceVoiceAgent:
    """
    Production-grade Voice Agent executing lead qualification, dynamic KB retrieval,
    objection handling, and zero-hallucination safe fallback.
    """

    def __init__(self, call_id: Optional[str] = None):
        self.call_id = call_id or str(uuid.uuid4())
        self.state = "GREETING"
        self.profile = {
            "age": None,
            "location": None,
            "pre_existing_conditions": None,
            "tobacco_user": None,
            "sum_insured": None,
            "quote": None
        }
        self.history: List[Dict[str, str]] = []
        self.crm_record: Optional[Dict[str, Any]] = None
        self.escalated = False

    def _extract_entities(self, user_text: str):
        """Rule-based entity extractor for discovery slot-filling."""
        text = user_text.lower()

        # Extract Age
        if self.profile["age"] is None:
            age_match = re.search(r'\b(i am|i\'m|age is|turned)?\s*(\d{2})\b', text)
            if age_match:
                candidate_age = int(age_match.group(2))
                if 18 <= candidate_age <= 85:
                    self.profile["age"] = candidate_age

        # Extract Location
        if self.profile["location"] is None and self.state == "COLLECTING_LOCATION":
            # Match common city or general alphanumeric text
            cleaned_loc = re.sub(r'(i live in|in|at|city of)', '', text).strip().title()
            if cleaned_loc:
                self.profile["location"] = cleaned_loc

        # Extract Pre-existing conditions
        if self.profile["pre_existing_conditions"] is None and self.state == "COLLECTING_HEALTH":
            if any(w in text for w in ['no', 'none', 'healthy', 'nothing', 'nope', 'clean']):
                self.profile["pre_existing_conditions"] = "None"
            elif any(w in text for w in ['diabetes', 'hypertension', 'bp', 'blood pressure', 'asthma', 'thyroid']):
                conditions = []
                if 'diabetes' in text: conditions.append('Diabetes Type 2')
                if 'hypertension' in text or 'bp' in text: conditions.append('Hypertension')
                if 'asthma' in text: conditions.append('Asthma')
                if 'thyroid' in text: conditions.append('Thyroid')
                self.profile["pre_existing_conditions"] = ', '.join(conditions) if conditions else 'Declared Condition'

        # Extract Tobacco
        if self.profile["tobacco_user"] is None and self.state == "COLLECTING_TOBACCO":
            if any(w in text for w in ['no', 'nope', 'never', 'non-smoker', 'dont smoke', "don't", 'clean']):
                self.profile["tobacco_user"] = False
            elif any(w in text for w in ['yes', 'yeah', 'smoke', 'vape', 'smoker', 'tobacco', 'cigars']):
                self.profile["tobacco_user"] = True

        # Extract Sum Insured
        if self.profile["sum_insured"] is None and self.state in ["COLLECTING_BUDGET", "COLLECTING_TOBACCO"]:
            if any(w in text for w in ['1m', '1 million', 'million', '1000000', 'gold', '1,000,000']):
                self.profile["sum_insured"] = 1000000
            elif any(w in text for w in ['500k', '500000', '500,000', '500']):
                self.profile["sum_insured"] = 500000
            elif any(w in text for w in ['250k', '250000', '250,000', '250']):
                self.profile["sum_insured"] = 250000

    def process_turn(self, user_input: str) -> Dict[str, Any]:
        """
        Processes a single conversational turn from the customer audio/text.
        Returns bot response, current state, citation metadata, and actions taken.
        """
        self.history.append({"speaker": "CUSTOMER", "text": user_input})
        self._extract_entities(user_input)
        user_lower = user_input.lower()
        rag_citation = None
        action_triggered = None

        # 1. Immediate Escalation Trigger Check
        escalation_keywords = ['human', 'agent', 'supervisor', 'representative', 'operator', 'talk to person', 'real person', 'manager']
        if any(kw in user_lower for kw in escalation_keywords):
            self.escalated = True
            self.state = "ESCALATED"
            speech = QUALIFICATION_SCRIPT_STEPS["ESCALATE_HUMAN"]
            action_triggered = BusinessActionHandler.schedule_callback(self.profile, reason="Customer Demanded Human Transfer")
            self.history.append({"speaker": "AGENT", "text": speech})
            return {
                "speech_text": speech,
                "state": self.state,
                "rag_grounding": None,
                "action_executed": action_triggered,
                "profile": self.profile,
                "escalated": True
            }

        # 2. Out-of-Scope Detection (e.g. pet, dog, cat, car, auto, vehicle, tesla, flight) -> Safe Fallback Guardrail
        if re.search(r'\b(pet|dog|cat|car|auto|vehicle|tesla|crypto|flight|baggage|property)\b', user_lower):
            speech = (
                "I specialize strictly in Aegis Comprehensive Human Health Insurance, so I do not have verified "
                "data regarding property, pet, or auto insurance in my knowledge base. Would you like me to connect "
                "you with our general lines department?"
            )
            self.history.append({"speaker": "AGENT", "text": speech})
            return {
                "speech_text": speech,
                "state": self.state,
                "rag_grounding": {"verdict": "SAFE_FALLBACK_TRIGGERED", "reason": "Query out of domain"},
                "action_executed": None,
                "profile": self.profile,
                "escalated": False
            }

        # 3. Dynamic RAG Query Check (Consultation, Policy Questions, Objections)
        is_question_syntax = '?' in user_input or any(user_lower.strip().startswith(w) for w in ['what', 'why', 'how', 'can i', 'does', 'is ', 'are ', 'tell me', 'explain'])
        kb_trigger_keywords = [
            'room rent', 'icu', 'waiting period', 'maternity', 'pregnancy',
            'cashless', 'non-network', 'smoker loading', 'why is aegis', 'expensive',
            'cheaper', 'aggregator', 'online quote', 'medical checkup', 'ppmc', 'age limit'
        ]
        
        is_kb_query = is_question_syntax or any(kw in user_lower for kw in kb_trigger_keywords)
        # Exclude pure slot-filling discovery turns
        if self.state in ["COLLECTING_AGE", "COLLECTING_LOCATION", "COLLECTING_HEALTH", "COLLECTING_TOBACCO", "COLLECTING_BUDGET"] and not is_question_syntax:
            is_kb_query = False

        if is_kb_query:
            search_results = default_kb.search(user_input, top_k=1, min_score=0.18)
            if search_results:
                top_doc = search_results[0]
                rag_citation = top_doc
                
                # Grounded Response Construction
                if top_doc["record_id"] == "kb_product_002":
                    speech = (
                        "For Gold Care with $750,000+ coverage, there is zero room rent capping—single private or deluxe "
                        "AC rooms are covered at actuals. For plans up to $500,000, room rent is capped at 1% and ICU at 2% daily."
                    )
                elif top_doc["record_id"] == "kb_policy_001":
                    speech = (
                        "The standard waiting period for pre-existing conditions like diabetes or hypertension is 24 months. "
                        "However, our 1-Year PED Buyback Rider can reduce this waiting period to just 12 months."
                    )
                elif top_doc["record_id"] == "kb_objection_001":
                    speech = (
                        "Online aggregators often advertise base teaser rates that exclude room rent caps and require 20% co-pay. "
                        "Our direct plan includes zero co-pay, no room rent sublimits, and guaranteed 60-minute cashless approvals."
                    )
                elif top_doc["record_id"] == "kb_pricing_001":
                    speech = (
                        "Tobacco users have a 20% to 35% premium loading due to actuarial risk, but it can be completely removed "
                        "upon policy renewal after completing a 12-month cessation program."
                    )
                elif top_doc["record_id"] == "kb_claims_001":
                    speech = (
                        "We offer 100% cashless hospitalization across 8,500+ network hospitals, plus our 'Cashless Anywhere' "
                        "facility for non-network hospitals if notified 48 hours prior."
                    )
                elif top_doc["record_id"] == "kb_underwriting_001":
                    speech = (
                        "The maximum entry age is 65 with lifelong renewability. Applicants under 55 without chronic illness "
                        "do not need any pre-policy medical checkup."
                    )
                elif top_doc["record_id"] == "kb_policy_002":
                    speech = (
                        "Maternity expenses are covered up to $50,000 per delivery after a 24-month waiting period, and newborn "
                        "babies are covered from Day 1."
                    )
                else:
                    speech = f"According to our verified guidelines: {top_doc['content'][:150]}..."

                # Transition back to discovery if incomplete
                if self.profile["age"] is None:
                    speech += " To proceed with your quote, could you share your current age?"
                    self.state = "COLLECTING_AGE"
                elif self.profile["sum_insured"] is None:
                    speech += " Would you prefer the $500,000 or $1,000,000 Sum Insured plan?"
                    self.state = "COLLECTING_BUDGET"

                self.history.append({"speaker": "AGENT", "text": speech})
                return {
                    "speech_text": speech,
                    "state": self.state,
                    "rag_grounding": rag_citation,
                    "action_executed": None,
                    "profile": self.profile,
                    "escalated": False
                }

        # 4. Sequential Discovery State Machine
        if self.state == "GREETING":
            if any(w in user_lower for w in ['yes', 'sure', 'okay', 'yeah', 'fine', 'go ahead', 'hello', 'hi']):
                self.state = "COLLECTING_AGE"
                speech = QUALIFICATION_SCRIPT_STEPS["ASK_AGE"]
            else:
                speech = "No problem at all! Feel free to reach back out when you are ready to explore comprehensive coverage. Have a great day!"
                self.state = "COMPLETED"

        elif self.state == "COLLECTING_AGE":
            if self.profile["age"] is not None:
                if self.profile["age"] > 65:
                    speech = (
                        "Our standard direct enrollment is available up to age 65. Because you are above 65, let me connect you "
                        "with our Senior Underwriting Specialist for our Aegis Silver Senior Care program."
                    )
                    self.state = "ESCALATED"
                    action_triggered = BusinessActionHandler.schedule_callback(self.profile, "Senior Citizen Custom Underwriting")
                else:
                    self.state = "COLLECTING_LOCATION"
                    speech = QUALIFICATION_SCRIPT_STEPS["ASK_LOCATION"]
            else:
                speech = "Could you please clarify your numerical age in years?"

        elif self.state == "COLLECTING_LOCATION":
            if self.profile["location"] is not None:
                self.state = "COLLECTING_HEALTH"
                speech = QUALIFICATION_SCRIPT_STEPS["ASK_HEALTH"]
            else:
                speech = "Which city are you currently based in?"

        elif self.state == "COLLECTING_HEALTH":
            if self.profile["pre_existing_conditions"] is not None:
                self.state = "COLLECTING_TOBACCO"
                speech = QUALIFICATION_SCRIPT_STEPS["ASK_TOBACCO"]
            else:
                speech = "Do you have any existing medical conditions like diabetes, hypertension, or asthma?"

        elif self.state == "COLLECTING_TOBACCO":
            if self.profile["tobacco_user"] is not None:
                self.state = "COLLECTING_BUDGET"
                speech = QUALIFICATION_SCRIPT_STEPS["ASK_BUDGET"]
            else:
                speech = "Have you used any tobacco or nicotine products in the last 12 months?"

        elif self.state == "COLLECTING_BUDGET":
            if self.profile["sum_insured"] is not None:
                # Calculate Quote and Dispatch CRM Action
                has_ped = self.profile["pre_existing_conditions"] != "None"
                quote = BusinessActionHandler.calculate_preliminary_quote(
                    age=self.profile["age"],
                    sum_insured=self.profile["sum_insured"],
                    is_tobacco_user=self.profile["tobacco_user"],
                    has_ped=has_ped
                )
                self.profile["quote"] = quote
                self.crm_record = BusinessActionHandler.create_crm_lead(self.profile, self.call_id)
                action_triggered = self.crm_record
                self.state = "QUALIFIED_COMPLETED"
                speech = (
                    f"Congratulations! You are pre-qualified for the Aegis Gold Care Plan with ${self.profile['sum_insured']:,} "
                    f"coverage at an estimated premium of ${quote['estimated_monthly_premium']}/month. I have logged your file "
                    f"into our CRM and dispatched a confirmation link to your phone."
                )
            else:
                speech = "Would you prefer a $250,000, $500,000, or $1,000,000 coverage limit?"

        else:
            speech = "Thank you for consulting with Aegis Health Shield. Is there anything else I can assist you with today?"

        self.history.append({"speaker": "AGENT", "text": speech})
        return {
            "speech_text": speech,
            "state": self.state,
            "rag_grounding": rag_citation,
            "action_executed": action_triggered,
            "profile": self.profile,
            "escalated": self.escalated
        }
