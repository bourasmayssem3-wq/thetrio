import logging
import uuid

log = logging.getLogger("payment")

OUTCOMES = {
    "pay": "simulated_success",
    "refuse": "refused",
    "pending": "pending",
}


class PaymentAgent:
    def run(self, amount, input_fn=input, output_fn=print):
        output_fn("SIMULATION ONLY: no real payment. Do not enter card details.")
        output_fn(f"Course amount: €{amount}")
        choice = input_fn("Type 'pay', 'refuse', 'pending' or 'cancel': ").strip().lower()

        status = OUTCOMES.get(choice, "cancelled")
        transaction_id = None
        if status != "cancelled":
            transaction_id = "SIM-" + uuid.uuid4().hex[:8].upper()
        log.info("payment status=%s id=%s", status, transaction_id)
        return {
            "agent": "payment",
            "status": status,
            "amount_eur": amount,
            "transaction_id": transaction_id,
        }