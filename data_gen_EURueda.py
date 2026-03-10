import numpy as np

from cdr_method import CDRMethod

def generate_random_portfolioEUR(pseed):
    #In line with CRCF EU 2026, only three possible methods
    main_types = ["Biochar", "BECCS", "DACCS"]

    raw_side_effects = {
        "Biochar": 22.2,
        "BECCS": -22.3,
        "DACCS": 11.1,
    }
    scaled_side_effects = {k: v / 100.0 for k, v in raw_side_effects.items()}

    removal_max = {
        "Biochar": (0.07,0.290), #Tisserant et al. 2023
        "BECCS": (0.2,0.2), #Rosa et al 2021
        "DACCS": (0.288,0.288) #Lux et al 2023
    }

    storage_types = {
        "Biochar": "sediments",
        "BECCS": "geological formations",
        "DACCS": "geological formations",
    }
    #ipcc AR6 estimate, unless notes
    cost_ranges = {
        "Biochar": (10, 345),
        "BECCS": (50, 200),
        "DACCS": (100, 300),
    }

    rng = np.random.default_rng(pseed)

    portfolio = []
    for main in main_types:
        #sub = str(i)  # "1".."10"

        low, high = cost_ranges[main]
        lowr, highr = removal_max[main]
        mac = float(rng.uniform(low, high))
        maxRemove=float(rng.uniform(lowr,highr))

        portfolio.append(
            CDRMethod(
                mainType=main,
                subType=main,
                mac=mac,
                maxRemove=maxRemove,
                initialCost=0.0,
                storageType=storage_types[main],
                sideEffect=float(scaled_side_effects[main]),
                sideEffectMax=maxRemove
            )
        )

    return portfolio