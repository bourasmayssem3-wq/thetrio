from agents.llm_client import OpenAIClientError, answer_sales_question, load_env_file


class SalesAgent:
    """Present the offer and use AI for grounded answers when configured."""

    OFFER = {
        "name": "AI Training Course",
        "price": "€99",
        "duration": "4 weeks",
        "format": "online, self-paced",
        "topics": "AI fundamentals, practical tools, and hands-on exercises",
    }

    def __init__(self):
        self.last_answer_mode = "rules"

    def present_offer(self):
        return (
            f"{self.OFFER['name']} — {self.OFFER['price']}, {self.OFFER['duration']}. "
            f"It is {self.OFFER['format']} and covers {self.OFFER['topics']}."
        )

    def _rule_answer(self, question):
        question = question.lower()
        if any(word in question for word in ("price", "cost", "much", "€")):
            return f"The course costs {self.OFFER['price']}."
        if any(word in question for word in ("duration", "long", "weeks", "time")):
            return f"The course takes {self.OFFER['duration']} at your own pace."
        if any(word in question for word in ("online", "format", "where")):
            return f"It is {self.OFFER['format']}."
        if any(word in question for word in ("learn", "content", "include", "topic")):
            return f"It covers {self.OFFER['topics']}."
        return None

    def answer_question(self, question):
        """Try a grounded model answer, then fall back to known offer facts."""
        load_env_file()
        self.last_answer_mode = "rules"
        try:
            result = answer_sales_question(question, self.OFFER)
            if result is not None:
                answer, _model = result
                self.last_answer_mode = "openai"
                return answer["answer"] if answer["known"] else None
        except OpenAIClientError:
            self.last_answer_mode = "rules_fallback"
        return self._rule_answer(question)

    @staticmethod
    def detect_interest(answer):
        answer = answer.strip().lower().replace("'", "")
        if answer in ("no", "nope", "not interested", "not now", "dont", "do not"):
            return False
        if answer in ("yes", "yeah", "yep", "interested", "i am", "sure", "okay", "ok"):
            return True
        return None
