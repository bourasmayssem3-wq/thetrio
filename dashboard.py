"""THETRIO - local web app for the customer journey and the dashboard."""

import os
import uuid
from datetime import datetime, timezone
from html import escape
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs

from agents.business_agent import BusinessStrategyAgent
from agents.customer_agent import CustomerIntelligenceAgent
from agents.payment_agent import PaymentAgent
from agents.sales_agent import SalesAgent
from agents.security_agent import SecurityAgent
from orchestrator import compute_stats, load_records, record_event, review_payment, save_result

SESSIONS = {}
ADMIN_PIN = os.environ.get("ADMIN_PIN", "1234")

CSS = """
:root{
  --bg:#060912;
  --surface:rgba(255,255,255,.045);
  --surface-strong:rgba(255,255,255,.075);
  --line:rgba(255,255,255,.09);
  --line-strong:rgba(255,255,255,.18);
  --text:#e8ecf6;
  --text-dim:#9aa6bf;
  --text-faint:#6b7894;
  --violet:#7c5cff;
  --cyan:#22d3ee;
  --mint:#34d399;
  --amber:#fbbf24;
  --rose:#fb7185;
  --grad-brand:linear-gradient(135deg,var(--violet),var(--cyan));
  --grad-ok:linear-gradient(135deg,#10b981,var(--cyan));
  --space-1:.25rem; --space-2:.5rem; --space-3:.75rem; --space-4:1rem;
  --space-5:1.5rem; --space-6:2rem; --space-7:3rem;
  --radius-sm:10px; --radius-md:16px; --radius-lg:22px; --radius-pill:999px;
  --shadow-card:0 10px 40px -12px rgba(0,0,0,.6);
  --shadow-glow:0 0 40px -10px rgba(124,92,255,.35);
  --font-sans:"Inter","Segoe UI",system-ui,-apple-system,Roboto,sans-serif;
  --font-mono:ui-monospace,"Cascadia Code",Consolas,monospace;
  --ease:cubic-bezier(.2,.8,.2,1);
  --dur:.22s;
}
*{box-sizing:border-box}
html{color-scheme:dark}
body{
  margin:0;min-height:100vh;color:var(--text);
  font:400 16px/1.6 var(--font-sans);
  -webkit-font-smoothing:antialiased;
  background:
    radial-gradient(900px 500px at 12% -10%,rgba(124,92,255,.22),transparent 60%),
    radial-gradient(800px 500px at 100% 0%,rgba(34,211,238,.14),transparent 60%),
    radial-gradient(700px 500px at 50% 110%,rgba(52,211,153,.10),transparent 60%),
    var(--bg);
  background-attachment:fixed;
}
body::before{
  content:"";position:fixed;inset:0;pointer-events:none;z-index:0;opacity:.35;
  background-image:
    linear-gradient(var(--line) 1px,transparent 1px),
    linear-gradient(90deg,var(--line) 1px,transparent 1px);
  background-size:56px 56px;
  -webkit-mask-image:radial-gradient(ellipse at 50% 0%,#000,transparent 70%);
  mask-image:radial-gradient(ellipse at 50% 0%,#000,transparent 70%);
}
::selection{background:rgba(124,92,255,.5)}
.wrap{position:relative;z-index:1;max-width:960px;margin:0 auto;padding:var(--space-6) 20px var(--space-7)}

header{
  position:sticky;top:0;z-index:10;
  display:flex;flex-wrap:wrap;align-items:center;gap:var(--space-2) var(--space-3);
  padding:14px max(calc((100% - 960px)/2),20px);
  background:rgba(8,12,24,.65);
  -webkit-backdrop-filter:blur(16px) saturate(140%);
  backdrop-filter:blur(16px) saturate(140%);
  border-bottom:1px solid var(--line);
}
header b{
  display:flex;align-items:center;gap:12px;margin-right:auto;
  font-size:1.05rem;font-weight:800;letter-spacing:.16em;
}
header b::before{
  content:"";width:30px;height:30px;border-radius:10px;
  border:1px solid var(--line-strong);
  box-shadow:0 0 22px rgba(124,92,255,.45);
  background:
    radial-gradient(circle 5px at 9px 10px,var(--violet) 0,var(--violet) 4px,transparent 5px),
    radial-gradient(circle 5px at 21px 10px,var(--cyan) 0,var(--cyan) 4px,transparent 5px),
    radial-gradient(circle 5px at 15px 21px,var(--mint) 0,var(--mint) 4px,transparent 5px),
    rgba(255,255,255,.06);
}
header a{
  padding:8px 16px;border-radius:var(--radius-pill);border:1px solid transparent;
  color:var(--text-dim);text-decoration:none;font-size:.92rem;font-weight:600;
  transition:all var(--dur) var(--ease);
}
header a:hover{color:var(--text);background:var(--surface-strong);border-color:var(--line)}

.card{
  position:relative;margin:var(--space-4) 0;padding:var(--space-5);
  border-radius:var(--radius-lg);border:1px solid var(--line);
  background:linear-gradient(180deg,var(--surface-strong),var(--surface));
  -webkit-backdrop-filter:blur(14px);backdrop-filter:blur(14px);
  box-shadow:var(--shadow-card);
  transition:border-color var(--dur) var(--ease),box-shadow var(--dur) var(--ease);
}
.card::before{
  content:"";position:absolute;inset:0 0 auto 0;height:1px;opacity:.75;
  background:linear-gradient(90deg,transparent,rgba(124,92,255,.8),rgba(34,211,238,.8),transparent);
}
.card:hover{border-color:var(--line-strong);box-shadow:var(--shadow-card),var(--shadow-glow)}

h1{
  margin:0 0 var(--space-3);font-size:clamp(1.6rem,3.5vw,2.1rem);
  font-weight:800;line-height:1.15;letter-spacing:-.02em;
  background:linear-gradient(120deg,#fff,#b9c4ff 55%,var(--cyan));
  -webkit-background-clip:text;background-clip:text;color:transparent;
}
h2{
  display:flex;align-items:center;gap:10px;
  margin:var(--space-5) 0 var(--space-3);font-size:1.05rem;font-weight:700;color:var(--text);
}
h2:first-child{margin-top:0}
h2::before{content:"";width:4px;height:1.1em;border-radius:4px;background:var(--grad-brand)}
p{margin:.55em 0;color:var(--text-dim)}
.muted{color:var(--text-faint)}

label{
  display:block;margin:var(--space-4) 0 var(--space-2);
  font-size:.78rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--text-dim);
}
input,select,textarea{
  width:100%;padding:13px 15px;font:inherit;color:var(--text);
  background:rgba(4,7,16,.6);border:1px solid var(--line-strong);
  border-radius:var(--radius-md);outline:none;
  transition:border-color var(--dur) var(--ease),box-shadow var(--dur) var(--ease);
}
input::placeholder{color:var(--text-faint)}
input:focus,select:focus,textarea:focus{border-color:var(--cyan);box-shadow:0 0 0 4px rgba(34,211,238,.15)}
select option{background:#0b1020;color:var(--text)}

button,.button{
  display:inline-flex;align-items:center;justify-content:center;gap:8px;
  margin:var(--space-4) var(--space-2) 0 0;padding:12px 22px;
  font:inherit;font-weight:700;color:#fff;text-decoration:none;cursor:pointer;
  border:0;border-radius:var(--radius-pill);background:var(--grad-brand);
  box-shadow:0 8px 24px -8px rgba(124,92,255,.8);
  transition:transform var(--dur) var(--ease),box-shadow var(--dur) var(--ease),filter var(--dur) var(--ease);
}
button:hover,.button:hover{transform:translateY(-2px);filter:brightness(1.1);box-shadow:0 12px 30px -8px rgba(34,211,238,.7)}
button:active,.button:active{transform:translateY(0)}
button:focus-visible,.button:focus-visible,header a:focus-visible,input:focus-visible{outline:2px solid var(--cyan);outline-offset:3px}

button[style]{
  background:var(--surface-strong) !important;color:var(--text-dim);
  border:1px solid var(--line-strong);box-shadow:none;
}
button[style]:hover{color:var(--text);border-color:var(--cyan);box-shadow:none}
button[value="pay"],button[value="approve"]{background:var(--grad-ok);box-shadow:0 8px 24px -8px rgba(16,185,129,.8)}
button[value="refuse"]{color:var(--rose);border-color:rgba(251,113,133,.5)}
button[value="pending"]{color:var(--amber);border-color:rgba(251,191,36,.5)}
button[value="refuse"]:hover{border-color:var(--rose);color:var(--rose)}
button[value="pending"]:hover{border-color:var(--amber);color:var(--amber)}

.note{
  position:relative;padding:14px 16px 14px 22px;border-radius:var(--radius-md);
  font-size:.95rem;color:var(--text);
  background:linear-gradient(135deg,rgba(124,92,255,.14),rgba(34,211,238,.08));
  border:1px solid rgba(124,92,255,.28);
  transition:transform var(--dur) var(--ease),border-color var(--dur) var(--ease);
}
.note::before{content:"";position:absolute;left:0;top:12px;bottom:12px;width:3px;border-radius:3px;background:var(--grad-brand)}
.note:hover{transform:translateX(3px);border-color:rgba(34,211,238,.5)}

.status{
  display:inline-flex;align-items:center;gap:10px;padding:6px 14px;
  border-radius:var(--radius-pill);font-size:.9rem;font-weight:700;color:var(--cyan);
  background:rgba(34,211,238,.1);border:1px solid rgba(34,211,238,.35);
}
.status::before{
  content:"";width:8px;height:8px;border-radius:50%;background:var(--cyan);
  animation:pulse 1.8s infinite;
}
@keyframes pulse{
  0%{box-shadow:0 0 0 0 rgba(34,211,238,.6)}
  100%{box-shadow:0 0 0 9px rgba(34,211,238,0)}
}
.alert{
  margin:6px 0;padding:12px 16px;border-radius:var(--radius-md);color:#ffd5db;
  background:rgba(251,113,133,.1);border:1px solid rgba(251,113,133,.35);
  border-left:3px solid var(--rose);
}

.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:var(--space-3)}
.stat{
  --accent:var(--violet);
  position:relative;overflow:hidden;padding:16px 16px 14px 20px;
  border-radius:var(--radius-md);border:1px solid var(--line);background:rgba(255,255,255,.04);
  font-size:.74rem;font-weight:600;letter-spacing:.06em;text-transform:uppercase;color:var(--text-dim);
  transition:transform var(--dur) var(--ease),border-color var(--dur) var(--ease);
}
.stat::before{content:"";position:absolute;left:0;top:0;bottom:0;width:3px;background:var(--accent);box-shadow:0 0 14px var(--accent)}
.stat::after{
  content:"";position:absolute;right:-30px;top:-30px;width:90px;height:90px;border-radius:50%;
  background:var(--accent);opacity:.12;filter:blur(18px);transition:opacity var(--dur) var(--ease);
}
.stat b{
  display:block;margin-bottom:4px;font-size:clamp(1.5rem,3vw,1.9rem);font-weight:800;
  letter-spacing:-.02em;text-transform:none;color:var(--text);font-variant-numeric:tabular-nums;
}
.stat:hover{transform:translateY(-3px);border-color:var(--accent)}
.stat:hover::after{opacity:.32}
.stat:nth-child(2){--accent:var(--cyan)}
.stat:nth-child(4),.stat:nth-child(5){--accent:var(--mint)}
.stat:nth-child(6),.stat:nth-child(8){--accent:var(--rose)}
.stat:nth-child(7){--accent:var(--amber)}

ul{list-style:none;margin:0;padding:0;display:grid;gap:8px}
li{
  display:flex;justify-content:space-between;align-items:center;padding:10px 14px;
  border-radius:var(--radius-sm);border:1px solid var(--line);background:rgba(255,255,255,.035);
  color:var(--text-dim);transition:border-color var(--dur) var(--ease),color var(--dur) var(--ease);
}
li:hover{border-color:var(--line-strong);color:var(--text)}
li b{min-width:34px;padding:2px 10px;border-radius:var(--radius-pill);text-align:center;font-size:.85rem;color:#fff;background:var(--grad-brand)}

table{
  width:100%;border-collapse:separate;border-spacing:0;overflow:hidden;
  font-size:.92rem;border:1px solid var(--line);border-radius:var(--radius-md);
}
th{
  padding:12px 16px;text-align:left;font-size:.72rem;font-weight:700;
  letter-spacing:.1em;text-transform:uppercase;color:var(--text-dim);background:rgba(255,255,255,.06);
}
td{padding:12px 16px;color:var(--text);border-top:1px solid var(--line);font-variant-numeric:tabular-nums;transition:background var(--dur) var(--ease)}
td:first-child{font-family:var(--font-mono);font-size:.82rem;color:var(--text-dim)}
tr:hover td{background:rgba(124,92,255,.09)}

@media (max-width:720px){
  header{padding:12px 16px}
  .wrap{padding:var(--space-4) 14px var(--space-7)}
  .card{padding:var(--space-4);border-radius:var(--radius-md)}
  .grid{grid-template-columns:repeat(2,1fr)}
  button,.button{width:100%;margin-right:0}
  table{display:block;overflow-x:auto;white-space:nowrap}
}
@media (prefers-reduced-motion:reduce){
  *,*::before,*::after{animation:none !important;transition:none !important}
}
"""


