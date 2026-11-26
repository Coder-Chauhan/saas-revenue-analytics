"""Generate synthetic source data for a fictional B2B SaaS company.

Three source systems, each in the format it would arrive in from a real stack:
  * CRM          -> data/raw/crm_accounts.csv            (CSV export)
  * Billing API  -> data/raw/billing_invoices.json       (paginated JSON API dump)
                    data/raw/billing_subscriptions.json
  * Product      -> data/raw/product_events.csv          (product-analytics event export)
                    data/raw/product_features.csv

The data is synthetic, generated with a fixed seed so every run is reproducible.
A small number of deliberate data-quality issues are injected (duplicates, nulls,
bad currency codes, orphan events) so the validation layer has real work to do.
"""
from __future__ import annotations

import csv
import json
import random
from datetime import date, datetime, timedelta
from pathlib import Path

SEED = 42
RAW = Path(__file__).resolve().parents[1] / "data" / "raw"
START = date(2024, 1, 1)
END = date(2026, 9, 30)
EVENTS_START = date(2025, 10, 1)

INDUSTRIES = ["Banking", "Asset Management", "Insurance", "Fintech", "Exchanges", "Corporate Treasury"]
REGIONS = {"APAC": ["India", "Singapore", "Australia"], "EMEA": ["United Kingdom", "Germany", "UAE"],
           "AMER": ["United States", "Canada", "Brazil"]}
SEGMENTS = {"SMB": (3, 20), "Mid-Market": (20, 120), "Enterprise": (120, 600)}
PLANS = {"Starter": 25, "Professional": 60, "Enterprise": 110}  # price per seat per month (USD)
FEATURES = [
    ("F01", "Dashboards", "Core"), ("F02", "Report Builder", "Core"), ("F03", "Data Connectors", "Core"),
    ("F04", "Alerts", "Monitoring"), ("F05", "Anomaly Detection", "AI"), ("F06", "Natural Language Query", "AI"),
    ("F07", "Scheduled Exports", "Automation"), ("F08", "API Access", "Automation"),
    ("F09", "Audit Log", "Governance"), ("F10", "Role-Based Access", "Governance"),
]
EVENT_TYPES = ["page_view", "feature_used", "report_run", "export"]


