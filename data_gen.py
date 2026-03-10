import numpy as np

from cdr_method import CDRMethod

def generate_random_portfolio(pseed):
    # Fixed 10 method families (mainType)
    #PWR and blue carbon dropped due to lack of data on global potetials
    main_types = ["AR", "SCS", "Biochar", "BECCS", "DACCS", "ERW", "OAE", "OF"]
    
    """"
        raw survey data
            Question                Mean Median  Min Max  N Range
          AR  CB05_01  CB05_01  49.454545   56.5  -13  99 22   112
          SCS CB05_02  CB05_02  55.666667   43.0    2  99 21    97
       BiocharCB05_03  CB05_03  38.952381   40.0  -61  99 21   160
        BECCS CB05_04  CB05_04   9.318182   21.5 -100  73 22   173
        DACCS CB05_05  CB05_05  -4.857143   -1.0  -89  77 21   166
         ERW  CB05_06  CB05_06  35.260870   34.0  -17  84 23   101
         PWR  CB05_07  CB05_07  63.952381   75.0   12  99 21    87
         BC   CB05_08  CB05_08  57.764706   56.0   11  96 17    85
         OAE  CB05_09  CB05_09  34.500000   36.5  -58  97 14   155
      OF      CB05_10  CB05_10 -29.428571  -36.5  -83  93 14   176
    """
    raw_side_effects = {
        "AR": 49.45,
        "SCS": 55.67,
        "Biochar": 38.95,
        "BECCS": 9.32,
        "DACCS": -4.86,
        "ERW": 35.26,
       # "PWR": 63.95,
        #"BC": 57.76,
        "OAE": 34.50,
        "OF": -29.43
    }
    scaled_side_effects = {k: v / 100.0 for k, v in raw_side_effects.items()}

    removal_max = {
        "AR": (0.5,3.6), #Rueda et al. 2021
        "SCS": (2,5), #Rueda et al. 2021
        "Biochar": (0.5,2), #Rueda et al. 2021
        "BECCS": (0.5,5), #Rueda et al. 2021
        "DACCS": (0.7,7),#Rueda et al. 2021
        "ERW": (2.5,5),#Rueda et al. 2021
       # "PWR": .250, 
       # "BC": .025, 
        "OAE": (.1,10), #Fuss et al. 2018
        "OF": (0.000152,98) #Fuss et al. 2018
    }

    removal_SEmax = {
        "AR": 1.500, "SCS": .250, "Biochar": .750, "BECCS": .750, "DACCS": 1.000,
        "ERW": 1.000, 
       # "PWR": .100,
         # "BC": 2.150, 
          "OAE": 1.000, "OF": .100
    }

    storage_types = {
        "AR": "vegetation",
        "SCS": "sediments",
        "Biochar": "sediments",
        "BECCS": "geological formations",
        "DACCS": "geological formations",
        "ERW": "minerals",
       # "PWR": "sediments",
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
       # "PWR": (0, 45), # Niemi et al 2024 https://www.sciencedirect.com/science/article/pii/S0264837724002825
        #"BC": (10, 50), #using NOAA data https://sciencecouncil.noaa.gov/wp-content/uploads/2023/06/mCDR-glossy-final.pdf
        "OAE": (40, 260),
        "OF": (7, 500),
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
                sideEffectMax=float(removal_SEmax[main])
            )
        )

    return portfolio