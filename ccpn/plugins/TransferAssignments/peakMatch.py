from dataclasses import dataclass


@dataclass
class PeakMatch:
    sourcePeak: object
    targetPeak: object
    distance: float
    isClosest: bool = False