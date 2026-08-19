from backend.ai.graph import conversation_state_node, intent_classifier, action_router
from backend.ai.language import classify_intent, missing_fields


def test_short_followup_keeps_labour_issue():
    state = {
        "normalized_text": "Daily wage.",
        "current_issue": "My employer hasn't paid me for two months.",
        "conversation_history": [
            {"role": "user", "content": "My employer hasn't paid me for two months."},
            {"role": "assistant", "content": "Are you a permanent employee or a daily-wage worker?"},
        ],
        "collected_information": {},
        "pending_slot": "employment_type",
        "legal_domain": "labour",
    }
    from backend.ai.graph import input_processor

    processed = input_processor({**state, "text": "Daily wage.", "input_type": "text"})
    merged = conversation_state_node({**state, **processed})
    assert merged["collected_information"]["employment_type"] == "daily_wage"
    assert "employer" in merged["current_issue"].lower()


def test_state_followup_records_karnataka():
    updated = conversation_state_node(
        {
            "normalized_text": "Karnataka.",
            "current_issue": "My landlord kept my deposit.",
            "collected_information": {},
            "conversation_history": [{"role": "user", "content": "My landlord kept my deposit."}],
        }
    )
    assert updated["collected_information"]["state"] == "Karnataka"


def test_intent_routing_and_missing_rti_fields():
    assert classify_intent("I want to file an RTI") == "drafting"
    assert classify_intent("Find a lawyer for wage dispute") == "lawyer_matching"
    assert missing_fields("rti", {"applicant_name": "A"}) == ["address", "public_authority", "information_sought"]
    routed = action_router({"intent": "drafting", "safety_status": "ok"})
    assert routed == "drafting"
