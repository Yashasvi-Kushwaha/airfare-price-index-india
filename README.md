# Airfare Price Index — India

## Problem Statement (SIH26056)
Development of a Real-time Airfare Price Index for India through Automated
Web Scraping of Airline and Online Travel Aggregator Portals, to augment the
Consumer Price Index (CPI) — MoSPI, Department: Data Informatics & Innovation
Division (DIID).

## The Actual Gap — Our Reframing
MoSPI's CPI 2024 series **already** collects airfare data through online
platforms (verified via MoSPI's own FAQ documentation). This is not a
"digital collection doesn't exist" problem. The real gaps, drawn from MoSPI's
own Expert Group Report on Comprehensive Updation of CPI:

1. **Frequency gap** — Official CPI is released monthly, with a ~12-day
   lag after month-end. Airfares can move 20-30% within a single day.
   Short-lived shocks (festival demand, fuel-price jumps) can fully resolve
   before the monthly figure is ever published.
2. **Aggregation hides route-level stress** — The Expert Group explicitly
   flags that thin routes / states with few airports produce volatile,
   under-representative sub-indices (their own example: Haryana, using
   Delhi as an airport proxy). Weighted national aggregation, by
   construction, dilutes exactly these low-traffic routes — a route under
   severe stress can be nearly invisible in the topline number.

## Our Idea
A daily, flight-matched airfare index that stays statistically trustworthy
on thin route data — using actuarial credibility theory to prevent noise
from distorting the aggregate, while separately surfacing exactly the
route-level stress that same weighting would otherwise hide.

**In short:** we don't just give one number. We show which route is under
stress, how much, and whether that number is backed by enough data to trust.

## Who This Serves
- **RBI** — early signal on services inflation, ahead of the monthly CPI print
- **Civil Aviation / DGCA** — route-level connectivity and affordability monitoring
- **State governments** — visibility into whether their residents face
  disproportionate fare hikes
- **Researchers** — studying how fast shocks (fuel, capacity, policy changes)
  pass through into realized fares

## Methodology

### Two statistics, deliberately kept separate
- **Median** — daily snapshot of "what's a typical fare today," a
  standalone dashboard statistic. Never used in the index calculation.
- **Jevons Index** — the actual measure of price movement. We match the
  *same flight* (by airline + flight number) across two consecutive
  collection days, compute each matched flight's price relative
  (`today_fare / yesterday_fare`), and take the **geometric mean** of
  those relatives. This avoids composition bias from comparing different
  flight mixes day to day — a mistake naive average-to-average comparison
  makes.

price_relative_i = fare_today_i / fare_yesterday_i
Jevons movement = (Π price_relative_i)^(1/n) × 100
Chained index = previous_index × (Jevons movement / 100)

### Credibility Weighting (experimental / illustrative)
Bühlmann-style credibility blends a route's own price relative with a
pooled class-average relative, weighted by how many observations back it:

Z = n / (n + k)
credibility_weighted_relative = Z × route_relative + (1 - Z) × pooled_relative

A route with plenty of matched observations is trusted almost entirely on
its own signal. A thin route leans more on the pooled average, preventing
noise from distorting the trusted index. **The constant `k` is illustrative,
chosen to demonstrate differentiation at MVP data scale — not empirically
fitted from historical variance.** This is explicitly an experimental
reliability layer, not a validated production methodology.

### Stress Score (the actual differentiator)
Computed independently, unweighted — the raw deviation regardless of
observation count:
stress_score = (route_relative - 1) × 100
This ensures a genuinely stressed thin route is never hidden just because
credibility weighting dampens its contribution to the trusted aggregate.
**Credibility weighting answers "how much should we trust this number?"
Stress score answers "how bad is it really?" — both are shown, side by side.**

### Lead-Time Relationship
Compares median fare at two booking horizons (T+7 vs T+30) for the same
travel date. Labeled explicitly as an **observed relationship, not a
causal estimate**.

### Quality Control (deterministic, not ML)
- Required-field validation
- Availability check (sold-out ≠ ₹0)
- Duplicate detection via flight identity (airline + flight_number +
  origin + destination + departure_time + travel_date)
- Outliers flagged, not silently deleted

## Architecture / Workflow
Airline / OTA Website
↓
Scraper (Playwright)
↓
Fare Decomposition & Normalization (pandas)
↓
Quality Control (deterministic rules)
↓
SQLite Database (via SQLAlchemy)
↓
Index Engine (Jevons, numpy)
↓
Credibility + Stress Layer
↓
FastAPI (REST endpoints)
↓
Dashboard (Vanilla JS + Chart.js, sidebar navigation)

## API Endpoints
| Endpoint | Purpose |
|---|---|
| `GET /api/index` | Daily Jevons movement, credibility-adjusted relative, and stress score per route |
| `GET /api/observations/{origin}/{destination}` | Raw observations — audit trail |
| `GET /api/median-history/{origin}/{destination}` | Median fare trend over recent days |
| `GET /api/lead-time/{origin}/{destination}` | T+7 vs T+30 fare comparison |

## Current Status — Honest Scope

**What's fully working:** the complete pipeline — schema, index calculation,
credibility weighting, stress score, all four API endpoints, and a
full sidebar-navigated dashboard (Overview, Route Stress Comparison, Fare
Trends, Lead-Time Analysis, Audit Trail) — verified end-to-end with real
calculations on representative data.

**Data source:** Our Playwright scraper successfully automates search and
navigation on SpiceJet's website, reaching live results pages. Fare
extraction from SpiceJet's dynamically-rendered results (built on React
Native for Web, with auto-generated, non-persistent CSS class names) is an
active engineering task. To demonstrate the complete measurement
methodology within our build window, we validated the index, credibility,
and stress-detection logic against representative sample data matching our
exact schema — the same pipeline that will consume live scraped data once
extraction is finalized.

