# ============================================================
#  visualize.py  —  Semua grafik hasil analisis
#  Strategi Algoritma — UAS Research-Based Project
# ============================================================

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import os

OUTPUT_DIR = "static/output_charts"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Palet warna konsisten
TIER_COLORS = {
    "Bronze":  "#CD7F32",
    "Silver":  "#A8A9AD",
    "Gold":    "#FFD700",
    "Diamond": "#7EC8E3",
}
CAT_COLORS = {
    "Weapon-AR":     "#EF4444",
    "Weapon-Sniper": "#DC2626",
    "Weapon-SMG":    "#F97316",
    "Weapon-SG":     "#FB923C",
    "Weapon-Pistol": "#FCD34D",
    "Armor-Helmet":  "#3B82F6",
    "Armor-Vest":    "#60A5FA",
    "Medical":       "#22C55E",
    "Ammo":          "#94A3B8",
    "Utility":       "#A855F7",
    "Backpack":      "#F59E0B",
}
SC_COLORS  = ["#EF4444", "#22C55E", "#3B82F6"]
SC_LABELS  = ["Skenario A\n(Hot Zone)", "Skenario B\n(Safe Zone)", "Skenario C\n(Early Game)"]

plt.rcParams.update({
    "font.family":    "DejaVu Sans",
    "axes.spines.top":    False,
    "axes.spines.right":  False,
    "axes.grid":          True,
    "grid.alpha":         0.3,
    "grid.linestyle":     "--",
    "figure.dpi":         120,
})


# ── Chart 1: Perbandingan Total Combat Score ─────────────────────────────────

def chart_combat_score(results: list):
    """
    Bar chart — total effective value per skenario.
    results = [{"scenario": str, "total_value": float, ...}, ...]
    """
    fig, ax = plt.subplots(figsize=(8, 5))

    labels = [r["scenario"].split("—")[0].strip() for r in results]
    values = [r["total_value"] for r in results]
    bars   = ax.bar(labels, values, color=SC_COLORS, width=0.5, edgecolor="white", linewidth=1.2)

    for bar, val in zip(bars, values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 4,
            f"{val:.1f}", ha="center", va="bottom",
            fontsize=11, fontweight="bold", color="#1E293B"
        )

    ax.set_title("Perbandingan Total Combat Score Antar Skenario",
                 fontsize=13, fontweight="bold", pad=14, color="#1E293B")
    ax.set_ylabel("Total Effective Value (Combat Score)", fontsize=10)
    ax.set_ylim(0, max(values) * 1.2)
    ax.tick_params(axis="x", labelsize=10)

    path = f"{OUTPUT_DIR}/chart1_combat_score.png"
    plt.tight_layout()
    plt.savefig(path, bbox_inches="tight")
    plt.close()
    print(f"  Tersimpan: {path}")


# ── Chart 2: Distribusi Kategori Item Terpilih ──────────────────────────────

def chart_kategori_distribusi(selected_items: list, scenario_name: str, chart_id: str):
    """
    Pie chart — proporsi kategori item yang dipilih greedy.
    """
    from collections import Counter

    cats = [it["category"] for it in selected_items]
    count = Counter(cats)
    labels = list(count.keys())
    sizes  = list(count.values())
    colors = [CAT_COLORS.get(l, "#CBD5E1") for l in labels]

    fig, ax = plt.subplots(figsize=(7, 6))
    wedges, texts, autotexts = ax.pie(
        sizes, labels=None, colors=colors,
        autopct="%1.0f%%", startangle=140,
        pctdistance=0.78,
        wedgeprops={"edgecolor": "white", "linewidth": 1.5}
    )
    for at in autotexts:
        at.set_fontsize(9)
        at.set_fontweight("bold")
        at.set_color("white")

    ax.legend(
        wedges, labels,
        loc="lower center", ncol=3,
        bbox_to_anchor=(0.5, -0.18),
        fontsize=8, frameon=False
    )
    ax.set_title(f"Distribusi Kategori Item Terpilih\n{scenario_name}",
                 fontsize=12, fontweight="bold", color="#1E293B")

    path = f"{OUTPUT_DIR}/{chart_id}_kategori.png"
    plt.tight_layout()
    plt.savefig(path, bbox_inches="tight")
    plt.close()
    print(f"  Tersimpan: {path}")


# ── Chart 3: Pengaruh Kapasitas Tas terhadap Total Value ─────────────────────

