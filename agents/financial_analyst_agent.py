class FinancialDataAnalystAgent:
    """Calculate sales, payment, conversion, customer, and security indicators."""

    @staticmethod
    def _count(table, key):
        table[key] = table.get(key, 0) + 1

    def analyze(self, records):
        stats = {
            "total_journeys": 0, "interested": 0, "payments_success": 0,
            "payments_refused": 0, "payments_pending": 0,
            "payments_cancelled": 0, "blocked_by_security": 0,
            "simulated_revenue_eur": 0, "conversion_rate_percent": 0,
            "security_alerts": 0, "alert_types": {}, "objections": {},
            "sentiments": {},
        }
        for record in records:
            stats["total_journeys"] += 1
            if (record.get("sales") or {}).get("interested"):
                stats["interested"] += 1

            status = record.get("journey_status")
            if status == "simulated_success":
                stats["payments_success"] += 1
                stats["simulated_revenue_eur"] += (record.get("payment") or {}).get("amount_eur", 0)
            elif status == "refused":
                stats["payments_refused"] += 1
            elif status == "pending":
                stats["payments_pending"] += 1
            elif status == "cancelled":
                stats["payments_cancelled"] += 1
            elif status == "blocked_by_security":
                stats["blocked_by_security"] += 1

            customer = record.get("customer") or {}
            for objection in customer.get("objections", []):
                self._count(stats["objections"], objection)
            if customer.get("sentiment"):
                self._count(stats["sentiments"], customer["sentiment"])

            security = record.get("security") or {}
            alerts = list(security.get("alerts", [])) + list(record.get("input_alerts", []))
            for alert in alerts:
                stats["security_alerts"] += 1
                self._count(stats["alert_types"], alert)

        if stats["total_journeys"]:
            stats["conversion_rate_percent"] = round(
                stats["payments_success"] / stats["total_journeys"] * 100, 1)
        return stats
