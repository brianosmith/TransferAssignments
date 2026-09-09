from collections import OrderedDict as od
import pandas as pd

from PyQt5 import QtWidgets

from ccpn.api import PluginBase, PluginGUIModule

import ccpn.ui.gui.widgets.PulldownListsForObjects as objectPulldowns
import ccpn.ui.gui.widgets.CompoundWidgets as compoundWidget
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.Frame import Frame
from ccpn.ui.gui.widgets.Splitter import Splitter
from ccpn.ui.gui.widgets.table.Table import Table

from ccpn.api import getApplication, getLogger

from .matchingEngine import MatchingEngine
from .assignmentTransfer import AssignmentTransfer


SettingsWidgetFixedWidths = (180, 300, 200)

SOURCE_PEAKLIST = 'SOURCE_PEAKLIST'
TARGET_PEAKLIST = 'TARGET_PEAKLIST'

DISTANCE_THRESHOLD = 'DISTANCE_THRESHOLD'

OVERWRITE = 'OVERWRITE'
ONLY_GOOD = 'ONLY_GOOD'

ASSIGN_SINGLE = 'ASSIGN_SINGLE'
ASSIGN_ALL = 'ASSIGN_ALL'


class TransferAssignmentsGui(PluginGUIModule):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._selectedSourcePeak = None
        self._selectedTargetPeak = None

        self._buildResultsArea()

    def _buildResultsArea(self):
        #row = self.mainWidget.layout().rowCount()
        row = 10

        self.resultsFrame = Frame(
            self.mainWidget,
            setLayout=True,
            grid=(row, 0),
            gridSpan=(1, 4)
        )

        r = 0

        self.statsLabel = Label(
            self.resultsFrame,
            text='No matches calculated',
            grid=(r, 0)
        )

        r += 1

        self.splitter = Splitter(
            self.resultsFrame,
            horizontal=False,
            grid=(r, 0)
        )

        self.sourceTable = Table(
            parent=self.splitter
        )

        self.targetTable = Table(
            parent=self.splitter
        )

        r += 1

        self.buttonFrame = Frame(
            self.resultsFrame,
            setLayout=True,
            grid=(r, 0)
        )

        self.assignSelectedButton = Button(
            self.buttonFrame,
            text='Assign Selected Target',
            callback=self._assignSelectedTarget,
            grid=(0, 0)
        )

        self.assignSingleButton = Button(
            self.buttonFrame,
            text='Assign Singly Matched',
            callback=self._assignSingle,
            grid=(0, 1)
        )

        self.assignClosestButton = Button(
            self.buttonFrame,
            text='Assign All To Closest',
            callback=self._assignClosest,
            grid=(0, 2)
        )

        self.sourceTable.selectionCallback = (
            self._sourceTableSelection
        )

        self.targetTable.selectionCallback = (
            self._targetTableSelection
        )

    def updateSourceTable(self, matchResults):
        rows = []

        for sourcePeak, matches in matchResults.items():
            rows.append({

                '_object': sourcePeak,

                '_peakPid': sourcePeak.pid,

                'Serial': sourcePeak.serial,

                'Assignment':
                    sourcePeak.annotation,

                'Matches':
                    len(matches),

                'Closest':
                    matches[0].distance
                    if matches else None,

                'Best Match':
                    matches[0].targetPeak.serial
                    if matches else None,
            })

        df = pd.DataFrame(rows)

        self.sourceTable.updateDf(df)

        self._matchResults = matchResults

        self._updateStatistics()

    def _populateTargetTable(self,
                             peakMatches):

        rows = []

        for match in peakMatches:
            rows.append({

                '_object': match,

                '_peakPid': match.targetPeak.pid,

                'Serial':
                    match.targetPeak.serial,

                'Assignment':
                    match.targetPeak.annotation,

                'Distance':
                    round(match.distance, 4),
            })

        df = pd.DataFrame(rows)

        self.targetTable.updateDf(df)

    def _sourceTableSelection(
            self,
            selected,
            deselected,
            selection,
            lastItem):

        if selection.empty:
            return

        row = selection.iloc[0]

        sourcePeak = row['_object']

        self._selectedSourcePeak = sourcePeak

        matches = self._matchResults.get(
            sourcePeak,
            []
        )

        self._populateTargetTable(matches)

        self.application.current.peaks = [
            sourcePeak
        ]

    def _targetTableSelection(
            self,
            selected,
            deselected,
            selection,
            lastItem):

        if selection.empty:
            return

        row = selection.iloc[0]

        peakMatch = row['_object']

        self._selectedTargetPeak = (
            peakMatch.targetPeak
        )

        self.application.current.peaks = [
            self._selectedSourcePeak,
            self._selectedTargetPeak
        ]

    def _updateStatistics(self):
        total = len(self._matchResults)

        matched = len([
            x
            for x in self._matchResults.values()
            if x
        ])

        unmatched = total - matched

        self.statsLabel.setText(
            f'Source Peaks: {total}    '
            f'Matched: {matched}    '
            f'Unmatched: {unmatched}'
        )



    def getWidgetDefinitions(self):

        return od((

            (
                SOURCE_PEAKLIST,
                {
                    'label': 'Source PeakList',
                    'type': objectPulldowns.PeakListPulldown,
                    'callBack': self._peakListsChanged,
                    'kwds': {
                        'labelText': 'Source PeakList',
                        'showSelectName': True,
                        'objectName': SOURCE_PEAKLIST,
                        'fixedWidths': SettingsWidgetFixedWidths,
                    }
                }
            ),

            (
                TARGET_PEAKLIST,
                {
                    'label': 'Target PeakList',
                    'type': objectPulldowns.PeakListPulldown,
                    'callBack': self._peakListsChanged,
                    'kwds': {
                        'labelText': 'Target PeakList',
                        'showSelectName': True,
                        'objectName': TARGET_PEAKLIST,
                        'fixedWidths': SettingsWidgetFixedWidths,
                    }
                }
            ),

            (
                DISTANCE_THRESHOLD,
                {
                    'label': 'Distance Threshold',
                    'type': compoundWidget.DoubleSpinBoxCompoundWidget,
                    'kwds': {
                        'labelText': 'Distance',
                        'value': 0.1,
                    }
                }
            ),

            (
                OVERWRITE,
                {
                    'label': 'Overwrite',
                    'type': compoundWidget.CheckBoxCompoundWidget,
                    'kwds': {
                        'labelText': 'Overwrite assignments'
                    }
                }
            ),

            (
                ONLY_GOOD,
                {
                    'label': 'Only Good',
                    'type': compoundWidget.CheckBoxCompoundWidget,
                    'kwds': {
                        'labelText': 'Only good matches'
                    }
                }
            ),

            (
                ASSIGN_SINGLE,
                {
                    'label': 'Assign Single',
                    'type': compoundWidget.ButtonCompoundWidget,
                    'callBack': self._assignSingle,
                    'kwds': {
                        'labelText': 'Action',
                        'text': 'Assign Singly Matched',
                    }
                }
            ),

            (
                ASSIGN_ALL,
                {
                    'label': 'Assign Closest',
                    'type': compoundWidget.ButtonCompoundWidget,
                    'callBack': self._assignClosest,
                    'kwds': {
                        'labelText': 'Action',
                        'text': 'Assign All To Closest',
                    }
                }
            ),

        ))

    def _peakListsChanged(self, *args):

        settings = self.getSettingsAsDict()

        self.sourcePeakList = self.project.getByPid(settings[SOURCE_PEAKLIST])
        self.targetPeakList = self.project.getByPid(settings[TARGET_PEAKLIST])

        self._updateMatches()

    def _calculateMatches(self):
        if not self.sourcePeakList or not self.targetPeakList:
            return

        isotopeCodes = self.sourcePeakList.spectrum.isotopeCodes

        self.plugin.matchEngine.threshold = (
            self.getSettingsAsDict()[DISTANCE_THRESHOLD]
        )

        return self.plugin.matchEngine.findMatches(
                self.sourcePeakList,
                self.targetPeakList,
                isotopeCodes,
                scales=None #TODO make user settable self._getScales()
        )

    def _updateMatches(self):

        self._matchResults = self._calculateMatches()

        if not self._matchResults:
            self.sourceTable.updateDf(pd.DataFrame())
            self.targetTable.updateDf(pd.DataFrame())

            self.statsLabel.setText(
                'No matches calculated'
            )
            return

        self.updateSourceTable(self._matchResults)
        self._updateStatistics()

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

    def _assignSingle(self):

        count = (
            AssignmentTransfer.assignSinglyMatched(
                self._matchResults,
                overwrite=self._getOverwrite()
            )
        )

        getLogger().info(
            f'Copied assignments to {count} target peaks'
        )

    def _assignClosest(self):

        count, unmatched = (
            AssignmentTransfer.assignAllToClosest(
                self._matchResults,
                overwrite=self._getOverwrite()
            )
        )

        if unmatched:
            getLogger().warning(
                f'{len(unmatched)} peaks had no matching target peak'
            )

        getLogger().info(
            f'Copied assignments to {count} target peaks'
        )



