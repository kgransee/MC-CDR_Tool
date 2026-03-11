import os
from datetime import datetime
from collections import defaultdict
from data_gen_SurveyRange import *
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import FuncFormatter
from data_gen_EU import *
from cdr_viable import is_method_viable
from data_gen import generate_random_portfolio
from data_gen_Rueda import generate_random_portfolioR
from adjustText import adjust_text
from output_portfolio_sim import (
    lexicographic_opt_iterative,
    pareto_portfolio_iterative_layers,
)
def build_macc_steps(portfolio, storage_target):
    if not portfolio:
        return [0.0], []

    entries = [e for e in portfolio if float(e.get("actual_contribution", 0.0)) > 0]

    edges = [0.0]
    heights = []
    installed = 0.0

    for e in entries:
        contrib = float(e["actual_contribution"])
        mac = float(e["mac"])

        remaining = float(storage_target) - installed
        if remaining <= 0:
            break

        contrib = min(contrib, remaining)
        if contrib <= 0:
            continue

        installed += contrib
        edges.append(installed)
        heights.append(mac)

    return edges, heights


def evaluate_step_curve(edges, heights, x_grid):
    y = np.full_like(x_grid, np.nan, dtype=float)

    if len(heights) == 0:
        return y

    for i, x in enumerate(x_grid):
        if x < edges[0]:
            continue

        assigned = False
        for j in range(len(heights)):
            if edges[j] <= x < edges[j + 1]:
                y[i] = heights[j]
                assigned = True
                break

        if not assigned and np.isclose(x, edges[-1]):
            y[i] = heights[-1]

    return y

#usd in creating the standard MACC
def aggregate_macc_curves(results, portfolio_key, storage_target, n_grid=250):
    x_grid = np.linspace(0, float(storage_target), n_grid)
    curves = []
    final_extents = []

    for r in results:
        portfolio = r.get(portfolio_key, []) or []
        edges, heights = build_macc_steps(portfolio, storage_target)
        y = evaluate_step_curve(edges, heights, x_grid)
        curves.append(y)
        final_extents.append(edges[-1] if edges else 0.0)

    if not curves:
        nan_arr = np.full_like(x_grid, np.nan)
        return x_grid, nan_arr, nan_arr, 0.0

    curves = np.array(curves, dtype=float)
    final_extents = np.array(final_extents, dtype=float)

    mean_curve = np.nanmean(curves, axis=0)
    std_curve = (
        np.nanstd(curves, axis=0, ddof=1)
        if curves.shape[0] > 1
        else np.zeros_like(mean_curve)
    )

    mean_final_extent = float(np.mean(final_extents))

    # Clip the aggregate curve to the mean achieved cumulative removal
    mask_beyond_extent = x_grid > mean_final_extent
    mean_curve[mask_beyond_extent] = np.nan
    std_curve[mask_beyond_extent] = np.nan

    return x_grid, mean_curve, std_curve, mean_final_extent

#as described
def extract_method_name(method):
    return method.mainType

#used in some graphs to represent billions.
def _format_billions(x, pos):
    return f"{x:,.0f}"


def _step_fill_arrays(edges, mean_vals, std_vals):
    if not mean_vals:
        return np.array([]), np.array([]), np.array([])

    x = np.array(edges, dtype=float)
    y = np.array([mean_vals[0]] + mean_vals, dtype=float)
    s = np.array([std_vals[0]] + std_vals, dtype=float)

    lower = np.maximum(0.0, y - s)
    upper = y + s
    return x, lower, upper

def _method_label(method):
    return f"{method.mainType} | {method.subType}"


def _aggregate_metric_by_method(results, metric_key):
    aggregates = {
        "Lexicographic": defaultdict(float),
        "Pareto": defaultdict(float),
    }

    for result in results or []:
        for entry in result.get("lg_portfolio", []):
            method = entry["method"]
            label = _method_label(method)
            aggregates["Lexicographic"][label] += float(entry.get(metric_key, 0.0))

        for entry in result.get("pareto_portfolio", []):
            method = entry["method"]
            label = _method_label(method)
            aggregates["Pareto"][label] += float(entry.get(metric_key, 0.0))

    return aggregates

def plot_aggregate_method_social_decomposition(results, output_path):
    climate_agg = _aggregate_metric_by_method(results, "pv_climate_benefit")
    ext_agg = _aggregate_metric_by_method(results, "pv_externality")

    all_methods = sorted(
        set(climate_agg["Lexicographic"].keys())
        | set(climate_agg["Pareto"].keys())
        | set(ext_agg["Lexicographic"].keys())
        | set(ext_agg["Pareto"].keys())
    )

    if not all_methods:
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.set_title("Monte Carlo Aggregate Externality Decomposition by Method")
        ax.set_ylabel("PV ($)")
        ax.text(0.5, 0.5, "No data available", ha="center", va="center")
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        plt.close(fig)
        return

    lg_climate = np.array([climate_agg["Lexicographic"].get(m, 0.0) for m in all_methods], dtype=float)
    p_climate = np.array([climate_agg["Pareto"].get(m, 0.0) for m in all_methods], dtype=float)

    lg_ext = np.array([ext_agg["Lexicographic"].get(m, 0.0) for m in all_methods], dtype=float)
    p_ext = np.array([ext_agg["Pareto"].get(m, 0.0) for m in all_methods], dtype=float)

    lg_ext_pos = np.maximum(lg_ext, 0.0)
    lg_ext_neg = np.minimum(lg_ext, 0.0)
    p_ext_pos = np.maximum(p_ext, 0.0)
    p_ext_neg = np.minimum(p_ext, 0.0)

    x = np.arange(len(all_methods))
    width = 0.38

    fig, ax = plt.subplots(figsize=(max(12, len(all_methods) * 0.7), 8))

    ax.bar(
        x - width / 2,
        lg_climate,
        width,
        label="Lexicographic Net Climate Benefit",
        color="black",
        edgecolor="black",
        linewidth=0.8,
    )
    ax.bar(
        x - width / 2,
        lg_ext_pos,
        width,
        bottom=lg_climate,
        label="Lexicographic Positive Externality",
        color="dimgray",
        edgecolor="black",
        linewidth=0.8,
    )
    ax.bar(
        x - width / 2,
        lg_ext_neg,
        width,
        bottom=0,
        label="Lexicographic Negative Externality",
        color="lightgray",
        edgecolor="black",
        linewidth=0.8,
    )

    ax.bar(
        x + width / 2,
        p_climate,
        width,
        label="Pareto Net Climate Benefit",
        color="#d62728",
        edgecolor="black",
        linewidth=0.8,
    )
    ax.bar(
        x + width / 2,
        p_ext_pos,
        width,
        bottom=p_climate,
        label="Pareto Positive Externality",
        color="#ff6b6b",
        edgecolor="black",
        linewidth=0.8,
    )
    ax.bar(
        x + width / 2,
        p_ext_neg,
        width,
        bottom=0,
        label="Pareto Negative Externality",
        color="#f4a3a3",
        edgecolor="black",
        linewidth=0.8,
    )
    ax.set_xticks(x)
    ax.set_xticklabels(all_methods, rotation=45, ha="right")
    ax.set_ylabel("Discounted PV ($)")
    ax.set_title("Monte Carlo Aggregate Externality Decomposition by Method")
    ax.axhline(0, linewidth=1.0)
    ax.legend(ncol=2)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)

