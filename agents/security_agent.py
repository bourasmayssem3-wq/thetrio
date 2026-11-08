import logging

BAD_PHRASES = [
    "ignore previous instructions",
    "disregard earlier",
    "reveal your prompt",
    "system prompt",
]
MAX_AMOUNT = 500

log = logging.getLogger("security")


class SecurityAgent:
    def check_text(self, text):
        """Yverifi input mta3 el client (prompt injection). Yarja3 liste alertes."""
        text = (text or "").lower()
        for phrase in BAD_PHRASES:
            if phrase in text:
                log.warning("prompt_injection detected")
                return ["prompt_injection"]
        return []

    def check(self, sales, customer, consent):
        alerts = []

        if not sales or not sales.get("interested"):
            alerts.append("customer_not_interested")

        if not consent:
            alerts.append("no_consent")

        goal = (customer or {}).get("goal", "")
        alerts += self.check_text(goal)

        amount = (sales or {}).get("price_eur", 0)
        if amount > MAX_AMOUNT:
            alerts.append("high_amount_needs_human_validation")

        if alerts:
            log.warning("payment blocked: %s", ", ".join(alerts))
            return {
                "agent": "security",
                "status": "blocked",
                "alerts": alerts,
                "message": "Blocked: " + ", ".join(alerts),
            }
        log.info("security approved")
        return {
            "agent": "security",
            "status": "approved",
            "alerts": [],
            "message": "All checks passed.",
        }