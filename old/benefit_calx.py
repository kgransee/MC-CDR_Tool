import os
import matplotlib.pyplot as plt

def plot_total_pv_net_lg_vs_pareto(lg_methods, pareto_portfolio):
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)

    # --- Without externality adjustment ---
    lg_total = sum(float(e.get("pv_net", 0.0)) for e in lg_methods)
    p_total  = sum(float(e.get("pv_net", 0.0)) for e in pareto_portfolio)

    # convert to billions
    lg_total_b = lg_total / 1e9
    p_total_b  = p_total / 1e9

    values = [lg_total_b, p_total_b]
    labels = ["Lexicographic", "Pareto"]

    fig, ax = plt.subplots(figsize=(8,5))
    bars = ax.bar(labels, values)

    ax.set_ylabel("Total PV (Net) (€ billions)")
    ax.set_title("Total Net Present Value (No Externality Adjustment)")

    # annotate exact values
    for bar, v in zip(bars, values):
        ax.text(
            bar.get_x() + bar.get_width()/2,
            bar.get_height(),
            f"{v:.2f}B",
            ha='center',
            va='bottom'
        )

    # show range on axis
    ymin = 0
    ymax = max(values) * 1.15
    ax.set_ylim(ymin, ymax)

    plt.tight_layout()

    output_path = os.path.join(output_dir, "total_pv_net_comparison.png")
    plt.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close()

    print(f"Saved PV comparison plot: {output_path}")
    print(f"Range: {ymin:.2f}B – {ymax:.2f}B")
    print(f"Lexicographic: {lg_total_b:.2f}B")
    print(f"Pareto: {p_total_b:.2f}B")

    # --- With externality adjustment ---
    lg_adj = 0.0
    for e in lg_methods:
        m = e["method"]
        pv_net = float(e.get("pv_net", 0.0))
        se = float(getattr(m, "sideEffect", 0.0))
        lg_adj += pv_net + (se * pv_net)

    p_adj = 0.0
    for e in pareto_portfolio:
        m = e["method"]
        pv_net = float(e.get("pv_net", 0.0))
        se = float(getattr(m, "sideEffect", 0.0))
        p_adj += pv_net + (se * pv_net)

    lg_adj_b = lg_adj / 1e9
    p_adj_b  = p_adj / 1e9

    values_adj = [lg_adj_b, p_adj_b]

    fig, ax = plt.subplots(figsize=(8,5))
    bars = ax.bar(labels, values_adj)

    ax.set_ylabel("Total PV (Adjusted Net) (€ billions)")
    ax.set_title("Externality-Adjusted Net Present Value")

    for bar, v in zip(bars, values_adj):
        ax.text(
            bar.get_x() + bar.get_width()/2,
            bar.get_height(),
            f"{v:.2f}B",
            ha='center',
            va='bottom'
        )

    ymin = 0
    ymax = max(values_adj) * 1.15
    ax.set_ylim(ymin, ymax)

    plt.tight_layout()

    output_path2 = os.path.join(output_dir, "total_pv_net_comparison_externality_adjusted.png")
    plt.savefig(output_path2, dpi=220, bbox_inches="tight")
    plt.close()

    print(f"Saved externality-adjusted PV comparison plot: {output_path2}")
    print(f"Range: {ymin:.2f}B – {ymax:.2f}B")
    print(f"Lexicographic (adj): {lg_adj_b:.2f}B")
    print(f"Pareto (adj): {p_adj_b:.2f}B")

    return output_path, output_path2