def compute_adjusted_total_pv(portfolio):
    total_climate_benefit = 0.0
    total_externality = 0.0
    total_social_benefit = 0.0
    total_positive_externality = 0.0
    total_negative_externality = 0.0

    for entry in portfolio or []:
        total_climate_benefit += float(entry.get("pv_climate_benefit", 0.0))
        total_externality += float(entry.get("pv_externality", 0.0))
        total_social_benefit += float(entry.get("pv_social_net_benefit", 0.0))
        total_positive_externality += float(entry.get("pv_positive_externality", 0.0))
        total_negative_externality += float(entry.get("pv_negative_externality", 0.0))

    return (
        total_climate_benefit,
        total_externality,
        total_social_benefit,
        total_positive_externality,
        total_negative_externality,
    )

def aggregate_method_removal(results, portfolio_key):
    all_methods = set()

    for r in results:
        portfolio = r.get(portfolio_key, []) or []
        for e in portfolio:
            method_name = extract_method_name(e["method"])
            all_methods.add(method_name)

    all_methods = sorted(all_methods)
    method_totals = {method_name: [] for method_name in all_methods}

    for r in results:
        portfolio = r.get(portfolio_key, []) or []
        run_totals = {method_name: 0.0 for method_name in all_methods}

        for e in portfolio:
            method_name = extract_method_name(e["method"])
            run_totals[method_name] += float(e.get("actual_contribution", 0.0))

        for method_name in all_methods:
            method_totals[method_name].append(run_totals[method_name])

    return method_totals


def aggregate_lexicographic_scatter_data(results):
    method_mac = defaultdict(list)
    method_side = defaultdict(list)
    method_position = defaultdict(list)
    method_contrib = defaultdict(list)
    method_selected_runs = defaultdict(int)

    n_runs = len(results)

    all_methods = set()
    for r in results:
        portfolio = r.get("lg_portfolio", []) or []
        for e in portfolio:
            method = extract_method_name(e["method"])
            all_methods.add(method)

    for r in results:
        portfolio = r.get("lg_portfolio", []) or []
        entries = [
            e for e in portfolio
            if float(e.get("actual_contribution", 0.0)) > 0
        ]

        # initialize run positions as NaN (not implemented)
        run_positions = {m: np.nan for m in all_methods}

        seen_this_run = set()

        for pos, e in enumerate(entries, start=1):
            method_obj = e["method"]
            method = extract_method_name(method_obj)

            run_positions[method] = float(pos)

            method_mac[method].append(float(e["mac"]))
            method_side[method].append(float(getattr(method_obj, "sideEffect", np.nan)))
            method_contrib[method].append(float(e.get("actual_contribution", 0.0)))

            seen_this_run.add(method)

        # store one position per method per run
        for method in all_methods:
            method_position[method].append(run_positions[method])

        for method in seen_this_run:
            method_selected_runs[method] += 1

    rows = []
    for method in sorted(all_methods):
        rows.append({
            "method": method,
            "avg_mac": float(np.mean(method_mac[method])) if method_mac[method] else np.nan,
            "avg_side_effect": float(np.mean(method_side[method])) if method_side[method] else np.nan,
            "avg_position": float(np.nanmean(method_position[method])) if method_position[method] else np.nan,
            "avg_contribution": float(np.mean(method_contrib[method])) if method_contrib[method] else 0.0,
            "selection_frequency": method_selected_runs[method] / n_runs if n_runs > 0 else 0.0,
        })

    return rows