def page(content, title="THETRIO"):
    return ("<!doctype html><html lang='en'><head><meta charset='utf-8'>"
            "<meta name='viewport' content='width=device-width, initial-scale=1'>"
            "<meta name='theme-color' content='#060912'>"
            "<title>" + escape(title) + "</title><style>" + CSS + "</style></head><body>"
            "<header><b>THETRIO</b>"
            "<a href='/'>Customer journey</a><a href='/journeys'>Dashboard</a>"
            "<a href='/admin'>Human review</a></header>"
            "<div class='wrap'>" + content + "</div></body></html>")


def form(action, fields, button="Continue"):
    return "<form method='post' action='" + action + "'>" + fields + ("<button type='submit'>" + escape(button) + "</button>" if button else "") + "</form>"


def field(label, name, placeholder="", kind="text"):
    return "<label for='" + name + "'>" + escape(label) + "</label><input id='" + name + "' name='" + name + "' type='" + kind + "' placeholder='" + escape(placeholder) + "' maxlength='300' required>"


def stat_card(label, value):
    return "<div class='stat'><b>" + escape(str(value)) + "</b>" + escape(label) + "</div>"


def dict_list(table, empty="None"):
    if not table:
        return "<p class='muted'>" + empty + "</p>"
    return "<ul>" + "".join("<li>" + escape(str(k)) + ": <b>" + str(v) + "</b></li>" for k, v in table.items()) + "</ul>"


