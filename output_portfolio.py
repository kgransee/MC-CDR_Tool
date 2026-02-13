import os
import matplotlib.pyplot as plt

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

    for i in range(1, len(step_macs)):
        plt.annotate("",
                     xy=(step_macs[i], step_side_effects[i]),
                     xytext=(step_macs[i-1], step_side_effects[i-1]),
                     arrowprops=dict(arrowstyle="->", color="red", lw=1.5))
        plt.text(step_macs[i], step_side_effects[i]+0.5, str(i+1), color="red", fontsize=9)

    plt.xlabel("Cost per ton of CO₂ removed (€/tCO₂)")
    plt.ylabel("Side effect")
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

    # Filter usable entries
    entries = [e for e in lg_methods if e["actual_contribution"] and e["actual_contribution"] > 0]

    # Typical MAC curve: order by increasing MAC (and optional tie-breaker)
    if sort_by_mac:
        entries = sorted(entries, key=lambda e: (e["mac"], -e["actual_contribution"]))

    # Build bin edges (x) and heights (y)
    edges = [0.0]
    heights = []

    installed = 0.0
    used_entries = []

    for e in entries:
        contrib = float(e["actual_contribution"])
        mac = float(e["mac"])

        # Cap at storage_target
        remaining = storage_target - installed
        if remaining <= 0:
            break

        contrib = min(contrib, remaining)
        if contrib <= 0:
            continue

        installed += contrib
        edges.append(installed)
        heights.append(mac)

        # keep a version for labels (respecting capping)
        used_entries.append({**e, "actual_contribution": contrib})

    if not heights:
        print("Warning: No positive contributions available for MAC curve.")
        return [], []

    plt.figure(figsize=(10, 6))

    # Matplotlib has stairs (nice for MAC curves). If unavailable, we fall back to step logic.
    try:
        plt.stairs(heights, edges, fill=False)
    except AttributeError:
        # Fallback: draw a correct post-step using duplicated points
        xs = [edges[0]]
        ys = [heights[0]]
        for i in range(len(heights)):
            xs += [edges[i+1]]
            ys += [heights[i]]
            if i + 1 < len(heights):
                xs += [edges[i+1]]
                ys += [heights[i+1]]
        plt.plot(xs, ys)

    # Optional: markers at segment midpoints
    mids = [(edges[i] + edges[i+1]) / 2 for i in range(len(heights))]
    plt.scatter(mids, heights)

    # Labels (1, 2, 3...) at midpoints, with a small vertical offset
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

    # Return cumulative endpoints and heights (common outputs)
    return edges[1:], heights