def plot_aggregate_lexicographic_scatter(
    results,
    output_path,
    title="Monte Carlo Aggregate Lexicographic Scatter by Average Selection Position",
):
    rows = aggregate_lexicographic_scatter_data(results)
    if not rows:
        print("No aggregate lexicographic scatter data available.")
        return None

    methods = np.array([r["method"] for r in rows], dtype=object)
    x = np.array([r["avg_mac"] for r in rows], dtype=float)
    y = np.array([r["avg_side_effect"] for r in rows], dtype=float)
    c = np.array([r["avg_position"] for r in rows], dtype=float)
    s_raw = np.array([r["avg_contribution"] for r in rows], dtype=float)
    freq = np.array([r.get("selection_frequency", np.nan) for r in rows], dtype=float)

    valid_xy = np.isfinite(x) & np.isfinite(y)
    if not np.any(valid_xy):
        print("No valid aggregate lexicographic scatter data to plot.")
        return None

    methods = methods[valid_xy]
    x = x[valid_xy]
    y = y[valid_xy]
    c = c[valid_xy]
    s_raw = s_raw[valid_xy]
    freq = freq[valid_xy]

    max_s = np.nanmax(s_raw) if np.any(np.isfinite(s_raw)) else 0.0
    sizes = (
        100 + 900 * (s_raw / max_s)
        if max_s > 0
        else np.full_like(s_raw, 200.0)
    )

    fig, ax = plt.subplots(figsize=(10, 7))

    ranked_mask = np.isfinite(c)

    if np.any(ranked_mask):
        vmax = np.nanmax(c[ranked_mask])
        sc = ax.scatter(
            x[ranked_mask],
            y[ranked_mask],
            c=c[ranked_mask],
            s=sizes[ranked_mask],
            cmap="turbo",
            vmin=1,
            vmax=vmax,
            alpha=0.85,
        )

        cbar = plt.colorbar(sc, ax=ax)
        cbar.set_label("Average Implemented Lexicographic Selection Position")

        tick_max = int(np.ceil(vmax))
        if tick_max >= 1:
            cbar.set_ticks(np.arange(1, tick_max + 1))

    unranked_mask = ~ranked_mask
    if np.any(unranked_mask):
        ax.scatter(
            x[unranked_mask],
            y[unranked_mask],
            s=sizes[unranked_mask],
            marker="x",
            alpha=0.9,
            label="Not implemented",
        )
        ax.legend()

    texts = []
    for i, method in enumerate(methods):
        label = f"{method} ({freq[i]:.0%})"
        texts.append(
            ax.text(
                x[i],
                y[i],
                label,
                fontsize=9,
                ha="center",
                va="center",
                bbox=dict(
                    boxstyle="round,pad=0.2",
                    fc="white",
                    ec="none",
                    alpha=0.85,
                ),
            )
        )

    adjust_text(
        texts,
        ax=ax,
        arrowprops=dict(arrowstyle="-", color="gray", lw=0.8),
    )

    ax.set_xlabel("Average MAC ($/tCO₂)")
    ax.set_ylabel("Average Side Effect")
    ax.set_title(title)
    ax.grid(True, alpha=0.25)

    plt.tight_layout()
    plt.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close()
    print(f"Saved aggregate lexicographic scatter plot: {output_path}")
    return output_path

def aggregate_pareto_scatter_data(results):
    method_mac = defaultdict(list)
    method_side = defaultdict(list)
    method_layer = defaultdict(list)
    method_contrib = defaultdict(list)
    method_selected_runs = defaultdict(int)

    n_runs = len(results)

    # collect all methods that ever appear in any pareto portfolio
    all_methods = set()
    for r in results:
        portfolio = r.get("pareto_portfolio", []) or []
        for e in portfolio:
            method = extract_method_name(e["method"])
            all_methods.add(method)

    for r in results:
        portfolio = r.get("pareto_portfolio", []) or []

        # default: not implemented in this run
        run_layers = {m: np.nan for m in all_methods}
        seen_this_run = set()

        for e in portfolio:
            method_obj = e["method"]
            method = extract_method_name(method_obj)

            contrib = float(e.get("actual_contribution", 0.0))
            if contrib <= 0:
                continue

            method_mac[method].append(float(e["mac"]))
            method_side[method].append(float(getattr(method_obj, "sideEffect", np.nan)))
            method_contrib[method].append(contrib)

            run_layers[method] = float(e.get("round", np.nan))
            seen_this_run.add(method)

        # store one layer value per method per run
        for method in all_methods:
            method_layer[method].append(run_layers[method])

        for method in seen_this_run:
            method_selected_runs[method] += 1

    rows = []
    for method in sorted(all_methods):
        rows.append({
            "method": method,
            "avg_mac": float(np.mean(method_mac[method])) if method_mac[method] else np.nan,
            "avg_side_effect": float(np.mean(method_side[method])) if method_side[method] else np.nan,
            "avg_layer": float(np.nanmean(method_layer[method])) if np.any(np.isfinite(method_layer[method])) else np.nan,
            "avg_contribution": float(np.mean(method_contrib[method])) if method_contrib[method] else 0.0,
            "selection_frequency": method_selected_runs[method] / n_runs if n_runs > 0 else 0.0,
        })

    return rows

def plot_aggregate_pareto_scatter(
    results,
    output_path,
    title="Monte Carlo Aggregate Pareto Scatter by Average Implemented Layer",
):
    rows = aggregate_pareto_scatter_data(results)
    if not rows:
        print("No aggregate Pareto scatter data available.")
        return None

    methods = np.array([r["method"] for r in rows], dtype=object)
    x = np.array([r["avg_mac"] for r in rows], dtype=float)
    y = np.array([r["avg_side_effect"] for r in rows], dtype=float)
    c = np.array([r["avg_layer"] for r in rows], dtype=float)
    s_raw = np.array([r["avg_contribution"] for r in rows], dtype=float)
    freq = np.array([r.get("selection_frequency", np.nan) for r in rows], dtype=float)

    valid_xy = np.isfinite(x) & np.isfinite(y)
    if not np.any(valid_xy):
        print("No valid aggregate Pareto scatter data to plot.")
        return None

    methods = methods[valid_xy]
    x = x[valid_xy]
    y = y[valid_xy]
    c = c[valid_xy]
    s_raw = s_raw[valid_xy]
    freq = freq[valid_xy]

    max_s = np.nanmax(s_raw) if np.any(np.isfinite(s_raw)) else 0.0
    sizes = (
        100 + 900 * (s_raw / max_s)
        if max_s > 0
        else np.full_like(s_raw, 200.0)
    )

    fig, ax = plt.subplots(figsize=(10, 7))

    ranked_mask = np.isfinite(c)

    if np.any(ranked_mask):
        vmax = np.nanmax(c[ranked_mask])

        sc = ax.scatter(
            x[ranked_mask],
            y[ranked_mask],
            c=c[ranked_mask],
            s=sizes[ranked_mask],
            cmap="turbo",
            vmin=1,
            vmax=vmax,
            alpha=0.85,
        )

        cbar = plt.colorbar(sc, ax=ax)
        cbar.set_label("Average Implemented Pareto Layer")

        tick_max = int(np.ceil(vmax))
        if tick_max >= 1:
            cbar.set_ticks(np.arange(1, tick_max + 1))

    unranked_mask = ~ranked_mask
    if np.any(unranked_mask):
        ax.scatter(
            x[unranked_mask],
            y[unranked_mask],
            s=sizes[unranked_mask],
            marker="x",
            alpha=0.9,
            label="Not implemented",
        )
        ax.legend()

    texts = []
    for i, method in enumerate(methods):

        label = method
        if np.isfinite(freq[i]):
            label = f"{method} ({freq[i]:.0%})"

        texts.append(
            ax.text(
                x[i],
                y[i],
                label,
                fontsize=9,
                ha="center",
                va="center",
                bbox=dict(
                    boxstyle="round,pad=0.2",
                    fc="white",
                    ec="none",
                    alpha=0.85,
                ),
            )
        )

    adjust_text(
        texts,
        ax=ax,
        arrowprops=dict(arrowstyle="-", color="gray", lw=0.8),
    )

    ax.set_xlabel("Average MAC ($/tCO₂)")
    ax.set_ylabel("Average Side Effect")
    ax.set_title(title)
    ax.grid(True, alpha=0.25)

    plt.tight_layout()
    plt.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close()

    print(f"Saved aggregate Pareto scatter plot: {output_path}")
    return output_path

