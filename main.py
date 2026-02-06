from cdr_input import get_cdr_from_user
#from cdr_viable import is_method_viable 
from cdr_viable import check_storage_feasibility, read_storage_potential, is_method_viable
from define_removal_target import define_removal_target

def main():
    #step 0 is to define removal target
    removal_target = define_removal_target()
    print("\n--- CDR Configuration Summary ---")
    print(f"Region: {removal_target['region']}")
    print(f"Target type: {removal_target['target_type_name']}")
    print(f"Storage target: {removal_target['storage_target']}")

    EuropeanStoragePotential, NorthAmericanStoragePotential = read_storage_potential()

    # Capture returned (possibly updated) value
    updated_target = check_storage_feasibility(
    removal_target,
    EuropeanStoragePotential,
    NorthAmericanStoragePotential
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
    while True:
        method = get_cdr_from_user()
        cdr_methods.append(method)
        print("CDR Method added!")

        again = input("Add another? (y/n): ").lower()
        if again != 'y':
            break

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
    viable_methods = is_method_viable(cdr_methods, SCC, SDR, start_year=start_year,
        duration_years=duration_years, current_year=current_year)
    
    if viable_methods:
        print("\n--- Viable CDR Methods ---")
        for m in viable_methods:
            print(
                f"{m.mainType} ({m.subType}) | "
                f"MAC: {m.mac} €/tCO₂ | "
                f"Side-effect constrained max: {m.sideEffectMax} Gt"
            )
    else:
        print("\nNo CDR methods are viable under the given parameters.")

if __name__ == "__main__":
    main()