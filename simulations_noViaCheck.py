import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import os

from data_gen import generate_random_portfolio
from cdr_method import CDRMethod
from main import (
    is_method_viable,
    lexicographic_opt_iterative,
    pareto_portfolio_iterative_layers,
    marginal_abatement_cost_curve,
    marginal_abatement_cost_curve_pareto,
)

# --------------------------------------------------
# Helpers
# --------------------------------------------------

def build_macc_steps(portfolio, target_gt):
    """
    Convert a portfolio into MACC step data without plotting.

    Returns:
        edges: cumulative capacity bin edges, starting with 0.0
        heights: MAC values for each step
    """
    if not portfolio:
        return [0.0], []

    entries = [e for e in portfolio if float(e.get("actual_contribution", 0.0)) > 0]

    edges = [0.0]
    heights = []
    installed = 0.0

    for e in entries:
        contrib = float(e["actual_contribution"])
        mac = float(e["mac"])

        remaining = float(target_gt) - installed
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
    """
    Evaluate a stepwise MACC on a common x-grid.

    Returns NaN beyond the curve's final extent.
    """
    y = np.full_like(x_grid, np.nan, dtype=float)

    if len(heights) == 0:
        return y

    for i, x in enumerate(x_grid):
        for j in range(len(heights)):
            if edges[j] <= x <= edges[j + 1]:
                y[i] = heights[j]
                break

    return y


def aggregate_macc_curves(results, portfolio_key, target_gt, n_grid=250):
    """
    Aggregate MACC curves across runs by evaluating each run on a common grid.
    """
    x_grid = np.linspace(0, float(target_gt), n_grid)
    curves = []

    for r in results:
        portfolio = r.get(portfolio_key, []) or []
        edges, heights = build_macc_steps(portfolio, target_gt)
        y = evaluate_step_curve(edges, heights, x_grid)
        curves.append(y)

    if not curves:
        return x_grid, np.full_like(x_grid, np.nan), np.full_like(x_grid, np.nan)

    curves = np.array(curves, dtype=float)

    mean_curve = np.nanmean(curves, axis=0)
    std_curve = np.nanstd(curves, axis=0, ddof=1) if curves.shape[0] > 1 else np.zeros_like(mean_curve)

    return x_grid, mean_curve, std_curve


def plot_aggregate_macc_curve(results, target_gt, output_path, title_prefix=""):
    """
    Plot aggregate Lexicographic and Pareto MACC curves with ±1 std bands.
    """
    x_lg, lg_mean, lg_std = aggregate_macc_curves(
        results, "lg_portfolio", target_gt=target_gt
    )
    x_p, p_mean, p_std = aggregate_macc_curves(
        results, "pareto_portfolio", target_gt=target_gt
    )

    fig, ax = plt.subplots(figsize=(10, 6))

    ax.plot(x_lg, lg_mean, linewidth=2.2, label="Lexicographic")
    ax.fill_between(x_lg, lg_mean - lg_std, lg_mean + lg_std, alpha=0.2)

    ax.plot(x_p, p_mean, linewidth=2.2, label="Pareto")
    ax.fill_between(x_p, p_mean - p_std, p_mean + p_std, alpha=0.2)

    ax.set_xlim(left=0, right=float(target_gt))
    ax.set_ylim(bottom=0)
    ax.set_xlabel("Cumulative Storage Capacity (Gt CO₂)")
    ax.set_ylabel("Marginal Abatement Cost (€/tCO₂)")
    ax.set_title(f"{title_prefix}Aggregate MACC Across Runs".strip())
    ax.grid(True, alpha=0.25)
    ax.legend()

    plt.tight_layout()
    plt.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close()

    print(f"Saved aggregate MACC plot: {output_path}")
    return output_path


def compute_total_pv(portfolio):
    """Sum raw pv_net across a portfolio."""
    return sum(float(e.get("pv_net", 0.0)) for e in (portfolio or []))


def compute_adjusted_total_pv(portfolio):
    """
    Sum externality-adjusted pv_net across a portfolio.

    Assumes method.sideEffect is already scaled to [-1, 1].
    """
    total = 0.0
    for e in (portfolio or []):
        m = e["method"]
        pv = float(e.get("pv_net", 0.0))
        se = float(getattr(m, "sideEffect", 0.0))
        total += pv * (1 + se)
    return total