#used for th structural graph, maintains the ordering. Due to the aggregation, this is not as representative. 
def aggregate_lexicographic_macc(results):
    all_positions = set()

    for r in results:
        portfolio = r.get("lg_portfolio", []) or []
        entries = [
            e for e in portfolio
            if float(e.get("actual_contribution", 0.0)) > 0
        ]
        for i, _ in enumerate(entries):
            all_positions.add(i)

    all_positions = sorted(all_positions)
    if not all_positions:
        return [0.0], [], [], []

    pos_macs = {i: [] for i in all_positions}
    pos_caps = {i: [] for i in all_positions}
    pos_methods = {i: [] for i in all_positions}

    for r in results:
        portfolio = r.get("lg_portfolio", []) or []
        entries = [
            e for e in portfolio
            if float(e.get("actual_contribution", 0.0)) > 0
        ]

        run_data = {}
        for i, e in enumerate(entries):
            run_data[i] = (
                float(e["mac"]),
                float(e["actual_contribution"]),
                extract_method_name(e["method"]),
            )

        for i in all_positions:
            if i in run_data:
                mac, cap, method = run_data[i]
                pos_macs[i].append(mac)
                pos_caps[i].append(cap)
                pos_methods[i].append(method)
            else:
                pos_macs[i].append(np.nan)
                pos_caps[i].append(0.0)
                pos_methods[i].append(None)

    edges = [0.0]
    heights_mean = []
    heights_std = []
    aggregated_segments = []

    installed = 0.0

    for i in all_positions:
        cap_vals = np.array(pos_caps[i], dtype=float)
        mac_vals = np.array(pos_macs[i], dtype=float)

        cap_mean = float(np.mean(cap_vals))
        if cap_mean <= 0:
            continue

        mac_mean = float(np.nanmean(mac_vals))
        mac_std = float(np.nanstd(mac_vals, ddof=1)) if np.sum(~np.isnan(mac_vals)) > 1 else 0.0

        valid_methods = [m for m in pos_methods[i] if m is not None]
        method_name = max(set(valid_methods), key=valid_methods.count) if valid_methods else None

        x0 = installed
        installed += cap_mean
        x1 = installed

        edges.append(x1)
        heights_mean.append(mac_mean)
        heights_std.append(mac_std)

        aggregated_segments.append({
            "position": i + 1,
            "method": method_name,
            "cap_mean": cap_mean,
            "mac_mean": mac_mean,
            "mac_std": mac_std,
            "x0": x0,
            "x1": x1,
        })

    return edges, heights_mean, heights_std, aggregated_segments

def extract_pareto_layers(portfolio):
    layers = {}

    for e in portfolio:
        layer = e.get("round")
        contrib = float(e.get("actual_contribution", 0.0))
        if layer is None or contrib <= 0:
            continue

        method = extract_method_name(e["method"])

        layers.setdefault(layer, []).append({
            "method": method,
            "mac": float(e["mac"]),
            "cap": contrib
        })

    for layer in layers:
        layers[layer].sort(key=lambda x: x["mac"])

    return layers


def aggregate_pareto_macc(results):

    all_keys = set()

    # discover all (layer, index) slots
    for r in results:
        layers = extract_pareto_layers(r.get("pareto_portfolio", []) or [])
        for layer, entries in layers.items():
            for i, _ in enumerate(entries):
                all_keys.add((layer, i))

    all_keys = sorted(all_keys)

    layer_macs = {k: [] for k in all_keys}
    layer_caps = {k: [] for k in all_keys}
    layer_methods = {k: [] for k in all_keys}

    # collect data from each run
    for r in results:
        layers = extract_pareto_layers(r.get("pareto_portfolio", []) or [])

        run_data = {}
        for layer, entries in layers.items():
            for i, entry in enumerate(entries):
                run_data[(layer, i)] = (
                    float(entry["mac"]),
                    float(entry["cap"]),
                    entry["method"],
                )

        for k in all_keys:
            if k in run_data:
                mac, cap, method = run_data[k]
                layer_macs[k].append(mac)
                layer_caps[k].append(cap)
                layer_methods[k].append(method)
            else:
                layer_macs[k].append(np.nan)
                layer_caps[k].append(0.0)
                layer_methods[k].append(None)

    aggregated_by_layer = {}

    for layer, idx in all_keys:
        cap_vals = np.array(layer_caps[(layer, idx)], dtype=float)
        mac_vals = np.array(layer_macs[(layer, idx)], dtype=float)

        cap_mean = float(np.mean(cap_vals))
        if cap_mean <= 0:
            continue

        mac_mean = float(np.nanmean(mac_vals))
        mac_std = float(np.nanstd(mac_vals, ddof=1)) if np.sum(~np.isnan(mac_vals)) > 1 else 0.0

        valid_methods = [m for m in layer_methods[(layer, idx)] if m is not None]
        method_name = max(set(valid_methods), key=valid_methods.count) if valid_methods else None

        aggregated_by_layer.setdefault(layer, []).append({
            "mac_mean": mac_mean,
            "mac_std": mac_std,
            "cap_mean": cap_mean,
            "method": method_name,
        })

    # sort aggregated entries inside each layer by MAC
    for layer in aggregated_by_layer:
        aggregated_by_layer[layer].sort(key=lambda d: d["mac_mean"])

    edges = [0.0]
    heights_mean = []
    heights_std = []
    layer_boundaries = {}

    installed = 0.0

    for layer in sorted(aggregated_by_layer.keys()):
        for entry in aggregated_by_layer[layer]:
            installed += entry["cap_mean"]

            edges.append(installed)
            heights_mean.append(entry["mac_mean"])
            heights_std.append(entry["mac_std"])

        layer_boundaries[layer] = installed

    return edges, heights_mean, heights_std, layer_boundaries, aggregated_by_layer

