def define_removal_target():
    regions = ["Europe", "North America"]

    # Select region
    while True:
        print("Select the region where the CDR portfolio will be deployed:")
        for i, region in enumerate(regions, start=1):
            print(f"{i}. {region}")

        try:
            region_choice = int(input("Enter the number of your choice: "))
            if 1 <= region_choice <= len(regions):
                selected_region = regions[region_choice - 1]
                break
            else:
                print("Invalid choice. Try again.\n")
        except ValueError:
            print("Please enter a number.\n")

    # Select target type
    while True:
        print("\nDefine the removal target type:")
        print("0. Cumulative storage target")
        print("1. Yearly storage target")

        try:
            target_type = int(input("Enter 0 or 1: "))
            if target_type in (0, 1):
                break
            else:
                print("Invalid choice. Try again.\n")
        except ValueError:
            print("Please enter a number.\n")

    # Enter storage target
    while True:
        try:
            storage_target = float(input("\nEnter the storage target amount in gigatons(Gt): "))
            if storage_target > 0:
                break
            else:
                print("Storage target must be greater than 0.\n")
        except ValueError:
            print("Please enter a numeric value.\n")

    target_type_map = {
    0: "Cumulative",
    1: "Yearly"
    }
    while True:
        try:
            current_year = int(input("What is the current year? "))
            break
        except ValueError:
            print("Please enter a valid integer year.") 
    if target_type == 1:  # Yearly target
        while True:
            try:
                start_year = int(input("In which year will the removals begin? "))
                break
            except ValueError:
                print("Please enter a valid integer year.")

        while True:
            try:
                duration_years = int(input("For how many years will the removals be sustained? "))
                if duration_years > 0:
                    break
                else:
                    print("Duration must be a positive integer.")
            except ValueError:
                print("Please enter a valid integer.")

    elif target_type == 0:  # Cumulative target
        duration_years = 50 #baseline scenario, will then calculate till 2100 when start year is 20250
        start_year = None
        while True:
            try:
                start_year = int(input("In which year will the removals begin? "))
                break
            except ValueError:
                print("Please enter a valid integer year.")

    return {
    "region": selected_region,
    "target_type": target_type,             
    "target_type_name": target_type_map[target_type],
    "storage_target": storage_target,
    "start_year": start_year,
    "duration_years": duration_years,
    "current_year": current_year
}