def _format_billions(x, pos):
    return f"{x:,.0f}"


def plot_bar_comparison(values, errors, labels, ylabel, title, output_path):
    values_b = np.array(values, dtype=float) / 1e9
    errors_b = np.array(errors, dtype=float) / 1e9

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(labels, values_b, yerr=errors_b, capsize=6)

    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.yaxis.set_major_formatter(FuncFormatter(_format_billions))

    ymax = max(values_b + errors_b) * 1.15 if len(values_b) else 1.0
    ymin = min(0.0, np.min(values_b - errors_b) * 1.05)
    ax.set_ylim(ymin, ymax)

    for bar, v, e in zip(bars, values_b, errors_b):
        y = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            y + e,
            f"{v:,.2f}B",
            ha="center",
            va="bottom"
        )

    plt.tight_layout()
    plt.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close()

    print(f"Saved plot: {output_path}")
    print(f"Y-axis range: {ymin:,.2f}B to {ymax:,.2f}B")
    for label, v, e in zip(labels, values_b, errors_b):
        print(f"{label}: {v:,.2f}B ± {e:,.2f}B")


def extract_method_name(method):
    return method.mainType


def aggregate_method_pv(results, portfolio_key):
    """
    Every method gets one value per run; if absent in a run, its value is 0.
    """
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
            run_totals[method_name] += float(e.get("pv_net", 0.0))

        for method_name in all_methods:
            method_totals[method_name].append(run_totals[method_name])

    return method_totals


def plot_aggregate_method_pv(results, output_path, title_prefix=""):
    lg_totals = aggregate_method_pv(results, "lg_portfolio")
    pareto_totals = aggregate_method_pv(results, "pareto_portfolio")

    all_methods = sorted(set(lg_totals.keys()) | set(pareto_totals.keys()))

    lg_means = []
    lg_stds = []
    pareto_means = []
    pareto_stds = []

    for method in all_methods:
        lg_vals = np.array(lg_totals.get(method, []), dtype=float)
        p_vals = np.array(pareto_totals.get(method, []), dtype=float)

        lg_means.append(lg_vals.mean() / 1e9 if lg_vals.size else 0.0)
        pareto_means.append(p_vals.mean() / 1e9 if p_vals.size else 0.0)

        lg_stds.append(lg_vals.std(ddof=1) / 1e9 if lg_vals.size > 1 else 0.0)
        pareto_stds.append(p_vals.std(ddof=1) / 1e9 if p_vals.size > 1 else 0.0)

    x = np.arange(len(all_methods))
    width = 0.38

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(x - width / 2, lg_means, width, yerr=lg_stds, capsize=4, label="Lexicographic")
    ax.bar(x + width / 2, pareto_means, width, yerr=pareto_stds, capsize=4, label="Pareto")

    ax.set_xticks(x)
    ax.set_xticklabels(all_methods, rotation=45, ha="right")
    ax.set_ylabel("Average PV contribution (€ billions)")
    ax.set_title(f"{title_prefix}Aggregate PV Contribution by Method Across Runs".strip())
    ax.yaxis.set_major_formatter(FuncFormatter(_format_billions))
    ax.legend()

    ymax = max(
        [0.0]
        + [m + s for m, s in zip(lg_means, lg_stds)]
        + [m + s for m, s in zip(pareto_means, pareto_stds)]
    ) * 1.15
    ax.set_ylim(0, ymax if ymax > 0 else 1)

    plt.tight_layout()
    plt.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close()

    print(f"Saved aggregate method PV plot: {output_path}")
    print("Methods plotted:", all_methods)
    return output_path


# --------------------------------------------------
# Core simulation: NC version
# --------------------------------------------------

