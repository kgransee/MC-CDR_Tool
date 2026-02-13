import os
import matplotlib.pyplot as plt

def _allocate_equal_among_front(front_methods, remaining_target, duration_years, sp, geo_used):

    remaining_target = float(remaining_target)

    n = len(front_methods)
    allocations = [0.0] * n

    # Compute caps per method
    caps = []
    for m in front_methods:
        cap = float(m.sideEffectMax) * float(duration_years)

        if getattr(m, "storageType", None) == "geological formations":
            cap = min(cap, max(0.0, float(sp) - float(geo_used)))

        caps.append(max(0.0, cap))

    active = [i for i in range(n) if caps[i] > 0.0]

    # Progressive equal allocation
    while active and remaining_target > 1e-12:

        share = remaining_target / len(active)
        progressed = False

        for i in active[:]:

            take = min(share, caps[i])

            if take > 0:
                allocations[i] += take
                remaining_target -= take
                caps[i] -= take
                progressed = True

                if getattr(front_methods[i], "storageType", None) == "geological formations":
                    geo_used += take

            if caps[i] <= 1e-12:
                active.remove(i)

        if not progressed:
            break

        # Update geo caps after geo_used changed
        for i in active:
            if getattr(front_methods[i], "storageType", None) == "geological formations":
                caps[i] = min(
                    caps[i],
                    max(0.0, float(sp) - float(geo_used))
                )

    return allocations, geo_used



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


