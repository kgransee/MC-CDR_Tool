from cdr_input import get_cdr_from_user
#from cdr_viable import is_method_viable 
from cdr_viable import check_storage_feasibility, read_storage_potential
from define_removal_target import define_removal_target

def main():
    #step 0 is to define removal target
    removal_target = define_removal_target()
    print("\n--- CDR Configuration Summary ---")
    print(f"Region: {removal_target['region']}")
    print(f"Target type: {removal_target['target_type_name']}")
    print(f"Storage target: {removal_target['storage_target']}")
    
    EuropeanStoragePotential, NorthAmericanStoragePotential = read_storage_potential()

    check_storage_feasibility(removal_target, EuropeanStoragePotential,NorthAmericanStoragePotential)
    
    #first step is to get the CDR methods from the user, then we will ask for the SCC and SDR values, and finally we will check which methods are viable based on the input values.
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
    #define CDR
    while True:
        try:
            SCC = float(input("Please define a social discount rate (SDR): "))
            if SCC >= 0:
                break
            else:
                print("Error: The value must be greater than or equal to 0. Please try again.")
        except ValueError:
            print("Invalid input. Please enter a numeric value.")
    
    #check which methods are viable based on the input values
    #viable_methods = cdr_viable(cdr_methods, SCC, SDR)


if __name__ == "__main__":
    main()