def _step_xy(edges, heights):
    if not heights:
        return [], []

    xs = [edges[0]]
    ys = [heights[0]]

    for i in range(len(heights)):
        xs.append(edges[i + 1])
        ys.append(heights[i])

        if i + 1 < len(heights):
            xs.append(edges[i + 1])
            ys.append(heights[i + 1])

    return xs, ys

def plot_structural_macc_curve(results, output_path, title_prefix=""):
    lg_edges, lg_heights_mean, lg_heights_std, lg_segments = aggregate_lexicographic_macc(results)    
    p_edges, p_heights_mean, p_heights_std, layer_boundaries, aggregated_by_layer = aggregate_pareto_macc(results)
    fig, ax = plt.subplots(figsize=(12, 7))

    if lg_heights_mean:
        ax.step(
            lg_edges,
            [lg_heights_mean[0]] + lg_heights_mean,
            where="post",
            linewidth=2.4,
            color="black",
            label="Lexicographic",
        )
        x, lower, upper = _step_fill_arrays(lg_edges, lg_heights_mean, lg_heights_std)
        ax.fill_between(x, lower, upper, step="post", color="black",alpha=0.20)
        for seg in lg_segments:
            if seg["method"] is not None:
                mid_x = 0.5 * (seg["x0"] + seg["x1"])
                mid_y = seg["mac_mean"]

                ax.text(
                    mid_x,
                    mid_y,
                    seg["method"],
                    ha="center",
                    va="bottom",
                    fontsize=8,
                    rotation=45,
                    color="black",
                )

    if p_heights_mean and layer_boundaries:
        sorted_layers = sorted(layer_boundaries.keys())

        start_idx = 0
        prev_boundary = 0.0

        for li, layer in enumerate(sorted_layers):
            layer_end = layer_boundaries[layer]

            # collect this layer's entries
            layer_edges = [prev_boundary]
            layer_means = []
            layer_stds = []

            while start_idx < len(p_heights_mean) and p_edges[start_idx + 1] <= layer_end + 1e-12:
                layer_edges.append(p_edges[start_idx + 1])
                layer_means.append(p_heights_mean[start_idx])
                layer_stds.append(p_heights_std[start_idx])
                start_idx += 1
            pareto_color = "#d62728"
            if layer_means:
                # mean step curve for this layer only
                layer_xs, layer_ys = _step_xy(layer_edges, layer_means)
                ax.plot(
                    layer_xs,
                    layer_ys,
                    color=pareto_color,
                    linewidth=2.4,
                    label="Pareto" if li == 0 else None
                )

                # std band for this layer only
                x = np.array(layer_edges, dtype=float)
                y = np.array([layer_means[0]] + layer_means, dtype=float)
                s = np.array([layer_stds[0]] + layer_stds, dtype=float)

                lower = np.maximum(0.0, y - s)
                upper = y + s

                ax.fill_between(
                    x,
                    lower,
                    upper,
                    step="post",
                    color = pareto_color,
                    alpha=0.20
                )
                
                running_x = prev_boundary
                for entry in aggregated_by_layer[layer]:
                    mid_x = running_x + entry["cap_mean"] / 2.0
                    mid_y = entry["mac_mean"]

                    if entry["method"] is not None:
                        ax.text(
                        mid_x,
                        mid_y,
                        entry["method"],
                        ha="center",
                        va="bottom",
                        fontsize=8,
                        rotation=45,
                        color=pareto_color,
                    )

                    running_x += entry["cap_mean"]
            # vertical line at end of layer
            ax.axvline(
                x=layer_end,
                linestyle="--",
                linewidth=1.2,
                color= pareto_color,
                alpha=0.7
            )

            prev_boundary = layer_end
    xmax = max(
        [0.0]
        + ([lg_edges[-1]] if lg_heights_mean else [])
        + ([p_edges[-1]] if p_heights_mean else [])
    )

    ymax_candidates = [0.0]
    if lg_heights_mean:
        ymax_candidates.extend(np.array(lg_heights_mean) + np.array(lg_heights_std))
    if p_heights_mean:
        ymax_candidates.extend(np.array(p_heights_mean) + np.array(p_heights_std))
    ymax = max(ymax_candidates) * 1.10 if ymax_candidates else 1.0

    ax.set_xlim(left=0, right=xmax if xmax > 0 else 1.0)
    ax.set_ylim(bottom=0, top=ymax if ymax > 0 else 1.0)
    ax.margins(x=0)
    ax.set_xlabel("Cumulative Storage Capacity (Gt CO₂)")
    ax.set_ylabel("Marginal Abatement Cost ($/tCO₂)")
    ax.set_title(f"{title_prefix}Average MACC Across Monte Carlo Runs".strip())
    ax.grid(True, alpha=0.25)
    ax.legend()

    plt.tight_layout()
    plt.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close()

    print(f"Saved aggregate MACC plot: {output_path}")
    print(f"Lexicographic aggregate total: {lg_edges[-1] if lg_heights_mean else 0:.2f} Gt")
    print(f"Pareto aggregate total: {p_edges[-1] if p_heights_mean else 0:.2f} Gt")
    return output_path

def plot_bar_comparison(values, errors, labels, ylabel, title, output_path):
    values_b = np.array(values, dtype=float) / 1e9
    errors_b = np.array(errors, dtype=float) / 1e9

    fig, ax = plt.subplots(figsize=(7, 4.5))

    colors = ["black", "#d62728"] 

    bars = ax.bar(
        labels,
        values_b,
        width=0.65,
        color=colors[:len(values_b)],
        edgecolor="black",
        linewidth=0.8,
        yerr=errors_b,
        capsize=5,
        error_kw={
            "elinewidth": 1.2,
            "capthick": 1.2,
            "ecolor": "black",
        },
        zorder=3,
    )

    ax.set_ylabel(ylabel)
    ax.set_title(title, pad=10)

    ax.yaxis.set_major_formatter(FuncFormatter(_format_billions))

    ymax = max(values_b + errors_b) * 1.15 if len(values_b) else 1.0
    ymin = min(0.0, np.min(values_b - errors_b) * 1.05)
    ax.set_ylim(ymin, ymax)

    # cleaner grid
    ax.grid(axis="y", linestyle="--", alpha=0.35, zorder=0)

    # remove clutter
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # value labels
    for bar, v, e in zip(bars, values_b, errors_b):
        y = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            y + e,
            f"{v:,.2f}B",
            ha="center",
            va="bottom",
            fontsize=9,
        )

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()

    print(f"Saved plot: {output_path}")
    print(f"Y-axis range: {ymin:,.2f}B to {ymax:,.2f}B")


