from cdr_input import *
from cdr_viable import check_storage_feasibility, read_storage_potential
from define_removal_target import define_removal_target
from data_gen import *
from data_gen_Rueda import *
from data_gen_EU import *
from simulations import *
from data_gen_Rueda import *
from data_gen_SurveyRange import *

def main():
    #step 0 is to define removal target
    removal_target = define_removal_target()
    print("\n--- CDR Configuration Summary ---")
    print(f"Region: {removal_target['region']}")
    region = removal_target['region']
    print(f"Storage target: {removal_target['storage_target']}")
    print(f"Start year: {removal_target['start_year']}")
    print(f"Current year: {removal_target['current_year']}")
    print(f"Target type: {removal_target['target_type']}")


    EuropeanStoragePotential, NorthAmericanStoragePotential, GlobalStoragePotential = read_storage_potential()

    # Capture updated value from feasibility check
    #makes sure that the target is withi the 15 year goal
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
    print(f"Target type: {removal_target['target_type']}")
    print(f"Storage target: {removal_target['storage_target']}")

    #first step is to get the CDR methods from the user, then we will ask for the SCC and SDR values, and finally we will check which methods are viable based on the input values.
    print("\n--- Next Step ---")
    print("Please provide potential CDR methods.")
    cdr_methods = []
    #loop for getting CDR methods
    cdr_methods = []

    #variable to specify which data generation is to be used
    dataUse = None
    sim_choice = None
    print("\nHow would you like to provide CDR methods?")
    print("2. Import methods from an Excel file")
    print("3. Generate Global Portfolio (based on survey results)")
    print("4. Generate Global Portfolio (based on Rueda et al. 2021)")
    print("5. Generate EU Portfolio (based literature, EU Policy, and survey)")
    print("6. Generate Global Portfolio (based on survey results, use of range of side impact esitmates)")
    while True:
        choice = input("Select an option (2-6): ").strip()
        if choice in ("2", "3", "4", "5", "6"):
            break
        print("Invalid selection. Please enter 2, 3, 4, 5, or 6.")
    #manual Entry

    #Excel Import, file CDRInputs.xlsx is a template file with example CDR methods, users can modify this file and input their own methods, but they need to keep the same format for the code to work. The code will read the file and create CDR method objects based on the data in the file.
    if choice == "2":
        while True:
            filepath = input("Enter path to Excel file name: ").strip()

            try:
                imported_methods = import_cdr_from_excel(filepath)
                cdr_methods.extend(imported_methods)
                print(f"{len(imported_methods)} CDR methods imported successfully.")
                break  
            except Exception as e:
                print(f"Failed to import Excel file: {e}")

    elif choice == "3":
            print("\nGenerate global portfolio based on survey results")
            print("a) Single run (one seed)")
            print("b) 1000-run simulation (fixed seed order for replication)")
            dataUse = "Survey"
            while True:
                sim_choice = input("Select (a/b): ").strip().lower()
                if sim_choice in ("a", "b"):
                    break
                print("Invalid selection. Enter a or b.")

            if sim_choice == "a":
                seed = 13
                cdr_methods = generate_random_portfolio(pseed=seed)
                print(f"Generated {len(cdr_methods)} CDR methods using seed={seed}.")
    elif choice == "4":
            print("\nGenerate global portfolio based on Rueda et al. 2021")
            print("a) Single run (one seed)")
            print("b) 1000-run simulation (fixed seed order for replication)")
            dataUse = "Rueda"
            while True:
                sim_choice = input("Select (a/b): ").strip().lower()
                if sim_choice in ("a", "b"):
                    break
                print("Invalid selection. Enter a or b.")

            if sim_choice == "a":
                seed = 13
                cdr_methods = generate_random_portfolioR(pseed=seed)
                print(f"Generated {len(cdr_methods)} CDR methods using seed={seed}.")
    elif choice == "5":
            print("\nGenerate EU portfolio based on literature, EU Policy, and survey")
            print("a) Single run (one seed)")
            print("b) 10,000-run simulation")
            dataUse = "EU"
            while True:
                sim_choice = input("Select (a/b): ").strip().lower()
                if sim_choice in ("a", "b"):
                    break
                print("Invalid selection. Enter a or b.")

            if sim_choice == "a":
                seed = 13
                cdr_methods = generate_random_portfolioEU(pseed=seed)
                print(f"Generated {len(cdr_methods)} CDR methods using seed={seed}.")
    elif choice == "6":
            print("\nGenerating Full Monte Carlo Global Simulation")
            print("a) Single run (one seed)")
            print("b) 10,000-run simulation (fixed seed order for replication)")
            dataUse = "SurveyRange"
            while True:
                sim_choice = input("Select (a/b): ").strip().lower()
                if sim_choice in ("a", "b"):
                    break
                print("Invalid selection. Enter a or b.")

            if sim_choice == "a":
                seed = 13
                cdr_methods = generate_random_portfolioSR(pseed=seed)
                print(f"Generated {len(cdr_methods)} CDR methods using seed={seed}.")
    #confirmation of the imported methods or entered methods
    print("\nCollected CDR methods:")
    for m in cdr_methods:
        print(m)
    #define SCC
    while True:
        try:
            SCC = float(input("Define a value for the Social Cost of Carbon (SCC) in USD at the start of removals for the 15 year activity period: "))
            if SCC >= 0:
                break
            else:
                print("Error: The value must be greater than or equal to 0. Please try again.")
        except ValueError:
            print("Invalid input. Please enter a numeric value.")
    #define SDR
    while True:
        try:
            user_input = input("Please define a social discount rate (SDR) (e.g. x.y or x.y%): ").strip()
            user_input = user_input.replace("%", "")

            SDR = float(user_input)

            if SDR >= 0:
                break
            else:
                print("Error: The value must be greater than or equal to 0. Please try again.")

        except ValueError:
            print("Invalid input. Please enter a numeric value (e.g. x.uy or x.y%).")

        print("SDR =", SDR)

    if choice in ("3", "4", "5", "5", "6") and sim_choice == "b":
        seeds = list(range(1, 10001))
        seeds2 = list(range(1, 10001))
        #first simulations with viability check
        run_100_simulations(
            viaCheck=True,
            dataUse = dataUse,
            seeds=seeds,
            removal_target=removal_target,
            SCC=SCC,
            SDR=SDR,
            duration_years=15,
            region=region,
            EuropeanStoragePotential=EuropeanStoragePotential,
            NorthAmericanStoragePotential=NorthAmericanStoragePotential,
            GlobalStoragePotential=GlobalStoragePotential
        )
        run_100_simulations(
            viaCheck=False,
            dataUse = dataUse,
            seeds=seeds2,
            removal_target=removal_target,
            SCC=SCC,
            SDR=SDR,
            duration_years=15,
            region=region,
            EuropeanStoragePotential=EuropeanStoragePotential,
            NorthAmericanStoragePotential=NorthAmericanStoragePotential,
            GlobalStoragePotential=GlobalStoragePotential
        )
        return  # stop main() here
if __name__ == "__main__":
    main()