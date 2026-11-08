# The Autonomous FinTech Team (THETRIO)

A local hackathon prototype that demonstrates a connected FinTech customer journey for an AI training course. It uses Python's standard library only.

## Run the website

From PowerShell in the project folder:

```powershell
python dashboard.py
```

Open <http://127.0.0.1:8000>. The website guides a customer through the sales offer and questions, interest, customer analysis, security checks, and a simulated payment. Use **Dashboard** to see journey metrics and strategy recommendations. Use **Human review** for simulated payments marked pending. Stop the server with Ctrl+C.

The terminal version is also available:

```powershell
python orchestrator.py
```

## Connected agents

1. `SalesAgent` presents the offer and records customer interest; it can use the LLM to answer questions using only the supplied offer facts.
2. `CustomerIntelligenceAgent` uses the OpenAI Responses API for structured feedback analysis when configured; otherwise it uses local keyword rules.
3. `SecurityAgent` checks risky text, consent, customer intent, and payment amount.
4. `PaymentAgent` records a simulated outcome: success, refused, pending, or cancelled.
5. `FinancialDataAnalystAgent` calculates sales, revenue, conversion, payment, and security indicators.
6. `BusinessStrategyAgent` turns those metrics into recommendations, using the LLM when configured and local rules otherwise.

The orchestrator and website pass structured dictionaries between agents, save completed journeys in `data/transactions.json`, and write operational events to `logs/app.log`. The Dashboard includes a recent agent-event history; event details avoid storing raw conversation text.

## Hackathon deliverables

- [Multi-agent architecture diagram and responsibilities](docs/architecture.md)
- [Presentation script and end-to-end demo steps](docs/presentation.md)

## Human review

Choose **pending** in the simulated payment step, then open **Human review**. The demo PIN is `1234`. It can be changed by setting the `ADMIN_PIN` environment variable before starting the web app. In PowerShell:

```powershell
$env:ADMIN_PIN = "your-demo-pin"
python dashboard.py
```

## Demo limitations

## Optional AI analysis

Sales answers, customer-feedback analysis, and business recommendations can use the OpenAI Responses API when `OPENAI_API_KEY` is set in `.env`. Structured Outputs keep model results in the expected JSON shape. If the key is missing or a request fails, the app clearly labels and uses local rules instead. Financial calculations, security checks, and payment outcomes remain deterministic. No API key is required to run the demo.

1. Add your API key to `.env` locally as `OPENAI_API_KEY=...` (do not paste it in chat or commit the file).
2. Set `OPENAI_MODEL` to a model enabled for your API account (the sample `.env` uses `gpt-6-astra`).
3. Restart `python dashboard.py` and complete a journey; the sales event, customer analysis, and strategy result show whether OpenAI or local rules were used.

Only use fictional questions and feedback in this demo. Sales questions and feedback are sent to the configured OpenAI API; the business agent sends aggregated metrics. Do not enter names, emails, payment data, or other personal information. The app may make one model request per sales question and additional requests for customer analysis and strategy recommendations. API usage may be billed by the provider.

The course description, four-week duration, and €99 price are sample values. No actual payment provider or bank is contacted, and no card details are collected. Security checks remain educational rules, not production fraud detection or identity checks. Voice interaction is not implemented. Keep the local demo PIN out of real or shared deployments.
