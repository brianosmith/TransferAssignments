from collections import defaultdict

from .distanceMetrics import peakDistance
from .peakMatch import PeakMatch


class MatchingEngine:

    def __init__(self):

        self.threshold = 10.0
        self.considerAliasing = False

    def findMatches(self,
                    sourcePeakList,
                    targetPeakList,
                    isotopeCodes,
                    scales):

        results = defaultdict(list)

        for sourcePeak in sourcePeakList.peaks:

            matches = []

            for targetPeak in targetPeakList.peaks:

                distance = peakDistance(
                    sourcePeak,
                    targetPeak,
                    isotopeCodes,
                    scales
                )

                if distance <= self.threshold:

                    matches.append(
                        PeakMatch(
                            sourcePeak=sourcePeak,
                            targetPeak=targetPeak,
                            distance=distance
                        )
                    )

            matches.sort(key=lambda m: m.distance)

            if matches:
                matches[0].isClosest = True

            results[sourcePeak] = matches

        return results