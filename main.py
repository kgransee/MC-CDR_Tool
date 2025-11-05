
#function to determine the aggregate levels of carbon emissions 
# from hard-to-abate sectors
def ag_carbon_emissions():

#specific CDR capacity of given technolgy
def calc_current_cdr_level(tech:str, trl:int, deploymentLevel:int):
    cdrTechList = ["RRS", "agPraxis", "RA", "PeatlandRR", "DACCS", "BECCS"]
    #RRS=Restoration/Recovery of Seagrass
    #agPraxis=Agricultural practices to increase organic top-soil carbon
    #RA= Reforestation and Afforestation 
    #PeatlandRR=Peatland Restoration/Rewetting
    #DACCS=Direct Air Carbon Dioxide Capture and Storage (DACCS) 
    #BECCS=Bioenergy with Carbon Dioxide Capture and Storage (BECCS) 
    pass

def carbon_valuation(SCC:float, SDR:float,volumeTons:int):
    return SCC*SDR*volumeTons
#valuation of covercrop has to be considered as well
def cover_crop_valuation():
    pass
def corn_soybean_price_diff(cornFuture: float, soybeanFuture:float, SDR:float):
    #important to consider this price difference for demand dynamics
    #if future crops are converted to corn from soy, implies that less soybeans available
    #soybeans are used in a variety of vegetarian diets
    #does the cost of cropRotation to corn from soybeans take into these demand dyanmics?

    return cornFuture-soybeanFuture
    Í

def next_period_cdr_level(current_cdr_level, learningRate):
    pass
def main():
    #test
    pass