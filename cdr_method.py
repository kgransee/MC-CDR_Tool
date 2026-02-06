from dataclasses import dataclass, field

@dataclass
class CDRMethod:
    mainType: str
    subType: str
    mac: float
    maxRemove: float
    initialCost: float
    location: str
    storageType: str
    sideEffect: str
    sideEffectMax: float = field(repr=False)

    def __post_init__(self):
        possibleMethods = [
            "LULUCF", "SCS", "BC", "BECCS", "DACCS",
            "EW", "PWR", "BCM", "OAE", "OF"
        ]

        if self.mainType not in possibleMethods:
            raise ValueError(
                f"Invalid CDR method: {self.mainType}. "
                f"Must be one of {possibleMethods}"
            )

        if self.initialCost < 0:
            raise ValueError("Initial cost must be >= 0")
        if self.mac < 0:
            raise ValueError("MAC must be >= 0")
        if self.maxRemove < 0:
            raise ValueError("maxRemove must be >= 0")
        if self.sideEffectMax < 0:
            raise ValueError("sideEffectMax must be >= 0")