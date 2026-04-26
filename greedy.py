TIER_MULTIPLIER = {
    "Bronze":  1.0,
    "Silver":  1.3,
    "Gold":    1.6,
    "Diamond": 2.0,
}


def hitung_effective_value(base_value: float, tier: str) -> float:
    """Hitung nilai efektif item setelah dikali multiplier tier."""
    multiplier = TIER_MULTIPLIER.get(tier, 1.0)
    return round(base_value * multiplier, 2)


def hitung_ratio(effective_value: float, weight: float) -> float:
    """Hitung rasio value/weight — kunci utama greedy."""
    if weight == 0:
        return 0.0
    return round(effective_value / weight, 4)


def greedy_loot(items: list, capacity: int) -> dict:
    """
    Algoritma Greedy Fractional Knapsack untuk looting item.

    Prinsip: ambil item dengan rasio effective_value/weight
             tertinggi lebih dulu.

    Parameter
    ---------
    items    : list of dict, setiap dict berisi:
                  item_name, category, tier,
                  base_value, weight, effective_value, ratio_v_w
    capacity : int — kapasitas tas (jumlah slot)

    Return
    ------
    dict berisi:
        selected_items  : item yang dipilih (utuh)
        fractional_item : item yang diambil sebagian (jika ada)
        total_value     : total effective value terkumpul
        total_weight    : total berat terpakai
        utilization_pct : persentase kapasitas terpakai
        steps           : log langkah greedy (untuk laporan)
    """

    # Langkah 1: Urutkan berdasarkan rasio descending (inti greedy)
    sorted_items = sorted(
        items,
        key=lambda x: x["ratio_v_w"],
        reverse=True
    )

    selected_items  = []
    fractional_item = None
    total_value  = 0.0
    total_weight = 0
    steps = []   # log untuk laporan & debugging

    # Langkah 2: Iterasi item dari rasio tertinggi
    for i, item in enumerate(sorted_items):
        nama   = item["item_name"]
        berat  = item["weight"]
        nilai  = item["effective_value"]
        rasio  = item["ratio_v_w"]

        sisa_kapasitas = capacity - total_weight

        if sisa_kapasitas <= 0:
            steps.append({
                "rank": i + 1,
                "item": nama,
                "action": "SKIP — tas penuh",
                "value_added": 0,
            })
            break

        if berat <= sisa_kapasitas:
            # Ambil item penuh
            selected_items.append(item)
            total_weight += berat
            total_value  += nilai
            steps.append({
                "rank": i + 1,
                "item": nama,
                "action": f"AMBIL penuh ({berat} slot)",
                "value_added": round(nilai, 2),
            })
        else:
            # Ambil sebagian (fractional)
            fraksi       = sisa_kapasitas / berat
            nilai_parsial = round(nilai * fraksi, 2)
            total_value  += nilai_parsial
            total_weight += sisa_kapasitas
            fractional_item = {
                **item,
                "fraction": round(fraksi, 4),
                "partial_value": nilai_parsial,
                "partial_weight": sisa_kapasitas,
            }
            steps.append({
                "rank": i + 1,
                "item": nama,
                "action": f"AMBIL sebagian {round(fraksi*100,1)}% ({sisa_kapasitas} slot)",
                "value_added": nilai_parsial,
            })
            break

    utilization = round((total_weight / capacity) * 100, 1) if capacity > 0 else 0

    return {
        "selected_items":  selected_items,
        "fractional_item": fractional_item,
        "total_value":     round(total_value, 2),
        "total_weight":    total_weight,
        "capacity":        capacity,
        "utilization_pct": utilization,
        "steps":           steps,
    }


def brute_force_loot(items: list, capacity: int) -> dict:
    """
    Brute Force 0/1 Knapsack — O(2^n) — HANYA untuk perbandingan
    dengan n item kecil (≤ 20 item, lebih dari itu sangat lambat!).

    Mengecek SEMUA kombinasi item yang mungkin.
    """
    from itertools import combinations

    best_value  = 0.0
    best_combo  = []

    for r in range(1, len(items) + 1):
        for combo in combinations(items, r):
            total_w = sum(it["weight"] for it in combo)
            total_v = sum(it["effective_value"] for it in combo)
            if total_w <= capacity and total_v > best_value:
                best_value = total_v
                best_combo = list(combo)

    total_w = sum(it["weight"] for it in best_combo)
    return {
        "selected_items": best_combo,
        "total_value":    round(best_value, 2),
        "total_weight":   total_w,
        "utilization_pct": round(total_w / capacity * 100, 1) if capacity else 0,
    }
