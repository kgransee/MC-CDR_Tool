import os
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import MaxNLocator

def _allocate_by_increasing_mac(front_methods, remaining_target, duration_years, sp, geo_used):

    remaining_target = float(remaining_target)

    # Sort by increasing MAC
    sorted_front = sorted(front_methods, key=lambda m: float(m.mac))

    n = len(sorted_front)
    allocations = [0.0] * n

    for i, m in enumerate(sorted_front):
        if remaining_target <= 1e-12:
            break

        cap = float(m.sideEffectMax) * float(duration_years)

        # Apply geological potential constraint (dynamic because geo_used changes)
        if getattr(m, "storageType", None) == "geological formations":
            cap = min(cap, max(0.0, float(sp) - float(geo_used)))

        cap = max(0.0, cap)
        if cap <= 1e-12:
            continue

        take = min(cap, remaining_target)
        allocations[i] = take
        remaining_target -= take

        if getattr(m, "storageType", None) == "geological formations":
            geo_used += take

    return sorted_front, allocations, geo_used

def _pareto_front(methods):
    front = []
    for m in methods:
        dominated = False
        for o in methods:
            if o is m:
                continue
            if (o.mac <= m.mac and o.sideEffect >= m.sideEffect) and (o.mac < m.mac or o.sideEffect > m.sideEffect):
                dominated = True
                break
        if not dominated:
            front.append(m)
    return front


