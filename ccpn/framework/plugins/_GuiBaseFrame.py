from __future__ import annotations

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
__dateModified__ = "$dateModified: 2025-08-18 17:38:26 +0100 (Mon, August 18, 2025) $"
__version__ = "$Revision: 3.3.3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu  $"
__date__ = "$Date: 2025-08-06 15:08:39 +0100 (Wed, August 06, 2025) $"

#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtCore, QtWidgets
from collections import OrderedDict as od
from ccpn.util.Logging import getLogger
from ccpn.ui.gui.widgets.Frame import Frame
import ccpn.ui.gui.widgets.SettingsWidgets as settingWidgets
from ccpn.ui.gui.widgets.Spacer import Spacer


class FrameBase(Frame):
    """
    A temporary frame to hold widgets
    """

    def __init__(self, parent, guiObject,  *args, **Framekwargs):
        Frame.__init__(self, setLayout=True, **Framekwargs)
        self.parent = parent
        self.guiObject = guiObject
        self.getLayout().setAlignment(QtCore.Qt.AlignTop)
        self._widget = None # the widgets the collects all autogen widgets
        self.widgetDefinitions = self.getWidgetDefinitions()


    def getWidgetDefinitions(self) -> od:
        """ Override in subclass. Define the widgets in an orderedDict.
        See ccpn.ui.gui.widgets.SettingsWidgets.ModuleSettingsWidget. Example:
            od((
                (WidgetVarName,
                {'label': Label_toShow,
                'type': WidgetClass-not-init,
                'kwds': {'text': Label_toShow,
                       'height': 30,
                       'gridSpan': (1, 2),
                       'tipText': TipText}})
            ))
        """
        return od()

    def initWidgets(self, widgetDefinitions):
        mainWindow = self.guiObject.mainWindow
        self._widget = settingWidgets.ModuleSettingsWidget(parent=self.parent, mainWindow=mainWindow,
                                                                         settingsDict=widgetDefinitions,
                                                                         grid=(0, 0))
        self._widget.getLayout().setAlignment(QtCore.Qt.AlignLeft)
        Spacer(self, 0, 2, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding,
               grid=(1, 0), gridSpan=(1, 1))

    def postInitWidgets(self):
        pass

    def closeEvent(self, event):
        from ccpn.ui.gui.lib.WidgetClosingLib import CloseHandler

        with CloseHandler(self):
            super().closeEvent(event)

    def getWidget(self, name):
        if self._widget is not None:
            w = self._widget.getWidget(name)
            return w

    def getSettingsAsDict(self):
        settingsDict = {}
        for varName, widget in self._widget.widgetsDict.items():
            try:
                settingsDict[varName] = widget._getSaveState()
            except Exception as e:
                getLogger().warn('Could not find get for: varName, widget',  varName, widget, e)
        return settingsDict

    def _commonCallback(self, *args):
        self.guiObject.settingsChanged.emit(self.getSettingsAsDict())
