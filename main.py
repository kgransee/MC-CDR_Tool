from cdr_input import get_cdr_from_user

def main():
    cdr_methods = []

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

    while True:
        try:
            SCC = float(input("Please define a value for the Social Cost of Carbon (SCC): "))
            if SCC >= 0:
                break
            else:
                print("Error: The value must be greater than or equal to 0. Please try again.")
        except ValueError:
            print("Invalid input. Please enter a numeric value.")

    while True:
        try:
            SCC = float(input("Please define a social discount rate (SDR): "))
            if SCC >= 0:
                break
            else:
                print("Error: The value must be greater than or equal to 0. Please try again.")
        except ValueError:
            print("Invalid input. Please enter a numeric value.")


if __name__ == "__main__":
    main()