def pareto_portfolio_iterative_layers(SDR, SCC, start_year, current_year,viable_methods, storage_target, duration_years, pass_storage_potential,max_rounds=10_000, plot=True, plot_rounds_limit=8):

    sp = float(pass_storage_potential)
    geo_used = 0.0

    if not viable_methods:
        print("No viable methods provided.")
        return []

    remaining = viable_methods.copy()
    portfolio = []
    installed = 0.0
    round_idx = 0

    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)

    round_front_snapshots = []

    while remaining and installed < storage_target and round_idx < max_rounds:
        round_idx += 1
        front = _pareto_front(remaining)
        if not front:
            print("No non-dominated methods found. Stopping.")
            break

        round_front_snapshots.append({
            "round": round_idx,
            "front": front.copy(),
            "remaining": remaining.copy()
        })

        print(f"\n=== Round {round_idx}: Pareto front size = {len(front)} ===")

        remaining_target = float(storage_target) - installed

        sorted_front, allocs, geo_used = _allocate_by_increasing_mac(
        front_methods=front,
        remaining_target=remaining_target,
        duration_years=duration_years,
        sp=sp,
        geo_used=geo_used
        )

        for idx, m in enumerate(sorted_front):
            actual = allocs[idx]
            if actual <= 0:
                remaining.remove(m)
                continue

            installed += actual
            contribution = float(m.sideEffectMax) * float(duration_years)
            partial = actual < contribution or installed >= storage_target
            annual_gt = min(float(m.maxRemove), float(m.sideEffectMax))
            if annual_gt <= 0:
                pv_net = 0.0
            else:
                r = float(SDR) / 100.0
                GT_TO_T = 1e9
                net_per_ton = (SCC - float(m.mac))

                pv_net = 0.0
                remaining_gt = float(actual)
                y = 0
                while remaining_gt > 0 and y < duration_years:
                    year = start_year + y
                    t = year - current_year
                    if t < 0:
                        y += 1
                        continue

                    implemented_gt = annual_gt if remaining_gt >= annual_gt else remaining_gt
                    remaining_gt -= implemented_gt

                    discount_factor = (1 + r) ** t
                    tons = implemented_gt * GT_TO_T
                    pv_net += (tons * net_per_ton) / discount_factor
                    y += 1
                            

            portfolio.append({
                "method": m,
                "actual_contribution": actual,
                "mac": m.mac,
                "partial": partial,
                "round": round_idx,
                "pv_net": pv_net
            })

            status = "PARTIAL" if partial else "FULL"
            print(
                f"Added {m.mainType} ({m.subType}) [{status}] | "
                f"MAC: {m.mac} €/tCO₂ | "
                f"Implemented: {actual:.2f} Gt | "
                f"Cumulative: {installed:.2f} Gt"
            )

            remaining.remove(m)

            if installed >= storage_target:
                print("Storage target met.")
                break
        if plot:
            plt.figure(figsize=(10, 6))
            ax = plt.gca()

            # Ensure these always exist
            selected_set = set()
            unused_methods = viable_methods.copy()

            # --- Selected (portfolio) colored by round ---
            if portfolio:
                rounds = sorted({e["round"] for e in portfolio})
                cmap = plt.get_cmap("tab10")
                round_colors = {r: cmap(i % 10) for i, r in enumerate(rounds)}

                for r in rounds:
                    xs = [e["mac"] for e in portfolio if e["round"] == r]
                    ys = [e["method"].sideEffect for e in portfolio if e["round"] == r]
                    ax.scatter(xs, ys, label=f"Pareto selection {r}", color=round_colors[r], s=85, zorder=4)

                # labels for selected points
                offsets = [(8, 8), (8, -10), (-12, 8), (-12, -10), (12, 0), (-14, 0)]
                for i, entry in enumerate(portfolio):
                    x = entry["mac"]
                    y = entry["method"].sideEffect
                    label = f"{entry['method'].subType}"
                    dx, dy = offsets[i % len(offsets)]

                    ax.annotate(
                            label,
                        xy=(x, y),
                        xytext=(dx, dy),
                        textcoords="offset points",
                        ha="center",
                        va="center",
                        fontsize=9,
                        color="black",
                        bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="none", alpha=0.9),
                        zorder=6
                    )

                def _mkey(m):
                    return (getattr(m, "mainType", None), getattr(m, "subType", None))

                selected_keys = {_mkey(e["method"]) for e in portfolio}
                unused_methods = [m for m in viable_methods if _mkey(m) not in selected_keys]

            if unused_methods:
                ax.scatter(
                    [m.mac for m in unused_methods],
                    [m.sideEffect for m in unused_methods],
                    label="Viable but not selected",
                    color="red",
                    s=60,
                    zorder=3
                )

                for m in unused_methods:
                    ax.annotate(
                        f"{m.subType}",
                        xy=(m.mac, m.sideEffect),
                        xytext=(6, 6),
                        textcoords="offset points",
                        ha="left",
                        va="bottom",
                        fontsize=9,
                        color="black",
                        bbox=dict(boxstyle="round,pad=0.2", fc="none", ec="none", alpha=0.85),
                        zorder=5
                    )

             # --- Proper limits that include scatter collections ---
            xs_all = [float(m.mac) for m in viable_methods]
            ys_all = [float(m.sideEffect) for m in viable_methods]

            # Fallback in case list is empty (shouldn't happen)
            xmax = max(xs_all) if xs_all else 1.0
            ymax = max(ys_all) if ys_all else 1.0

            pad_x = 0.05 * xmax if xmax > 0 else 1.0
            pad_y = 0.08 * ymax if ymax > 0 else 1.0

            ax.set_xlim(0, xmax + pad_x)
            ax.set_ylim(0, ymax + pad_y)

            plt.xlabel("MAC (€/tCO₂)")
            plt.ylabel("δ(m)")
            plt.title("Pareto Optimization Results")
            plt.legend()
            plt.tight_layout()

            output_path = os.path.join(output_dir, "pareto_optimization_results.png")
            plt.savefig(output_path, dpi=200, bbox_inches="tight")
            plt.close()

            print(f"\nSaved final plot: {output_path}")

    print("\n--- Final Pareto Portfolio ---")

    for i, e in enumerate(portfolio, start=1):
        m = e["method"]
        status = "PARTIAL" if e["partial"] else "FULL"
        print(
            f"{i}. {m.mainType} ({m.subType}) [{status}] | "
            f"MAC: {e['mac']} | "
            f"Impl: {e['actual_contribution']:.2f} Gt | "
            f"Round: {e['round']}"
        )

    print(f"\nTotal installed capacity: {installed:.2f} Gt in {round_idx} rounds.")

    return portfolio