def run_single_seedNC(
    seed,
    removal_target,
    SCC,
    SDR,
    duration_years,
    region,
    EuropeanStoragePotential,
    NorthAmericanStoragePotential,
    GlobalStoragePotential
):
    cdr_methods = generate_random_portfolio(pseed=seed)

    current_year = removal_target["current_year"]
    start_year = removal_target["start_year"]
    target_gt = removal_target["storage_target"]

    # NC condition: skip viability check
    viable_methods = cdr_methods

    if region == "Europe":
        sp = EuropeanStoragePotential
    elif region == "North America":
        sp = NorthAmericanStoragePotential
    else:
        sp = GlobalStoragePotential

    lg = lexicographic_opt_iterative(
        SDR,
        SCC,
        start_year,
        current_year,
        viable_methods,
        target_gt,
        duration_years,
        pass_storage_potential=sp
    )

    pareto = pareto_portfolio_iterative_layers(
        SDR,
        SCC,
        start_year,
        current_year,
        viable_methods,
        target_gt,
        duration_years,
        pass_storage_potential=sp,
        plot=False
    )

    lg_total_pv = compute_total_pv(lg)
    p_total_pv = compute_total_pv(pareto)

    lg_adj = compute_adjusted_total_pv(lg)
    p_adj = compute_adjusted_total_pv(pareto)

    return {
        "seed": seed,
        "lg_total_pv": lg_total_pv,
        "pareto_total_pv": p_total_pv,
        "lg_adj_pv": lg_adj,
        "pareto_adj_pv": p_adj,
        "lg_count": len(lg or []),
        "pareto_count": len(pareto or []),
        "lg_portfolio": lg or [],
        "pareto_portfolio": pareto or [],
    }


def run_100_simulationsNC(
    seeds,
    removal_target,
    SCC,
    SDR,
    duration_years,
    region,
    EuropeanStoragePotential,
    NorthAmericanStoragePotential,
    GlobalStoragePotential
):
    target_gt = removal_target["storage_target"]

    results = []
    for seed in seeds:
        res = run_single_seedNC(
            seed=seed,
            removal_target=removal_target,
            SCC=SCC,
            SDR=SDR,
            duration_years=duration_years,
            region=region,
            EuropeanStoragePotential=EuropeanStoragePotential,
            NorthAmericanStoragePotential=NorthAmericanStoragePotential,
            GlobalStoragePotential=GlobalStoragePotential
        )
        results.append(res)

    # Arrays
    lg_vals = np.array([r["lg_total_pv"] for r in results], dtype=float)
    p_vals = np.array([r["pareto_total_pv"] for r in results], dtype=float)

    lg_adj_vals = np.array([r["lg_adj_pv"] for r in results], dtype=float)
    p_adj_vals = np.array([r["pareto_adj_pv"] for r in results], dtype=float)

    # Means
    lg_mean = lg_vals.mean()
    p_mean = p_vals.mean()
    lg_adj_mean = lg_adj_vals.mean()
    p_adj_mean = p_adj_vals.mean()

    # Std dev
    lg_std = lg_vals.std(ddof=1)
    p_std = p_vals.std(ddof=1)
    lg_adj_std = lg_adj_vals.std(ddof=1)
    p_adj_std = p_adj_vals.std(ddof=1)

    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)

    # Graph 1: no externality
    out1 = os.path.join(output_dir, "NOVCcomposite_avg_pv_net_no_externality.png")
    plot_bar_comparison(
        values=[lg_mean, p_mean],
        errors=[lg_std, p_std],
        labels=["Lexicographic", "Pareto"],
        ylabel="Mean Total PV (Net) (€ billions)",
        title="No VC: 100-run Average Total Net PV (No Externality Adjustment)",
        output_path=out1
    )

    # Graph 2: externality-adjusted
    out2 = os.path.join(output_dir, "NOVCcomposite_avg_pv_net_externality_adjusted.png")
    plot_bar_comparison(
        values=[lg_adj_mean, p_adj_mean],
        errors=[lg_adj_std, p_adj_std],
        labels=["Lexicographic", "Pareto"],
        ylabel="Mean Total PV (Adjusted Net) (€ billions)",
        title="No VC: 100-run Average Total Net PV (Externality-Adjusted)",
        output_path=out2
    )

    # Graph 3: aggregate PV contribution by method
    out3 = os.path.join(output_dir, "NOVCaggregate_pv_contribution_by_method.png")
    plot_aggregate_method_pv(results, out3, title_prefix="No VC: ")

    # Graph 4: aggregate MACC curves
    out4 = os.path.join(output_dir, "NOVCaggregate_macc_curves.png")
    plot_aggregate_macc_curve(results, target_gt, out4, title_prefix="No VC: ")

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
            "out_no_externality": out1,
            "out_externality": out2,
            "out_method_pv_contribution": out3,
            "out_aggregate_macc": out4,
        }
    }