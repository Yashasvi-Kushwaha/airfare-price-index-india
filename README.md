# Airfare Price Index — India

> A high-frequency, quality-controlled airfare measurement system for tracking route-level airfare movements across India.

## 📌 Overview

Airfare prices change dynamically based on booking time, route demand, airline availability, taxes, seasonality, and other factors. A single aggregate airfare measure can hide short-lived price shocks and route-level differences.

This project develops an automated airfare price measurement pipeline that collects flight-fare observations, standardizes them into a common schema, applies quality checks, computes flight-matched price movements, and presents the results through an interactive dashboard.

The system is designed as a **measurement and analytical layer** that can complement existing official airfare price collection rather than replace it.

---

## 🎯 Problem Statement

The objective is to develop a system capable of:

* Automatically collecting airfare data from airline/OTA sources.
* Standardizing different fare formats into a common structure.
* Tracking airfare movements at high frequency.
* Measuring route-level price changes.
* Identifying routes experiencing unusual price stress.
* Studying the relationship between booking lead time and airfare.
* Providing transparent access to the underlying observations used in calculations.
* Supporting future development of a more granular airfare price index for India.

---

## 💡 Our Approach

The system follows the pipeline:

```text
Airline / OTA Websites
          ↓
      Web Scraper
          ↓
   Fare Normalization
          ↓
     Quality Control
          ↓
   Flight Matching
          ↓
   Price Relatives
          ↓
   Jevons Index
          ↓
 Credibility + Stress
          ↓
       FastAPI
          ↓
 Interactive Dashboard
```

The important design principle is that **raw observations are preserved** rather than immediately reducing everything to a single number.

---

# 🚀 MVP Features

### 1. Automated Fare Collection

The MVP uses **Python + Playwright** to collect flight-fare information from a live booking source.

Each observation records information such as:

* Airline
* Flight number
* Origin
* Destination
* Travel date
* Departure time
* Cabin
* Booking lead time
* Base fare
* Taxes
* Airport charges
* Convenience fee
* Baggage fee
* Total fare
* Collection timestamp
* Source

---

### 2. Canonical Fare Schema

Different websites represent fares differently.

For example:

```text
Taxes & Fees
Government Taxes
Airport Fee
Convenience Fee
```

are converted into our standard schema:

```text
base_fare
taxes
airport_charges
convenience_fee
baggage_fee
total_fare
```

Missing components are **not artificially assigned zero values**.

The system also records whether a complete fare breakdown was actually available.

---

### 3. Quality Control

Before observations enter the index calculation, deterministic checks are applied.

The system checks for:

* Missing required fields
* Invalid/unavailable flights
* Duplicate flight observations
* Invalid fare values
* Inconsistent flight identities
* Potential outliers

Importantly, an outlier is **flagged rather than automatically deleted**, preserving the audit trail.

---

### 4. Flight-Level Matching

Instead of comparing arbitrary fares from yesterday and today, the MVP attempts to compare the **same flight specification**.

The flight identity is based on:

```text
Airline
+
Flight Number
+
Origin
+
Destination
+
Departure Time
+
Travel Date
```

This reduces the risk of interpreting a change in flight composition as a genuine price change.

---

# 📊 Airfare Price Index

The MVP uses matched individual fare observations to calculate price relatives.

For observation `i`:

```text
rᵢ = Pᵢ,t / Pᵢ,t-1
```

The daily movement is calculated using a **Jevons index**:

```text
Jₜ = (Π rᵢ)^(1/n) × 100
```

The index is then chained over time:

```text
Iₜ = Iₜ₋₁ × Jₜ / 100
```

This produces a time series showing airfare price movement while maintaining like-for-like flight comparisons.

---

# 📈 Dashboard

The dashboard provides several levels of analysis.

### Route Summary

Shows:

* Route
* Number of observations
* Price movement
* Route status

### Median Fare

The median is displayed separately as a robust measure of the **typical fare observed today**.

We do **not** use the median as a substitute for the Jevons index.

### Distribution

The dashboard can display:

* Median
* Q1
* Q3
* Fare spread

This helps distinguish a broad price increase from a change concentrated in a few fares.

### Stress Analysis

Routes can be examined for unusually strong price movements.

Example:

```text
DEL → BOM      +2%       LOW
DEL → GAU     +30%      HIGH
```

This allows users to see **which routes are driving airfare pressure**, rather than looking only at an aggregate index.

---

# 🔍 Credibility Adjustment

The MVP includes an experimental **Bühlmann-style credibility adjustment**.

The idea is to avoid giving a route with very few observations the same statistical confidence as a route with substantially more information.

Conceptually:

```text
Z = n / (n + k)
```

where:

* `n` = amount of route-specific information
* `k` = smoothing/credibility parameter

The adjusted estimate is blended with a broader pooled estimate.

### Important

The credibility adjustment is **not an official CPI methodology**.

It is an experimental reliability layer intended to demonstrate how sparse-route estimates can be stabilized.

The raw index remains available separately.

---

# ⏱️ Lead-Time Analysis

Airfares depend strongly on how far in advance a ticket is purchased.

The MVP therefore compares matched flights at different booking horizons.

For example:

```text
Same flight
Same route
Same travel date

T+30 → ₹4,379
T+7  → ₹5,199.50
```

Observed increase:

```text
+18.7%
```

The dashboard visualizes this relationship using a **T+30 vs T+7 comparison**.

This is explicitly treated as an **observed relationship, not a causal claim**.

The architecture can later be extended to:

```text
T+45
T+30
T+21
T+15
T+7
T+3
T+1
```