def month_starts(start: date, end: date):
    d = date(start.year, start.month, 1)
    while d <= end:
        yield d
        d = date(d.year + (d.month // 12), d.month % 12 + 1, 1)


def main() -> None:
    rng = random.Random(SEED)
    RAW.mkdir(parents=True, exist_ok=True)

    # ---------------- CRM accounts ----------------
    accounts = []
    for i in range(1, 421):
        region = rng.choice(list(REGIONS))
        segment = rng.choices(list(SEGMENTS), weights=[0.5, 0.35, 0.15])[0]
        signup = START + timedelta(days=rng.randint(0, (END - START).days - 60))
        accounts.append({
            "account_id": f"ACC-{i:04d}",
            "account_name": f"Client {i:04d} Ltd",
            "industry": rng.choice(INDUSTRIES),
            "segment": segment,
            "region": region,
            "country": rng.choice(REGIONS[region]),
            "account_owner": f"rep_{rng.randint(1, 12):02d}",
            "created_date": signup.isoformat(),
        })
    # injected issues: one exact duplicate row and one missing industry
    dup = dict(accounts[10])
    accounts.append(dup)
    accounts[25]["industry"] = ""
    with open(RAW / "crm_accounts.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(accounts[0]))
        w.writeheader()
        w.writerows(accounts)
    accounts = accounts[:-1]

    # ---------------- Billing: subscriptions + invoices ----------------
    subs, invoices = [], []
    inv_n = 0
    for n, acc in enumerate(accounts, 1):
        lo, hi = SEGMENTS[acc["segment"]]
        seats = rng.randint(lo, hi)
        plan = {"SMB": "Starter", "Mid-Market": "Professional", "Enterprise": "Enterprise"}[acc["segment"]]
        if rng.random() < 0.2:
            plan = rng.choice(list(PLANS))
        start = date.fromisoformat(acc["created_date"]) + timedelta(days=rng.randint(0, 30))
        churn_p = {"SMB": 0.022, "Mid-Market": 0.012, "Enterprise": 0.006}[acc["segment"]]
        status, end = "active", None
        for m in month_starts(start, END):
            if m <= start:
                continue
            if rng.random() < churn_p:
                status, end = "cancelled", m
                break
            # expansion / contraction
            r = rng.random()
            if r < 0.04:
                seats = int(seats * rng.uniform(1.1, 1.4)) + 1
            elif r < 0.06:
                seats = max(1, int(seats * rng.uniform(0.7, 0.95)))
            amount = round(seats * PLANS[plan] * (0.85 if acc["segment"] == "Enterprise" else 1.0), 2)
            status_i = rng.choices(["paid", "open", "void"], weights=[0.95, 0.04, 0.01])[0]
            # a voided invoice is re-issued as a new paid invoice for the same period
            for st in (["void", "paid"] if status_i == "void" else [status_i]):
                inv_n += 1
                invoices.append({
                    "invoice_id": f"INV-{inv_n:06d}",
                    "subscription_id": f"SUB-{n:04d}",
                    "account_id": acc["account_id"],
                    "invoice_date": m.isoformat(),
                    "period_start": m.isoformat(),
                    "seats": seats,
                    "amount": amount,
                    "currency": "USD",
                    "status": st,
                })
        subs.append({
            "subscription_id": f"SUB-{n:04d}", "account_id": acc["account_id"], "plan": plan,
            "start_date": start.isoformat(), "end_date": end.isoformat() if end else None,
            "status": status, "billing_interval": "monthly",
        })
    # injected issues: lowercase / invalid currency, a negative amount, a duplicated invoice
    invoices[100]["currency"] = "usd"
    invoices[200]["currency"] = "XXX"
    invoices[300]["amount"] = -invoices[300]["amount"]
    invoices.append(dict(invoices[400]))

    def paginate(records, page_size=500):
        pages = [records[i:i + page_size] for i in range(0, len(records), page_size)]
        return [{"page": p + 1, "total_pages": len(pages), "data": rows} for p, rows in enumerate(pages)]

    (RAW / "billing_subscriptions.json").write_text(json.dumps(paginate(subs), indent=1))
    (RAW / "billing_invoices.json").write_text(json.dumps(paginate(invoices), indent=1))

    # ---------------- Product analytics events ----------------
    with open(RAW / "product_features.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["feature_id", "feature_name", "feature_area"])
        w.writerows(FEATURES)

    sub_by_acc = {s["account_id"]: s for s in subs}
    events = []
    ev_n = 0
    for acc in accounts:
        s = sub_by_acc[acc["account_id"]]
        # usage only while the account is billed: from its first invoiced month until the day before cancellation
        start_d = date.fromisoformat(s["start_date"])
        s_start = date(start_d.year + (start_d.month // 12), start_d.month % 12 + 1, 1)
        s_end = date.fromisoformat(s["end_date"]) - timedelta(days=1) if s["end_date"] else END
        n_users = max(2, int(rng.randint(*SEGMENTS[acc["segment"]]) * 0.3))
        engagement = rng.uniform(0.2, 1.0)
        adopted = rng.sample(FEATURES, k=rng.randint(3, len(FEATURES)))
        # some paying accounts go quiet for a whole month (no logins): a churn-risk signal
        dormant_p = {"SMB": 0.20, "Mid-Market": 0.12, "Enterprise": 0.06}[acc["segment"]]
        dormant_months = {m for m in month_starts(EVENTS_START, END) if rng.random() < dormant_p}
        d = max(s_start, EVENTS_START)  # keep twelve full months of events
        while d <= s_end:
            if date(d.year, d.month, 1) in dormant_months:
                d += timedelta(days=1)
                continue
            if d.weekday() < 5 and rng.random() < engagement:
                for _ in range(rng.randint(1, min(6, n_users))):
                    ev_n += 1
                    feat = rng.choice(adopted)
                    ts = datetime(d.year, d.month, d.day, rng.randint(1, 22), rng.randint(0, 59))
                    events.append([f"EV-{ev_n:07d}", acc["account_id"],
                                   f"{acc['account_id']}-U{rng.randint(1, n_users):03d}",
                                   ts.isoformat(), rng.choices(EVENT_TYPES, weights=[0.4, 0.35, 0.2, 0.05])[0],
                                   feat[0]])
            d += timedelta(days=1)
    # injected issues: orphan events from an unknown account
    for k in range(25):
        ev_n += 1
        events.append([f"EV-{ev_n:07d}", "ACC-9999", "ACC-9999-U001", "2026-06-01T10:00:00", "page_view", "F01"])
    with open(RAW / "product_events.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["event_id", "account_id", "user_id", "event_timestamp", "event_type", "feature_id"])
        w.writerows(events)

    print(f"accounts={len(accounts)} subscriptions={len(subs)} invoices={len(invoices)} events={len(events)}")


if __name__ == "__main__":
    main()
