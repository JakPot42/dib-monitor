# DIB Financial Resilience Monitor

Defense Industrial Base supplier financial risk assessment tool. Pulls SEC 10-K/10-Q filings, uses Claude to extract debt terms and covenant language, runs a Monte Carlo (GBM) distress simulation, screens institutional ownership for CFIUS-relevant foreign connections, and generates a Supplier Financial Resilience Report PDF.

**Bridge tool:** [FriendShore](https://github.com/JakPot42/friendshore-supply-chain) flags your Tier-2 supplier as a critical single point of failure. This tool tells you whether that supplier is also financially distressed — and whether their ownership structure raises national security flags.

**Policy context:** The DoD Industrial Base Policy office tracks exactly this in its Annual Industrial Capabilities Report to Congress. This tool automates that analysis using public SEC data.

**Live demo:** [dib-monitor.onrender.com](https://dib-monitor.onrender.com)

---

## What it does

1. **Financial extraction** — Claude Haiku reads the 10-K "Liquidity and Capital Resources" section and extracts: revenue, total debt, cash, EBITDA, annual debt service, covenant language, and going-concern flags
2. **Monte Carlo simulation** — GBM model simulates 10,000 EBITDA paths; outputs P(distress) at 1, 2, and 3 years (distress = EBITDA falls below annual debt-service obligation)
3. **Ownership screening** — 13F institutional ownership data screened for CFIUS-relevant foreign connections, government-controlled entities, and shell-company structures
4. **Risk scoring** — deterministic engine combines financial score (leverage + distress probability + covenants) and ownership score (CFIUS flags + country risk) into a combined LOW/MEDIUM/HIGH/CRITICAL rating
5. **PDF report** — ReportLab report with DEMO watermark, same pattern as CFIUS Screener

---

## Demo suppliers (auto-seeded, fictional)

| Supplier | DIB Category | Combined Risk | Notable |
|----------|-------------|---------------|---------|
| Arrowhead Defense Systems | Tier 1 Subcontractor | HIGH | 8.3x leverage, $400M maturity in 2027, CFIUS-flagged owner (Bering Alpha Fund LP) |
| Meridian Propulsion Corp | Critical Sole-Source Supplier | LOW | 3.4x leverage, clean ownership, sole-source on PrSM propulsion |

---

## Architecture

```
dib_monitor/
├── config.py          — constants, risk weights, CLAUDE_MODEL pin
├── models.py          — Supplier, FinancialAssessment, OwnershipRecord (SQLAlchemy)
├── database.py        — SQLite init + session
├── edgar_client.py    — SEC EDGAR API client (EFTS search + submissions + 10-K text)
├── monte_carlo.py     — GBM distress simulation (numpy, deterministic with fixed seed)
├── risk_engine.py     — deterministic financial + ownership scoring (0–100, 4 levels)
├── claude_analyst.py  — extract_financials() + flag_ownership_concerns() (Claude Haiku)
├── pdf_export.py      — ReportLab Supplier Financial Resilience Report
├── seed_data.py       — two fictional demo suppliers (Arrowhead HIGH, Meridian LOW)
├── main.py            — FastAPI routes
└── templates/         — Jinja2 HTML templates
```

**Key design decisions:**

- **Claude extracts, code scores.** Claude Haiku reads filing text and proposes extracted facts. The risk engine (pure Python, cited weights in config.py) makes every determination. Same pattern as CFIUS Screener and ATO Accelerator.
- **DEMO_MODE pre-seeds.** The two demo suppliers have pre-baked assessments. Live EDGAR + Claude analysis is available for non-demo suppliers when `ANTHROPIC_API_KEY` is set.
- **Deterministic Monte Carlo.** Fixed `seed=42` means the demo output is reproducible. Weights and thresholds in `config.py`.
- **Exception handling.** `claude_analyst.py` catches `Exception` (not `anthropic.APIError`) — same cross-project pattern from the June 11 bug fix.

---

## Financial model

The GBM model is intentional simplification: EBITDA follows geometric Brownian motion with drift (estimated from historical revenue growth) and volatility. Distress is defined as the simulated EBITDA path falling below the annual debt-service obligation.

This is a screening model, not a valuation. It surfaces companies that warrant deeper analysis — the same directional signal the DoD IBP office uses in its supply chain resilience assessments.

---

## Running locally

```bash
git clone https://github.com/JakPot42/dib-monitor
cd dib-monitor
pip install -r requirements.txt

# Demo works without API key
uvicorn dib_monitor.main:app --reload

# Open http://localhost:8000
```

Set `ANTHROPIC_API_KEY` to enable live 10-K analysis on non-demo suppliers.

---

## Tests

```bash
pytest tests/ -v
```

50 tests. No real API calls — Claude is mocked throughout. Tests cover the Monte Carlo engine, risk scoring, seed data, and Claude extraction/ownership flagging.

---

## Honest limitations

- Monte Carlo model does not account for covenant triggers, refinancing, asset disposals, or macroeconomic shocks
- 13F data only covers institutional holders ≥$100M in AUM — meaningful ownership by smaller funds or individuals will not appear
- EDGAR 10-K text extraction truncated to 8,000 characters — very long filings may miss key sections
- Not a professional financial opinion or valuation
- CFIUS and ownership flags are for research use only
