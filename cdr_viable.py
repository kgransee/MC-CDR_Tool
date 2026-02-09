#take in input from main.py, which is the list, cdr_methods
import pandas as pd
from pathlib import Path
def read_storage_potential(excel_path="Storage_Data.xlsx"):
    if excel_path is None:
        # Path to this file → project root → Excel file
        project_root = Path(__file__).resolve().parent
        excel_path = project_root / "Storage_Data.xlsx"
    # Read sheets
    europe_df = pd.read_excel(excel_path, sheet_name="Europe")
    northam_df = pd.read_excel(excel_path, sheet_name="NorthAm")

    # Sum storage potentials
    EuropeanStoragePotential = europe_df["Potential Storage (Gt)"].sum()
    NorthAmericanStoragePotential = northam_df["Potential Storage (Gt)"].sum()

    return EuropeanStoragePotential, NorthAmericanStoragePotential

def check_storage_feasibility(removal_target, european_potential, north_american_potential):
    region = removal_target["region"]
    target = removal_target["storage_target"]

    if region == "Europe":
        available = european_potential
    elif region == "North America":
        available = north_american_potential
    else:
        raise ValueError(f"Unknown region: {region}")

    print(f"\n--- Storage Feasibility Check ({region}) ---")
    print(f"Requested storage target: {target} Gt")
    print(f"Available storage potential: {available} Gt")

    if target <= available:
        print("Storage target is feasible within regional potential.")
        return target
    else:
        print("Storage target exceeds regional storage potential.")

        while True:
            try:
                new_target = float(
                    input(f"Please redefine the storage target (≤ {available} Gt): ")
                )
                if new_target <= available:
                    print("Updated storage target is feasible.")
                    removal_target["storage_target"] = new_target
                    return new_target
                else:
                    print("Still exceeds available potential. Please correct the input.")
            except ValueError:
                print("Invalid input. Please enter a numeric value.")

def is_method_viable(cdr_methods, SCC, SDR, start_year, duration_years, current_year):

    viable_methods = []
    GT_TO_T = 1e9  # 1 Gt = 1e9 tCO₂

    for m in cdr_methods:
        name = f"{m.mainType} ({m.subType})"

        MAC = m.mac                      
        SCC = SCC                        
        annual_gt = m.sideEffectMax      
        initial_cost = m.initialCost  
        side_effect = m.sideEffect

        # --- Constraints ---
        if side_effect < 0:
            print(f"{name} is not viable: negative side effect ({side_effect}).")
            continue

        if annual_gt <= 0:
            print(f"{name} is not viable: non-positive removal capacity.")
            continue

        if MAC >= SCC:
            print(f"{name} is not viable: MAC ≥ SCC.")
            continue

        annual_tons = annual_gt * GT_TO_T

        discounted_benefit = 0.0
        discounted_cost = 0.0

        for y in range(duration_years):
            year = start_year + y
            t = year - current_year

            if t < 0:
                print(f"Warning: {name} has removals in the past ({year}). Skipping.")
                continue

            discount_factor = (1 + SDR) ** t

            yearly_benefit = annual_tons * SCC
            yearly_cost = annual_tons * MAC

            discounted_benefit += yearly_benefit / discount_factor
            discounted_cost += yearly_cost / discount_factor

        # --- Initial cost ---
        if start_year >= current_year:
            discounted_cost += initial_cost / (1 + SDR) ** (start_year - current_year)
        else:
            discounted_cost += initial_cost

        # --- Viability check ---
        if discounted_benefit >= discounted_cost:
            m.discounted_benefit = discounted_benefit
            m.discounted_cost = discounted_cost
            viable_methods.append(m)
        else:
            print(
                f"{name} not viable: "
                f"NPV benefit ({discounted_benefit:.2e}) < "
                f"NPV cost ({discounted_cost:.2e})"
            )

    return viable_methods



