import numpy as np

from cdr_method import CDRMethod

def generate_random_portfolio(pseed):
    # Fixed 10 method families (mainType)
    main_types = ["AR", "SCS", "Biochar", "BECCS", "DACCS", "ERW", "PWR", "BC", "OAE", "OF"]

    raw_side_effects = {
        "AR": 49.45,
        "SCS": 55.67,
        "Biochar": 38.95,
        "BECCS": 9.32,
        "DACCS": -4.86,
        "ERW": 35.26,
        "PWR": 63.95,
        "BC": 57.76,
        "OAE": 34.50,
        "OF": -29.43
    }
    #scaled_side_effects = {k: v / 100.0 for k, v in raw_side_effects.items()}

    removal_max = {
        "AR": 1.100, "SCS": .350, "Biochar": .325, "BECCS": .150, "DACCS": .400,
        "ERW": .400, "PWR": .250, "BC": .025, "OAE": .01, "OF": 0
    }

    removal_SEmax = {
        "AR": 1.500, "SCS": .250, "Biochar": .750, "BECCS": .750, "DACCS": 1.000,
        "ERW": 1.000, "PWR": .100, "BC": 2.150, "OAE": 1.000, "OF": .100
    }

    storage_types = {
        "AR": "vegetation",
        "SCS": "sediments",
        "Biochar": "sediments",
        "BECCS": "geological formations",
        "DACCS": "geological formations",
        "ERW": "minerals",
        "PWR": "sediments",
        "BC": "soils",
        "OAE": "sediments",
        "OF": "sediments"
    }
    #ipcc AR6 estimate, unless notes
    cost_ranges = {
        "BECCS": (50, 200),
        "Biochar": (10, 345),
        "DACCS": (100, 300),
        "AR": (0, 240),
        "SCS": (0, 100),
        "ERW": (50, 200),
        "PWR": (0, 45), # Niemi et al 2024 https://www.sciencedirect.com/science/article/pii/S0264837724002825
        "BC": (10, 50), #using NOAA data https://sciencecouncil.noaa.gov/wp-content/uploads/2023/06/mCDR-glossy-final.pdf
        "OAE": (40, 260),
        "OF": (7, 500),
    }

    rng = np.random.default_rng(pseed)

    portfolio = []
    for i, main in enumerate(main_types, start=1):
        #sub = str(i)  # "1".."10"

        low, high = cost_ranges[main]
        mac = float(rng.uniform(low, high))

        portfolio.append(
            CDRMethod(
                mainType=main,
                subType=main,
                mac=mac,
                maxRemove=float(removal_max[main]),
                initialCost=0.0,
                storageType=storage_types[main],
                sideEffect=float(raw_side_effects[main]),
                sideEffectMax=float(removal_SEmax[main])
            )
        )

    return portfolio