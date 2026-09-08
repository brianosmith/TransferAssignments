from ccpn.ui.gui.popups.Dialog import CcpnDialogMainWidget
from ccpn.framework.plugins._GuiBaseFrame import FrameBase
from collections import OrderedDict as od
from ccpn.framework.Application import getApplication, getMainWindow, getCurrent, getProject

class PluginBasePopup(CcpnDialogMainWidget):
    """

    """
    FIXEDWIDTH = True
    FIXEDHEIGHT = False

    title = 'Demo Base Popup'

    def __init__(self, plugin, **kwargs):
        self.plugin = plugin
        super().__init__(None, windowTitle=plugin.name,  setLayout=True,  **kwargs)
        self.mainWindow = getMainWindow()
        self.frameWidgets = FrameBase(parent=self.mainWidget, guiObject=self)
        self.widgetDefinitions = self.getWidgetDefinitions()
        self.frameWidgets.initWidgets(self.widgetDefinitions)
        self.setOkButton(callback=self._runCallback, text='Run ', enabled=True)
        self.setCloseButton(callback=self.reject, tipText='Close')

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

    def _runCallback(self, *args, **kwargs):
        self.plugin.run(**self.getSettingsAsDict())

    def getWidget(self, name):
        return self.frameWidgets.getWidget(name)

    def getSettingsAsDict(self):
        return self.frameWidgets.getSettingsAsDict()