def plot_aggregate_method_removal(results, output_path, title_prefix=""):
    lg_totals = aggregate_method_removal(results, "lg_portfolio")
    pareto_totals = aggregate_method_removal(results, "pareto_portfolio")

    all_methods = sorted(set(lg_totals.keys()) | set(pareto_totals.keys()))
    lg_means, lg_stds, pareto_means, pareto_stds = [], [], [], []

    for method in all_methods:
        lg_vals = np.array(lg_totals.get(method, []), dtype=float)
        p_vals = np.array(pareto_totals.get(method, []), dtype=float)

        lg_means.append(lg_vals.mean() if lg_vals.size else 0.0)
        pareto_means.append(p_vals.mean() if p_vals.size else 0.0)
        lg_stds.append(lg_vals.std(ddof=1) if lg_vals.size > 1 else 0.0)
        pareto_stds.append(p_vals.std(ddof=1) if p_vals.size > 1 else 0.0)

    x = np.arange(len(all_methods))
    width = 0.38

    fig, ax = plt.subplots(figsize=(10, 5.5))

    ax.bar(
        x - width / 2,
        lg_means,
        width,
        yerr=lg_stds,
        capsize=5,
        color="black",
        edgecolor="black",
        linewidth=0.8,
        error_kw={
            "elinewidth": 1.2,
            "capthick": 1.2,
            "ecolor": "black",
        },
        label="Lexicographic",
        zorder=3,
    )

    ax.bar(
        x + width / 2,
        pareto_means,
        width,
        yerr=pareto_stds,
        capsize=5,
        color="#d62728",
        edgecolor="black",
        linewidth=0.8,
        error_kw={
            "elinewidth": 1.2,
            "capthick": 1.2,
            "ecolor": "black",
        },
        label="Pareto",
        zorder=3,
    )

    ax.set_xticks(x)
    ax.set_xticklabels(all_methods, rotation=45, ha="right")
    ax.set_ylabel("Average Removal (Gt CO₂ per simulation)")
    ax.set_title(f"{title_prefix}Average Removal by Method Across Runs".strip(), pad=10)
    ax.legend()

    ymax = max(
        [0.0]
        + [m + s for m, s in zip(lg_means, lg_stds)]
        + [m + s for m, s in zip(pareto_means, pareto_stds)]
    ) * 1.15
    ax.set_ylim(0, ymax if ymax > 0 else 1)

    ax.grid(axis="y", linestyle="--", alpha=0.35, zorder=0)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()

    print(f"Saved aggregate method removal plot: {output_path}")
    print("Methods plotted:", all_methods)
    return output_path

def plot_adjusted_pv_six_bars(values, errors, output_path, title):
    labels = [
        "Lexicographic\nTotal Social Net PV",
        "Lexicographic\nPositive Ext.",
        "Lexicographic\nNegative Ext.",
        "Pareto\nTotal Social Net PV",
        "Pareto\nPositive Ext.",
        "Pareto\nNegative Ext.",
    ]

    x = np.arange(len(labels))
    values = np.array(values, dtype=float)
    errors = np.array(errors, dtype=float)

    fig, ax = plt.subplots(figsize=(12, 7))
    colors = [
        "black",      # Lexicographic total social PV
        "dimgray",    # Lexicographic positive ext
        "lightgray",  # Lexicographic negative ext
        "#d62728",    # Pareto total social PV
        "#ff6b6b",    # Pareto positive ext
        "#f4a3a3",    # Pareto negative ext
    ]
    ax.bar(
        x,
        values,
        yerr=errors,
        capsize=5,
        color=colors,
        edgecolor="black",
        linewidth=0.8,
        error_kw={
            "elinewidth": 1.2,
            "capthick": 1.2,
            "ecolor": "black",
        },
    )

    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=20, ha="right")
    ax.set_ylabel("Mean PV ($)")
    ax.set_title(title)

    # zero reference line so negative bars are visually clear
    ax.axhline(0, linewidth=1.0)

    # allow room for negative and positive bars including error bars
    lower = np.min(values - errors)
    upper = np.max(values + errors)

    if lower == upper:
        pad = max(1.0, abs(lower) * 0.1)
        ax.set_ylim(lower - pad, upper + pad)
    else:
        span = upper - lower
        pad = span * 0.1
        ax.set_ylim(lower - pad, upper + pad)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)

def plot_standard_macc_curve(results, storage_target, output_path):
    x_lg, lg_mean, lg_std, lg_extent = aggregate_macc_curves(
        results,
        "lg_portfolio",
        storage_target=storage_target,
    )
    x_p, p_mean, p_std, p_extent = aggregate_macc_curves(
        results,
        "pareto_portfolio",
        storage_target=storage_target,
    )

    fig, ax = plt.subplots(figsize=(10, 6))

    # Lexicographic
    ax.step(
        x_lg,
        lg_mean,
        where="post",
        linewidth=2.2,
        color="black",
        label="Lexicographic",
    )
    ax.fill_between(
        x_lg,
        lg_mean - lg_std,
        lg_mean + lg_std,
        step="post",
        color="black",
        alpha=0.2,
    )

    # Pareto
    ax.step(
        x_p,
        p_mean,
        where="post",
        linewidth=2.2,
        color="#d62728",
        label="Pareto",
    )
    ax.fill_between(
        x_p,
        p_mean - p_std,
        p_mean + p_std,
        step="post",
        color="#d62728",
        alpha=0.2,
    )

    xmax = max(lg_extent, p_extent)

    ax.set_xlim(left=0, right=xmax if xmax > 0 else 1.0)
    ax.set_ylim(bottom=0)
    ax.set_xlabel("Cumulative Storage Capacity (Gt CO₂)")
    ax.set_ylabel("Marginal Abatement Cost ($/tCO₂)")
    ax.set_title("Mean MACC Across Monte Carlo Runs")
    ax.grid(True, alpha=0.25)
    ax.legend()

    plt.tight_layout()
    plt.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close()

    print(f"Saved Mean MACC Across Monte Carlo Runs: {output_path}")
    print(f"Lexicographic mean extent: {lg_extent:.2f} Gt")
    print(f"Pareto mean extent: {p_extent:.2f} Gt")
    return output_path

