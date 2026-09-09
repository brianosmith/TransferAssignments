from ccpn.ui.gui.modules.CcpnModule import CcpnModule

from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.CheckBox import CheckBox
from ccpn.ui.gui.widgets.DoubleSpinbox import DoubleSpinbox

try:
    from ccpn.ui.gui.widgets.PulldownListsForObjects import PeakListPulldown
except ImportError:
    PeakListPulldown = None

from ccpn.plugins.TransferAssignments.MatchingEngine import MatchingEngine
from ccpn.plugins.TransferAssignments.AssignmentTransfer import AssignmentTransfer

from ..widgets.SourcePeakTable import SourcePeakTable
from ..widgets.TargetPeakTable import TargetPeakTable


DEFAULT_SCALES = {
    '1H': 0.02,
    '15N': 0.2,
    '13C': 0.2,
}


class TransferAssignmentsModule(CcpnModule):
    """
    CCPN V3 implementation of the V2
    Copy Assignments -> Between Peak Lists popup.
    """

    className = 'TransferAssignmentsModule'

    includeSettingsWidget = False

    def __init__(self,
                 mainWindow=None,
                 name='Transfer Assignments'):

        super().__init__(
            mainWindow=mainWindow,
            name=name
        )

        self.application = mainWindow.application
        self.project = mainWindow.project
        self.current = mainWindow.application.current

        self.matchEngine = MatchingEngine()

        self.matchResults = {}

        self._currentSourcePeak = None
        self._currentTargetPeak = None

        self.scales = dict(DEFAULT_SCALES)

        self._buildWidgets()

    # -------------------------------------------------------------------------
    # GUI

    def _buildWidgets(self):

        row = 0

        Label(
            self.mainWidget,
            text='Source Peak List',
            grid=(row, 0)
        )

        self.sourcePeakListPulldown = PeakListPulldown(
            self.mainWidget,
            grid=(row, 1),
            callback=self._parametersChanged
        )

        row += 1

        Label(
            self.mainWidget,
            text='Target Peak List',
            grid=(row, 0)
        )

        self.targetPeakListPulldown = PeakListPulldown(
            self.mainWidget,
            grid=(row, 1),
            callback=self._parametersChanged
        )

        row += 1

        Label(
            self.mainWidget,
            text='Distance Threshold'
        , grid=(row, 0))

        self.thresholdSpinbox = DoubleSpinbox(
            self.mainWidget,
            value=10.0,
            min=0.0,
            max=999.0,
            step=0.1,
            grid=(row, 1)
        )

        self.thresholdSpinbox.valueChanged.connect(
            self._parametersChanged
        )

        row += 1

        self.overwriteCheckBox = CheckBox(
            self.mainWidget,
            text='Overwrite Assignments',
            checked=False,
            grid=(row, 0)
        )

        row += 1

        self.showAlreadyCopiedCheckBox = CheckBox(
            self.mainWidget,
            text='Show Already Copied',
            checked=False,
            grid=(row, 0)
        )

        row += 1

        self.onlyGoodMatchesCheckBox = CheckBox(
            self.mainWidget,
            text='Only Good Matches',
            checked=True,
            grid=(row, 0)
        )

        row += 1

        Label(
            self.mainWidget,
            text='Source Peaks',
            grid=(row, 0)
        )

        row += 1

        self.sourceTable = SourcePeakTable(
            self.mainWidget,
            grid=(row, 0),
            gridSpan=(1, 4)
        )

        if hasattr(self.sourceTable, 'selectionCallback'):
            self.sourceTable.selectionCallback = (
                self._sourceSelectionChanged
            )

        row += 1

        Label(
            self.mainWidget,
            text='Target Peaks',
            grid=(row, 0)
        )

        row += 1

        self.targetTable = TargetPeakTable(
            self.mainWidget,
            grid=(row, 0),
            gridSpan=(1, 4)
        )

        if hasattr(self.targetTable, 'selectionCallback'):
            self.targetTable.selectionCallback = (
                self._targetSelectionChanged
            )

        row += 1

        self.assignSelectedButton = Button(
            self.mainWidget,
            text='Assign Selected Target',
            callback=self._assignSelectedTarget,
            grid=(row, 0)
        )

        self.assignSingleButton = Button(
            self.mainWidget,
            text='Assign Singly Matched',
            callback=self._assignSinglyMatched,
            grid=(row, 1)
        )

        self.assignClosestButton = Button(
            self.mainWidget,
            text='Assign All To Closest',
            callback=self._assignAllToClosest,
            grid=(row, 2)
        )

    # -------------------------------------------------------------------------
    # Match calculation

    def _parametersChanged(self, *args):

        self.updateMatches()

    def updateMatches(self):

        sourcePeakList = (
            self.sourcePeakListPulldown.getSelectedObject()
        )

        targetPeakList = (
            self.targetPeakListPulldown.getSelectedObject()
        )

        if sourcePeakList is None:
            return

        if targetPeakList is None:
            return

        self.matchEngine.threshold = (
            self.thresholdSpinbox.value()
        )

        isotopeCodes = []

        try:
            isotopeCodes = (
                sourcePeakList.spectrum.isotopeCodes
            )

        except Exception:
            pass

        self.matchResults = self.matchEngine.findMatches(
            sourcePeakList=sourcePeakList,
            targetPeakList=targetPeakList,
            isotopeCodes=isotopeCodes,
            scales=self.scales
        )

        if self.onlyGoodMatchesCheckBox.isChecked():

            self.matchResults = {
                sourcePeak: matches
                for sourcePeak, matches
                in self.matchResults.items()
                if len(matches) > 0
            }

        self._populateSourceTable()

    # -------------------------------------------------------------------------
    # Source table

    def _populateSourceTable(self):

        rows = []

        showAssigned = (
            self.showAlreadyCopiedCheckBox.isChecked()
        )

        for sourcePeak, matches in self.matchResults.items():

            if not showAssigned:

                alreadyCopied = False

                for match in matches:

                    assignments = (
                        match.targetPeak.assignmentsByDimensions
                    )

                    if any(a for a in assignments):

                        alreadyCopied = True
                        break

                if alreadyCopied:
                    continue

            row = {
                'peak': sourcePeak,
                'serial': sourcePeak.serial,
                'assignment': sourcePeak.annotation,
                'numMatches': len(matches),
                'closestDistance':
                    matches[0].distance if matches else None,
                'bestMatch':
                    matches[0].targetPeak.serial
                    if matches else None,
            }

            rows.append(row)

        self.sourceTable.populate(rows)

    # -------------------------------------------------------------------------
    # Target table

    def _populateTargetTable(self, peakMatches):

        rows = []

        for match in peakMatches:

            rows.append({
                'peak': match.targetPeak,
                'serial': match.targetPeak.serial,
                'assignment': match.targetPeak.annotation,
                'distance': round(match.distance, 4),
            })

        self.targetTable.populate(rows)

    # -------------------------------------------------------------------------
    # Selection handling

    def _sourceSelectionChanged(self, rowObject):

        if rowObject is None:
            return

        sourcePeak = rowObject.get('peak')

        self._currentSourcePeak = sourcePeak

        peakMatches = self.matchResults.get(
            sourcePeak,
            []
        )

        self._populateTargetTable(peakMatches)

        self._followPeak(sourcePeak)

    def _targetSelectionChanged(self, rowObject):

        if rowObject is None:
            return

        self._currentTargetPeak = rowObject.get('peak')

        self._followPeak(self._currentTargetPeak)

    # -------------------------------------------------------------------------
    # Peak navigation

    def _followPeak(self, peak):

        if peak is None:
            return

        try:

            if self.current.strip:

                self.current.peaks = [peak]

        except Exception:
            pass

    # -------------------------------------------------------------------------
    # Assignment actions

    def _assignSelectedTarget(self):

        if self._currentSourcePeak is None:
            return

        if self._currentTargetPeak is None:
            return

        overwrite = (
            self.overwriteCheckBox.isChecked()
        )

        AssignmentTransfer.copyAssignment(
            self._currentSourcePeak,
            self._currentTargetPeak,
            overwrite=overwrite
        )

        self.updateMatches()

    def _assignSinglyMatched(self):

        overwrite = (
            self.overwriteCheckBox.isChecked()
        )

        count = (
            AssignmentTransfer.assignSinglyMatched(
                self.matchResults,
                overwrite=overwrite
            )
        )

        self._showStatus(
            f'{count} peaks assigned'
        )

        self.updateMatches()

    def _assignAllToClosest(self):

        overwrite = (
            self.overwriteCheckBox.isChecked()
        )

        count = (
            AssignmentTransfer.assignAllToClosest(
                self.matchResults,
                overwrite=overwrite
            )
        )

        self._showStatus(
            f'{count} peaks assigned'
        )

        self.updateMatches()

    # -------------------------------------------------------------------------
    # Utility

    def _showStatus(self, message):

        try:

            self.mainWindow.statusBar().showMessage(
                message,
                5000
            )

        except Exception:
            print(message)