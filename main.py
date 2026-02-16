from cdr_input import *
#from cdr_viable import is_method_viable 
from cdr_viable import check_storage_feasibility, read_storage_potential, is_method_viable
from define_removal_target import define_removal_target
from output_portfolio import *

def main():
    #step 0 is to define removal target
    removal_target = define_removal_target()
    print("\n--- CDR Configuration Summary ---")
    print(f"Region: {removal_target['region']}")
    region = removal_target['region']
    print(f"Target type: {removal_target['target_type_name']}")
    print(f"Storage target: {removal_target['storage_target']}")

    EuropeanStoragePotential, NorthAmericanStoragePotential, GlobalStoragePotential = read_storage_potential()

    # Capture returned (possibly updated) value
    updated_target = check_storage_feasibility(
    removal_target,
    EuropeanStoragePotential,
    NorthAmericanStoragePotential,
    GlobalStoragePotential
    )

    # Ensure main state is updated
    removal_target["storage_target"] = updated_target

    print("\n--- Final Stored Values ---")
    print(f"Region: {removal_target['region']}")
    print(f"Target type: {removal_target['target_type_name']}")
    print(f"Storage target: {removal_target['storage_target']}")

    #first step is to get the CDR methods from the user, then we will ask for the SCC and SDR values, and finally we will check which methods are viable based on the input values.
    print("\n--- Next Step ---")
    print("Please provide potential CDR methods.")
    cdr_methods = []
    #loop for getting CDR methods
    cdr_methods = []

    print("\nHow would you like to provide CDR methods?")
    print("1. Enter methods manually")
    print("2. Import methods from an Excel file")

    while True:
        choice = input("Select an option (1 or 2): ").strip()
        if choice in ("1", "2"):
            break
        print("Invalid selection. Please enter 1 or 2.")
    if choice == "1":
        while True:
            method = get_cdr_from_user()
            cdr_methods.append(method)
            print("CDR Method added!")

            again = input("Add another? (y/n): ").lower()
            if again != 'y':
                 break

    # ---- Option 2: Excel import ----
    elif choice == "2":
        while True:
            filepath = input("Enter path to Excel file name: ").strip()

            try:
                imported_methods = import_cdr_from_excel(filepath)
                cdr_methods.extend(imported_methods)
                print(f"{len(imported_methods)} CDR methods imported successfully.")
                break  # exit loop only on success
            except Exception as e:
                print(f"Failed to import Excel file: {e}")

    print("\nCollected CDR methods:")
    for m in cdr_methods:
        print(m)
    #define SCC
    while True:
        try:
            SCC = float(input("Please define a value for the Social Cost of Carbon (SCC): "))
            if SCC >= 0:
                break
            else:
                print("Error: The value must be greater than or equal to 0. Please try again.")
        except ValueError:
            print("Invalid input. Please enter a numeric value.")
    #define SDR
    while True:
        try:
            SDR = float(input("Please define a social discount rate (SDR): "))
            if SDR >= 0:
                break
            else:
                print("Error: The value must be greater than or equal to 0. Please try again.")
        except ValueError:
            print("Invalid input. Please enter a numeric value.")
    
    #check which methods are viable based on the input values
    current_year = removal_target["current_year"]
    start_year = removal_target["start_year"]
    duration_years = removal_target["duration_years"]
    storage_target = removal_target["storage_target"]
    viable_methods = is_method_viable(cdr_methods, SCC, SDR, start_year=start_year,
        duration_years=duration_years, current_year=current_year)
    
    if viable_methods:
        print("\n--- Viable CDR Methods ---")
        for m in viable_methods:
            print(
                f"{m.mainType} ({m.subType}) | "
                f"MAC: {m.mac} €/tCO₂ | "
                f"Side-effect constrained max: {m.sideEffectMax:.2e} Gt |"
                f"Discounted Social Benefit: {m.discounted_benefit:.2e} € | "
                f"Discounted Economic Cost: {m.discounted_cost} € | "
            )
    else:
        print("\nNo CDR methods are viable under the given parameters.")
    #first code block deals with lexicographic optimization
    if (region == "Europe"):
        lg_dimensions = lexicographic_opt_iterative(viable_methods,storage_target,duration_years, pass_storage_potential = EuropeanStoragePotential)
    elif (region == "North America"):
        lg_dimensions = lexicographic_opt_iterative(viable_methods,storage_target,duration_years, pass_storage_potential = NorthAmericanStoragePotential)
    elif(region == "Global"):
        lg_dimensions = lexicographic_opt_iterative(viable_methods,storage_target,duration_years, pass_storage_potential = GlobalStoragePotential)
    #MAC curve code block
    if lg_dimensions:
        marginal_abatement_cost_curve(lg_dimensions, storage_target, start_year, duration_years, SDR, current_year)
    else:
        print("No portfolio selected, skipping MAC curve.")
    #now pareto optimization with iterative layers
    if (region == "Europe"):
        pareto_dimensions = pareto_portfolio_iterative_layers(viable_methods, storage_target, duration_years, pass_storage_potential = EuropeanStoragePotential)
    elif (region == "North America"):
        pareto_dimensions = pareto_portfolio_iterative_layers(viable_methods, storage_target, duration_years, pass_storage_potential = NorthAmericanStoragePotential)
    elif(region == "Global"):
        pareto_dimensions = pareto_portfolio_iterative_layers(viable_methods, storage_target, duration_years, pass_storage_potential = GlobalStoragePotential)
    #now pareto MACC
    if pareto_dimensions:
        marginal_abatement_cost_curve_pareto(pareto_dimensions, storage_target, start_year, duration_years, SDR, current_year)
    else:
        print("No portfolio selected, skipping MAC curve.")

if __name__ == "__main__":
    main()