def plot_aggregate_method_removal(results, output_path, title_prefix=""):
    lg_totals = aggregate_method_removal(results, "lg_portfolio")
    pareto_totals = aggregate_method_removal(results, "pareto_portfolio")

    all_methods = sorted(set(lg_totals.keys()) | set(pareto_totals.keys()))
    lg_means, lg_stds, pareto_means, pareto_stds = [], [], [], []

    for method in all_methods:
        lg_vals = np.array(lg_totals.get(method, []), dtype=float)
        p_vals = np.array(pareto_totals.get(method, []), dtype=float)

        lg_means.append(lg_vals.mean() if lg_vals.size else 0.0)
        pareto_means.append(p_vals.mean() if p_vals.size else 0.0)

        lg_stds.append(lg_vals.std(ddof=1) if lg_vals.size > 1 else 0.0)
        pareto_stds.append(p_vals.std(ddof=1) if p_vals.size > 1 else 0.0)

    x = np.arange(len(all_methods))
    width = 0.38

    fig, ax = plt.subplots(figsize=(10, 5.5))

    ax.bar(
        x - width / 2,
        lg_means,
        width,
        yerr=lg_stds,
        capsize=5,
        color="black",
        edgecolor="black",
        linewidth=0.8,
        label="Lexicographic",
    )

    ax.bar(
        x + width / 2,
        pareto_means,
        width,
        yerr=pareto_stds,
        capsize=5,
        color="#d62728",
        edgecolor="black",
        linewidth=0.8,
        label="Pareto",
    )

    ax.set_xticks(x)
    ax.set_xticklabels(all_methods, rotation=45, ha="right")
    ax.set_ylabel("Average Removal (Gt CO₂ per simulation)")
    ax.set_title(f"{title_prefix}Average Removal by Method Across Runs".strip())
    ax.legend()

    ymax = max(
        [0.0]
        + [m + s for m, s in zip(lg_means, lg_stds)]
        + [m + s for m, s in zip(pareto_means, pareto_stds)]
    ) * 1.15

    ax.set_ylim(0, ymax if ymax > 0 else 1)
    ax.grid(axis="y", linestyle="--", alpha=0.35)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()

    print(f"Saved aggregate removal plot: {output_path}")
    
#########################################
#########################################
#########################################
# Below is the core code for simulation, all above deals with plotting and helper functions. 
def run_single_seed(
    viaCheck,
    dataUse,
    seed,
    removal_target,
    SCC,
    SDR,
    duration_years,
    region,
    EuropeanStoragePotential,
    NorthAmericanStoragePotential,
    GlobalStoragePotential,
):
    if dataUse == "Survey":
        cdr_methods = generate_random_portfolio(pseed=seed)
    elif dataUse == "Rueda":
        cdr_methods = generate_random_portfolioR(pseed=seed)
    elif dataUse == "EU":
        cdr_methods = generate_random_portfolioEU(pseed=seed)
    elif dataUse == "SurveyRange":
        cdr_methods = generate_random_portfolioSR(pseed=seed)
    else:
        raise ValueError(f"Unknown dataUse: {dataUse}")

    current_year = removal_target["current_year"]
    start_year = removal_target["start_year"]
    storage_target = removal_target["storage_target"]

    if viaCheck == True:
        viable_methods = is_method_viable(
            cdr_methods,
            SCC,
            SDR,
            start_year=start_year,
            duration_years=duration_years,
            current_year=current_year,
        )
    elif viaCheck == False:
        viable_methods = cdr_methods

    if region == "Europe":
        sp = EuropeanStoragePotential
    elif region == "North America":
        sp = NorthAmericanStoragePotential
    elif region == "Global":
        sp = GlobalStoragePotential

    lg = lexicographic_opt_iterative(
        viaCheck,
        SDR,
        SCC,
        start_year,
        current_year,
        viable_methods,
        storage_target,
        duration_years,
        pass_storage_potential=sp,
    )

    pareto = pareto_portfolio_iterative_layers(
        viaCheck,
        SDR,
        SCC,
        start_year,
        current_year,
        viable_methods,
        storage_target,
        duration_years,
        pass_storage_potential=sp,
    )

    (
        lg_climate_pv,
        lg_ext_climate_pv,
        lg_total_adj,
        lg_adj_pos_ext,
        lg_adj_neg_ext,
    ) = compute_adjusted_total_pv(lg)

    (
        p_climate_pv,
        p_ext_climate_pv,
        p_total_adj,
        p_adj_pos_ext,
        p_adj_neg_ext,
    ) = compute_adjusted_total_pv(pareto)


    return {
        "seed": seed,
        "lg_climate_pv": lg_climate_pv,
        "lg_externality_pv": lg_ext_climate_pv,
        "lg_adj_pv": lg_total_adj,
        "lg_adj_pos": lg_adj_pos_ext,
        "lg_adj_neg": lg_adj_neg_ext,
        "pareto_climate_pv": p_climate_pv,
        "pareto_externality_pv": p_ext_climate_pv,
        "pareto_adj_pv": p_total_adj,
        "pareto_adj_pos": p_adj_pos_ext,
        "pareto_adj_neg": p_adj_neg_ext,
        "lg_count": len(lg or []),
        "pareto_count": len(pareto or []),
        "lg_portfolio": lg or [],
        "pareto_portfolio": pareto or [],
    }

