from collections import OrderedDict as od
import pandas as pd

from PyQt5 import QtWidgets

from ccpn.api import PluginBase, PluginGUIModule

import ccpn.ui.gui.widgets.PulldownListsForObjects as objectPulldowns
import ccpn.ui.gui.widgets.CompoundWidgets as compoundWidget
from ccpn.ui.gui.lib.StripLib import navigateToPositionInStrip, _getCurrentZoomRatio
from ccpn.ui.gui.widgets.CompoundWidgets import CheckBoxCompoundWidget
from ccpn.core.lib.peakUtils import getPeakAnnotation
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.Frame import Frame
from ccpn.ui.gui.widgets.SettingsWidgets import SpectrumDisplaySelectionWidget
from ccpn.ui.gui.widgets.Splitter import Splitter
from ccpn.ui.gui.widgets.table.Table import Table
from ccpn.ui.gui.widgets.CheckBox import CheckBox
from ccpn.ui.gui.widgets.DoubleSpinbox import DoubleSpinbox

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

        self._buildSettingsWidgets()
        self._buildResultsArea()


    def getWidgetDefinitions(self):
        '''The settings for the widgets that appear at the top of the module. Currently no management of the layout
        Plugin automatic construction style'''

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
            ))
        )


    def _buildResultsArea(self):
        '''Main widget area with peak tables and action buttons'''

        #row = self.mainWidget.layout().rowCount()
        row = 10

        self.resultsFrame = Frame(
            self.mainWidget,
            setLayout=True,
            grid=(row, 0),
            gridSpan=(1, 4)
        )

        r = 0

        self.refreshButton = Button(
            self.resultsFrame,
            text='Refresh Matches',
            callback=self._refreshMatches,
            grid=(r,0)
        )

        r += 1

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
            parent=self.splitter,
            callback=self._sourceTableSelection
        )

        self.targetTable = Table(
            parent=self.splitter,
            callback=self._targetTableSelection
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

    def _buildSettingsWidgets(self):
        '''Settings (cog) widgets'''

        row = 0

        texts = ['> select-to-add <', '<Use all>'] + [display.pid for display in self.application.ui.mainWindow.spectrumDisplays]
        self.displaySelectionWidget = SpectrumDisplaySelectionWidget(parent=self.settingsWidget, mainWindow=self.mainWindow,
                                                                     grid=(row, 0), gridSpan=(1, 1),
                                                                     labelText='Display(s)', texts=texts
                                                                     )
        row += 1
        self.markPositionCheckbox = CheckBoxCompoundWidget(parent=self.settingsWidget,
                                                                          grid=(row, 0), vAlign='top', stretch=(0, 0), hAlign='left',
                                                                          orientation='left',
                                                                          labelText='Mark Positions',
                                                                          checked=False,
                                                                          )

        row += 1
        self.clearMarksCheckbox = CheckBoxCompoundWidget(parent=self.settingsWidget,
                                                                        grid=(row, 0), vAlign='top', stretch=(0, 0), hAlign='left',
                                                                        orientation='left',
                                                                        labelText='Auto Clear Marks',
                                                                        tipText='Auto clear all previous marks',
                                                                        checked=False,
                                                                        )

        row += 1

        self.overwriteCheckBox = CheckBox(
            self.settingsWidget,
            checked=False,
            grid=(row, 1)
        )

        Label(
            self.settingsWidget,
            text='Overwrite Assignments',
            grid=(row, 0)
        )

        row += 1

        self.onlyGoodCheckBox = CheckBox(
            self.settingsWidget,
            checked=True,
            grid=(row, 1)
        )

        Label(
            self.settingsWidget,
            text='Only Good Matches',  # V2 hangover - filter for the targets table?
            grid=(row, 0)
        )
        row += 1

        Label(
            self.settingsWidget,
            text='1H Scale',
            grid=(row, 0)
        )

        self.hScaleSpinBox = DoubleSpinbox(
            self.settingsWidget,
            value=1.0,
            grid=(row, 1)
        )

        row += 1

        Label(
            self.settingsWidget,
            text='15N Scale',
            grid=(row, 0)
        )

        self.nScaleSpinBox = DoubleSpinbox(
            self.settingsWidget,
            value=0.2,
            grid=(row, 1)
        )

        row += 1

        Label(
            self.settingsWidget,
            text='13C Scale',
            grid=(row, 0)
        )

        self.cScaleSpinBox = DoubleSpinbox(
            self.settingsWidget,
            value=0.2,
            grid=(row, 1)
        )



    def updateSourceTable(self, matchResults):
        rows = []
        ndims = self.sourcePeakList.spectrum.dimensionCount

        for sourcePeak, matches in matchResults.items():
            row = {
                'Serial': sourcePeak.serial,
                'Matches': len(matches),
            }

            row.update({
                f'Ass D{dim + 1}':
                    getPeakAnnotation(sourcePeak, dim)
                for dim in range(ndims)
            })

            row['Closest'] = (
                matches[0].distance
                if matches else None
            )

            row['Best Match'] = (
                matches[0].targetPeak.serial
                if matches else None
            )

            row.update({
                '_object': sourcePeak,
                '_peakPid': sourcePeak.pid
            })

            rows.append(row)

        df = pd.DataFrame(rows)
        df['Best Match'] = df['Best Match'].astype('Int64')

        self.sourceTable.updateDf(df)

        self._matchResults = matchResults

        self._updateStatistics()

    def _populateTargetTable(self,
                             peakMatches):

        rows = []
        ndims = self.targetPeakList.spectrum.dimensionCount

        for match in peakMatches:
            row = {
                'Serial': match.targetPeak.serial,
                'Distance':
                    round(match.distance, 4)
            }

            row.update({
                f'Ass D{dim + 1}':
                    getPeakAnnotation(match.targetPeak, dim)
                for dim in range(ndims)
            })

            row.update({
                '_object': match.targetPeak,
                '_peakPid': match.targetPeak.pid
            })

            rows.append(row)

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

        self._navigateToPeak(sourcePeak)

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

        targetPeak = row['_object']

        self._selectedTargetPeak = targetPeak

        self.application.current.peaks = [
            self._selectedSourcePeak,
            self._selectedTargetPeak
        ]

        #TODO clear marks and mark self._selectedSourcePeak and self._selectedTargetPeak

    def _navigateToPeak(self, peak):

        if peak is None:
            return

        if self.clearMarksCheckbox.isChecked():
            self.mainWindow.clearMarks()

        displays = (
            self.displaySelectionWidget.getDisplays()
        )

        strips = [
            strip
            for display in displays
            for strip in display.strips
        ]

        strips = strips or [self.current.strip]

        for strip in strips:

            widths = None

            if peak.peakList.spectrum.dimensionCount <= 2:
                widths = _getCurrentZoomRatio(
                    strip.viewRange()
                )

            navigateToPositionInStrip(
                strip=strip,
                positions=peak.position,
                axisCodes=peak.axisCodes,
                widths=widths,
                markPositions=
                self.markPositionCheckbox.isChecked()
            )


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




    def _peakListsChanged(self, *args):

        settings = self.getSettingsAsDict()

        self.sourcePeakList = self.project.getByPid(settings[SOURCE_PEAKLIST])
        self.targetPeakList = self.project.getByPid(settings[TARGET_PEAKLIST])

        self._updateMatches()

    def _refreshMatches(self, *args):
        '''Called by the Refresh matches button. Probably superfluous: just call _updateMatches()'''

        self._updateMatches()


    def _calculateMatches(self):
        if not self.sourcePeakList or not self.targetPeakList:
            return

        isotopeCodes = self.sourcePeakList.spectrum.isotopeCodes

        self.plugin.matchEngine.threshold = (
            self.getSettingsAsDict()[DISTANCE_THRESHOLD]
        )

        scales = {
            '1H': self.hScaleSpinBox.get(),
            '15N': self.nScaleSpinBox.get(),
            '13C': self.cScaleSpinBox.get(),
        }

        return self.plugin.matchEngine.findMatches(
                self.sourcePeakList,
                self.targetPeakList,
                isotopeCodes,
                scales=scales
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

        if self._selectedSourcePeak is None:
            return

        if self._selectedTargetPeak is None:
            return

        overwrite = (
            self.overwriteCheckBox.isChecked()
        )

        AssignmentTransfer.copyAssignment(
            self._selectedSourcePeak,
            self._selectedTargetPeak,
            overwrite=overwrite
        )

        self.updateMatches()

    def _assignSingle(self):

        count = (
            AssignmentTransfer.assignSinglyMatched(
                self._matchResults,
                overwrite=self.overwriteCheckBox.isChecked()
            )
        )

        getLogger().info(
            f'Copied assignments to {count} target peaks'
        )

    def _assignClosest(self):

        count, unmatched = (
            AssignmentTransfer.assignAllToClosest(
                self._matchResults,
                overwrite=self.overwriteCheckBox.isChecked()
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

