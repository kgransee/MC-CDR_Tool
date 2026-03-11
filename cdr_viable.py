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
    global_df = pd.read_excel(excel_path, sheet_name="Global")

    # Sum storage potentials
    EuropeanStoragePotential = europe_df["Potential Storage (Gt)"].sum()
    NorthAmericanStoragePotential = northam_df["Potential Storage (Gt)"].sum()
    GlobalStoragePotential = global_df["Potential Storage (Gt)"].sum()

    return EuropeanStoragePotential, NorthAmericanStoragePotential, GlobalStoragePotential

def check_storage_feasibility(removal_target, european_potential, north_american_potential, global_potential):
    region = removal_target["region"]
    target = removal_target["storage_target"]

    if region == "Europe":
        available = european_potential
    elif region == "North America":
        available = north_american_potential
    elif region == "Global":
        available = global_potential
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
        #user must enter a new target that is in line with the sustainable storage estimate
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
    GT_TO_T = 1e9  #conversion factor from gigatons to tons

    for m in cdr_methods:
        name = f"{m.mainType} ({m.subType})"

        MAC = m.mac                      
        SCC = SCC                        
        annual_gt = m.sideEffectMax      
        #initial_cost = m.initialCost       initial cost is not included due to the lack of data
        side_effect = m.sideEffect

        #constriants for viability
        #first one makes sure that the expected side effect is not negative
        if side_effect < 0:
            print(f"{name} is not viable: negative side effect ({side_effect}).")
            continue
        #redundant, but makes sure that positive removals exist
        if annual_gt <= 0:
            print(f"{name} is not viable: non-positive removal capacity.")
            continue
        #economic viability check based on the MAC and SCC, if the cost per ton is higher than the social benefit per ton, then the method is not viable
        #this puts dependence on the evaluation of the SCC, a potential low evaluation would then make less methods viable
        if MAC > SCC:
            print(f"{name} is not viable: MAC ≥ SCC.")
            continue
        
        if MAC <= SCC:
            viable_methods.append(m)


    return viable_methods