def lexicographic_opt_iterative(SDR, SCC, start_year, current_year, viable_methods, storage_target, duration_years, pass_storage_potential, max_iterations=1000):
    sp = pass_storage_potential
    geo_store_counter = 0
    if not viable_methods:
        print("No viable methods provided.")
        return []

    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)

    remaining_methods = viable_methods.copy()
    lg_methods = []
    installed_capacity = 0

    step_macs = []
    step_side_effects = []

    iterations = 0

    while remaining_methods and installed_capacity < storage_target and iterations < max_iterations:
        iterations += 1
        lg_canidate = None
        for m in remaining_methods:
            dominated = False
            for other in remaining_methods:
                if other is m:
                    continue
                if other.mac < m.mac or (other.mac == m.mac and other.sideEffect > m.sideEffect):
                    dominated = True
                    break
            if not dominated:
                lg_canidate = m
                break

        if lg_canidate is None:
            print("No lexicographic-dominant method found. Stopping loop.")
            break
        annual_gt = min(lg_canidate.maxRemove, lg_canidate.sideEffectMax)
        if annual_gt <= 0:
            print(f"{lg_canidate.mainType} ({lg_canidate.subType}) has non-positive annual_gt. Skipping.")
            remaining_methods.remove(lg_canidate)
            continue

        # "Full feasible" contribution over the horizon (Gt)
        contribution = annual_gt * duration_years
        actual_contribution = contribution
        partial = False 
         
        #test for geological storage constraint
        if lg_canidate.storageType == "geological formations":
            remaining_sp = sp - geo_store_counter
            if remaining_sp <= 0:
                print("Geological storage potential exhausted. Method cannot be implemented.")
                remaining_methods.remove(lg_canidate)
                continue
            actual_contribution = min(actual_contribution, remaining_sp)

        remaining_capacity = storage_target - installed_capacity
        if remaining_capacity <= 0:
            print("Storage target met. Stopping selection.")
            break

        actual_contribution = min(actual_contribution, remaining_capacity)
        
        # PV calcuation based on actual contributions
        annual_gt = min(lg_canidate.maxRemove, lg_canidate.sideEffectMax)
        if annual_gt <= 0:
            pv_net = 0.0
        else:
            r = float(SDR) / 100.0
            GT_TO_T = 1e9

            net_per_ton = (SCC - float(lg_canidate.mac))  # SCC - MAC
            pv_net = 0.0

            remaining_gt = actual_contribution
            y = 0

            while remaining_gt > 0 and y < duration_years:
                year = start_year + y
                t = year - current_year
                if t < 0:
                    y += 1
                    continue

                implemented_gt = annual_gt if remaining_gt >= annual_gt else remaining_gt
                remaining_gt -= implemented_gt

                discount_factor = (1 + r) ** t
                tons = implemented_gt * GT_TO_T

                pv_net += (tons * net_per_ton) / discount_factor

                y += 1

            if remaining_gt > 0:
                print(
                    f"Warning: {lg_canidate.mainType} ({lg_canidate.subType}) "
                    f"could not deliver full actual_contribution within duration_years. "
                    f"Undelivered: {remaining_gt:.4f} Gt"
                )
        if actual_contribution < contribution:
            partial = True

        installed_capacity += actual_contribution

        if lg_canidate.storageType == "geological formations":
            geo_store_counter += actual_contribution

        lg_methods.append({
            "method": lg_canidate,
            "actual_contribution": actual_contribution,
            "mac": lg_canidate.mac,
            "partial": partial,
            "pv_net": pv_net,
        })

        status = "PARTIAL" if partial else "FULL"

        print(
            f"Iteration {iterations}: Added {lg_canidate.mainType} "
            f"({lg_canidate.subType}) [{status}] | "
            f"MAC: {lg_canidate.mac} €/tCO₂ | "
            f"Contribution: {actual_contribution:.2f} Gt | "
            f"Cumulative capacity: {installed_capacity:.2f} Gt"
        )

        step_macs.append(lg_canidate.mac)
        step_side_effects.append(lg_canidate.sideEffect)

        remaining_methods.remove(lg_canidate)

        if installed_capacity >= storage_target:
            print("Storage target met. Stopping selection.")
            break

        if not remaining_methods:
            print("Viable methods exhausted, maximum storage capacity reached.")
            break


    plt.figure(figsize=(10, 6))
    ax = plt.gca()
    def _mkey(m):
        return (getattr(m, "mainType", None), getattr(m, "subType", None))

    selected_keys = {_mkey(e["method"]) for e in lg_methods}
    unused_methods = [m for m in viable_methods if _mkey(m) not in selected_keys]

    if unused_methods:
        ax.scatter(
            [m.mac for m in unused_methods],
            [m.sideEffect for m in unused_methods],
            label="Viable but not selected",
            color="red",
            s=60,
            zorder=2
        )

        for m in unused_methods:
            ax.annotate(
                f"{m.subType}",
                xy=(m.mac, m.sideEffect),
                xytext=(6, 6),
                textcoords="offset points",
                ha="left",
                va="bottom",
                fontsize=9,
                color="black",
                bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.85),
                zorder=3
            )

    step_macs = [entry["mac"] for entry in lg_methods]
    step_side_effects = [entry["method"].sideEffect for entry in lg_methods]

    plt.plot(step_macs, step_side_effects,
         color="black", marker="o",
         label="Lexicographic selection")

    offsets = [(8, 8), (8, -10), (-12, 8), (-12, -10), (12, 0), (-14, 0)]

    for i, entry in enumerate(lg_methods):

        dx, dy = offsets[i % len(offsets)]

        subtype = entry["method"].subType

        label = f"{subtype}"

        plt.annotate(
            label,
            xy=(entry["mac"], entry["method"].sideEffect),
            xytext=(dx, dy),
            textcoords="offset points",
            ha="center",
            va="center",
            fontsize=9,
            color="black",
            bbox=dict(
                boxstyle="round,pad=0.25",
                fc="none",
                ec="none",
                alpha=0.9
            ),
            zorder=5
        )

    for i in range(1, len(step_macs)):
        plt.annotate(
            "",
            xy=(step_macs[i], step_side_effects[i]),
            xytext=(step_macs[i-1], step_side_effects[i-1]),
            arrowprops=dict(arrowstyle="-|>", color="black", lw=1.2, alpha=0.9, mutation_scale=15),
            zorder=4

    )
    # --- Proper limits that include scatter collections ---
    xs_all = [float(m.mac) for m in viable_methods]
    ys_all = [float(m.sideEffect) for m in viable_methods]

    # Fallback in case list is empty (shouldn't happen)
    xmax = max(xs_all) if xs_all else 1.0
    ymax = max(ys_all) if ys_all else 1.0

    pad_x = 0.05 * xmax if xmax > 0 else 1.0
    pad_y = 0.08 * ymax if ymax > 0 else 1.0

    ax.set_xlim(0, xmax + pad_x)
    ax.set_ylim(0, ymax + pad_y)
    
    plt.xlabel("MAC (€/tCO₂)")
    plt.ylabel("δ(m)")
    plt.title("Lexicographic Optimization Results")
    plt.legend()

    output_path = os.path.join(output_dir, "lexicographic_opt.png")
    plt.savefig(output_path)
    plt.close()

    print("\n--- Final Lexicographic-Optimal Portfolio ---")
    for entry in lg_methods:
        m = entry["method"]
        print(
            f"{m.mainType} ({m.subType}) | "
            f"MAC: {entry['mac']} €/tCO₂ | "
            f"Implemented: {entry['actual_contribution']:.2f} Gt | "
            f"Side effect: {m.sideEffect}"
        )

    print(f"\nLexicographic Optimization plot saved to: {output_path}")
    print(f"Total installed capacity: {installed_capacity:.2f} Gt after {iterations} iterations.")

    return lg_methods