class TransferAssignmentsPlugin(PluginBase):

    def __init__(self, descriptor, application):

        super().__init__(descriptor, application)

        self.project = application.project

        self.ui = TransferAssignmentsGui

        self.matchEngine = MatchingEngine()

    def run(self, *args, **kwargs):

        sourcePeakList = self.project.getByPid(kwargs.get(SOURCE_PEAKLIST))
        targetPeakList = self.project.getByPid(kwargs.get(TARGET_PEAKLIST))

        overwrite = kwargs.get(OVERWRITE, False)

        threshold = kwargs.get(
            DISTANCE_THRESHOLD,
            0.1
        )

        mode = kwargs.get(
            'mode',
            'single'
        )

        if not sourcePeakList:
            return

        if not targetPeakList:
            return

        isotopeCodes = []

        try:
            isotopeCodes = (
                sourcePeakList.spectrum.isotopeCodes
            )
        except Exception:
            getLogger().info(f'\n No spectrum isotopeCodes found for sourcePeakList {sourcePeakList} \n')
            pass

        self.matchEngine.threshold = threshold

        matches = self.matchEngine.findMatches(
            sourcePeakList,
            targetPeakList,
            isotopeCodes,
            scales=None
        )

        if hasattr(self, 'guiModule'):

            self.guiModule.updateSourceTable(
                matches
            )

        if mode == 'single':

            count = (
                AssignmentTransfer.assignSinglyMatched(
                    matches,
                    overwrite=overwrite
                )
            )

        else:

            count, unmatched = (
                AssignmentTransfer.assignAllToClosest(
                    matches,
                    overwrite=overwrite
                )
            )

            if unmatched:
                getLogger().warning(
                    f'{len(unmatched)} peaks had no matching target peak'
                )

            getLogger().info(
                f'Copied assignments to {count} target peaks'
            )

        print(
            f'Transferred assignments '
            f'for {count} peaks'
        )

