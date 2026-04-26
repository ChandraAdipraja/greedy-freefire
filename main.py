import time
import pandas as pd
from tabulate import tabulate

from greedy import greedy_loot, brute_force_loot
from visualize import (
    chart_combat_score,
    chart_kategori_distribusi,
    chart_kapasitas_vs_value,
    chart_tier_distribusi,
    chart_greedy_vs_brute,
)

ITEMS_CSV     = "items.csv"
SCENARIOS_CSV = "scenarios.csv"

TIER_MULTIPLIER = {"Bronze": 1.0, "Silver": 1.3, "Gold": 1.6, "Diamond": 2.0}


def load_data():
    """Load dan validasi dataset dari CSV."""
    df_items = pd.read_csv(ITEMS_CSV)
    df_scen  = pd.read_csv(SCENARIOS_CSV)

    required = ["item_name","category","tier","base_value","weight",
                "effective_value","ratio_v_w"]
    for col in required:
        assert col in df_items.columns, f"Kolom '{col}' tidak ditemukan di items.csv!"

    items = df_items.to_dict("records")
    return items, df_scen


def parse_scenario(row, all_items):
    """Ubah satu baris scenario CSV menjadi list item."""
    indices = list(map(int, str(row["item_indices"]).split(";")))
    return [all_items[i] for i in indices]


def cetak_header(teks: str):
    print("\n" + "=" * 62)
    print(f"  {teks}")
    print("=" * 62)


def cetak_subheader(teks: str):
    print(f"\n── {teks} " + "─" * (55 - len(teks)))

