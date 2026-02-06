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
  
    viableMethods = []
    GT_TO_T = 1e9  # 1 Gt = 1e9 tCO₂

    for m in cdr_methods:
        name = f"{m.mainType} ({m.subType})"

        sideEffect = m.sideEffect
        sideEffectMax = m.sideEffectMax  # in Gt
        MAC = m.mac  # €/tCO₂
        initialCost = m.initialCost  # Euro

        # 1. Constraint: side effect must be non-negative
        if sideEffect < 0:
            print(f"{name} is not viable: side effect is negative ({sideEffect}).")
            continue

        # 2. Constraint: side-effect constrained capacity must be non-negative
        if sideEffectMax < 0:
            print(f"{name} is not viable: side-effect constrained capacity is negative.")
            continue

        # 3. Constraint: MAC must be less than SCC
        if MAC >= SCC:
            print(f"{name} is not viable: MAC ({MAC} €/tCO₂) >= SCC ({SCC} €/tCO₂).")
            continue

        # 4. Discounted total benefit calculation
        sideEffectMax_tons = sideEffectMax * GT_TO_T
        total_benefit = 0

        for year_offset in range(duration_years):
            t = (start_year + year_offset) - current_year
            if t < 0:
                print(f"Warning: {name} has removals in the past (year {start_year + year_offset}). Ignoring those years.")
                continue
            discounted_benefit = (sideEffectMax_tons * SCC) / (1 + SDR)**t
            total_benefit += discounted_benefit

        # 5. Total cost (assuming initial cost today + MAC * sideEffectMax)
        total_cost = initialCost + (MAC * sideEffectMax_tons)
        discounted_total_cost = total_cost / (1 + SDR)**max(0, start_year - current_year)

        # 6. Viability check
        if total_benefit >= discounted_total_cost:
            viableMethods.append(m)
        else:
            print(
                f"{name} is not viable: total discounted benefit ({total_benefit:.2e}) "
                f"is less than discounted total cost ({discounted_total_cost:.2e})."
            )

    return viableMethods


