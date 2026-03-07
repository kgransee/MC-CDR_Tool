from benefit_calx import *
from cdr_input import *
#from cdr_viable import is_method_viable 
from cdr_viable import check_storage_feasibility, read_storage_potential, is_method_viable
from define_removal_target import define_removal_target
from output_portfolio import *
from data_gen import *
from simulations import *
from simulations_noViaCheck import *
from data_gen_Rueda import *


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

    print("\nHow would you like to provide CDR methods?")
    print("1. Enter methods manually")
    print("2. Import methods from an Excel file")
    print("3. Generate Global Portfolio (based on survey results)")
    print("4. Generate Global Portfolio (based on Rueda et al. 2021)")

    while True:
        choice = input("Select an option (1 or 2): ").strip()
        if choice in ("1", "2", "3", "4"):
            break
        print("Invalid selection. Please enter 1, 2, 3, or 4.")
    #manual Entry
    if choice == "1":
        while True:
            method = get_cdr_from_user()
            cdr_methods.append(method)
            print("CDR Method added!")

            again = input("Add another? (y/n): ").lower()
            if again != 'y':
                 break

    #Excel Import, file CDRInputs.xlsx is a template file with example CDR methods, users can modify this file and input their own methods, but they need to keep the same format for the code to work. The code will read the file and create CDR method objects based on the data in the file.
    elif choice == "2":
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
            print("\nGenerating global portfolio based on survey results...")
            print("a) Single run (one seed)")
            print("b) 100-run simulation (fixed seed order for replication)")

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
            print("\nGenerating global portfolio based on Rueda et al. 2021...")
            print("a) Single run (one seed)")
            print("b) 100-run simulation (fixed seed order for replication)")

            while True:
                sim_choice = input("Select (a/b): ").strip().lower()
                if sim_choice in ("a", "b"):
                    break
                print("Invalid selection. Enter a or b.")

            if sim_choice == "a":
                seed = 13
                cdr_methods = generate_random_portfolioR(pseed=seed)
                print(f"Generated {len(cdr_methods)} CDR methods using seed={seed}.")

    #confirmation of the imported methods or entered methods
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

    if choice == "3" and sim_choice == "b":
        seeds = list(range(1, 100))
        run_100_simulations(
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
        run_100_simulationsNC(
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
        return  # stop main() here
    
    if choice == "4" and sim_choice == "b":
        seeds = list(range(1, 100))
        run_100_simulations(
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
        run_100_simulationsNC(
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
        return  # stop main() here    
    
    #check which methods are viable based on the input values
    current_year = removal_target["current_year"]
    start_year = removal_target["start_year"]
    duration_years = 15 #fixed duration period in line with new EU policy for BECCS and DACCS. Biochar activit period is 5 years. 
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
                f"Discounted Social Benefit: {m.initial_discounted_benefit:.2e} € | "
                f"Discounted Economic Cost: {m.initial_discounted_cost} € | "
            )
    else:
        print("\nNo CDR methods are viable under the given parameters.")
    #first code block deals with lexicographic optimization
    if (region == "Europe"):
        lg_dimensions = lexicographic_opt_iterative(SDR, SCC, start_year, current_year, viable_methods, storage_target, duration_years, pass_storage_potential = EuropeanStoragePotential)
    elif (region == "North America"):
        lg_dimensions = lexicographic_opt_iterative(SDR, SCC, start_year, current_year, viable_methods, storage_target, duration_years, pass_storage_potential = NorthAmericanStoragePotential)
    elif(region == "Global"):
        lg_dimensions = lexicographic_opt_iterative(SDR, SCC, start_year, current_year, viable_methods, storage_target, duration_years, pass_storage_potential = GlobalStoragePotential)
    #MAC curve code block
    if lg_dimensions:
        marginal_abatement_cost_curve(lg_dimensions, storage_target, start_year, duration_years, SDR, current_year)
    else:
        print("No portfolio selected, skipping MAC curve.")

    #now pareto optimization with iterative layers
    if (region == "Europe"):
        pareto_dimensions = pareto_portfolio_iterative_layers(SDR, SCC, start_year, current_year,viable_methods, storage_target, duration_years, pass_storage_potential = EuropeanStoragePotential)
    elif (region == "North America"):
        pareto_dimensions = pareto_portfolio_iterative_layers(SDR, SCC, start_year, current_year,viable_methods, storage_target, duration_years, pass_storage_potential = NorthAmericanStoragePotential)
    elif(region == "Global"):
        pareto_dimensions = pareto_portfolio_iterative_layers(SDR, SCC, start_year, current_year,viable_methods, storage_target, duration_years, pass_storage_potential = GlobalStoragePotential)
    #now pareto MACC
    if pareto_dimensions:
        marginal_abatement_cost_curve_pareto(pareto_dimensions, storage_target, start_year, duration_years, SDR, current_year)
    else:
        print("No portfolio selected, skipping MAC curve.")

    plot_total_pv_net_lg_vs_pareto(lg_dimensions, pareto_dimensions)
if __name__ == "__main__":
    main()