from agents.llm_client import OpenAIClientError, recommend_business_strategy


class BusinessStrategyAgent:
    """Turn dashboard metrics into recommendations, optionally with an LLM."""

    def __init__(self):
        self.last_mode = "rules"

    def _rule_recommendations(self, stats):
        recs = []
        if stats["total_journeys"] == 0:
            return ["Not enough data yet. Run some customer journeys first."]

        objections = stats["objections"]
        if stats["conversion_rate_percent"] < 30:
            recs.append("Conversion is low: improve the sales script and ask about the customer's goal earlier.")
        if objections.get("price", 0) > 0:
            recs.append("Price is an objection (" + str(objections["price"]) + " times): offer a discount or installments.")
        if objections.get("time", 0) > 0:
            recs.append("Lack of time is an objection (" + str(objections["time"]) + " times): promote the flexible, self-paced format.")
        if stats["payments_refused"] > 0:
            recs.append("Some payments were refused: add a second payment method and a retry option.")
        if stats["payments_pending"] > 0:
            recs.append("Some payments are pending: send a reminder to finish the payment.")
        if stats["blocked_by_security"] > 0 or stats["security_alerts"] > 0:
            recs.append("Security alerts were detected: review the logs and the human validation steps.")
        if not recs:
            recs.append("Results are good. Keep the current offer and test a higher price or a new course.")
        return recs

    def recommend(self, stats, use_ai=True):
        rule_recommendations = self._rule_recommendations(stats)
        self.last_mode = "rules"
        if not use_ai:
            return rule_recommendations
        try:
            result = recommend_business_strategy(stats, rule_recommendations)
            if result is not None:
                recommendations, _model = result
                if recommendations:
                    self.last_mode = "openai"
                    return recommendations
        except OpenAIClientError:
            self.last_mode = "rules_fallback"
        return rule_recommendations