def chart_kapasitas_vs_value(items: list, capacity_range: range, label: str, chart_id="chart3_kapasitas_vs_value"):
    from greedy import greedy_loot

    kapasitas_list = list(capacity_range)
    value_list = []

    for cap in kapasitas_list:
        hasil = greedy_loot(items, cap)
        value_list.append(hasil["total_value"])

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(
        kapasitas_list,
        value_list,
        color="#6366F1",
        linewidth=2.5,
        marker="o",
        markersize=6,
        markerfacecolor="white",
        markeredgewidth=2
    )

    for x, y in zip(kapasitas_list, value_list):
        ax.annotate(
            f"{y:.0f}",
            (x, y),
            textcoords="offset points",
            xytext=(0, 10),
            ha="center",
            fontsize=8,
            color="#475569"
        )

    ax.fill_between(kapasitas_list, value_list, alpha=0.08, color="#6366F1")
    ax.set_title(
        f"Pengaruh Kapasitas Tas terhadap Total Combat Score\n({label})",
        fontsize=12,
        fontweight="bold",
        color="#1E293B",
        pad=12
    )
    ax.set_xlabel("Kapasitas Tas (slot)", fontsize=10)
    ax.set_ylabel("Total Effective Value", fontsize=10)
    ax.set_xticks(kapasitas_list)

    path = f"{OUTPUT_DIR}/{chart_id}.png"
    plt.tight_layout()
    plt.savefig(path, bbox_inches="tight")
    plt.close()
    print(f"  Tersimpan: {path}")


# ── Chart 4: Distribusi Item per Tier Terpilih ───────────────────────────────

def chart_tier_distribusi(results: list):
    """
    Grouped bar chart — jumlah item per tier di tiap skenario.
    """
    tiers = ["Bronze", "Silver", "Gold", "Diamond"]
    x     = np.arange(len(SC_LABELS))
    width = 0.18

    fig, ax = plt.subplots(figsize=(10, 5))

    for i, tier in enumerate(tiers):
        counts = []
        for r in results:
            items = r.get("selected_items", [])
            counts.append(sum(1 for it in items if it["tier"] == tier))
        offset = (i - 1.5) * width
        bars = ax.bar(x + offset, counts, width,
                      label=tier, color=TIER_COLORS[tier],
                      edgecolor="white", linewidth=1)
        for bar, val in zip(bars, counts):
            if val > 0:
                ax.text(bar.get_x() + bar.get_width()/2,
                        bar.get_height() + 0.05,
                        str(val), ha="center", va="bottom",
                        fontsize=9, fontweight="bold")

    ax.set_title("Jumlah Item per Tier yang Terpilih Greedy\nper Skenario",
                 fontsize=12, fontweight="bold", color="#1E293B", pad=12)
    ax.set_ylabel("Jumlah Item", fontsize=10)
    ax.set_xticks(x)
    ax.set_xticklabels(SC_LABELS, fontsize=10)
    ax.legend(title="Tier", fontsize=9, title_fontsize=9)
    ax.set_ylim(0, ax.get_ylim()[1] * 1.2)

    path = f"{OUTPUT_DIR}/chart4_tier_distribusi.png"
    plt.tight_layout()
    plt.savefig(path, bbox_inches="tight")
    plt.close()
    print(f"  Tersimpan: {path}")


# ── Chart 5: Greedy vs Brute Force ──────────────────────────────────────────

def chart_greedy_vs_brute(greedy_val: float, brute_val: float,
                           greedy_time: float, brute_time: float):
    """
    Side-by-side comparison — nilai & waktu eksekusi.
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 5))

    # Subplot kiri: total value
    bars1 = ax1.bar(["Greedy", "Brute Force"],
                    [greedy_val, brute_val],
                    color=["#22C55E", "#EF4444"],
                    width=0.4, edgecolor="white")
    for bar, val in zip(bars1, [greedy_val, brute_val]):
        ax1.text(bar.get_x() + bar.get_width()/2,
                 bar.get_height() + 1,
                 f"{val:.1f}", ha="center", fontweight="bold", fontsize=11)
    ax1.set_title("Total Effective Value", fontweight="bold", fontsize=11)
    ax1.set_ylabel("Nilai")
    ax1.set_ylim(0, max(greedy_val, brute_val) * 1.25)

    # Subplot kanan: waktu eksekusi
    bars2 = ax2.bar(["Greedy", "Brute Force"],
                    [greedy_time * 1000, brute_time * 1000],
                    color=["#22C55E", "#EF4444"],
                    width=0.4, edgecolor="white")
    for bar, val in zip(bars2, [greedy_time*1000, brute_time*1000]):
        ax2.text(bar.get_x() + bar.get_width()/2,
                 bar.get_height() + 0.01,
                 f"{val:.3f} ms", ha="center", fontweight="bold", fontsize=10)
    ax2.set_title("Waktu Eksekusi", fontweight="bold", fontsize=11)
    ax2.set_ylabel("Waktu (ms)")
    ax2.set_ylim(0, max(greedy_time, brute_time) * 1000 * 1.4)

    fig.suptitle("Perbandingan Greedy vs Brute Force\nO(n log n) vs O(2ⁿ)",
                 fontsize=12, fontweight="bold", color="#1E293B", y=1.02)

    path = f"{OUTPUT_DIR}/chart5_greedy_vs_brute.png"
    plt.tight_layout()
    plt.savefig(path, bbox_inches="tight")
    plt.close()
    print(f"  Tersimpan: {path}")