#function name is a legacy, code was imporoved upon and now runs with 10,000 simulations.
def run_100_simulations(
    viaCheck,
    dataUse,
    seeds,
    removal_target,
    SCC,
    SDR,
    duration_years,
    region,
    EuropeanStoragePotential,
    NorthAmericanStoragePotential,
    GlobalStoragePotential,
):
    results = []
    for seed in seeds:
        res = run_single_seed(
            viaCheck=viaCheck,
            dataUse=dataUse,
            seed=seed,
            removal_target=removal_target,
            SCC=SCC,
            SDR=SDR,
            duration_years=duration_years,
            region=region,
            EuropeanStoragePotential=EuropeanStoragePotential,
            NorthAmericanStoragePotential=NorthAmericanStoragePotential,
            GlobalStoragePotential=GlobalStoragePotential,
        )
        results.append(res)

    lg_vals = np.array([r["lg_climate_pv"] for r in results], dtype=float)
    p_vals = np.array([r["pareto_climate_pv"] for r in results], dtype=float)

    lg_adj_vals = np.array([r["lg_adj_pv"] for r in results], dtype=float)
    p_adj_vals = np.array([r["pareto_adj_pv"] for r in results], dtype=float)

    lg_adj_pos_vals = np.array([r["lg_adj_pos"] for r in results], dtype=float)
    lg_adj_neg_vals = np.array([r["lg_adj_neg"] for r in results], dtype=float)
    p_adj_pos_vals = np.array([r["pareto_adj_pos"] for r in results], dtype=float)
    p_adj_neg_vals = np.array([r["pareto_adj_neg"] for r in results], dtype=float)

    lg_mean, p_mean = lg_vals.mean(), p_vals.mean()
    lg_std, p_std = lg_vals.std(ddof=1), p_vals.std(ddof=1)

    lg_adj_mean, p_adj_mean = lg_adj_vals.mean(), p_adj_vals.mean()
    lg_adj_std, p_adj_std = lg_adj_vals.std(ddof=1), p_adj_vals.std(ddof=1)

    lg_adj_pos_mean, lg_adj_pos_std = lg_adj_pos_vals.mean(), lg_adj_pos_vals.std(ddof=1)
    lg_adj_neg_mean, lg_adj_neg_std = lg_adj_neg_vals.mean(), lg_adj_neg_vals.std(ddof=1)
    p_adj_pos_mean, p_adj_pos_std = p_adj_pos_vals.mean(), p_adj_pos_vals.std(ddof=1)
    p_adj_neg_mean, p_adj_neg_std = p_adj_neg_vals.mean(), p_adj_neg_vals.std(ddof=1)

    #custom output path per sesssion, so it can be seen what has been done
    #the time element prevents over writing in the case that the same 
    #simulation is ran again.
    #NO VC output means no viability constraint
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    storage_target = removal_target["storage_target"]
    output_root = "with_VC_output" if viaCheck else "no_VC_output"
    output_dir = os.path.join(output_root, f"{dataUse}_Region{region}_SCC{SCC}_SDR{SDR}_target{storage_target}Gt_output")
    os.makedirs(output_dir, exist_ok=True)

    out1 = os.path.join(
        output_dir,
        f"{dataUse}_composite_avg_climate_benefit_pv_{timestamp}.png"
    )
    plot_bar_comparison(
        values=[lg_mean, p_mean],
        errors=[lg_std, p_std],
        labels=["Lexicographic", "Pareto"],
        ylabel="Mean Net Climate Benefit PV ($)",
        title="100-run Average climate-Benefit PV",
        output_path=out1,
        )

    out2b = os.path.join(
        output_dir,
        f"{dataUse}_composite_avg_social_pv_externality_decomposition_{timestamp}.png"
    )
    plot_adjusted_pv_six_bars(
        values=[
            lg_adj_mean,
            lg_adj_pos_mean,
            lg_adj_neg_mean,
            p_adj_mean,
            p_adj_pos_mean,
            p_adj_neg_mean,
        ],
        errors=[
            lg_adj_std,
            lg_adj_pos_std,
            lg_adj_neg_std,
            p_adj_std,
            p_adj_pos_std,
            p_adj_neg_std,
        ],
    output_path=out2b,
    title="10,000-run Average Social Net Benefit PV and Externality Decomposition",
    )

    out3_decomp = os.path.join(
        output_dir,
        f"{dataUse}_aggregate_social_decomposition_by_method_{timestamp}.png"
    )
    plot_aggregate_method_social_decomposition(results, out3_decomp)

    out4_structural = os.path.join(
        output_dir,
        f"{dataUse}_aggregate_structural_macc_{timestamp}.png"
    )
    plot_structural_macc_curve(results, out4_structural)

    out4_standard = os.path.join(
        output_dir,
        f"{dataUse}_aggregate_standard_macc_{timestamp}.png"
    )
    plot_standard_macc_curve(
        results,
        storage_target=removal_target["storage_target"],
        output_path=out4_standard,
    )

    out5 = os.path.join(
        output_dir,
        f"{dataUse}_aggregate_pareto_scatter_{timestamp}.png"
    )
    plot_aggregate_pareto_scatter(results, out5)

    out6 = os.path.join(
        output_dir,
        f"{dataUse}_aggregate_lexicographic_scatter_{timestamp}.png"
    )
    plot_aggregate_lexicographic_scatter(results, out6)
    out_removal = os.path.join(
        output_dir,
        f"{dataUse}_aggregate_removal_by_method_{timestamp}.png"
    )
    plot_aggregate_method_removal(results, out_removal)

    return {
    "results": results,
    "summary": {
        "lg_mean": lg_mean,
        "pareto_mean": p_mean,
        "lg_std": lg_std,
        "pareto_std": p_std,
        "lg_adj_mean": lg_adj_mean,
        "pareto_adj_mean": p_adj_mean,
        "lg_adj_std": lg_adj_std,
        "pareto_adj_std": p_adj_std,
        "lg_adj_pos_mean": lg_adj_pos_mean,
        "lg_adj_neg_mean": lg_adj_neg_mean,
        "pareto_adj_pos_mean": p_adj_pos_mean,
        "pareto_adj_neg_mean": p_adj_neg_mean,
        "out_climate_benefit": out1,
        "out_social_decomposition": out2b,
        "out_method_social_decomposition": out3_decomp,
        "out_structural_macc": out4_structural,
        "out_standard_macc": out4_standard,
        "out_aggregate_pareto_scatter": out5,
        "out_aggregate_lexicographic_scatter": out6,
        "out_aggregate_method_removal": out_removal,
    },
}
