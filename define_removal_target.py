def define_removal_target():
    while True:
        try:
            removalTarget = float(input("Please define a a removal target: "))
            if removalTarget >= 0:
                break
            else:
                print("Error: The value must be greater than or equal to 0. Please try again.")
        except ValueError:
            print("Invalid input. Please enter a numeric value.")

    while True:
        try:
            currentYear = int(input("Please define your investment strategy:\n"
                                 "Enter 1 to invest all at once\n"
                                 "Enter 2 to calculate optimal investment date\n"
                                 "Enter 3 to specify investment times (years from now)\n"
                                 "Your choice (1/2/3): "))
            if currentYear in [1, 2, 3]:
                break
            else:
                print("Invalid choice. Please enter 1, 2, or 3.")
        except ValueError:
            print("Invalid input. Please enter a number (1, 2, or 3).")
