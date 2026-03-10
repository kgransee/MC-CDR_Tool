def define_removal_target():
    regions = ["Europe", "North America", "Global"]

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
        print("1. 15 Year Activity Period")

        try:
            target_type = int(input("Enter 1: "))
            if target_type == 1:
                break
            else:
                print("Invalid choice. Try again.\n")
        except ValueError:
            print("Please enter a number.\n")

    # Enter storage target
    #this is strictly for geological storage, the check is to make sure
    #that the GCS limits are not exceeded
    while True:
        try:
            storage_target = float(input("\nEnter the  cummulative removal target in gigatons(Gt): "))
            if storage_target > 0:
                break
            else:
                print("Storage target must be greater than 0.\n")
        except ValueError:
            print("Please enter a numeric value.\n")

    while True:
        try:
            current_year = int(input("What is the current year? "))
            break
        except ValueError:
            print("Please enter a valid integer year.") 
    
    while True:
        try:
            start_year = int(input("In which year will the removals begin? "))
            break
        except ValueError:
            print("Please enter a valid integer year.")

    return {
    "region": selected_region,
    "target_type": target_type,             
    "storage_target": storage_target,
    "start_year": start_year,
    "current_year": current_year
}