def start_session():
    return {"stage": "sales_questions", "sales": None, "customer": None,
            "security": None, "payment": None, "created_at": None,
            "input_alerts": [], "events": [], "strategy": None}


def finalize(session, status):
    session["created_at"] = datetime.now(timezone.utc).isoformat()
    session["journey_status"] = status
    stats = compute_stats(load_records() + [session])
    strategy_agent = BusinessStrategyAgent()
    recommendations = strategy_agent.recommend(stats)
    session["strategy"] = {"agent": "business_strategy", "mode": strategy_agent.last_mode,
                            "recommendations": recommendations}
    record_event(session, "financial_data_analyst", "journey_metrics_calculated", "complete")
    record_event(session, "business_strategy", "recommendations_generated", "complete",
                 {"count": len(recommendations), "mode": strategy_agent.last_mode})
    record_event(session, "orchestrator", "journey_completed", status)
    save_result(session)
    session["stage"] = "complete"


class AppHandler(BaseHTTPRequestHandler):
    def get_session(self):
        cookies = SimpleCookie(self.headers.get("Cookie", ""))
        sid = cookies.get("sid").value if cookies.get("sid") else None
        if not sid:
            sid = uuid.uuid4().hex
        if sid not in SESSIONS:
            SESSIONS[sid] = start_session()
        self.sid = sid
        return SESSIONS[sid]

    def send_page(self, content, title="THETRIO"):
        payload = page(content, title).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Set-Cookie", "sid=" + self.sid + "; HttpOnly; SameSite=Lax; Path=/")
        self.end_headers()
        self.wfile.write(payload)

    def read_form(self):
        length = min(int(self.headers.get("Content-Length", "0")), 5000)
        data = self.rfile.read(length).decode("utf-8")
        return {key: values[0] for key, values in parse_qs(data).items()}

    def do_GET(self):
        session = self.get_session()
        if self.path == "/new":
            SESSIONS[self.sid] = start_session()
            self.render_stage(SESSIONS[self.sid])
            return
        if self.path == "/journeys":
            self.render_journeys()
            return
        if self.path == "/admin":
            self.render_admin()
            return
        self.render_stage(session)

    def do_POST(self):
        session = self.get_session()
        data = self.read_form()
        if self.path == "/admin":
            self.handle_admin(data)
            return
        stage = session["stage"]

        if stage == "sales_questions":
            question = data.get("question", "").strip()
            alerts = SecurityAgent().check_text(question)
            if alerts:
                session["input_alerts"] += alerts
                record_event(session, "security", "customer_input_check", "blocked",
                             {"alerts": alerts})
                session["message"] = "Security: this message was blocked."
            elif question.lower() in ("done", "continue", "no questions"):
                record_event(session, "sales", "offer_questions_completed", "complete")
                session["stage"] = "interest"
                session["message"] = "Great. Are you interested in joining the course?"
            else:
                sales_agent = SalesAgent()
                answer = sales_agent.answer_question(question)
                record_event(session, "sales", "customer_question",
                             sales_agent.last_answer_mode,
                             {"outcome": "answered" if answer else "unknown_topic"})
                session["message"] = answer or "I can help with the price, duration, format, or course topics."
        elif stage == "interest":
            interested = SalesAgent.detect_interest(data.get("interest", ""))
            if interested is None:
                session["message"] = "Please answer yes or no."
            else:
                session["sales"] = {"agent": "sales", "offer": SalesAgent.OFFER["name"], "price_eur": 99,
                                    "interested": interested, "status": "interested" if interested else "not_interested"}
                record_event(session, "sales", "interest_recorded", session["sales"]["status"])
                if interested:
                    session["stage"] = "customer"
                else:
                    finalize(session, "not_interested")
        elif stage == "customer":
            session["customer"] = CustomerIntelligenceAgent().analyze({
                "experience": data.get("experience", "beginner"),
                "goal": data.get("goal", ""),
            })
            record_event(session, "customer_intelligence", "profile_analyzed", "complete",
                         {"sentiment": session["customer"].get("sentiment"),
                          "objections": session["customer"].get("objections", []),
                          "mode": session["customer"].get("analysis_mode", "rules")})
            session["stage"] = "consent"
        elif stage == "consent":
            consent = data.get("consent") == "yes"
            session["security"] = SecurityAgent().check(session["sales"], session["customer"], consent)
            record_event(session, "security", "payment_authorization", session["security"]["status"],
                         {"alerts": session["security"].get("alerts", [])})
            if session["security"]["status"] == "approved":
                session["stage"] = "payment"
            else:
                finalize(session, "blocked_by_security")
        elif stage == "payment":
            choice = data.get("payment", "cancel")
            session["payment"] = PaymentAgent().run(99, input_fn=lambda _p: choice, output_fn=lambda _t: None)
            record_event(session, "payment", "payment_simulation", session["payment"]["status"])
            finalize(session, session["payment"]["status"])

        self.render_stage(session)

    def render_stage(self, session):
        stage = session["stage"]
        grey = "style='background:#65758b'"
        if stage == "sales_questions":
            offer = SalesAgent().present_offer()
            content = "<div class='card'><h1>Discover the course</h1><p>" + escape(offer) + "</p><p class='note'>Demo offer: price and course details are sample values.</p>"
            if session.get("message"):
                content += "<p class='status'>" + escape(session["message"]) + "</p>"
            content += form("/", field("Ask a question (or type done)", "question", "What is the price?"), "Ask / continue") + "</div>"
        elif stage == "interest":
            content = "<div class='card'><h1>Are you interested?</h1><p>" + escape(session.get("message", "Would you like to learn more?")) + "</p>"
            content += form("/", "<button name='interest' value='yes'>Yes, continue</button><button name='interest' value='no' " + grey + ">No, thanks</button>", "") + "</div>"
        elif stage == "customer":
            content = "<div class='card'><h1>Personalize your learning path</h1>" + form("/", "<label for='experience'>AI experience</label><select id='experience' name='experience'><option>beginner</option><option>intermediate</option><option>advanced</option></select>" + field("What do you think about the course? What do you want to learn?", "goal", "Ex: I want to learn AI tools but it is expensive"), "Continue") + "</div>"
        elif stage == "consent":
            content = "<div class='card'><h1>Security and consent</h1><p>The demo checks customer interest, the sample amount, your message, and your consent before payment.</p><p class='note'>Educational checks only; no real identity verification or fraud detection.</p>"
            content += form("/", "<button name='consent' value='yes'>I agree, continue</button><button name='consent' value='no' " + grey + ">No, stop</button>", "") + "</div>"
        elif stage == "payment":
            content = "<div class='card'><h1>Payment simulation</h1><p class='note'>SIMULATION ONLY: this will not charge money. Do not enter card details.</p><p>Course amount: €99</p>"
            content += form("/", "<button name='payment' value='pay'>Simulate success</button><button name='payment' value='refuse' " + grey + ">Simulate refused</button><button name='payment' value='pending' " + grey + ">Simulate pending</button><button name='payment' value='cancel' " + grey + ">Cancel</button>", "") + "</div>"
        else:
            content = "<div class='card'><h1>Journey complete</h1><p class='status'>" + escape(session.get("journey_status", "")) + "</p>"
            content += "<p>Sales: " + escape((session.get("sales") or {}).get("status", "")) + "</p>"
            if session.get("customer"):
                c = session["customer"]
                content += "<p>Customer segment: " + escape(c.get("segment", "")) + "</p><p>Sentiment: " + escape(c.get("sentiment", "")) + "</p><p>Objections: " + escape(", ".join(c.get("objections", [])) or "none") + "</p><p>Recommendation: " + escape(c.get("recommendation", "")) + "</p>"
                model_label = "OpenAI: " + c.get("model", "configured model") if c.get("analysis_mode") == "openai" else c.get("analysis_mode", "rules")
                content += "<p>Analysis mode: " + escape(model_label) + "</p><p class='muted'>" + escape(c.get("analysis_note", "")) + "</p>"
                if c.get("summary"):
                    content += "<p>AI summary: " + escape(c["summary"]) + "</p>"
            if session.get("security"):
                content += "<p>Security: " + escape(session["security"].get("status", "")) + "</p>"
            if session.get("payment"):
                content += "<p>Payment: " + escape(session["payment"].get("status", "")) + "</p>"
            strategy = session.get("strategy") or {}
            if strategy.get("recommendations"):
                content += "<p>Strategy mode: " + escape(strategy.get("mode", "rules")) + "</p>"
                content += "<h2>Business recommendations</h2>" + "".join(
                    "<p class='note'>" + escape(item) + "</p>" for item in strategy["recommendations"])
            if session.get("journey_status") == "pending":
                content += "<p class='note'>Your payment is pending a human review.</p>"
            content += "<a class='button' href='/new'>Start a new journey</a><a class='button' href='/journeys'>View dashboard</a></div>"
        self.send_page(content)

    def handle_admin(self, data):
        if data.get("pin") != ADMIN_PIN:
            self.render_admin("Wrong PIN. Action refused.")
            return
        try:
            index = int(data.get("index", "-1"))
        except ValueError:
            index = -1
        ok = review_payment(index, data.get("decision", ""))
        self.render_admin("Decision saved." if ok else "Nothing to update.")

    def render_admin(self, message=""):
        records = load_records()
        pending = [(i, r) for i, r in enumerate(records) if r.get("journey_status") == "pending"]
        content = "<div class='card'><h1>Human review</h1><p>Sensitive payments wait here for a human decision. Nothing is charged: simulation only.</p>"
        if message:
            content += "<p class='status'>" + escape(message) + "</p>"
        if not pending:
            content += ("<p class='muted'>No pending payments right now. To create one, start a new customer journey and choose "
                        "<b>Simulate pending</b> at the payment step.</p>"
                        "<a class='button' href='/new'>Start a customer journey</a>")
        for i, r in pending:
            pay = r.get("payment") or {}
            info = (r.get("created_at", "")[:19] + " | " + str(pay.get("transaction_id")) +
                    " | EUR " + str(pay.get("amount_eur")))
            content += ("<div class='note' style='margin:12px 0'>" + escape(info) +
                        "<form method='post' action='/admin'>"
                        "<input type='hidden' name='index' value='" + str(i) + "'>"
                        "<label>Admin PIN</label><input type='password' name='pin' placeholder='Admin PIN' maxlength='50' required>"
                        "<button type='submit' name='decision' value='approve'>Approve</button>"
                        "<button type='submit' name='decision' value='reject' style='background:#65758b'>Reject</button>"
                        "</form></div>")
        reviewed = [(r.get("created_at", "")[:19],
                     (r.get("payment") or {}).get("transaction_id", "-"),
                     (r.get("human_review") or {}).get("decision", "-"),
                     r.get("journey_status", ""))
                    for r in reversed(records) if r.get("human_review")]
        if reviewed:
            content += "<h2>Recently reviewed</h2><table><tr><th>Time (UTC)</th><th>Transaction</th><th>Decision</th><th>Result</th></tr>"
            for when, transaction, decision, result in reviewed[:10]:
                content += "<tr>" + "".join("<td>" + escape(str(v)) + "</td>" for v in (when, transaction, decision, result)) + "</tr>"
            content += "</table>"
        content += "</div>"
        self.send_page(content, "THETRIO - Human review")

    def render_journeys(self):
        records = load_records()
        stats = compute_stats(records)
        strategy_agent = BusinessStrategyAgent()
        recs = strategy_agent.recommend(stats, use_ai=False)
        strategy_mode = "rules"
        for record in reversed(records):
            stored_strategy = record.get("strategy") or {}
            if stored_strategy.get("recommendations"):
                recs = stored_strategy["recommendations"]
                strategy_mode = stored_strategy.get("mode", "rules")
                break

        cards = "".join([
            stat_card("Journeys", stats["total_journeys"]),
            stat_card("Interested customers", stats["interested"]),
            stat_card("Conversion rate (%)", stats["conversion_rate_percent"]),
            stat_card("Simulated revenue (EUR)", stats["simulated_revenue_eur"]),
            stat_card("Payments success", stats["payments_success"]),
            stat_card("Payments refused", stats["payments_refused"]),
            stat_card("Payments pending", stats["payments_pending"]),
            stat_card("Security alerts", stats["security_alerts"]),
        ])
        content = "<div class='card'><h1>Dashboard</h1><div class='grid'>" + cards + "</div></div>"
        content += "<div class='card'><h2>Main objections</h2>" + dict_list(stats["objections"], "No objections detected") + "<h2>Customer sentiment</h2>" + dict_list(stats["sentiments"], "No data") + "</div>"
        content += "<div class='card'><h2>Security alerts by type</h2>" + dict_list(stats["alert_types"], "No alerts") + "</div>"
        content += "<div class='card'><h2>Business Strategy recommendations</h2><p>Analysis mode: " + escape(strategy_mode) + "</p>" + "".join("<div class='note' style='margin:8px 0'>" + escape(r) + "</div>" for r in recs) + "</div>"

        rows = []
        for record in reversed(records):
            sales, customer = record.get("sales") or {}, record.get("customer") or {}
            security, payment = record.get("security") or {}, record.get("payment") or {}
            vals = (record.get("created_at", "")[:19], sales.get("status", ""), customer.get("sentiment", "-"),
                    security.get("status", "-"), payment.get("status", "-"), record.get("journey_status", ""))
            rows.append("<tr>" + "".join("<td>" + escape(str(v)) + "</td>" for v in vals) + "</tr>")
        table = "<table><tr><th>Time (UTC)</th><th>Sales</th><th>Sentiment</th><th>Security</th><th>Payment</th><th>Journey</th></tr>"
        table += "".join(rows) if rows else "<tr><td colspan='6'>No journeys yet.</td></tr>"
        table += "</table>"
        content += "<div class='card'><h2>History</h2>" + table + "</div>"

        event_rows = []
        for record in reversed(records):
            for event in reversed(record.get("events", [])):
                event_rows.append((event.get("time", "")[:19], event.get("agent", ""),
                                   event.get("action", ""), event.get("status", "")))
                if len(event_rows) >= 30:
                    break
            if len(event_rows) >= 30:
                break
        events_table = "<table><tr><th>Time (UTC)</th><th>Agent</th><th>Action</th><th>Status</th></tr>"
        events_table += "".join("<tr>" + "".join("<td>" + escape(str(value)) + "</td>" for value in row) + "</tr>"
                                for row in event_rows)
        events_table += "</table>" if event_rows else "<p class='muted'>Event history will appear after new journeys.</p>"
        content += "<div class='card'><h2>Recent agent events</h2>" + events_table + "</div>"
        self.send_page(content, "THETRIO - Dashboard")


if __name__ == "__main__":
    print("THETRIO web app: http://127.0.0.1:8000 (Ctrl+C to stop)")
    HTTPServer(("127.0.0.1", 8000), AppHandler).serve_forever()
