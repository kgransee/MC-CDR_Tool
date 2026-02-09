from pathlib import Path
from cdr_method import CDRMethod
import pandas as pd

def get_cdr_from_user():
    print("\nEnter CDR Method Information")
    
    # List of valid main types
    possible_methods = [
        "LULUCF", "SCS", "BC", "BECCS", "DACCS",
        "EW", "PWR", "BCM", "OAE", "OF"
    ]
    
    # Show options for mainType
    print("Select Main Type from the following options:")
    for idx, method in enumerate(possible_methods, start=1):
        print(f"{idx}. {method}")
    
    # User selection for mainType
    while True:
        try:
            selection = int(input(f"Enter the number corresponding to the main type (1-{len(possible_methods)}): "))
            if 1 <= selection <= len(possible_methods):
                mainType = possible_methods[selection - 1]
                break
            else:
                print("Invalid input. Please enter a number within the valid range.")
        except ValueError:
            print("Invalid input. Please enter a number.")

    subType = input("Subtype: ")

    def input_float(prompt):
        while True:
            try:
                return float(input(prompt))
            except ValueError:
                print("Invalid input. Please enter a valid number.")
    
    mac = input_float("Cost per ton of CO2 removed (Euros): ")
    maxRemove = input_float("Maximum CO2 removal capacity (Gt)")
    initialCost = input_float("Initial cost (Euros): ")

    # Input validation for sideEffect
    def input_side_effect():
        while True:
            try:
                value = float(input("Side effect (-100 to 100): "))
                if -100 <= value <= 100:
                    return value
                else:
                    print("Value out of range. Please enter a number between -100 and 100.")
            except ValueError:
                print("Invalid input. Please enter a number.")

    sideEffect = input_side_effect()
    sideEffectMax = input_float("Side-effect constrained maximum removal capacity (Gt): ")

    # Options for storageType
    storage_options = [
        "soils",
        "vegetation",
        "buildings",
        "sediments",
        "geological formations",
        "minerals"
    ]
    print("Select Storage Type from the following options:")
    for idx, option in enumerate(storage_options, start=1):
        print(f"{idx}. {option}")
    while True:
        try:
            selection = int(input(f"Enter the number corresponding to the storage type (1-{len(storage_options)}): "))
            if 1 <= selection <= len(storage_options):
                storageType = storage_options[selection - 1]
                break
            else:
                print("Invalid input. Please enter a number within the valid range.")
        except ValueError:
            print("Invalid input. Please enter a number.")


    return CDRMethod(
        mainType=mainType,
        subType=subType,
        mac=mac,
        maxRemove=maxRemove,
        initialCost=initialCost,
        storageType=storageType,
        sideEffect=sideEffect,
        sideEffectMax=sideEffectMax
    )

def import_cdr_from_excel(excel_path="CDRMethods.xlsx"):
    if excel_path is None:
        project_root = Path(__file__).resolve().parent
        excel_path = project_root / "CDRMethods.xlsx"
    file = pd.read_excel(excel_path)
    cdr_methods = []

    for _, row in file.iterrows():
        method = CDRMethod(
            mainType=row["mainType"],
            subType=row["subType"],
            mac=float(row["mac"]),
            maxRemove=float(row["maxRemove"]),
            initialCost=float(row["initialCost"]),
            storageType=row["storageType"],
            sideEffect=float(row["sideEffect"]),
            sideEffectMax=float(row["sideEffectMax"])
        )
        cdr_methods.append(method)

    return cdr_methods

