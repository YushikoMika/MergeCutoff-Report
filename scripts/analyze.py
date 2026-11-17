#!/usr/bin/env python3
"""Analyze mergesort CUTOFF benchmark results.

Usage: python3 scripts/analyze.py [results/raw.csv] [results/]
Outputs (in the results dir):
  summary.csv         mean/median/std/n per (size, input_type, cutoff)
  best_cutoff.csv     best cutoff per (size, input_type) + comparison with 7 and 10
  summary_tables.md   the same as Markdown tables
  plot_<type>_abs.png        time vs cutoff, one panel per size, error bars = std
  plot_<type>_relative.png   time relative to the best cutoff, one line per size
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

raw_path = Path(sys.argv[1] if len(sys.argv) > 1 else "results/raw.csv")
out_dir = Path(sys.argv[2] if len(sys.argv) > 2 else raw_path.parent)
out_dir.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(raw_path)
df["time_ms"] = df["time_ns"] / 1e6

# ---------- summary statistics ----------
g = df.groupby(["size", "input_type", "cutoff"])["time_ms"]
summary = g.agg(mean="mean", median="median", std="std", n="count").reset_index()
summary["sem"] = summary["std"] / np.sqrt(summary["n"])
summary.to_csv(out_dir / "summary.csv", index=False, float_format="%.6f")

sizes = sorted(summary["size"].unique())
types = list(dict.fromkeys(df["input_type"]))  # keep file order
cutoffs = sorted(summary["cutoff"].unique())


# ---------- best cutoff per configuration ----------
def noise_equivalent(sub, best_row):
    """Cutoffs whose mean differs from the best by less than 2 combined standard errors."""
    d = (sub["mean"] - best_row["mean"]).abs()
    se = np.sqrt(sub["sem"] ** 2 + best_row["sem"] ** 2)
    return sub.loc[d <= 2 * se, "cutoff"].tolist()


def compact(values):
    """[3,4,5,7,8] -> '3-5, 7-8'"""
    values = sorted(values)
    out, start, prev = [], None, None
    for v in values:
        if start is None:
            start = prev = v
        elif v == prev + 1 or (v in cutoffs and prev in cutoffs and cutoffs.index(v) == cutoffs.index(prev) + 1 and v - prev == 1):
            prev = v
        else:
            out.append((start, prev))
            start = prev = v
    if start is not None:
        out.append((start, prev))
    return ", ".join(str(a) if a == b else f"{a}-{b}" for a, b in out)


rows = []
for (size, typ), sub in summary.groupby(["size", "input_type"]):
    best_mean = sub.loc[sub["mean"].idxmin()]
    best_med = sub.loc[sub["median"].idxmin()]
    r = {
        "size": size,
        "input_type": typ,
        "best_cutoff_mean": int(best_mean["cutoff"]),
        "best_mean_ms": best_mean["mean"],
        "best_cutoff_median": int(best_med["cutoff"]),
        "best_median_ms": best_med["median"],
        "indistinguishable_from_best": compact(noise_equivalent(sub, best_mean)),
    }
    for c in (1, 7, 10):
        row = sub[sub["cutoff"] == c]
        if len(row):
            r[f"mean_ms_c{c}"] = row["mean"].iloc[0]
            r[f"slowdown_c{c}_pct"] = 100 * (row["mean"].iloc[0] / best_mean["mean"] - 1)
    rows.append(r)
best = pd.DataFrame(rows)
best.to_csv(out_dir / "best_cutoff.csv", index=False, float_format="%.4f")

# overall recommendation: for each cutoff, geometric mean of (mean / best mean) over
# the random-input configurations (the main case) and over all inputs
summary = summary.merge(
    summary.groupby(["size", "input_type"])["mean"].min().rename("best_mean"),
    on=["size", "input_type"],
)
summary["rel"] = summary["mean"] / summary["best_mean"]


def overall(frame):
    return frame.groupby("cutoff")["rel"].apply(lambda x: np.exp(np.log(x).mean()))


ov_random = overall(summary[summary["input_type"] == "random"])
ov_all = overall(summary)

# ---------- markdown tables ----------
with open(out_dir / "summary_tables.md", "w") as f:
    f.write("# Summary tables (times in ms)\n\n")
    f.write("## Best cutoff per configuration\n\n")
    f.write(best.round(4).to_markdown(index=False) + "\n\n")
    f.write("## Overall relative cost per cutoff (geometric mean of mean/best-mean; 1.000 = best)\n\n")
    ov = pd.DataFrame({"random_inputs": ov_random, "all_inputs": ov_all}).round(4)
    f.write(ov.to_markdown() + "\n\n")
    for typ in types:
        for size in sizes:
            sub = summary[(summary["input_type"] == typ) & (summary["size"] == size)]
            f.write(f"## {typ}, n = {size:,}\n\n")
            f.write(sub[["cutoff", "mean", "median", "std", "n"]].round(4).to_markdown(index=False) + "\n\n")

print("Best cutoff per configuration:")
print(best[["size", "input_type", "best_cutoff_mean", "best_cutoff_median",
            "indistinguishable_from_best", "slowdown_c7_pct", "slowdown_c10_pct"]]
      .round(2).to_string(index=False))
print("\nOverall (random inputs) - 5 best cutoffs by relative cost:")
print(ov_random.sort_values().head(5).round(4).to_string())
print("\nOverall (all inputs) - 5 best cutoffs by relative cost:")
print(ov_all.sort_values().head(5).round(4).to_string())

# ---------- plots ----------
for typ in types:
    sub_t = summary[summary["input_type"] == typ]

    # (a) absolute time, one panel per size
    fig, axes = plt.subplots(1, len(sizes), figsize=(5 * len(sizes), 4), squeeze=False)
    for ax, size in zip(axes[0], sizes):
        s = sub_t[sub_t["size"] == size].sort_values("cutoff")
        ax.errorbar(s["cutoff"], s["mean"], yerr=s["std"], fmt="o-", ms=3, capsize=2, lw=1,
                    label="mean ± std")
        ax.plot(s["cutoff"], s["median"], "s--", ms=3, lw=0.8, alpha=0.7, label="median")
        b = s.loc[s["mean"].idxmin()]
        ax.axvline(b["cutoff"], color="green", ls=":", label=f"best = {int(b['cutoff'])}")
        ax.axvline(7, color="gray", ls="--", lw=0.8)
        ax.axvline(10, color="gray", ls="--", lw=0.8)
        ax.set_xscale("log")
        ax.set_title(f"n = {size:,}")
        ax.set_xlabel("CUTOFF (log scale)")
        ax.set_ylabel("time (ms)")
        ax.legend(fontsize=7)
    fig.suptitle(f"Mergesort time vs CUTOFF - {typ} (gray lines: 7 and 10)")
    fig.tight_layout()
    fig.savefig(out_dir / f"plot_{typ}_abs.png", dpi=150)
    plt.close(fig)

    # (b) relative to best cutoff, one line per size
    fig, ax = plt.subplots(figsize=(7, 4.5))
    for size in sizes:
        s = sub_t[sub_t["size"] == size].sort_values("cutoff")
        ax.errorbar(s["cutoff"], s["mean"] / s["best_mean"], yerr=s["sem"] / s["best_mean"],
                    fmt="o-", ms=3, capsize=2, lw=1, label=f"n = {size:,}")
    ax.axvline(7, color="gray", ls="--", lw=0.8)
    ax.axvline(10, color="gray", ls="--", lw=0.8)
    ax.set_xscale("log")
    ax.set_xlabel("CUTOFF (log scale)")
    ax.set_ylabel("mean time / best mean time")
    ax.set_title(f"Relative time vs CUTOFF - {typ} (error bars: ±1 SEM)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_dir / f"plot_{typ}_relative.png", dpi=150)
    plt.close(fig)

# (c) overall curve
fig, ax = plt.subplots(figsize=(7, 4.5))
ax.plot(ov_random.index, ov_random.values, "o-", ms=3, label="random inputs")
ax.plot(ov_all.index, ov_all.values, "s-", ms=3, label="all input types")
ax.axvline(7, color="gray", ls="--", lw=0.8)
ax.axvline(10, color="gray", ls="--", lw=0.8)
ax.set_xscale("log")
ax.set_xlabel("CUTOFF (log scale)")
ax.set_ylabel("geometric mean of mean/best")
ax.set_title("Overall relative cost vs CUTOFF")
ax.legend()
fig.tight_layout()
fig.savefig(out_dir / "plot_overall.png", dpi=150)
plt.close(fig)

print(f"\nWrote tables and plots to {out_dir.resolve()}")
