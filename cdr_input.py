from cdr_method import CDRMethod

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
    
    mac = input_float("MAC (number): ")
    maxRemove = input_float("Max removal (number): ")
    initialCost = input_float("Initial cost (number): ")
    sideEffectMax = input_float("Side effect max (number): ")

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

    location = input("Location: ")

    return CDRMethod(
        mainType=mainType,
        subType=subType,
        mac=mac,
        maxRemove=maxRemove,
        initialCost=initialCost,
        location=location,
        storageType=storageType,
        sideEffect=sideEffect,
        sideEffectMax=sideEffectMax
    )

def collect_cdr_methods():
    cdr_methods = []

    while True:
        try:
            cdr = get_cdr_from_user()
            cdr_methods.append(cdr)
            print("CDR Method added!\n")

        except ValueError as e:
            print(f"Error: {e}")
            print("Please try entering this method again.\n")
            continue

        again = input("Add another CDR method? (y/n): ").strip().lower()
        if again != "y":
            break

    return cdr_methods