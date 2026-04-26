import json
import operator
from typing import List, Optional, Dict, Any, Annotated, Sequence

from pydantic import BaseModel, Field
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage

from core.logging import get_logger
from core.domain import Scheme, FarmerProfile, LanguageCode
from services.llm_service import LLMService
from services.scheme_service import SchemeService
from services.eligibility_engine import HybridEligibilityEngine
from repositories.farmer_repository import FarmerRepository

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Request / Response models (kept for backward compat with routes.py)
# ---------------------------------------------------------------------------

class SchemeQueryRequest(BaseModel):
    query: str
    user_id: str
    state: Optional[str] = None
    language: LanguageCode = LanguageCode.HINDI


class FarmerData(BaseModel):
    farmer_name: Optional[str] = None
    aadhaar_number: Optional[str] = None
    bank_account: Optional[str] = None
    bank_ifsc: Optional[str] = None
    mobile_number: Optional[str] = None
    land_area_hectares: Optional[float] = None
    state: Optional[str] = None
    district: Optional[str] = None
    is_complete: bool = False
    missing_fields: List[str] = Field(default_factory=list)
    next_question: Optional[str] = None


# ---------------------------------------------------------------------------
# LangGraph Agent State
# ---------------------------------------------------------------------------

class AgentState(dict):
    """Persistent graph state for multi-turn scheme form-filling."""
    messages: Annotated[Sequence[BaseMessage], operator.add]
    user_profile: Dict[str, Any]
    collected_data: Dict[str, Any]
    missing_fields: List[str]
    target_scheme: Dict[str, Any]
    current_step: str          # scheme_identified | collecting_data | eligibility_checked | form_generated | awaiting_user_confirmation | completed | rejected
    is_eligible: bool
    retry_count: int
    form_pdf_path: str
    language_pref: str         # e.g. "hi", "mr", "en"


# ---------------------------------------------------------------------------
# Multilingual prompt matrix for common required fields
# ---------------------------------------------------------------------------

FIELD_PROMPTS = {
    "hi": {
        "farmer_name": "योजना के लिए आपका पूरा नाम आवश्यक है। कृपया अपना नाम बताएं।",
        "aadhaar_number": "योजना के लिए आपका बारह अंकों का आधार नंबर आवश्यक है। कृपया अपना आधार नंबर बताएं।",
        "bank_account": "सब्सिडी के लिए आपके बैंक खाते का नंबर क्या है?",
        "bank_ifsc": "कृपया अपना बैंक IFSC कोड बताएं।",
        "mobile_number": "कृपया अपना मोबाइल नंबर बताएं।",
        "land_area": "आपकी खेती की जमीन कितने हेक्टेयर है?",
        "land_area_hectares": "आपकी खेती की जमीन कितने हेक्टेयर है?",
        "state": "आप किस राज्य में रहते हैं?",
        "district": "आप किस जिले में रहते हैं?",
        "caste_category": "कृपया अपनी जाति श्रेणी बताएं।",
    },
    "mr": {
        "farmer_name": "योजनेसाठी तुमचे पूर्ण नाव आवश्यक आहे. कृपया तुमचे नाव सांगा.",
        "aadhaar_number": "योजनेसाठी तुमचा बारा अंकी आधार क्रमांक आवश्यक आहे. कृपया तुमचा आधार क्रमांक सांगा.",
        "bank_account": "अनुदानासाठी तुमचा बँक खाते क्रमांक काय आहे?",
        "bank_ifsc": "कृपया तुमचा बँक IFSC कोड सांगा.",
        "mobile_number": "कृपया तुमचा मोबाइल नंबर सांगा.",
        "land_area": "तुमची शेतजमीन किती हेक्टर आहे?",
        "land_area_hectares": "तुमची शेतजमीन किती हेक्टर आहे?",
        "state": "तुम्ही कोणत्या राज्यात राहता?",
        "district": "तुम्ही कोणत्या जिल्ह्यात राहता?",
        "caste_category": "कृपया तुमची जात श्रेणी सांगा.",
    },
    "en": {
        "farmer_name": "Please provide your full name for the scheme application.",
        "aadhaar_number": "Your 12-digit Aadhaar number is required. Please share it.",
        "bank_account": "What is your bank account number for subsidy transfer?",
        "bank_ifsc": "Please provide your bank IFSC code.",
        "mobile_number": "Please provide your mobile number.",
        "land_area": "How many hectares of farmland do you own?",
        "land_area_hectares": "How many hectares of farmland do you own?",
        "state": "Which state do you reside in?",
        "district": "Which district do you reside in?",
        "caste_category": "Please provide your caste category.",
    },
}


