import os
import time
import shutil
import random
import pandas as pd
from flask import Flask, render_template, request

from greedy import greedy_loot, brute_force_loot
from visualize import (
    chart_combat_score,
    chart_kategori_distribusi,
    chart_kapasitas_vs_value,
    chart_tier_distribusi,
    chart_greedy_vs_brute,
)

app = Flask(__name__)

ITEMS_CSV = "data/items.csv"
SCENARIOS_CSV = "data/scenarios.csv"

OUTPUT_DIR = os.path.join(
    "static",
    "output_charts"
)

os.makedirs(OUTPUT_DIR, exist_ok=True)


def load_data():
    df_items = pd.read_csv(ITEMS_CSV)
    df_scen = pd.read_csv(SCENARIOS_CSV)
    all_items = df_items.to_dict("records")
    return all_items, df_items, df_scen


def parse_scenario(row, all_items):
    indices = list(map(int, str(row["item_indices"]).split(";")))
    return [all_items[i] for i in indices]


def random_spawn(row, all_items):
    fixed_items = parse_scenario(row, all_items)
    spawn_count = len(fixed_items)

    if spawn_count > len(all_items):
        spawn_count = len(all_items)

    return random.sample(all_items, spawn_count)


def get_scenario_items(row, all_items, spawn_mode):
    if spawn_mode == "random":
        return random_spawn(row, all_items)

    return parse_scenario(row, all_items)


def clear_charts():

    for file in os.listdir(OUTPUT_DIR):
        if file.endswith(".png"):
            os.remove(
                os.path.join(
                    OUTPUT_DIR,
                    file
                )
            )

def get_chart_files():
    return sorted([
        f"output_charts/{file}"
        for file in os.listdir(OUTPUT_DIR)
        if file.endswith(".png")
    ])


def run_single_scenario(row, all_items, spawn_mode="fixed"):
    scenario_items = get_scenario_items(row, all_items, spawn_mode)
    capacity = int(row["bag_capacity"])

    t0 = time.perf_counter()
    greedy_result = greedy_loot(scenario_items, capacity)
    greedy_time = time.perf_counter() - t0

    brute_result = None
    brute_time = None

    if len(scenario_items) <= 20:
        t0 = time.perf_counter()
        brute_result = brute_force_loot(scenario_items, capacity)
        brute_time = time.perf_counter() - t0

    return {
        "scenario": row,
        "scenario_items": scenario_items,
        "capacity": capacity,
        "greedy_result": greedy_result,
        "greedy_time": greedy_time,
        "greedy_time_ms": round(greedy_time * 1000, 4),
        "brute_result": brute_result,
        "brute_time": brute_time,
        "brute_time_ms": round(brute_time * 1000, 4) if brute_time else None,
    }


def run_all_results(all_items, df_scen, spawn_mode="fixed"):
    results = []

    for _, row in df_scen.iterrows():
        data = run_single_scenario(row, all_items, spawn_mode)
        hasil = data["greedy_result"]

        results.append({
            "scenario": row["scenario_name"],
            "description": row["description"],
            "capacity": data["capacity"],
            "scenario_items": data["scenario_items"],
            "items_available": len(data["scenario_items"]),
            "items_selected": len(hasil["selected_items"]),
            "selected_items": hasil["selected_items"],
            "steps": hasil["steps"],
            "fractional_item": hasil["fractional_item"],
            "total_value": hasil["total_value"],
            "total_weight": hasil["total_weight"],
            "utilization_pct": hasil["utilization_pct"],
            "exec_time_ms": data["greedy_time_ms"],
        })

    return results


def build_all_summary(all_results):
    if not all_results:
        return None

    best_result = max(all_results, key=lambda x: x["total_value"])
    avg_utilization = sum(r["utilization_pct"] for r in all_results) / len(all_results)
    avg_time = sum(r["exec_time_ms"] for r in all_results) / len(all_results)

    return {
        "total_scenarios": len(all_results),
        "best_scenario": best_result["scenario"],
        "best_value": best_result["total_value"],
        "avg_utilization": round(avg_utilization, 2),
        "avg_time": round(avg_time, 4),
    }


def make_single_charts(single_data, selected_row):
    chart_kategori_distribusi(
        single_data["greedy_result"]["selected_items"],
        selected_row["scenario_name"],
        "chart2_single_kategori"
    )

    chart_kapasitas_vs_value(
        single_data["scenario_items"],
        range(4, 16),
        selected_row["scenario_name"],
        "chart3_single_kapasitas"
    )

    if single_data["brute_result"]:
        chart_greedy_vs_brute(
            single_data["greedy_result"]["total_value"],
            single_data["brute_result"]["total_value"],
            single_data["greedy_time"],
            single_data["brute_time"]
        )


def make_all_charts(all_results, df_scen, all_items, spawn_mode):
    chart_combat_score(all_results)
    chart_tier_distribusi(all_results)

    for index, result in enumerate(all_results):
        chart_kategori_distribusi(
            result["selected_items"],
            result["scenario"],
            f"chart2_scenario_{index + 1}_kategori"
        )

        chart_kapasitas_vs_value(
            result["scenario_items"],
            range(4, 16),
            result["scenario"],
            f"chart3_scenario_{index + 1}_kapasitas"
        )

    if all_results:
        first_row = df_scen.iloc[0]
        first_data = run_single_scenario(first_row, all_items, spawn_mode)

        if first_data["brute_result"]:
            chart_greedy_vs_brute(
                first_data["greedy_result"]["total_value"],
                first_data["brute_result"]["total_value"],
                first_data["greedy_time"],
                first_data["brute_time"]
            )


@app.route("/", methods=["GET", "POST"])
def index():
    all_items, df_items, df_scen = load_data()

    has_run = request.method == "POST"

    if not has_run:
        return render_template(
            "index.html",
            scenarios=df_scen.to_dict("records"),
            selected_index=0,
            mode=None,
            spawn_mode=None,
            scenario=None,
            scenario_items=[],
            greedy_result=None,
            greedy_time_ms=None,
            brute_result=None,
            brute_time_ms=None,
            all_results=[],
            all_summary=None,
            chart_files=[],
            top_ratio_item=None,
        )

    mode = request.form.get("mode", "single")
    spawn_mode = request.form.get("spawn_mode", "fixed")
    selected_index = int(request.form.get("scenario_index", 0))

    selected_row = df_scen.iloc[selected_index]
    single_data = run_single_scenario(selected_row, all_items, spawn_mode)

    all_results = []
    all_summary = None

    clear_charts()

    if mode == "all":
        all_results = run_all_results(all_items, df_scen, spawn_mode)
        all_summary = build_all_summary(all_results)
        make_all_charts(all_results, df_scen, all_items, spawn_mode)
    else:
        make_single_charts(single_data, selected_row)

    chart_files = get_chart_files()

    top_ratio_item = None
    if single_data["scenario_items"]:
        top_ratio_item = sorted(
            single_data["scenario_items"],
            key=lambda x: x["ratio_v_w"],
            reverse=True
        )[0]

    return render_template(
        "index.html",
        scenarios=df_scen.to_dict("records"),
        selected_index=selected_index,
        mode=mode,
        spawn_mode=spawn_mode,
        scenario=single_data["scenario"],
        scenario_items=single_data["scenario_items"],
        greedy_result=single_data["greedy_result"],
        greedy_time_ms=single_data["greedy_time_ms"],
        brute_result=single_data["brute_result"],
        brute_time_ms=single_data["brute_time_ms"],
        all_results=all_results,
        all_summary=all_summary,
        chart_files=chart_files,
        top_ratio_item=top_ratio_item,
    )


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)