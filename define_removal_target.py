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
        print("0. Total (cumulative) storage target")
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
            storage_target = float(input("\nEnter the storage target amount in Megatons(Mt): "))
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

    return {
    "region": selected_region,
    "target_type": target_type,             
    "target_type_name": target_type_map[target_type],
    "storage_target": storage_target
}
