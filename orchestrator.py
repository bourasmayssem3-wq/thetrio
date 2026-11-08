"""Connect the demo agents into a terminal customer journey."""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from agents.business_agent import BusinessStrategyAgent
from agents.customer_agent import CustomerIntelligenceAgent
from agents.financial_analyst_agent import FinancialDataAnalystAgent
from agents.payment_agent import PaymentAgent
from agents.sales_agent import SalesAgent
from agents.security_agent import SecurityAgent

ROOT = Path(__file__).resolve().parent
DATA_FILE = ROOT / "data" / "transactions.json"
LOG_FILE = ROOT / "logs" / "app.log"

LOG_FILE.parent.mkdir(exist_ok=True)
DATA_FILE.parent.mkdir(exist_ok=True)
logging.basicConfig(filename=LOG_FILE, level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(name)s %(message)s")


def load_records():
    if not DATA_FILE.exists():
        return []
    try:
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []


def save_result(result):
    records = load_records()
    records.append(result)
    DATA_FILE.write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")
    logging.getLogger("orchestrator").info(
        "journey completed status=%s", result.get("journey_status"))


def record_event(record, agent, action, status, details=None):
    """Append an audit event without storing raw conversation text."""
    event = {"time": datetime.now(timezone.utc).isoformat(), "agent": agent,
             "action": action, "status": status}
    if details:
        event["details"] = details
    record.setdefault("events", []).append(event)
    logging.getLogger("agent_events").info(
        "agent=%s action=%s status=%s", agent, action, status)
    return event


def review_payment(index, decision):
    """Human-in-the-loop: admin ya3mel approve wala reject lel paiement pending."""
    records = load_records()
    if index < 0 or index >= len(records):
        return False
    record = records[index]
    if record.get("journey_status") != "pending" or decision not in ("approve", "reject"):
        return False

    new_status = "simulated_success" if decision == "approve" else "refused"
    record["journey_status"] = new_status
    if record.get("payment"):
        record["payment"]["status"] = new_status
    record["human_review"] = {
        "decision": decision,
        "reviewed_at": datetime.now(timezone.utc).isoformat(),
    }
    record_event(record, "human_reviewer", "payment_review", new_status,
                 {"decision": decision})
    DATA_FILE.write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")
    logging.getLogger("human_review").info(
        "payment %s %s by admin", (record.get("payment") or {}).get("transaction_id"), decision)
    return True


def compute_stats(records):
    """Compatibility wrapper used by the CLI and web dashboard."""
    return FinancialDataAnalystAgent().analyze(records)


def run_journey(input_fn=input, output_fn=print):
    output_fn("=== THETRIO: demo journey ===")
    security = SecurityAgent()
    input_alerts = []
    events = []

    # 1. Sales Agent
    sales = SalesAgent()
    output_fn("Welcome! Here is our offer:")
    output_fn(sales.present_offer())
    output_fn("Ask a question, or type 'done' when you are ready.")
    while True:
        question = input_fn("You: ").strip()
        if question.lower() in ("done", "no questions", "continue"):
            break
        alerts = security.check_text(question)
        if alerts:
            input_alerts += alerts
            events.append({"time": datetime.now(timezone.utc).isoformat(), "agent": "security",
                           "action": "customer_input_check", "status": "blocked",
                           "details": {"alerts": alerts}})
            output_fn("Security: this message was blocked.")
            continue
        answer = sales.answer_question(question)
        events.append({"time": datetime.now(timezone.utc).isoformat(), "agent": "sales",
                       "action": "customer_question", "status": sales.last_answer_mode,
                       "details": {"outcome": "answered" if answer else "unknown_topic"}})
        output_fn(answer or "I don't have that information yet. Ask about price, duration, format, or course topics.")

    while True:
        interested = sales.detect_interest(input_fn("Are you interested in this course? (yes/no): "))
        if interested is not None:
            break
        output_fn("Please answer yes or no so I can record your choice.")

    sales_result = {
        "agent": "sales",
        "offer": sales.OFFER["name"],
        "price_eur": 99,
        "interested": interested,
        "status": "interested" if interested else "not_interested",
    }
    result = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "sales": sales_result,
        "customer": None,
        "security": None,
        "payment": None,
        "input_alerts": input_alerts,
        "events": events,
    }
    record_event(result, "sales", "interest_recorded", sales_result["status"])

    if not interested:
        result["journey_status"] = "not_interested"
    else:
        # 2. Customer Intelligence Agent
        customer_result = CustomerIntelligenceAgent().run(input_fn, output_fn)
        result["customer"] = customer_result
        record_event(result, "customer_intelligence", "profile_analyzed", "complete",
                     {"sentiment": customer_result.get("sentiment"),
                      "objections": customer_result.get("objections", []),
                      "mode": customer_result.get("analysis_mode", "rules")})

        # 3. Security Agent
        answer = input_fn("Do you consent to continue to the payment simulation? (yes/no): ")
        consent = answer.strip().lower() in ("yes", "y")
        security_result = security.check(sales_result, customer_result, consent)
        result["security"] = security_result
        record_event(result, "security", "payment_authorization", security_result["status"],
                     {"alerts": security_result.get("alerts", [])})
        output_fn(f"Security: {security_result['status']} - {security_result['message']}")

        # 4. Payment Agent
        if security_result["status"] == "approved":
            payment_result = PaymentAgent().run(99, input_fn, output_fn)
            result["payment"] = payment_result
            result["journey_status"] = payment_result["status"]
            record_event(result, "payment", "payment_simulation", payment_result["status"])
        else:
            result["journey_status"] = "blocked_by_security"

    # 5. Financial Data Analyst + 6. Business Strategy Agent
    stats = compute_stats(load_records() + [result])
    strategy_agent = BusinessStrategyAgent()
    recommendations = strategy_agent.recommend(stats)
    result["strategy"] = {"agent": "business_strategy", "mode": strategy_agent.last_mode,
                          "recommendations": recommendations}
    record_event(result, "financial_data_analyst", "journey_metrics_calculated", "complete")
    record_event(result, "business_strategy", "recommendations_generated", "complete",
                 {"count": len(recommendations), "mode": strategy_agent.last_mode})
    save_result(result)
    output_fn("\nJourney summary:")
    output_fn(json.dumps(result, indent=2, ensure_ascii=False))
    output_fn("\nDashboard stats:")
    output_fn(json.dumps(stats, indent=2, ensure_ascii=False))
    output_fn("\nRecommendations:")
    for rec in recommendations:
        output_fn("- " + rec)
    return result


if __name__ == "__main__":
    run_journey()
