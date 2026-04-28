TIER_MULTIPLIER = {
    "Bronze": 1.0,
    "Silver": 1.3,
    "Gold": 1.6,
    "Diamond": 2.0,
}


MAIN_WEAPON_CATEGORIES = {
    "Weapon-AR",
    "Weapon-Sniper",
    "Weapon-SMG",
    "Weapon-SG",
}

FRACTIONAL_ALLOWED_CATEGORIES = {
    "Ammo",
    "Medical",
    "Utility",
}


def hitung_effective_value(base_value: float, tier: str) -> float:
    multiplier = TIER_MULTIPLIER.get(tier, 1.0)
    return round(base_value * multiplier, 2)


def hitung_ratio(effective_value: float, weight: float) -> float:
    if weight == 0:
        return 0.0
    return round(effective_value / weight, 4)


def greedy_loot(items: list, capacity: int) -> dict:
    """
    Greedy Fractional Knapsack dengan aturan inventory Free Fire:

    - Main weapon: max 2
      Weapon-AR, Weapon-Sniper, Weapon-SMG, Weapon-SG

    - Pistol: max 1

    - Helmet: max 1
    - Vest: max 1
    - Backpack: max 1

    - Fractional hanya boleh untuk Ammo, Medical, Utility
    """

    sorted_items = sorted(
        items,
        key=lambda x: x["ratio_v_w"],
        reverse=True
    )

    selected_items = []
    fractional_item = None

    total_value = 0.0
    total_weight = 0
    steps = []

    main_weapon_count = 0
    pistol_count = 0

    gear_taken = {
        "Armor-Helmet": False,
        "Armor-Vest": False,
        "Backpack": False,
    }

    for i, item in enumerate(sorted_items):
        nama = item["item_name"]
        category = item["category"]
        berat = item["weight"]
        nilai = item["effective_value"]

        sisa_kapasitas = capacity - total_weight

        if sisa_kapasitas <= 0:
            steps.append({
                "rank": i + 1,
                "item": nama,
                "action": "SKIP — tas penuh",
                "value_added": 0,
            })
            continue

        # Constraint slot main weapon
        if category in MAIN_WEAPON_CATEGORIES and main_weapon_count >= 2:
            steps.append({
                "rank": i + 1,
                "item": nama,
                "action": "SKIP — slot main weapon penuh",
                "value_added": 0,
            })
            continue

        # Constraint pistol
        if category == "Weapon-Pistol" and pistol_count >= 1:
            steps.append({
                "rank": i + 1,
                "item": nama,
                "action": "SKIP — slot pistol penuh",
                "value_added": 0,
            })
            continue

        # Constraint gear eksklusif
        if category in gear_taken and gear_taken[category]:
            steps.append({
                "rank": i + 1,
                "item": nama,
                "action": "SKIP — gear sejenis sudah dimiliki",
                "value_added": 0,
            })
            continue

        # Ambil item penuh
        if berat <= sisa_kapasitas:
            selected_items.append(item)

            total_weight += berat
            total_value += nilai

            if category in MAIN_WEAPON_CATEGORIES:
                main_weapon_count += 1

            if category == "Weapon-Pistol":
                pistol_count += 1

            if category in gear_taken:
                gear_taken[category] = True

            steps.append({
                "rank": i + 1,
                "item": nama,
                "action": f"AMBIL penuh ({berat} slot)",
                "value_added": round(nilai, 2),
            })

        else:
            # Fractional hanya boleh untuk item tertentu
            if category not in FRACTIONAL_ALLOWED_CATEGORIES:
                steps.append({
                    "rank": i + 1,
                    "item": nama,
                    "action": "SKIP — tidak bisa diambil sebagian",
                    "value_added": 0,
                })
                continue

            fraksi = sisa_kapasitas / berat
            nilai_parsial = round(nilai * fraksi, 2)

            total_value += nilai_parsial
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
                "action": f"AMBIL sebagian {round(fraksi * 100, 1)}% ({sisa_kapasitas} slot)",
                "value_added": nilai_parsial,
            })

            break

    utilization = round((total_weight / capacity) * 100, 1) if capacity > 0 else 0

    return {
        "selected_items": selected_items,
        "fractional_item": fractional_item,
        "total_value": round(total_value, 2),
        "total_weight": total_weight,
        "capacity": capacity,
        "utilization_pct": utilization,
        "steps": steps,
    }


def brute_force_loot(items: list, capacity: int) -> dict:
    """
    Brute Force 0/1 Knapsack untuk pembanding.
    Catatan: brute force ini belum memakai constraint slot weapon/gear.
    """
    from itertools import combinations

    best_value = 0.0
    best_combo = []

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
        "total_value": round(best_value, 2),
        "total_weight": total_w,
        "utilization_pct": round(total_w / capacity * 100, 1) if capacity else 0,
    }