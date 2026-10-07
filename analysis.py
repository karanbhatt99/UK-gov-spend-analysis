"""
Home Office spending analysis: is the 'March budget flush' real?
----------------------------------------------------------------
Tests the common belief that UK government departments dump unspent
budget in March (financial year end) by looking at 12 months of
Home Office 'spending over GBP 25,000' transparency data.

Data source: data.gov.uk, Home Office spending over GBP 25,000,
financial year 2025-26 (April 2025 to March 2026).

Author: Karan Bhatt
"""

import glob
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

RAW_DIR = "data/raw"          # put the 12 monthly CSVs here
NAVY, SLATE, MUTED, INK = "#1F3A5F", "#AEBECD", "#777777", "#333333"

FY_ORDER = ["2025-04", "2025-05", "2025-06", "2025-07", "2025-08", "2025-09",
            "2025-10", "2025-11", "2025-12", "2026-01", "2026-02", "2026-03"]
MONTH_LABELS = ["Apr", "May", "Jun", "Jul", "Aug", "Sep",
                "Oct", "Nov", "Dec", "Jan", "Feb", "Mar"]


def load_file(path):
    """Read one monthly CSV, trying encodings in order.
    Government CSVs are inconsistent: some carry a UTF-8 BOM, some use
    Windows-1252 (e.g. an en-dash byte), so we try the robust ones."""
    for enc in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            return pd.read_csv(path, encoding=enc)
        except UnicodeDecodeError:
            continue
    return pd.read_csv(path, encoding="latin-1")


def build_dataset(raw_dir):
    """Load every monthly file, clean, and combine into one tidy frame.
    Falls back to the committed cleaned dataset if no raw files are present,
    so the analysis runs out-of-the-box on clone."""
    files = sorted(glob.glob(f"{raw_dir}/*.csv"))
    if not files:
        print("No raw files found; using committed data/ho_fy2526_combined.csv")
        df = pd.read_csv("data/ho_fy2526_combined.csv")
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        df["Month"] = df["Date"].dt.to_period("M").astype(str)
        return df
    frames = []
    for f in files:
        df = load_file(f)
        # strip BOM char and whitespace from headers
        df.columns = [c.replace("﻿", "").strip() for c in df.columns]
        frames.append(df)

    df = pd.concat(frames, ignore_index=True)
    df = df.drop_duplicates()                       # one month was uploaded twice
    df["Date"] = pd.to_datetime(df["Date"], format="%d/%m/%Y", errors="coerce")
    df["Month"] = df["Date"].dt.to_period("M").astype(str)
    return df


def three_way_test(df):
    """A spike in total spend alone can be faked by one huge contract.
    So we test three ways: total value, transaction COUNT, and the share
    of spend from single transactions over GBP 1m. A real 'flush' would
    lift total AND count. A contract-driven spike lifts only value."""
    g = df.groupby("Month").agg(
        total_gbp=("Amount", "sum"),
        txn_count=("Amount", "size"),
        median_gbp=("Amount", "median"),
    )
    big = df[df["Amount"] > 1_000_000].groupby("Month")["Amount"].sum()
    g["big_contract_share_pct"] = (big / g["total_gbp"] * 100).round(1)
    return g.reindex(FY_ORDER)


def _bar(values, title, subtitle, ylabel, fmt, outfile, highlight="2025-04"):
    colors = [NAVY if m == highlight else SLATE for m in FY_ORDER]
    fig, ax = plt.subplots(figsize=(10, 5.2), dpi=150)
    fig.patch.set_facecolor("white"); ax.set_facecolor("white")
    ax.bar(range(12), values, color=colors, width=0.72, zorder=3)
    top = max(values) * 1.12
    for i, v in enumerate(values):
        ax.text(i, v + top * 0.012, fmt(v), ha="center", va="bottom", fontsize=8.5,
                color=NAVY if FY_ORDER[i] == highlight else MUTED,
                fontweight="bold" if FY_ORDER[i] == highlight else "normal")
    ax.set_xticks(range(12)); ax.set_xticklabels(MONTH_LABELS, fontsize=9.5, color=INK)
    ax.set_ylim(0, top)
    for s in ["top", "right", "left"]:
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color("#CCCCCC"); ax.tick_params(length=0)
    ax.yaxis.grid(True, color="#EEEEEE", zorder=0); ax.set_axisbelow(True)
    ax.set_yticklabels([]); ax.set_ylabel(ylabel, fontsize=9, color=MUTED)
    fig.text(0.065, 0.965, title, fontsize=15, fontweight="bold", color=NAVY, va="top")
    fig.text(0.065, 0.908, subtitle, fontsize=9.8, color=MUTED, va="top")
    fig.text(0.065, 0.02,
             "Source: data.gov.uk, Home Office spending over GBP 25,000 (Apr 2025 to Mar 2026).",
             fontsize=7.5, color="#999999")
    plt.subplots_adjust(top=0.84, bottom=0.12, left=0.065, right=0.97)
    plt.savefig(outfile, dpi=150, facecolor="white"); plt.close()


def main():
    df = build_dataset(RAW_DIR)
    print(f"Loaded {len(df):,} transactions, total GBP {df['Amount'].sum():,.0f}")
    summary = three_way_test(df)
    print(summary.to_string())
    summary.to_csv("monthly_summary.csv")

    _bar(summary["total_gbp"].values / 1e6,
         'The March "budget flush" is a myth at the Home Office',
         "Monthly spend over GBP 25,000, FY2025-26. Spending peaks in April, the first month, not March.",
         "Spend over GBP 25k (GBP millions)", lambda v: f"{v:,.0f}",
         "charts/chart_monthly_spend.png")

    _bar(summary["big_contract_share_pct"].values,
         "April's spike is a few big contracts, not a broad surge",
         "Share of each month's spend from single transactions over GBP 1m. April is 78 percent, the year's highest.",
         "Share from transactions over GBP 1m", lambda v: f"{v:.0f}%",
         "charts/chart_bigcontract_share.png")


if __name__ == "__main__":
    main()
