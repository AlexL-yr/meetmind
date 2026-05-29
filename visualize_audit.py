"""Generate academic-style audit result visualizations using seaborn/matplotlib."""
import json
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
import seaborn as sns

# ── Load data (deduplicate: keep latest entry per transcript_id) ──────────────
_seen: dict = {}
with open("audit_cases/results/audit_log.jsonl", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line:
            r = json.loads(line)
            _seen[r["transcript_id"]] = r   # last write wins
results = list(_seen.values())

# ── Palette & style ───────────────────────────────────────────────────────────
sns.set_theme(style="whitegrid", font="DejaVu Sans")
PALETTE = {
    "false_decision":  "#2c7bb6",
    "fabrication":     "#d7191c",
    "inferred_task":   "#fdae61",
    "misattribution":  "#1a9641",
    "omission":        "#969696",
}
DEFECT_LABELS = {
    "ambiguous_owner":      "Ambiguous\nOwner",
    "conflicting_deadline": "Conflicting\nDeadline",
    "implicit_action":      "Implicit\nAction",
    "missing_attendee":     "Missing\nAttendee",
    "no_decision":          "No\nDecision",
}
SEVERITY_COLORS = {"high": "#d7191c", "medium": "#fdae61", "low": "#2c7bb6"}
OUTPUT_DIR = Path("audit_cases/results/figures")
OUTPUT_DIR.mkdir(exist_ok=True)

# ── Build DataFrames ──────────────────────────────────────────────────────────
rows = []
flag_rows = []
for r in results:
    defect = r["defect_type"]
    rows.append({
        "transcript_id": r["transcript_id"],
        "defect_type": defect,
        "defect_label": DEFECT_LABELS[defect],
        "hallucination_score": r["hallucination_score"],
        "overall_risk": r["overall_risk"],
        "flag_count": len(r["hallucination_flags"]),
    })
    for flag in r["hallucination_flags"]:
        flag_rows.append({
            "defect_type": defect,
            "defect_label": DEFECT_LABELS[defect],
            "hallucination_type": flag["hallucination_type"],
            "severity": flag["severity"],
        })

df = pd.DataFrame(rows)
df_flags = pd.DataFrame(flag_rows)

# ══════════════════════════════════════════════════════════════════════════════
# Figure 1 — Hallucination Score by Defect Type
# ══════════════════════════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(7, 4))

order = [DEFECT_LABELS[d] for d in [
    "ambiguous_owner", "conflicting_deadline",
    "implicit_action", "missing_attendee", "no_decision"
]]
avg = df.groupby("defect_label")["hallucination_score"].mean().reindex(order)
std = df.groupby("defect_label")["hallucination_score"].std().reindex(order).fillna(0)

bars = ax.bar(order, avg.values, yerr=std.values, capsize=4,
              color="#4393c3", edgecolor="white", linewidth=0.8,
              error_kw=dict(ecolor="#555", elinewidth=1.2))

ax.set_ylim(0, 1.0)
ax.set_ylabel("Hallucination Score (0–1)", fontsize=11)
ax.set_xlabel("Injected Defect Type", fontsize=11)
ax.set_title("Figure 1. Mean Hallucination Score by Defect Type", fontsize=12, pad=10)
ax.axhline(df["hallucination_score"].mean(), color="#d7191c",
           linestyle="--", linewidth=1.2, label=f"Overall mean = {df['hallucination_score'].mean():.2f}")
ax.legend(fontsize=9)

for bar, val in zip(bars, avg.values):
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.03,
            f"{val:.2f}", ha="center", va="bottom", fontsize=9)

plt.tight_layout()
fig.savefig(OUTPUT_DIR / "fig1_score_by_defect.png", dpi=300, bbox_inches="tight")
plt.close()
print("Saved fig1_score_by_defect.png")

# ══════════════════════════════════════════════════════════════════════════════
# Figure 2 — Hallucination Type Distribution (horizontal bar)
# ══════════════════════════════════════════════════════════════════════════════
type_counts = df_flags["hallucination_type"].value_counts()
type_labels = {
    "false_decision": "False Decision",
    "fabrication":    "Fabrication",
    "inferred_task":  "Inferred Task",
    "misattribution": "Misattribution",
    "omission":       "Omission",
}

fig, ax = plt.subplots(figsize=(7, 3.5))
colors = [PALETTE.get(t, "#aaa") for t in type_counts.index]
bars = ax.barh([type_labels.get(t, t) for t in type_counts.index],
               type_counts.values, color=colors, edgecolor="white")

ax.set_xlabel("Number of Flags", fontsize=11)
ax.set_title("Figure 2. Hallucination Type Frequency", fontsize=12, pad=10)
ax.bar_label(bars, padding=3, fontsize=10)
ax.set_xlim(0, type_counts.max() + 2)

plt.tight_layout()
fig.savefig(OUTPUT_DIR / "fig2_hallucination_types.png", dpi=300, bbox_inches="tight")
plt.close()
print("Saved fig2_hallucination_types.png")

# ══════════════════════════════════════════════════════════════════════════════
# Figure 3 — Stacked severity breakdown per defect type
# ══════════════════════════════════════════════════════════════════════════════
sev_order = ["high", "medium", "low"]
pivot = (df_flags.groupby(["defect_label", "severity"])
         .size().unstack(fill_value=0)
         .reindex(columns=sev_order, fill_value=0)
         .reindex(order))