**Routes covered:** 2 — DEL-BOM (dense, high-traffic) and DEL-IXL (thin,
low-observation) — deliberately chosen to demonstrate the credibility /
stress differentiation live.

**Booking windows:** T+7 and T+30.

**Known limitation:** the current `/api/index` daily observation count
mixes T+7 and T+30 observations for "today" without filtering by
`advance_days` — a fix planned but not yet applied (the core index
calculation itself is correctly matched by flight and unaffected).

## Tech Stack

| Layer | MVP | Full-Scale Roadmap |
|---|---|---|
| Scraping | Python + Playwright | Playwright/Scrapy hybrid, all 11 sources |
| Normalization | pandas | Same, scaled |
| Index/Credibility/Stress | numpy, hand-written | Same core formulas, empirically-fitted k |
| Database | SQLite via SQLAlchemy | PostgreSQL |
| Backend | FastAPI | FastAPI |
| Frontend | Vanilla JS + Chart.js | React |
| Scheduling | Manual / cron | Apache Airflow |
| Caching/Queue | None | Redis + Kafka/RabbitMQ |
| Deployment | Local | Docker + Kubernetes, cloud-hosted |
| Anomaly Detection | Deterministic rules | ML (Isolation Forest), once sufficient volume exists |
| Monitoring | Logs | Prometheus + Grafana |

## Roadmap (Full-Scale Vision)
- Full coverage: 5 airlines + 6 OTAs, complete DGCA route basket
- 5 booking windows (T+1/7/15/30/45) for a full lead-time curve
- Full index hierarchy: route → city → region → national
- Full flight-product standardization (baggage, refundability, fare class)
- Airport-proxy mapping for airport-less states (per Expert Group precedent)
- Rigorously fitted credibility constant from real historical variance data
- ML-based anomaly detection once historical volume justifies it

## How to Run

1. Clone the repo and set up the environment:

python -m venv .venv
.venv\Scripts\activate.bat
pip install -r requirements.txt
playwright install chromium

2. Load sample data:

python pipeline\load_fake_data.py

3. Start the backend:

uvicorn backend.main:app --reload

4. In a separate terminal, start the frontend:

cd frontend
python -m http.server 5500

5. Open `http://127.0.0.1:5500` in your browser.

## Feasibility & Viability

**Feasibility:** Core methodology and full pipeline are technically
demonstrated end-to-end with real calculations. Production-scale requires
formal data-access agreements with airlines/OTAs (or DGCA-mediated access)
and infrastructure scale-up per the roadmap above.

**Viability:** Addresses two problems explicitly identified as open gaps in
MoSPI's own Expert Group Report. Positioned as a research / decision-support
supplementary indicator for RBI, DGCA, and state governments — not a
drop-in replacement for official CPI, and not claiming production-grade
statistical validation at MVP stage.