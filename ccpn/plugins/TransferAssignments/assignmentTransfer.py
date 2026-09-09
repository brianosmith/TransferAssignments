"""
Assignment transfer routines for the TransferAssignments plugin.

Uses CCPN-native assignment propagation via
AssignmentLib.copyAssignmentsFromReference()
rather than manually assigning dimensionNmrAtoms.
"""

from ccpn.core.lib.ContextManagers import undoBlock
from ccpn.core.lib.AssignmentLib import copyAssignmentsFromReference


class AssignmentTransfer:

    @staticmethod
    def _clearAssignments(peak):
        """
        Remove existing assignments from a peak.

        Used when overwrite=True.
        """

        try:

            peak.assignDimensions(
                peak.spectrum.axisCodes,
                [[] for _ in peak.spectrum.axisCodes]
            )

        except Exception:
            # fallback if API changes
            peak.dimensionNmrAtoms = tuple(
                [[] for _ in peak.dimensionNmrAtoms]
            )

    @classmethod
    def copyAssignment(cls,
                       sourcePeak,
                       targetPeak,
                       overwrite=False):
        """
        Copy assignments from sourcePeak to targetPeak.

        Returns True if assignment transfer was attempted.
        """

        if sourcePeak is None:
            return False

        if targetPeak is None:
            return False

        sourceAssignments = (
            sourcePeak.assignmentsByDimensions
        )

        if not any(sourceAssignments):
            return False


        if overwrite:
            cls._clearAssignments(targetPeak)

        copyAssignmentsFromReference(
            [targetPeak],
            sourcePeak
        )

        return True

    @classmethod
    def assignSinglyMatched(cls,
                            matchResults,
                            overwrite=False):
        """
        V2 Assign Singly Matched behaviour.

        Assign only source peaks that have exactly
        one matching target peak.
        """

        count = 0

        #
        # mirrors V2 logic:
        # once a target has been used,
        # further transfers should not clear it
        #
        targetsUsed = set()

        with undoBlock():

            for sourcePeak, matches in matchResults.items():

                if len(matches) != 1:
                    continue

                targetPeak = matches[0].targetPeak

                effectiveOverwrite = overwrite

                if targetPeak in targetsUsed:
                    effectiveOverwrite = False

                if cls.copyAssignment(
                        sourcePeak,
                        targetPeak,
                        overwrite=effectiveOverwrite):

                    count += 1
                    targetsUsed.add(targetPeak)

        return count


    @classmethod
    def assignAllToClosest(cls,
                           matchResults,
                           overwrite=False):
        """
        V2-style 'Assign All To Closest'.

        For every source peak:

          - choose the closest matching target peak
          - transfer assignments
          - honour overwrite semantics
          - track unmatched peaks

        Returns
        -------
        tuple
            (
              numberAssigned,
              unmatchedPeaks
            )
        """

        assignedCount = 0
        unmatchedPeaks = []

        #
        # V2 behaviour:
        # if multiple source peaks hit the same target,
        # only the first assignment may overwrite.
        #
        targetsUsed = set()

        with undoBlock():

            for sourcePeak, matches in matchResults.items():

                #
                # no valid matches found
                #
                if not matches:

                    unmatchedPeaks.append(sourcePeak)
                    continue

                #
                # matches should already be sorted
                # by distance ascending
                #
                closestMatch = matches[0]

                targetPeak = closestMatch.targetPeak

                effectiveOverwrite = overwrite

                #
                # replicate V2 targets-set logic
                #
                if targetPeak in targetsUsed:
                    effectiveOverwrite = False

                success = cls.copyAssignment(
                    sourcePeak,
                    targetPeak,
                    overwrite=effectiveOverwrite
                )

                if success:

                    assignedCount += 1
                    targetsUsed.add(targetPeak)

        return assignedCount, unmatchedPeaks