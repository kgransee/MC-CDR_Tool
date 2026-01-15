from cdr_input import collect_cdr_methods

def main():
    methods = collect_cdr_methods()

    print("\nCollected CDR methods:")
    for m in methods:
        print(m)

if __name__ == "__main__":
    main()