def marginal_abatement_cost_curve_pareto(portfolio, storage_target, start_year, duration_years, SDR, current_year):

    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)

    if not portfolio:
        print("No Pareto methods provided.")
        return [], []

    # Keep original implementation order
    entries = [e for e in portfolio if e.get("actual_contribution", 0) and e["actual_contribution"] > 0]

    edges = [0.0]   # x bin edges
    heights = []    # y step heights (mac)
    mids = []       # midpoints for markers/labels
    used_entries = []

    installed = 0.0

    round_end_x = {}   # round -> cumulative installed at end of that round (capped)
    current_round = None

    for e in entries:
        contrib = float(e["actual_contribution"])
        mac = float(e["mac"])
        r = e.get("round", None)

        remaining = float(storage_target) - installed
        if remaining <= 0:
            break

        contrib = min(contrib, remaining)
        if contrib <= 0:
            continue

        x0 = edges[-1]
        installed += contrib
        x1 = installed

        edges.append(x1)
        heights.append(mac)
        mids.append((x0 + x1) / 2)

        used_entries.append({**e, "actual_contribution": contrib})

        # record round boundary as we go
        if r is not None:
            current_round = r
            round_end_x[r] = x1  # overwritten until the last method of that round => end boundary

    if not heights:
        print("Warning: No positive contributions available for MAC curve.")
        return [], []
    r = float(SDR) / 100.0
    start_offset = start_year - current_year
    total_cost_eur = 0.0

    for e in used_entries:
        mac = float(e["mac"])
        q_gt = float(e["actual_contribution"])
        total_cost_eur += mac * q_gt * 1e9  # Gt → t

    # Spread cost evenly over duration
    annual_cost = total_cost_eur / duration_years

    discounted_cost = 0.0
    for t in range(duration_years):
        k = start_offset + t
        discounted_cost += annual_cost / ((1 + r) ** k)

    print(f"\nUndiscounted cost: {total_cost_eur:,.2e} €")
    print(f"Present Value cost of Pareto optimal portfolio: {discounted_cost:,.2e} €")
    

    # Plotting
    plt.figure(figsize=(12, 7))
    ax = plt.gca()

    #color coding
    rounds_sorted = sorted(round_end_x.keys())
    cmap = plt.get_cmap("tab10")
    round_colors = {r: cmap(i % 10) for i, r in enumerate(rounds_sorted)}

    #colored segments
    for i, e in enumerate(used_entries):
        r = e["round"]
        color = round_colors[r]

        x0 = edges[i]
        x1 = edges[i + 1]
        y = heights[i]

        # Horizontal segment
        ax.plot([x0, x1], [y, y], color=color, linewidth=2.5)

        # Vertical jump
        if i > 0:
            ax.plot([x0, x0], [heights[i - 1], y], color=color, linewidth=2.0)
        subtype = e["method"].subType
        label = f"{subtype}"
        ax.annotate(
            label,
            xy=(mids[i], y),
            xytext=(0, 8),
            textcoords="offset points",
            ha="center",
            fontsize=10,
            bbox=dict(
                boxstyle="round,pad=0.25",
                fc="none",
                ec="none",
                alpha=0.9
            ),
            zorder=6
        )

    ax.scatter(mids, heights, s=60, zorder=5, color="black")
    for r in rounds_sorted:
        x = round_end_x[r]
        ax.axvline(
            x=x,
            linestyle="--",
            linewidth=1.3,
            color=round_colors[r],
            alpha=0.7
        )
    ax.relim()
    ax.autoscale_view()
    ax.set_xlim(left=0)
    ax.set_ylim(bottom=0)

    ax.set_xlabel("Cumulative Storage Capacity (Gt CO₂)", fontsize=12)
    ax.set_ylabel("Marginal Abatement Cost (€/tCO₂)", fontsize=12)
    ax.set_title("MACC: Pareto Optimized Portfolio", fontsize=14)
    ax.grid(True, alpha=0.25)
    # ---- Legend ----
    legend_elements = [
    Line2D([0], [0], color=round_colors[r], lw=3, label=f"Pareto level {r}")
        for r in rounds_sorted
    ]

    ax.legend(handles=legend_elements, title="Pareto Levels")
    plt.tight_layout()

    output_path = os.path.join(output_dir, "marginal_abatement_cost_curve_pareto.png")
    plt.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close()

    print(f"MAC curve saved to: {output_path}")
    print(f"Final installed capacity: {edges[-1]:.2f} Gt")

    return edges[1:], heights

