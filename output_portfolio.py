import os
import matplotlib.pyplot as plt

def pareto_frontier_iterative(viable_methods, storage_target, duration_years, pass_storage_potential, max_iterations=1000):
    sp = pass_storage_potential
    geo_store_counter = 0
    if not viable_methods:
        print("No viable methods provided.")
        return []

    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)

    remaining_methods = viable_methods.copy()
    pareto_methods = []
    installed_capacity = 0

    step_macs = []
    step_side_effects = []

    iterations = 0

    while remaining_methods and installed_capacity < storage_target and iterations < max_iterations:
        iterations += 1
        pareto_candidate = None
        for m in remaining_methods:
            dominated = False
            for other in remaining_methods:
                if other is m:
                    continue
                if other.mac < m.mac or (other.mac == m.mac and other.sideEffect > m.sideEffect):
                    dominated = True
                    break
            if not dominated:
                pareto_candidate = m
                break

        if pareto_candidate is None:
            print("No Pareto-dominant method found. Stopping loop.")
            break

        contribution = pareto_candidate.sideEffectMax * duration_years
        actual_contribution = contribution
        partial = False

        if pareto_candidate.storageType == "geological formations":
            remaining_sp = sp - geo_store_counter
            if remaining_sp <= 0:
                print("Geological storage potential exhausted. Method cannot be implemented.")
                remaining_methods.remove(pareto_candidate)
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

        if pareto_candidate.storageType == "geological formations":
            geo_store_counter += actual_contribution

        pareto_methods.append({
            "method": pareto_candidate,
            "actual_contribution": actual_contribution,
            "mac": pareto_candidate.mac,
            "partial": partial
        })

        status = "PARTIAL" if partial else "FULL"

        print(
            f"Iteration {iterations}: Added {pareto_candidate.mainType} "
            f"({pareto_candidate.subType}) [{status}] | "
            f"MAC: {pareto_candidate.mac} €/tCO₂ | "
            f"Contribution: {actual_contribution:.2f} Gt | "
            f"Cumulative capacity: {installed_capacity:.2f} Gt"
        )

        step_macs.append(pareto_candidate.mac)
        step_side_effects.append(pareto_candidate.sideEffect)

        remaining_methods.remove(pareto_candidate)

        if installed_capacity >= storage_target:
            print("Storage target met. Stopping selection.")
            break

        if not remaining_methods:
            print("Viable methods exhausted, maximum storage capacity reached.")
            break


    plt.figure(figsize=(10, 6))

    plt.scatter([m.mac for m in viable_methods], [m.sideEffect for m in viable_methods],
                label="All viable methods", color="lightgray")

    selected_objects = [entry["method"] for entry in pareto_methods]
    unused_methods = [m for m in viable_methods if m not in selected_objects]
    if unused_methods:
        plt.scatter([m.mac for m in unused_methods], [m.sideEffect for m in unused_methods],
                    label="Viable but not selected", color="orange", s=60)

    plt.scatter([entry["mac"] for entry in pareto_methods],
            [entry["method"].sideEffect for entry in pareto_methods],
            label="Pareto frontier", color="blue", s=80)

    step_macs = [entry["mac"] for entry in pareto_methods]
    step_side_effects = [entry["method"].sideEffect for entry in pareto_methods]

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
    plt.title("Lexicographic Optimization Results - Stepwise Pareto Frontier")
    plt.legend()

    output_path = os.path.join(output_dir, "lexicographic_opt_pareto_frontier.png")
    plt.savefig(output_path)
    plt.close()

    # ---- Console output ----
    print("\n--- Final Pareto-Optimal Portfolio ---")
    for entry in pareto_methods:
        m = entry["method"]
        print(
            f"{m.mainType} ({m.subType}) | "
            f"MAC: {entry['mac']} €/tCO₂ | "
            f"Implemented: {entry['actual_contribution']:.2f} Gt | "
            f"Side effect: {m.sideEffect}"
        )

    print(f"\nLexicographic Stepwise Pareto frontier plot saved to: {output_path}")
    print(f"Total installed capacity: {installed_capacity:.2f} Gt after {iterations} iterations.")

    return pareto_methods

import os
import matplotlib.pyplot as plt


def marginal_abatement_cost_curve(pareto_methods, storage_target):
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    
    if not pareto_methods:
        print("No Pareto methods provided.")
        return [], []

    os.makedirs(output_dir, exist_ok=True)

    cumulative_storage = []
    mac_values = []

    installed_capacity = 0

    for entry in pareto_methods:

        contribution = entry["actual_contribution"]
        mac = entry["mac"]

        if contribution <= 0:
            continue

        installed_capacity += contribution
        cumulative_storage.append(installed_capacity)
        mac_values.append(mac)

        if installed_capacity >= storage_target:
            break

    plt.figure(figsize=(10, 6))

    if mac_values:
        x_values = [0] + cumulative_storage
        y_values = [mac_values[0]] + mac_values
        plt.step(x_values, y_values, where='post')
        plt.scatter(cumulative_storage, mac_values)

        for i, entry in enumerate(pareto_methods[:len(cumulative_storage)]):
            label = f"{i+1}"
            if entry["partial"]:
                label += " (P)"
            plt.text(
                cumulative_storage[i],
                mac_values[i],
                label,
                fontsize=9
            )

    else:
        print("Warning: No positive contributions available for MAC curve.")

    plt.xlabel("Cumulative Storage Capacity (Gt CO₂)")
    plt.ylabel("Marginal Abatement Cost (€/tCO₂)")
    plt.title("Marginal Abatement Cost Curve for Selected CDR Portfolio")
    plt.grid(True)

    output_path = os.path.join(output_dir, "marginal_abatement_cost_curve.png")
    plt.savefig(output_path)
    plt.close()

    print(f"MAC curve saved to: {output_path}")
    print(f"Final installed capacity: {installed_capacity:.2f} Gt")

    return cumulative_storage, mac_values