# ---------------------------------------------------------------------------
# Graph Node Functions  (stateless, receive & return state dicts)
# ---------------------------------------------------------------------------

async def extract_entities_node(state: Dict[str, Any], llm: LLMService) -> Dict[str, Any]:
    """
    Analyzes the latest HumanMessage and extracts entities to populate collected_data.
    Maintains a retry_count to handle continuous failures gracefully.
    """
    messages = state.get("messages", [])
    if not messages:
        return {"retry_count": state.get("retry_count", 0) + 1}

    last_message = messages[-1]
    last_text = last_message.content if hasattr(last_message, "content") else str(last_message)

    extraction_prompt = f"""Extract any agricultural or identity information from the text.
Text: {last_text}

Return a valid JSON object with keys like "farmer_name", "aadhaar_number", "land_area",
"bank_account", "bank_ifsc", "mobile_number", "state", "district", "caste_category", etc.
If no relevant entities are found, return an empty dictionary {{}}.
"""
    try:
        response = await llm.invoke(
            [
                SystemMessage(content="You are a precise entity extraction system. Return ONLY valid JSON."),
                HumanMessage(content=extraction_prompt),
            ],
            temperature=0,
        )
        raw_json = response.replace("```json", "").replace("```", "").strip()
        new_entities = json.loads(raw_json)

        updated_data = dict(state.get("collected_data", {}))
        # Only update with non-empty values
        for k, v in new_entities.items():
            if v not in [None, "", "unknown"]:
                updated_data[k] = v

        retry_val = 0 if new_entities else state.get("retry_count", 0) + 1
        return {"collected_data": updated_data, "retry_count": retry_val}
    except Exception as e:
        logger.warning(f"Entity extraction failed: {e}")
        return {"retry_count": state.get("retry_count", 0) + 1}


async def eligibility_check_node(
    state: Dict[str, Any], engine: HybridEligibilityEngine
) -> Dict[str, Any]:
    """Passes current state to the Hybrid Engine to assess status and missing parameters."""
    result = await engine.check_eligibility(
        state.get("collected_data", {}),
        state.get("target_scheme", {}),
    )

    current_step = (
        "eligibility_checked"
        if not result["missing_fields"]
        else "collecting_data"
    )
    if not result["eligible"] and not result["missing_fields"]:
        current_step = "rejected"

    return {
        "is_eligible": result["eligible"],
        "missing_fields": result["missing_fields"],
        "current_step": current_step,
    }


async def conversational_prompt_node(
    state: Dict[str, Any], llm: LLMService
) -> Dict[str, Any]:
    """Generates the next question systematically based on the missing_fields queue."""
    if state.get("retry_count", 0) > 3:
        return {
            "messages": [
                AIMessage(
                    content="I'm having trouble understanding. Let me connect you with a human agent."
                )
            ]
        }

    missing = state.get("missing_fields", [])
    language = state.get("language_pref", "hi")

    if missing:
        next_field = missing[0]
        lang_prompts = FIELD_PROMPTS.get(language, FIELD_PROMPTS["en"])

        # Use static prompt if available, else generate via LLM
        question = lang_prompts.get(next_field)
        if not question:
            lang_name = {"hi": "Hindi", "mr": "Marathi", "en": "English"}.get(
                language, "English"
            )
            try:
                question = await llm.invoke(
                    [
                        SystemMessage(
                            content=f"Generate a simple, friendly question in {lang_name} to ask a farmer. Maximum one sentence."
                        ),
                        HumanMessage(
                            content=f"Ask for their {next_field.replace('_', ' ')}"
                        ),
                    ]
                )
            except Exception:
                question = f"Please provide your {next_field.replace('_', ' ')}."

        return {"messages": [AIMessage(content=question)]}

    # All fields collected
    completion_msgs = {
        "hi": "सभी आवश्यक जानकारी एकत्र कर ली गई है। मैं अब आपका आवेदन फॉर्म तैयार कर रहा हूँ।",
        "mr": "सर्व आवश्यक माहिती गोळा केली आहे. मी आता तुमचा अर्ज तयार करत आहे.",
        "en": "All necessary data has been collected. I am preparing your application form now.",
    }
    msg = completion_msgs.get(language, completion_msgs["en"])
    return {"messages": [AIMessage(content=msg)]}