def marginal_abatement_cost_curve(lg_methods, storage_target, start_year, duration_years, SDR, current_year):
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)

    if not lg_methods:
        print("No Lexicographic methods provided.")
        return [], []

    # Keep only positive contributions
    entries = [e for e in lg_methods if e.get("actual_contribution", 0) > 0]

    # Optional economic ordering

    edges = [0.0]
    heights = []
    mids = []
    used_entries = []

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

        x0 = edges[-1]
        installed += contrib
        x1 = installed

        edges.append(x1)
        heights.append(mac)
        mids.append((x0 + x1) / 2)

        used_entries.append({**e, "actual_contribution": contrib})

    if not heights:
        print("Warning: No positive contributions available for MAC curve.")
        return [], []
    #present value costs of portfolio
    r = float(SDR) / 100.0
    start_offset = start_year - current_year
    total_cost_eur = 0.0

    for e in used_entries:
        mac = float(e["mac"])
        q_gt = float(e["actual_contribution"])
        total_cost_eur += mac * q_gt * 1e9  # Gt → t

    # Spread cost evenly over duration
    annual_cost = total_cost_eur / duration_years

    discounted_cost = 0.0
    for t in range(duration_years):
        k = start_offset + t
        discounted_cost += annual_cost / ((1 + r) ** k)

    print(f"\nUndiscounted cost: {total_cost_eur:,.2e} €")
    print(f"Present Value cost of Lexicographic portfolio: {discounted_cost:,.2e} €")
    
    #Plot
    plt.figure(figsize=(12, 7))
    ax = plt.gca()

    #stepwise
    xs = [0]
    ys = [heights[0]]

    for i in range(len(heights)):
        #horizontal segment
        xs.append(edges[i + 1])
        ys.append(heights[i])
        #vertical jumps
        if i + 1 < len(heights):
            xs.append(edges[i + 1])
            ys.append(heights[i + 1])

    ax.plot(xs, ys, linewidth=2.2)

    #Midpoints
    ax.scatter(mids, heights, s=55, zorder=5)

    #Labels
    for i, e in enumerate(used_entries):
        subtype = e["method"].subType
        label = f"{subtype}"

        ax.annotate(
            label,
            (mids[i], heights[i]),
            xytext=(0, 8),
            textcoords="offset points",
            ha="center",
            fontsize=10,
            bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="none", alpha=0.9)
        )

    #Formatting
    ax.set_xlim(left=0)
    ax.set_ylim(bottom=0)
    ax.margins(x=0)
    ax.set_xlabel("Cumulative Storage Capacity (Gt CO₂)")
    ax.set_ylabel("Marginal Abatement Cost (€/tCO₂)")
    ax.grid(True, alpha=0.25)

    plt.tight_layout()

    output_path = os.path.join(output_dir, "marginal_abatement_cost_curve.png")
    plt.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close()

    print(f"MAC curve saved to: {output_path}")
    print(f"Final installed capacity: {installed:.2f} Gt")

    return edges[1:], heights
