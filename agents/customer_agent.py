from agents.llm_client import OpenAIClientError, analyze_customer_feedback, load_env_file

load_env_file()


def contains(text, words):
    text = (text or "").lower()
    for punctuation in ".,!?;:":
        text = text.replace(punctuation, " ")
    tokens = text.split()
    return any(word in tokens for word in words)


class CustomerIntelligenceAgent:
    """Summarize customer needs, objections, interests, and sentiment."""

    OBJECTIONS = {
        "price": ["expensive", "ghali", "cher"],
        "time": ["busy", "wa9t"],
    }
    NEEDS = {"price": "lower price", "time": "flexible schedule"}
    INTERESTS = {
        "course content": ["course", "cours", "content", "learn"],
        "certificate": ["certificate", "certif"],
    }
    HESITATION = {
        "trust": ["scam", "legit", "unsure"],
        "comparing": ["compare", "other", "maybe"],
    }
    POSITIVE = ["great", "love", "good", "nice", "behi"]

    @staticmethod
    def find(text, table):
        return [name for name, words in table.items() if contains(text, words)]

    def analyse(self, text):
        """Local keyword-based analysis used when no API key is configured."""
        objections = self.find(text, self.OBJECTIONS)
        interests = self.find(text, self.INTERESTS)
        hesitation = self.find(text, self.HESITATION)
        positive = contains(text, self.POSITIVE)
        if positive and objections:
            sentiment = "mixed"
        elif objections:
            sentiment = "negative"
        elif positive:
            sentiment = "positive"
        else:
            sentiment = "neutral"
        return {
            "needs": [self.NEEDS[item] for item in objections],
            "interests": interests,
            "objections": objections,
            "hesitation": hesitation,
            "sentiment": sentiment,
            "summary": "Feedback analyzed with local keyword rules.",
        }

    def analyze(self, profile):
        """Return shared structured output; use the LLM when configured."""
        profile = profile or {}
        experience = (profile.get("experience") or "not specified").strip().lower()
        goal = (profile.get("goal") or profile.get("learning_goal") or "").strip()
        analysis = self.analyse(goal)
        analysis_mode = "rules"
        analysis_note = "Local rules used. Add OPENAI_API_KEY to .env to enable AI analysis."
        model = None

        try:
            ai_result = analyze_customer_feedback(goal)
            if ai_result is not None:
                analysis, model = ai_result
                analysis_mode = "openai"
                analysis_note = "Customer feedback analyzed with the OpenAI API."
        except OpenAIClientError as exc:
            analysis_mode = "rules_fallback"
            analysis_note = "AI request unavailable; local rules were used (" + str(exc) + ")."

        segment = "beginner" if "beginner" in experience or "new" in experience else "returning learner"
        recommendation = "Start with the AI fundamentals module." if segment == "beginner" else "Use the practical exercises to build on your experience."
        if "lower price" in analysis["needs"] or "price" in analysis["objections"]:
            recommendation += " The customer mentioned price sensitivity."
        if "flexible schedule" in analysis["needs"] or "time" in analysis["objections"]:
            recommendation += " Highlight the self-paced schedule."

        result = {
            "agent": "customer_intelligence",
            "experience": experience,
            "goal": goal,
            "segment": segment,
            "recommendation": recommendation,
            "analysis_mode": analysis_mode,
            "analysis_note": analysis_note,
            **analysis,
        }
        if model:
            result["model"] = model
        return result

    def run(self, input_fn=input, output_fn=print):
        output_fn("A few questions to understand what the customer needs.")
        experience = input_fn("AI experience (beginner/intermediate/advanced): ").strip()
        goal = input_fn("What do you think about the course, and what would you like to learn? ").strip()
        return self.analyze({"experience": experience, "goal": goal})