def pareto_portfolio_iterative_layers(
    viable_methods,
    storage_target,
    duration_years,
    pass_storage_potential,
    max_rounds=10_000,
    plot=True,
    plot_rounds_limit=8,
):

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

        allocs, geo_used = _allocate_equal_among_front(
        front_methods=front,
        remaining_target=remaining_target,
        duration_years=duration_years,
        sp=sp,
        geo_used=geo_used
        )

        for idx, m in enumerate(front):
            actual = allocs[idx]
            if actual <= 0:
                remaining.remove(m)
                continue
            installed += actual
            contribution = float(m.sideEffectMax) * float(duration_years)
            partial = actual < contribution or installed >= storage_target
            portfolio.append({
                "method": m,
                "actual_contribution": actual,
                "mac": m.mac,
                "partial": partial,
                "round": round_idx
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
        plt.scatter(
            [m.mac for m in viable_methods],
            [m.sideEffect for m in viable_methods],
            label="All viable methods",
            color="lightgray",
            s=40
        )
        if portfolio:
            rounds = sorted(set(e["round"] for e in portfolio))

            cmap = plt.get_cmap("tab10")  # good for up to 10 rounds
            round_colors = {r: cmap(i % 10) for i, r in enumerate(rounds)}

            for r in rounds:
                xs = [e["mac"] for e in portfolio if e["round"] == r]
                ys = [e["method"].sideEffect for e in portfolio if e["round"] == r]

                plt.scatter(
                    xs,
                    ys,
                    label=f"Pareto layer {r}",
                    color=round_colors[r],
                    s=85,
                    zorder=4
                )

            xs_all = [e["mac"] for e in portfolio]
            ys_all = [e["method"].sideEffect for e in portfolio]
    
            ax = plt.gca()
            ax.margins(x=0.05, y=0.08)

            offsets = [(8, 8), (8, -10), (-12, 8), (-12, -10), (12, 0), (-14, 0)]

            for i, entry in enumerate(portfolio):

                x = entry["mac"]
                y = entry["method"].sideEffect
                r = entry["round"]

                label = str(r)
                if entry["partial"]:
                    label += " (P)"

                dx, dy = offsets[i % len(offsets)]

                plt.annotate(
                    label,
                    xy=(x, y),
                    xytext=(dx, dy),
                    textcoords="offset points",
                    ha="center",
                    va="center",
                    fontsize=9,
                    color=round_colors[r],
                    bbox=dict(boxstyle="round,pad=0.2",
                        fc="white",
                        ec="none",
                        alpha=0.85),
                    zorder=6
                )

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

def lexicographic_opt_iterative(viable_methods, storage_target, duration_years, pass_storage_potential, max_iterations=1000):
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

        contribution = lg_canidate.sideEffectMax * duration_years
        actual_contribution = contribution
        partial = False

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

        if actual_contribution < contribution:
            partial = True

        installed_capacity += actual_contribution

        if lg_canidate.storageType == "geological formations":
            geo_store_counter += actual_contribution

        lg_methods.append({
            "method": lg_canidate,
            "actual_contribution": actual_contribution,
            "mac": lg_canidate.mac,
            "partial": partial
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

    plt.scatter([m.mac for m in viable_methods], [m.sideEffect for m in viable_methods],
                label="All viable methods", color="lightgray")

    selected_objects = [entry["method"] for entry in lg_methods]
    unused_methods = [m for m in viable_methods if m not in selected_objects]
    if unused_methods:
        plt.scatter([m.mac for m in unused_methods], [m.sideEffect for m in unused_methods],
                    label="Viable but not selected", color="orange", s=60)

    plt.scatter([entry["mac"] for entry in lg_methods],
            [entry["method"].sideEffect for entry in lg_methods],
            label="Lexicographic selection", color="blue", s=80)

    step_macs = [entry["mac"] for entry in lg_methods]
    step_side_effects = [entry["method"].sideEffect for entry in lg_methods]

    plt.plot(step_macs, step_side_effects,
         color="red", linestyle="--", marker="o",
         label="Stepwise selection")

    ax = plt.gca()
    ax.margins(x=0.05, y=0.08)
    offsets = [(8, 8), (8, -10), (-12, 8), (-12, -10), (12, 0), (-14, 0)]

    for i in range(len(step_macs)):
        dx, dy = offsets[i % len(offsets)]

        plt.annotate(
            str(i + 1),
            xy=(step_macs[i], step_side_effects[i]),
            xytext=(dx, dy),
            textcoords="offset points",
            ha="center", va="center",
            fontsize=9,
            color="red",
            bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.8),
            zorder=5
        )

    for i in range(1, len(step_macs)):
        plt.annotate(
            "",
            xy=(step_macs[i], step_side_effects[i]),
            xytext=(step_macs[i-1], step_side_effects[i-1]),
            arrowprops=dict(arrowstyle="->", color="red", lw=1.2, alpha=0.9),
            zorder=4
    )

    
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


def marginal_abatement_cost_curve(lg_methods, storage_target, sort_by_mac=False):
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)

    if not lg_methods:
        print("No Lexicographic methods provided.")
        return [], []

    entries = [e for e in lg_methods if e["actual_contribution"] and e["actual_contribution"] > 0]

    if sort_by_mac:
        entries = sorted(entries, key=lambda e: (e["mac"], -e["actual_contribution"]))

    edges = [0.0]
    heights = []

    installed = 0.0
    used_entries = []

    for e in entries:
        contrib = float(e["actual_contribution"])
        mac = float(e["mac"])

        remaining = storage_target - installed
        if remaining <= 0:
            break

        contrib = min(contrib, remaining)
        if contrib <= 0:
            continue

        installed += contrib
        edges.append(installed)
        heights.append(mac)

        used_entries.append({**e, "actual_contribution": contrib})

    if not heights:
        print("Warning: No positive contributions available for MAC curve.")
        return [], []

    plt.figure(figsize=(10, 6))

    try:
        plt.stairs(heights, edges, fill=False)
    except AttributeError:
        xs = [edges[0]]
        ys = [heights[0]]
        for i in range(len(heights)):
            xs += [edges[i+1]]
            ys += [heights[i]]
            if i + 1 < len(heights):
                xs += [edges[i+1]]
                ys += [heights[i+1]]
        plt.plot(xs, ys)

    mids = [(edges[i] + edges[i+1]) / 2 for i in range(len(heights))]
    plt.scatter(mids, heights)

    for i, e in enumerate(used_entries):
        label = f"{i+1}" + (" (P)" if e.get("partial") else "")
        plt.annotate(label, (mids[i], heights[i]), xytext=(0, 6), textcoords="offset points",
                     ha="center", fontsize=9)

    plt.xlabel("Cumulative Storage Capacity (Gt CO₂)")
    plt.ylabel("Marginal Abatement Cost (€/tCO₂)")
    plt.title("Marginal Abatement Cost Curve for Selected CDR Portfolio")
    plt.grid(True)

    output_path = os.path.join(output_dir, "marginal_abatement_cost_curve.png")
    plt.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close()

    print(f"MAC curve saved to: {output_path}")
    print(f"Final installed capacity: {installed:.2f} Gt")

    return edges[1:], heights

def marginal_abatement_cost_curve_pareto(portfolio, storage_target):
 
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    if not portfolio:
        print("No Pareto methods provided.")
        return [], []
    entries = [e for e in portfolio if e["actual_contribution"] > 0]
    edges = [0.0]
    heights = []
    installed = 0.0
    used_entries = []

    for e in entries:
        contrib = float(e["actual_contribution"])
        mac = float(e["mac"])
        remaining = storage_target - installed
        if remaining <= 0:
            break
        contrib = min(contrib, remaining)
        if contrib <= 0:
            continue
        installed += contrib
        edges.append(installed)
        heights.append(mac)

        used_entries.append({
            **e,
            "actual_contribution": contrib
        })

    if not heights:
        print("Warning: No positive contributions available for MAC curve.")
        return [], []

    plt.figure(figsize=(10, 6))

    try:
        plt.stairs(heights, edges, fill=False)
    except AttributeError:
        xs = [edges[0]]
        ys = [heights[0]]
        for i in range(len(heights)):
            xs += [edges[i+1]]
            ys += [heights[i]]
            if i + 1 < len(heights):
                xs += [edges[i+1]]
                ys += [heights[i+1]]
        plt.plot(xs, ys)

    mids = [(edges[i] + edges[i+1]) / 2 for i in range(len(heights))]
    plt.scatter(mids, heights)

    for i, e in enumerate(used_entries):
        label = f"{i+1}"
        if e.get("partial"):
            label += " (P)"

        plt.annotate(
            label,
            (mids[i], heights[i]),
            xytext=(0, 6),
            textcoords="offset points",
            ha="center",
            fontsize=9
        )

    plt.xlabel("Cumulative Storage Capacity (Gt CO₂)")
    plt.ylabel("Marginal Abatement Cost (€/tCO₂)")
    plt.title("Marginal Abatement Cost Curve (Pareto-Layer Order)")
    plt.grid(True)
    plt.tight_layout()

    output_path = os.path.join(output_dir, "marginal_abatement_cost_curve_pareto.png")
    plt.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close()

    print(f"MAC curve saved to: {output_path}")
    print(f"Final installed capacity: {installed:.2f} Gt")

    return edges[1:], heights
