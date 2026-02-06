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
        return True
    else:
        print("Storage target exceeds regional storage potential.")
        return False


#def is_method_viable(cdr_methods, SCC, SDR):
    #viableMethods = []
    #for m in cdr_methods:
        #if(cdr_methods[m].)