---

# 🧾 Auditability

A major design goal is transparency.

Every calculated result should be traceable back to the observations that generated it.

The dashboard therefore includes an observation-level audit view containing:

```text
Flight
Airline
Departure
Fare
Collection time
Source
```

This makes it possible to inspect the underlying data instead of treating the index as a black box.

---

# 🗺️ Current MVP Coverage

The MVP currently demonstrates the pipeline using:

```text
DEL → BOM
DEL → IXL
```

with:

* One live scraping source
* Dense and thin route examples
* T+7 observations
* T+30 lead-time observations
* Synthetic data used as a controlled test harness for pipeline validation

The architecture is designed to expand to additional routes and sources.

---

# 🏗️ Technology Stack

| Component       | Technology          | Purpose                   |
| --------------- | ------------------- | ------------------------- |
| Scraping        | Python + Playwright | Automated fare collection |
| Data validation | Pydantic            | Schema validation         |
| Data processing | pandas + NumPy      | Transformation/statistics |
| Database ORM    | SQLAlchemy          | Database interaction      |
| Database        | SQLite              | MVP persistence           |
| Backend         | FastAPI             | API layer                 |
| Frontend        | HTML/CSS/JavaScript | Dashboard                 |
| Charts          | Chart.js            | Data visualization        |
| Testing         | Pytest              | Validation/testing        |
| Version control | Git/GitHub          | Development/versioning    |

---

# 📁 Project Structure

```text
airfare-price-index-india/
│
├── scraper/
│   └── ...
│
├── pipeline/
│   ├── fake_data_generator.py
│   ├── load_fake_data.py
│   └── ...
│
├── index_engine/
│   └── ...
│
├── database/
│   ├── models.py
│   └── db_setup.py
│
├── backend/
│   └── main.py
│
├── frontend/
│   ├── index.html
│   ├── app.js
│   └── style.css
│
├── tests/
│   └── ...
│
├── data_sources/
│   └── ...
│
└── README.md
```

---

# ⚙️ Installation

Clone the repository:

```bash
git clone <repository-url>
cd airfare-price-index-india
```

Install dependencies:

```bash
python -m pip install sqlalchemy fastapi uvicorn pydantic pandas numpy playwright
```

Install the Playwright browser:

```bash
python -m playwright install chromium
```

---

# ▶️ Running the MVP

### 1. Load test data

```bash
python pipeline\load_fake_data.py
```

### 2. Start the API

```bash
python -m uvicorn backend.main:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

FastAPI documentation:

```text
http://127.0.0.1:8000/docs
```

### 3. Start the frontend

From another terminal:

```bash
cd frontend
python -m http.server 5500
```

Open:

```text
http://127.0.0.1:5500
```

---

# 🧪 Example API

Lead-time analysis:

```text
GET /api/lead-time/DEL/BOM
```

Example response:

```json
{
  "route": "DEL-BOM",
  "T+30_median_fare": 4379.0,
  "T+7_median_fare": 5199.5,
  "percent_increase_last_minute": 18.7,
  "matched_flights": 5
}
```

Flight-level results can then show which individual flights contributed to the observed movement.

---

# 🔮 Future Development

The MVP establishes the core measurement pipeline. Future versions can expand it into a production-scale system.

### Data Coverage

* Multiple airlines
* Multiple OTAs
* More domestic routes
* Non-metro cities
* North-East India
* Hill states
* Island regions
* Airport-proxy coverage where a locality has no airport

### Index Methodology

* DGCA passenger-traffic-based route weights
* More rigorous weight updating
* Route/class aggregation
* Alternative index formulas
* Hedonic quality adjustment
* Seasonal adjustment
* Improved credibility estimation

### Analytics

* Daily/weekly/monthly/yearly comparisons
* Shock duration detection
* Route contribution analysis
* Regional airfare inflation
* Metro vs tier-2 comparisons
* Airfare vs general inflation
* Fuel-price relationship
* Airline entry/exit effects
* Policy-event analysis
* Forecasting

### Production Infrastructure

```text
SQLite
   ↓
PostgreSQL

Python Scheduler
   ↓
Airflow / Prefect

Local deployment
   ↓
Cloud infrastructure

Basic anomaly detection
   ↓
ML-based anomaly detection & forecasting
```

---

# ⚠️ Limitations

The current MVP should not be interpreted as an official CPI replacement.

Important limitations include:

* Limited number of routes
* Limited source coverage
* Limited observation history
* Synthetic data is used for controlled pipeline testing
* Scraped availability may change dynamically
* Website layouts can change
* Fare definitions may differ between sources
* Search results may not represent the entire market
* Lead-time relationships are observational
* Experimental credibility adjustment has not been statistically calibrated for official use
* Route representativeness requires appropriate external traffic weights

---

# 🎯 Why This Project Matters

The objective is not simply to display cheap or expensive flights.

The objective is to build a **transparent airfare measurement system** that can answer questions such as:

> **When did airfare pressure begin?**

> **Which routes caused it?**

> **How large was the increase?**

> **How long did the shock last?**

> **Were non-metro or regional routes affected differently?**

> **Are fares rising faster than general inflation?**

> **How reliable is the estimate given the available observations?**

This moves airfare analysis from a single aggregate number toward a **high-frequency, route-level view of price dynamics**.

---

# 👥 Team / Project

**Project:** Airfare Price Index — India
**SIH Problem Statement:** SIH26056
**Organization:** Ministry of Statistics & Programme Implementation (MoSPI)
**Category:** Software
**Theme:** Travel & Tourism

---
