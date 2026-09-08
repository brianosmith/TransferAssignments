"""
 A module needed to create the Gui Widgets in the Preferences Popup.
 It is build as if was a Gui for the PluginManager and just in case eventually we want it out of the Preferences Popup.

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2025"
__credits__ = ("Ed Brooksbank, Morgan Hayward, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Daniel Thompson",
               "Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2025-08-20 12:43:21 +0100 (Wed, August 20, 2025) $"
__version__ = "$Revision: 3.3.3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu  $"
__date__ = "$Date: 2025-08-06 15:08:39 +0100 (Wed, August 06, 2025) $"
#=========================================================================================
# Start of code
#=========================================================================================

from functools import partial
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QSpacerItem, QSizePolicy
from ccpn.ui.gui.widgets.MessageDialog import showYesNoWarning, showWarning, showMessage, showYesNo
from PyQt5.QtGui import QPixmap
from ccpn.util.Logging import getLogger
from ccpn.framework.Application import getApplication
from ccpn.ui.gui.widgets.HLine import HLine, LabeledHLine
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.CheckBox import CheckBox
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.FilteringPulldownList import FilteringPulldownList
from ccpn.ui.gui.widgets.ButtonList import ButtonList

from ccpn.ui.gui.widgets.Frame import Frame, ScrollableFrame
import ccpn.ui.gui.widgets.CompoundWidgets as cw
from ccpn.ui.gui.guiSettings import getColours, DIVIDER

FILTERS = ['All', 'Enabled', 'Disabled', 'Built-in', 'Installed']
RELOAD = 'Reload'
LOAD = 'Load'
UPDATE = 'Update'
MORE = 'More...'

class PluginPreferencesFrame(Frame):
    """
    scroll area
    Filter:  pulldown:   show all, disabled, enabled, built-in, user
    install: from disk...  from url...
    disable/enable all/ update all
    layout:
        -- icon Name,                          Update button, checkbox enable
        -- Version, Author name
        -- more...

     -- more: popup with tabs?
     Settings, metadata, release info, certificate?
    """

    def __init__(self, parent=None, **kwds):
        super().__init__(parent, setLayout=True, **kwds)
        self.application = getApplication()
        if self.application is None:
            raise RuntimeError('Cannot continue without application')
        self._lineColour = getColours()[DIVIDER]
        self.pluginManager = self.application.pluginManager
        self._controlToolFrame = Frame(self, setLayout=True, grid=(0,0), margins=(0,0,0,0))
        self._pluginListFrameWidget = ScrollableFrame(parent=self, setLayout=True, grid=(1, 0), margins=(0,0,0,0))
        self._buildControlTools()
        self._buildPluginList()


    def _buildControlTools(self):
        from ccpn.ui.gui.popups.PreferencesPopup import PulldownListsMinimumWidth
        row = 0
        _label = Label(self._controlToolFrame, text='Install New From', grid=(row, 0), hAlign='r', bold=False)
        installNewFromButton = ButtonList(self._controlToolFrame, grid=(row, 1), hAlign='l', hPolicy='fixed', texts=['Disk...', 'Url...'], callbacks=[None, None], enabled=False)

        row += 1
        _label = Label(self._controlToolFrame, text='Filter By', grid=(row, 0), hAlign='r', bold=False)
        self.filterPulldown = FilteringPulldownList(self._controlToolFrame, orientation='l', texts=FILTERS, grid=(row,1), enabled=False, )
        row += 1
        _label = Label(self._controlToolFrame, text='Bulk Actions', grid=(row, 0), hAlign='r', bold=False)
        actionButtons = ButtonList(self._controlToolFrame, grid=(row, 1), hAlign='l', hPolicy='fixed',  texts=['Disable All', 'Enable All', 'Update All'], callbacks=[None]*3, enabled=False)

        row += 1

        self._controlToolFrame.getLayout().setAlignment(Qt.AlignCenter)
        self._controlToolFrame.getLayout().setContentsMargins(50,10,50,10)

    def _buildPluginList(self):

        row = 0
        result = LabeledHLine(self._pluginListFrameWidget, text='Available Plugins', grid=(row, 0), gridSpan=(1, 2), colour=self._lineColour, height=30, enabled=False)

        row += 1
        # Alphabetically Sorted for start. Once plugins will grow, we can think of funcy systems.
        descriptorsDict = dict(sorted(self.pluginManager._descriptors.items()))
        for pluginName, descriptor in descriptorsDict.items():
            isEnabled = self.pluginManager.isEnabled(pluginName)
            iconPath = descriptor.getIconPath()
            pixmap = QPixmap(str(iconPath)).scaled(
                    50, 50,
                    Qt.IgnoreAspectRatio,  # force exact size
                    Qt.SmoothTransformation
                    )

            # ~~ widgets
            outerFrame = Frame(self._pluginListFrameWidget, setLayout=True, grid=(row,0) , showBorder=True,
                           fShape='styledPanel', fShadow='raised', margins=(10,10,10,10))
            outerFrame.getLayout().setAlignment(Qt.AlignCenter)
            _icon = Label(outerFrame, grid=(0, 0), icon=pixmap, )
            outerFrame.getLayout().addItem(QSpacerItem(10, 0, QSizePolicy.Expanding, QSizePolicy.Minimum), 0, 1)

            frame =  Frame(outerFrame, setLayout=True, grid=(0,1))
            _innerRow = 0
            _label = Label(frame, text=f'{pluginName}', grid=(_innerRow, 0), hAlign='r', bold=True)
            _checkBox = CheckBox(frame, grid=(_innerRow, 1), hAlign='l', hPolicy='minimal', tipText='Set Enabled/Disabled', checked=isEnabled,
                                 callback=partial(self._toggleEnablePlugin, pluginName),)
            _innerRow += 1
            _updateButton = ButtonList(frame, grid=(_innerRow, 1), hAlign='l', hPolicy='minimal', texts=[RELOAD, UPDATE, MORE],
                                       callbacks=[partial(self._reloadPlugin, pluginName), None, None],
                                       enabled=True,
                                 callback=None, spacing=(0, 0))
            self._toggleReloadNameButton(_updateButton.getButton(RELOAD), pluginName)
            _updateButton.getButton(UPDATE).setEnabled(False)
            _updateButton.getButton(MORE).setEnabled(False)

            _versionValueLabel = Label(frame, grid=(_innerRow, 0), hAlign='r', hPolicy='minimal', text=f'<i>Version:</i> {descriptor.version}')
            _innerRow += 1
            _authorValueLabel = Label(frame, grid=(_innerRow, 0), hAlign='r', hPolicy='minimal', text=f'<i>Author:</i> {descriptor.author}')

            row += 1

    def _toggleReloadNameButton(self, button, pluginName):
        isLoaded = self.pluginManager.isLoaded(pluginName)
        button.setText(LOAD if not isLoaded else RELOAD)


    def _toggleEnablePlugin(self, pluginName, checked):
        """  Update the plugin preferences to reflect the plugin's enabled state. load/unload if enabled/disabled  """
        pluginManager = self.application.pluginManager
        pluginManager.enablePluginOnPreferences(pluginName, checked)

    def _reloadPlugin(self, pluginName):
        isEnabled = self.pluginManager.isEnabled(pluginName)
        if not isEnabled:
            showWarning('Plugin Not Enabled', 'Please enable the plugin by ticking the checkbox next to its name.')
            return
        try:
            self.pluginManager.reloadPlugin(pluginName)
        except Exception as err:
            msg = f'Error reloading Plugin; {pluginName}.\n{err}'
            getLogger().warning(msg)
            showWarning('Reload Failed', msg)
            return

        # let's redo the menus if needed
        pluginDescriptor = self.pluginManager._descriptors.get(pluginName)
        if pluginDescriptor is not None and not pluginDescriptor.menuTitle in [None, '']:
            # we could reload the titles only if it has changed.
            self.pluginManager._registerLazyMenus(self.application.mainWindow)
        self._toggleReloadNameButton(self.sender(), pluginName)
