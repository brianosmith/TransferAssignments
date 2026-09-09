import math


DEFAULT_SCALES = {
    '1H': 0.02,
    '15N': 0.2,
    '13C': 0.2,
}


def peakDistance(sourcePeak,
                 targetPeak,
                 isotopeCodes,
                 scales=None):

    scales = scales or DEFAULT_SCALES

    total = 0.0

    for dim, isotopeCode in enumerate(isotopeCodes):

        sourcePos = sourcePeak.position[dim]
        targetPos = targetPeak.position[dim]

        scale = scales.get(isotopeCode, 1.0)

        total += ((sourcePos - targetPos) / scale) ** 2

    return math.sqrt(total)