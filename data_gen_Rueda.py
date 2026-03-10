import numpy as np

from cdr_method import CDRMethod

def generate_random_portfolioR(pseed):
    # 6 methods from Rueda
    main_types = ["AR", "SCS", "Biochar", "BECCS", "DACCS", "ERW"]

    """
    #side impacts determined in paper
    Original score is 0 (highly negative) to 10 (highly positive)
    | Method | Environmental | Economic | Social | Average  | 
    | ------ | ------------- | -------- | ------ | -------- |
    | AR     | 8.33          | 5.00     | 5.00   | 6.11 |
    | BC     | 6.67          | 6.67     | 5.00   | 6.11 |
    | BECCS  | 0.00          | 8.33     | 3.33   | 3.89 |
    | DACCS  | 3.33          | 6.67     | 6.67   | 5.56 |
    | EW     | 3.33          | 6.67     | 3.33   | 4.44 |
    | OF     | 1.67          | 5.00     | 5.00   | 3.89 |
    | SCS    | 6.67          | 8.33     | 10.00  | 8.33 |
    Converted score =(Rueda score−5)×20
    | Method | Environmental | Economic | Social | Average   |
    | ------ | ------------- | -------- | ------ | --------- |
    | AR     | 66.6          | 0        | 0      | 22.2  |
    | BC     | 33.4          | 33.4     | 0      | 22.2  |
    | BECCS  | -100          | 66.6     | -33.4  | -22.3 |
    | DACCS  | -33.4         | 33.4     | 33.4   | 11.1  |
    | EW     | -33.4         | 33.4     | -33.4  | -11.1 |
    | OF     | -66.6         | 0        | 0      | -22.2 |
    | SCS    | 33.4          | 66.6     | 100    | 66.7  |
    score average is used.
    """

    raw_side_effects = {
        "AR": 22.2,
        "SCS": 66.77,
        "Biochar": 22.2,
        "BECCS": -22.3,
        "DACCS": 11.1,
        "ERW": -11.1
    }
    scaled_side_effects = {k: v / 100.0 for k, v in raw_side_effects.items()}

    removal_max = {
        "AR": (0.5,3.6), 
        "SCS": (2,5), 
        "Biochar": (0.5,2), 
        "BECCS": (0.5,5), 
        "DACCS": (0.7,7),
        "ERW": (2.5,5)
    }
    #same, no side effect max in paper
    #data not used, removal_max set to sideEffectMax
    """""
    removal_SEmax = {
        "AR": (0.5,3.6), 
        "SCS": (2,5), 
        "Biochar": (0.5,2), 
        "BECCS": (0.5,5), 
        "DACCS": (0.5,7),
        "ERW": (2.5,5)
    }
        """""
    storage_types = {
        "AR": "vegetation",
        "SCS": "sediments",
        "Biochar": "sediments",
        "BECCS": "geological formations",
        "DACCS": "geological formations",
        "ERW": "minerals",
    }
    #using minx et al 2018, in dollars 
    cost_ranges = {
        "AR": (5, 50),
        "SCS": (0, 100),
        "Biochar": (30, 120),
        "BECCS": (100, 200),
        "DACCS": (100, 300),
        "ERW": (50, 200),
    }

    rng = np.random.default_rng(pseed)

    portfolio = []
    for main in main_types:
        #sub = str(i)  # "1".."10"

        low, high = cost_ranges[main]
        lowr, highr = removal_max[main]
        mac = float(rng.uniform(low, high))
        maxRemove=float(rng.uniform(lowr,highr))
        sideEffectMax = maxRemove

        portfolio.append(
            CDRMethod(
                mainType=main,
                subType=main,
                mac=mac,
                maxRemove=maxRemove,
                storageType=storage_types[main],
                initialCost=0.0,
                sideEffect=float(scaled_side_effects[main]),
                sideEffectMax=sideEffectMax
            )
        )

    return portfolio