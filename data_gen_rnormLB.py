import numpy as np

from cdr_method import CDRMethod

def restricted_normal(mean, sd, rng, size=1,):
    x = rng.normal(loc=mean, scale=sd, size=size)
    x[x > 100] = 100
    x[x < -100] = -100
    return x

def generate_random_portfoliornormLB(pseed):
    # Fixed 10 method families (mainType)
    #PWR and blue carbon dropped due to lack of data on global potetials
    main_types = ["AR", "SCS", "Biochar", "BECCS", "DACCS", "ERW"]

    """"
> print(cb05_trunc_params)
# A tibble: 10 × 6
   Method      low  high   mean    sd     n
   <fct>     <dbl> <dbl>  <dbl> <dbl> <int>
 1 AR       -12.6  100    50.2   33.2    22
 2 SCS        2.51 100    56.4   36.6    21
 3 Biochar  -60.8  100    39.7   38.8    21
 4 BECCS   -100     73.9   9.87  43.3    22
 5 DACCS    -88.9   77.9  -4.38  47.2    21
 6 ERW      -16.6   84.9  35.9   29.4    23
 7 PWR       12.6  100    64.8   29.9    21
 8 BC        11.6   97.0  58.6   24.5    17
 9 OAE      -57.8   98.0  35.2   49.8    14
10 OF       -82.9   94.0 -29.1   48.3    14
    """
    side_impact_params = {
    "AR":      (-100.0, 100.0,  50.2, 33.2),
    "SCS":     (-100.0, 100.0,  56.4, 36.6),
    "Biochar": (-100.0, 100.0,  39.7, 38.8),
    "BECCS":   (-100.0, 100.0,   9.87,43.3),
    "DACCS":   (-100.0, 100.0,  -4.38,47.2),
    "ERW":     (-100.0, 100.0,  35.9, 29.4),
    }
    removal_max = {     #all numbers from Rueda et al. 2021 use peak potential, not 2050 potential. 
        "AR": (0.5,3.6), #Rueda et al. 2021
        "SCS": (2,5), #Rueda et al. 2021
        "Biochar": (0.5,2), #Rueda et al. 2021
        "BECCS": (0.5,5), #Rueda et al. 2021
        "DACCS": (0.7,7),#Rueda et al. 2021
        "ERW": (2.5,5),#Rueda et al. 2021 
    }

    """""
       Method        n  mean median    sd   min    q1    q3   max
       1 AR          6 1502.   1500 1376.     1 258.   2750  3000
       2 DACCS       5 1201.   1000 1642.     1   5    1000  4000
       3 ERW         6 1084.   1000 1020.     1 253    1750  2500
       4 BECCS       6 1004.    750 1044.     1 144.   1750  2500
       5 Biochar     6  835.    750  929.     1 132.   1000  2500
       6 SCS         6  667.    250  975.     1  26.5   850  2500
       7 OAE         5  622    1000  519.    10 100    1000  1000
       8 OF          3  370     100  547.    10  55     550  1000
       9 BC          4  325.    150  457.     1  75.2   400  1000
      10 PWR         5  240.    100  428.     1   1     100  1000
"""""
    removal_SEmax = {
        "AR": (.001,3.0), 
        "SCS": (.001,2.5), 
        "Biochar": (.001,2.5), 
        "BECCS": (.001,2.5), 
        "DACCS": (.001,4.0),
        "ERW": (.001,2.5), 
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
    }

    rng = np.random.default_rng(pseed)

    portfolio = []
    for main in main_types:
        #sub = str(i)  # "1".."10"

        low, high = cost_ranges[main]
        lowr, highr = removal_max[main]
        lowsi, highsi, meansi, sdsi = side_impact_params[main]
        raw_side_effect = restricted_normal(meansi, sdsi, rng, size=1)[0]
        scaledSideEffects = raw_side_effect / 100.0
        lowsm, highsm = removal_SEmax[main]
        mac = float(rng.uniform(low, high))
        maxRemove=float(rng.uniform(lowr,highr))
        sideEffectMax=float(rng.uniform(lowsm,highsm))
 
        portfolio.append(
            CDRMethod(
                mainType=main,
                subType=main,
                mac=mac,
                maxRemove=maxRemove,
                initialCost=0.0,
                storageType=storage_types[main],
                sideEffect=scaledSideEffects,
                sideEffectMax=sideEffectMax
            )
        )

    return portfolio