def main():

    print("=" * 62)
    print("  GREEDY ALGORITHM — Battle Royale Looting Simulation")
    print("  UAS Strategi Algoritma")
    print("=" * 62)

    # 1. Load data
    cetak_subheader("Memuat dataset")
    all_items, df_scen = load_data()
    print(f"  Total item tersedia : {len(all_items)} item")
    print(f"  Total skenario      : {len(df_scen)} skenario")

    # Tampilkan preview dataset
    df_items = pd.read_csv(ITEMS_CSV)
    cetak_subheader("Preview 5 item dengan rasio tertinggi")
    top5 = df_items.nlargest(5, "ratio_v_w")[
        ["item_name","tier","base_value","weight","effective_value","ratio_v_w"]
    ]
    print(tabulate(top5, headers="keys", tablefmt="rounded_outline",
                   showindex=False, floatfmt=".2f"))

    # 2. Jalankan greedy untuk tiap skenario
    cetak_header("HASIL GREEDY ALGORITHM PER SKENARIO")

    all_results = []

    for _, row in df_scen.iterrows():
        sc_name   = row["scenario_name"]
        sc_desc   = row["description"]
        capacity  = int(row["bag_capacity"])
        sc_items  = parse_scenario(row, all_items)

        cetak_subheader(sc_name)
        print(f"  Deskripsi  : {sc_desc}")
        print(f"  Kapasitas  : {capacity} slot")
        print(f"  Item spawn : {len(sc_items)} item")

        # Jalankan greedy
        t0     = time.perf_counter()
        hasil  = greedy_loot(sc_items, capacity)
        t_exec = time.perf_counter() - t0

        # Tampilkan langkah-langkah greedy
        print(f"\n  Langkah Greedy (urut rasio v/w tertinggi):")
        step_rows = [(
            s["rank"], s["item"],
            s["action"], s["value_added"]
        ) for s in hasil["steps"]]
        print(tabulate(
            step_rows,
            headers=["Rank","Item","Aksi","Value +"],
            tablefmt="simple",
            colalign=("center","left","left","right")
        ))

        # Ringkasan hasil
        print(f"\n  Hasil Akhir:")
        print(f"    Item terpilih  : {len(hasil['selected_items'])} item")
        if hasil["fractional_item"]:
            fi = hasil["fractional_item"]
            print(f"    Item parsial   : {fi['item_name']} "
                  f"({fi['fraction']*100:.1f}% diambil)")
        print(f"    Total value    : {hasil['total_value']}")
        print(f"    Berat terpakai : {hasil['total_weight']} / {capacity} slot")
        print(f"    Utilisasi tas  : {hasil['utilization_pct']}%")
        print(f"    Waktu eksekusi : {t_exec*1000:.4f} ms")

        all_results.append({
            "scenario":       sc_name,
            "capacity":       capacity,
            "items_available":len(sc_items),
            "items_selected": len(hasil["selected_items"]),
            "total_value":    hasil["total_value"],
            "total_weight":   hasil["total_weight"],
            "utilization_pct":hasil["utilization_pct"],
            "exec_time_ms":   round(t_exec * 1000, 4),
            "selected_items": hasil["selected_items"],
            "result_obj":     hasil,
        })

    # 3. Tabel perbandingan ringkas
    cetak_header("TABEL PERBANDINGAN ANTAR SKENARIO")
    summary_rows = [(
        r["scenario"].split("—")[0].strip(),
        r["capacity"],
        r["items_available"],
        r["items_selected"],
        r["total_value"],
        f"{r['utilization_pct']}%",
        f"{r['exec_time_ms']} ms",
    ) for r in all_results]
    print(tabulate(
        summary_rows,
        headers=["Skenario","Kapasitas","Tersedia","Terpilih",
                 "Total Value","Utilisasi","Waktu"],
        tablefmt="rounded_outline",
        colalign=("left","center","center","center","center","center","right")
    ))

    # 4. Analisis kompleksitas
    cetak_header("ANALISIS KOMPLEKSITAS ALGORITMA")
    print("""
  Greedy Fractional Knapsack:
    Sorting    → O(n log n)   ← dominan
    Iterasi    → O(n)
    Total      → O(n log n)
    Space      → O(n)

  Brute Force 0/1 Knapsack:
    Kombinasi  → O(2^n)       ← eksponensial
    Contoh: n=20 item → 2^20 = 1.048.576 kombinasi
            n=40 item → 2^40 ≈ 1 triliun kombinasi

  Kesimpulan: Greedy jauh lebih efisien untuk n besar.
    """)

    # 5. Perbandingan Greedy vs Brute Force (pakai skenario A, ambil 12 item saja)
    cetak_header("GREEDY vs BRUTE FORCE (Skenario A — 11 item)")
    sc_a_items = parse_scenario(df_scen.iloc[0], all_items)
    cap_a      = int(df_scen.iloc[0]["bag_capacity"])

    t0 = time.perf_counter()
    g_hasil = greedy_loot(sc_a_items, cap_a)
    t_greedy = time.perf_counter() - t0

    t0 = time.perf_counter()
    b_hasil = brute_force_loot(sc_a_items, cap_a)
    t_brute  = time.perf_counter() - t0

    print(tabulate([
        ["Total Value",    g_hasil["total_value"],  b_hasil["total_value"]],
        ["Item Terpilih",  len(g_hasil["selected_items"]),
                           len(b_hasil["selected_items"])],
        ["Waktu (ms)",     f"{t_greedy*1000:.4f}", f"{t_brute*1000:.4f}"],
    ], headers=["Metrik","Greedy","Brute Force"],
       tablefmt="rounded_outline"))

    # 6. Buat semua visualisasi
    cetak_header("MEMBUAT VISUALISASI")

    chart_combat_score(all_results)

    for r in all_results:
        sc_short = r["scenario"].split("—")[0].strip().replace(" ", "_").lower()
        chart_kategori_distribusi(
            r["selected_items"], r["scenario"], f"chart2_{sc_short}"
        )

    chart_kapasitas_vs_value(
        parse_scenario(df_scen.iloc[0], all_items),
        range(4, 16),
        df_scen.iloc[0]["scenario_name"]
    )

    chart_tier_distribusi(all_results)

    chart_greedy_vs_brute(
        g_hasil["total_value"], b_hasil["total_value"],
        t_greedy, t_brute
    )

    cetak_header("SELESAI")
    print("  Semua grafik tersimpan di folder: output_charts/")
    print("  File yang dihasilkan:")
    import os
    for f in sorted(os.listdir("output_charts")):
        print(f"    • {f}")
    print()


# ── Entry Point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    main()