def routing_logic(state: Dict[str, Any]) -> str:
    """Evaluates the state after eligibility check to route the graph."""
    if state.get("current_step") == "rejected":
        return "rejection_end"
    if state.get("missing_fields"):
        return "ask_question"
    return "generate_form"


# ---------------------------------------------------------------------------
# The Navigator Agent — backward-compatible + new graph-based pipeline
# ---------------------------------------------------------------------------

class SchemeNavigatorAgent:
    """
    Multi-role agent:
    1. search_schemes() — existing web-scrape + LLM extraction (backward compat)
    2. build_form_graph() — LangGraph state machine for conversational form-filling
    3. run_graph_step() — execute one turn of the graph for a given thread
    """

    def __init__(
        self,
        llm_service: LLMService,
        scheme_service: SchemeService,
        farmer_repo: FarmerRepository,
        eligibility_engine: Optional[HybridEligibilityEngine] = None,
        form_filler=None,
    ):
        self.llm = llm_service
        self.schemes = scheme_service
        self.farmer_repo = farmer_repo
        self.engine = eligibility_engine or HybridEligibilityEngine(llm_service)
        self.form_filler = form_filler

        # In-memory thread states (production: use AsyncPostgresSaver)
        self._threads: Dict[str, Dict[str, Any]] = {}

    # ------------------------------------------------------------------
    # Backward-compatible: simple scheme search
    # ------------------------------------------------------------------

    async def search_schemes(self, request: SchemeQueryRequest) -> List[Scheme]:
        logger.info(f"Searching schemes for: {request.query}")

        results = await self.schemes.search_schemes(
            request.query,
            state=request.state,
            limit=5,
            language=request.language.value,
        )

        return [
            Scheme(
                id=r.get("id", "unknown"),
                name=r.get("name", "Unknown Scheme"),
                description=r.get("description", ""),
                eligibility_criteria=r.get("eligibility_criteria", []),
                benefits=r.get("benefits", ""),
                state=r.get("state"),
                category=r.get("category", "agriculture"),
                documents_required=r.get("documents_required", []),
            )
            for r in results
        ]

    # ------------------------------------------------------------------
    # New: Graph-based multi-turn form filling
    # ------------------------------------------------------------------

    def _get_or_create_thread(
        self,
        thread_id: str,
        target_scheme: Optional[Dict[str, Any]] = None,
        language: str = "hi",
        user_profile: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Get existing thread state or create a new one."""
        if thread_id in self._threads:
            return self._threads[thread_id]

        state = {
            "messages": [],
            "user_profile": user_profile or {},
            "collected_data": {},
            "missing_fields": [],
            "target_scheme": target_scheme or {},
            "current_step": "scheme_identified" if target_scheme else "pending",
            "is_eligible": False,
            "retry_count": 0,
            "form_pdf_path": "",
            "language_pref": language,
        }
        self._threads[thread_id] = state
        return state

    async def run_graph_step(
        self,
        thread_id: str,
        user_message: str,
        target_scheme: Optional[Dict[str, Any]] = None,
        language: str = "hi",
        user_profile: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute one turn of the conversational form-filling graph.
        Returns the updated state with the latest AI message.
        """
        state = self._get_or_create_thread(
            thread_id, target_scheme, language, user_profile
        )

        # If a new target_scheme is provided and none exists, set it
        if target_scheme and not state.get("target_scheme"):
            state["target_scheme"] = target_scheme
            state["current_step"] = "scheme_identified"

        # Update language if changed
        state["language_pref"] = language

        # Append user message
        state["messages"].append(HumanMessage(content=user_message))

        # Step 1: Entity Extraction
        extraction_result = await extract_entities_node(state, self.llm)
        state["collected_data"].update(extraction_result.get("collected_data", {}))
        state["retry_count"] = extraction_result.get("retry_count", state["retry_count"])

        # Step 2: Eligibility Check
        eligibility_result = await eligibility_check_node(state, self.engine)
        state["is_eligible"] = eligibility_result.get("is_eligible", False)
        state["missing_fields"] = eligibility_result.get("missing_fields", [])
        state["current_step"] = eligibility_result.get("current_step", state["current_step"])

        # Step 3: Route
        route = routing_logic(state)

        if route == "rejection_end":
            lang = state["language_pref"]
            rejection_msgs = {
                "hi": "क्षमा करें, आपकी जानकारी के अनुसार आप इस योजना के लिए पात्र नहीं हैं।",
                "mr": "क्षमस्व, तुमच्या माहितीनुसार तुम्ही या योजनेसाठी पात्र नाहीत.",
                "en": "Sorry, based on your information you are not eligible for this scheme.",
            }
            msg = rejection_msgs.get(lang, rejection_msgs["en"])
            state["messages"].append(AIMessage(content=msg))
            state["current_step"] = "rejected"

        elif route == "ask_question":
            prompt_result = await conversational_prompt_node(state, self.llm)
            new_msgs = prompt_result.get("messages", [])
            state["messages"].extend(new_msgs)
            state["current_step"] = "collecting_data"

        elif route == "generate_form":
            # All data collected — generate form
            if self.form_filler:
                try:
                    scheme_id = state["target_scheme"].get("scheme_id", "default")
                    pdf_path = self.form_filler.generate_application_form(
                        user_data=state["collected_data"],
                        scheme_id=scheme_id,
                    )
                    state["form_pdf_path"] = pdf_path
                    state["current_step"] = "form_generated"

                    lang = state["language_pref"]
                    form_msgs = {
                        "hi": f"आपका आवेदन फॉर्म तैयार हो गया है। कृपया इसकी समीक्षा करें और पुष्टि करें।",
                        "mr": f"तुमचा अर्ज तयार झाला आहे. कृपया तपासा आणि पुष्टी करा.",
                        "en": f"Your application form has been generated. Please review and confirm.",
                    }
                    msg = form_msgs.get(lang, form_msgs["en"])
                    state["messages"].append(AIMessage(content=msg))
                except Exception as e:
                    logger.error(f"Form generation failed: {e}")
                    state["messages"].append(
                        AIMessage(content="Form generation encountered an error. Please try again.")
                    )
            else:
                state["current_step"] = "eligibility_checked"
                state["messages"].append(
                    AIMessage(content="All data collected. Eligibility confirmed.")
                )

        # Persist state
        self._threads[thread_id] = state

        return {
            "thread_id": thread_id,
            "current_step": state["current_step"],
            "is_eligible": state["is_eligible"],
            "missing_fields": state["missing_fields"],
            "collected_data": state["collected_data"],
            "form_pdf_path": state.get("form_pdf_path", ""),
            "last_ai_message": state["messages"][-1].content
            if state["messages"] and hasattr(state["messages"][-1], "content")
            else "",
            "messages": [
                {"role": "assistant" if isinstance(m, AIMessage) else "user", "content": m.content}
                for m in state["messages"]
                if hasattr(m, "content")
            ],
        }

    async def confirm_submission(
        self, thread_id: str, approved: bool
    ) -> Dict[str, Any]:
        """Handle HITL confirmation — approve or reject the generated form."""
        state = self._threads.get(thread_id)
        if not state:
            return {"error": "Thread not found"}

        if approved:
            state["current_step"] = "completed"
            lang = state["language_pref"]
            done_msgs = {
                "hi": "आपका आवेदन सफलतापूर्वक जमा हो गया है!",
                "mr": "तुमचा अर्ज यशस्वीरित्या सादर झाला आहे!",
                "en": "Your application has been successfully submitted!",
            }
            msg = done_msgs.get(lang, done_msgs["en"])
            state["messages"].append(AIMessage(content=msg))
        else:
            state["current_step"] = "collecting_data"
            state["missing_fields"] = list(state["collected_data"].keys())
            state["collected_data"] = {}
            lang = state["language_pref"]
            redo_msgs = {
                "hi": "ठीक है, आइए फिर से शुरू करते हैं। कृपया सही जानकारी दें।",
                "mr": "ठीक आहे, पुन्हा सुरू करूया. कृपया योग्य माहिती द्या.",
                "en": "Alright, let's start over. Please provide the correct information.",
            }
            msg = redo_msgs.get(lang, redo_msgs["en"])
            state["messages"].append(AIMessage(content=msg))

        self._threads[thread_id] = state
        return {
            "thread_id": thread_id,
            "current_step": state["current_step"],
            "last_ai_message": msg,
        }

    def get_thread_status(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of a thread."""
        state = self._threads.get(thread_id)
        if not state:
            return None
        return {
            "current_step": state["current_step"],
            "collected_data": state["collected_data"],
            "missing_fields": state["missing_fields"],
            "form_pdf_path": state.get("form_pdf_path", ""),
            "is_eligible": state["is_eligible"],
        }

    # ------------------------------------------------------------------
    # Legacy helper (kept for any existing callers)
    # ------------------------------------------------------------------

    async def collect_farmer_data(
        self,
        request: SchemeQueryRequest,
        user_profile: Optional[FarmerProfile] = None,
    ) -> FarmerData:
        logger.info(f"Collecting farmer data for user: {request.user_id}")

        if not user_profile:
            user_profile = await self.farmer_repo.get_by_user_id(request.user_id)

        required_fields = [
            "farmer_name",
            "aadhaar_number",
            "bank_account",
            "mobile_number",
            "land_area_hectares",
            "state",
            "district",
        ]

        existing_data = {}
        if user_profile:
            existing_data = {
                "farmer_name": user_profile.name,
                "aadhaar_number": user_profile.aadhaar_number,
                "bank_account": user_profile.bank_account,
                "bank_ifsc": user_profile.bank_ifsc,
                "mobile_number": user_profile.mobile_number,
                "land_area_hectares": user_profile.land_area_hectares,
                "state": user_profile.location.state if user_profile.location else None,
                "district": user_profile.location.district if user_profile.location else None,
            }

        missing_fields = [
            field for field in required_fields if not existing_data.get(field)
        ]

        next_question = await self._generate_next_question(
            missing_fields, request.language
        )

        return FarmerData(
            farmer_name=existing_data.get("farmer_name"),
            aadhaar_number=existing_data.get("aadhaar_number"),
            bank_account=existing_data.get("bank_account"),
            bank_ifsc=existing_data.get("bank_ifsc"),
            mobile_number=existing_data.get("mobile_number"),
            land_area_hectares=existing_data.get("land_area_hectares"),
            state=existing_data.get("state"),
            district=existing_data.get("district"),
            is_complete=len(missing_fields) == 0,
            missing_fields=missing_fields,
            next_question=next_question,
        )

    async def _generate_next_question(
        self, missing_fields: List[str], language: LanguageCode
    ) -> str:
        if not missing_fields:
            return None

        lang_map = {
            LanguageCode.HINDI: "Hindi",
            LanguageCode.MARATHI: "Marathi",
            LanguageCode.ENGLISH: "English",
        }
        language_name = lang_map.get(language, "English")

        field = missing_fields[0]
        field_labels = {
            "farmer_name": "farmer's name",
            "aadhaar_number": "Aadhaar number",
            "bank_account": "bank account number",
            "mobile_number": "mobile number",
            "land_area_hectares": "land area in hectares",
            "state": "state name",
            "district": "district name",
        }

        messages = [
            SystemMessage(
                content=f"Generate a simple question in {language_name} to ask a farmer.\nBe friendly and simple. Maximum one sentence."
            ),
            HumanMessage(content=f"Ask for their {field_labels.get(field, field)}"),
        ]

        return await self.llm.invoke(messages)