fig, ax = plt.subplots(figsize=(7, 4))
bottom = np.zeros(len(pivot))
for sev in sev_order:
    if sev in pivot.columns:
        vals = pivot[sev].values
        ax.bar(pivot.index, vals, bottom=bottom,
               label=sev.capitalize(), color=SEVERITY_COLORS[sev],
               edgecolor="white", linewidth=0.8)
        for i, (v, b) in enumerate(zip(vals, bottom)):
            if v > 0:
                ax.text(i, b + v / 2, str(v), ha="center", va="center",
                        fontsize=9, color="white", fontweight="bold")
        bottom += vals

ax.set_ylabel("Number of Flags", fontsize=11)
ax.set_xlabel("Injected Defect Type", fontsize=11)
ax.set_title("Figure 3. Flag Severity Distribution by Defect Type", fontsize=12, pad=10)
ax.legend(title="Severity", fontsize=9, title_fontsize=9)

plt.tight_layout()
fig.savefig(OUTPUT_DIR / "fig3_severity_by_defect.png", dpi=300, bbox_inches="tight")
plt.close()
print("Saved fig3_severity_by_defect.png")

# ══════════════════════════════════════════════════════════════════════════════
# Figure 4 — Per-case heatmap (hallucination score + flag types)
# ══════════════════════════════════════════════════════════════════════════════
type_order = ["false_decision", "fabrication", "inferred_task", "misattribution"]
heatmap_data = []
for r in results:
    row = {"Case": r["transcript_id"].replace("-", "‑")}  # non-breaking hyphen
    row["Score"] = r["hallucination_score"]
    counts = defaultdict(int)
    for flag in r["hallucination_flags"]:
        counts[flag["hallucination_type"]] += 1
    for t in type_order:
        row[type_labels.get(t, t)] = counts[t]
    heatmap_data.append(row)

hdf = pd.DataFrame(heatmap_data).set_index("Case")
score_col = hdf.pop("Score")

n_cases = len(hdf)
fig_h = max(4.0, n_cases * 0.42)
fig, axes = plt.subplots(1, 2, figsize=(11, fig_h),
                          gridspec_kw={"width_ratios": [1, 4]})

# Score column
sns.heatmap(score_col.to_frame(), ax=axes[0], annot=True, fmt=".2f",
            cmap="YlOrRd", vmin=0, vmax=1, linewidths=0.6,
            cbar_kws={"label": "Score"}, annot_kws={"size": 10})
axes[0].set_title("Score", fontsize=11)
axes[0].set_ylabel("")
axes[0].tick_params(axis="y", labelsize=9)

# Flag counts
sns.heatmap(hdf, ax=axes[1], annot=True, fmt="d",
            cmap="Blues", linewidths=0.6,
            cbar_kws={"label": "Flag count"}, annot_kws={"size": 10})
axes[1].set_title("Hallucination Flags per Type", fontsize=11)
axes[1].set_ylabel("")
axes[1].set_yticklabels([])
axes[1].tick_params(axis="x", labelsize=10)

fig.suptitle("Figure 4. Per-Case Audit Overview", fontsize=13, y=1.02)
plt.tight_layout()
fig.savefig(OUTPUT_DIR / "fig4_case_heatmap.png", dpi=300, bbox_inches="tight")
plt.close()
print("Saved fig4_case_heatmap.png")

# ══════════════════════════════════════════════════════════════════════════════
# Figure 5 — RAG cross-case Jaccard similarity of hallucination-type sets
# ══════════════════════════════════════════════════════════════════════════════
rag_path = Path("audit_cases/results/rag_analysis.json")
if rag_path.exists():
    import json as _json
    rag = _json.loads(rag_path.read_text(encoding="utf-8"))

    # Build N×N Jaccard matrix from all audit cases
    case_ids = sorted(rag["cases"])
    n = len(case_ids)
    idx = {c: i for i, c in enumerate(case_ids)}
    mat = np.zeros((n, n))
    np.fill_diagonal(mat, 1.0)   # self-similarity = 1

    # Fill from edges (symmetric)
    for e in rag["edges"]:
        q, nb, j = e["query"], e["neighbor"], e["jaccard"]
        if q in idx and nb in idx:
            mat[idx[q], idx[nb]] = j
            mat[idx[nb], idx[q]] = j

    # Short labels: "miss-att-001" → "MA-001" style
    short = [
        c.replace("missing-attendee", "MA")
         .replace("ambiguous-owner", "AO")
         .replace("conflicting-deadline", "CD")
         .replace("implicit-action", "IA")
         .replace("no-decision", "ND")
        for c in case_ids
    ]

    fig, ax = plt.subplots(figsize=(8, 6))
    sns.heatmap(
        mat, ax=ax,
        xticklabels=short, yticklabels=short,
        annot=True, fmt=".2f",
        cmap="YlGnBu", vmin=0, vmax=1,
        linewidths=0.4,
        cbar_kws={"label": "Jaccard similarity (hallucination types)"},
        annot_kws={"size": 8},
    )
    ax.set_title(
        "Figure 5. RAG Cross-Case Hallucination Pattern Similarity\n"
        "(Jaccard index of hallucination-type sets, retrieved via ChromaDB semantic search)",
        fontsize=11, pad=12,
    )
    ax.tick_params(axis="x", rotation=45, labelsize=8)
    ax.tick_params(axis="y", rotation=0,  labelsize=8)

    plt.tight_layout()
    fig.savefig(OUTPUT_DIR / "fig5_rag_similarity.png", dpi=300, bbox_inches="tight")
    plt.close()
    print("Saved fig5_rag_similarity.png")
else:
    print("Skipping fig5 — run: python run_audit.py --analyze  first")

print(f"\nAll figures saved to: {OUTPUT_DIR.resolve()}")
