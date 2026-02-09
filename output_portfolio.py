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

        # Find current Pareto-dominant method
        pareto_candidate = None
        for m in remaining_methods:
            dominated = False
            for other in remaining_methods:
                if other is m:
                    continue
                # Dominance: lower MAC or equal MAC but higher side effect
                if other.mac < m.mac or (other.mac == m.mac and other.sideEffect > m.sideEffect):
                    dominated = True
                    break
            if not dominated:
                pareto_candidate = m
                break

        if pareto_candidate is None:
            print("No Pareto-dominant method found. Stopping loop.")
            break

        # Add method to frontier
        pareto_methods.append(pareto_candidate)
        contribution = pareto_candidate.sideEffectMax * duration_years
        if(m.storageType == "geological formations"):
            geo_store_counter+= contribution
            if geo_store_counter > sp:
                print(f"Reached geological storage potential limit of {sp} Gt. Stopping selection of geological storage methods.")
                pareto_methods.remove(pareto_candidate)
                break

        installed_capacity += contribution

        print(f"Iteration {iterations}: Added {pareto_candidate.mainType} ({pareto_candidate.subType}) "
              f"MAC: {pareto_candidate.mac} €/tCO₂, Side effect: {pareto_candidate.sideEffect}, "
              f"Cumulative capacity: {installed_capacity:.2f} Gt")

        step_macs.append(pareto_candidate.mac)
        step_side_effects.append(pareto_candidate.sideEffect)

        remaining_methods.remove(pareto_candidate)

        if installed_capacity >= storage_target:
            print("Storage target met. Stopping selection.")
            break

    # ---- Plotting ----
    plt.figure(figsize=(10, 6))

    # All viable methods
    plt.scatter([m.mac for m in viable_methods], [m.sideEffect for m in viable_methods],
                label="All viable methods", color="lightgray")

    # Viable but not selected
    unused_methods = [m for m in viable_methods if m not in pareto_methods]
    if unused_methods:
        plt.scatter([m.mac for m in unused_methods], [m.sideEffect for m in unused_methods],
                    label="Viable but not selected", color="orange", s=60)

    # Pareto frontier points
    plt.scatter([m.mac for m in pareto_methods], [m.sideEffect for m in pareto_methods],
                label="Pareto frontier", color="blue", s=80)

    # Stepwise cumulative line with arrows
    plt.plot(step_macs, step_step_effects := step_side_effects, color="red", linestyle="--", marker="o",
             label="Stepwise selection")

    # Add arrows and step numbers
    for i in range(1, len(step_macs)):
        plt.annotate("",
                     xy=(step_macs[i], step_side_effects[i]),
                     xytext=(step_macs[i-1], step_side_effects[i-1]),
                     arrowprops=dict(arrowstyle="->", color="red", lw=1.5))
        # Step number annotation
        plt.text(step_macs[i], step_side_effects[i]+0.5, str(i+1), color="red", fontsize=9)

    plt.xlabel("Cost per ton of CO₂ removed (€/tCO₂)")
    plt.ylabel("Side effect")
    plt.title("Pareto Frontier")
    plt.legend()

    output_path = os.path.join(output_dir, "pareto_frontier_iterative_with_unused.png")
    plt.savefig(output_path)
    plt.close()

    # ---- Console output ----
    print("\n--- Final Pareto-Optimal CDR Methods ---")
    for m in pareto_methods:
        print(
            f"{m.mainType} ({m.subType}) | "
            f"MAC: {m.mac} €/tCO₂ | "
            f"Side-effect constrained max: {m.sideEffectMax} Gt | "
            f"Side effect: {m.sideEffect}"
        )

    print(f"\nStepwise Pareto frontier plot saved to: {output_path}")
    print(f"Total installed capacity: {installed_capacity:.2f} Gt after {iterations} iterations.")

    return pareto_methods
