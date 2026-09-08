from ccpn.ui.gui.modules.CcpnModule import CcpnModule
from ccpn.framework.Application import getApplication, getMainWindow, getCurrent, getProject
from ccpn.framework.plugins._GuiBaseFrame import FrameBase
from collections import OrderedDict as od

class PluginGUIModule(CcpnModule):
    maxSettingsState = 2
    settingsPosition = 'top'


    includeSettingsWidget = True

    def __init__(self, plugin, **kwargs):
        self.plugin = plugin
        self.mainWindow = getMainWindow()
        self.project = getProject()
        self.application = getApplication()
        self.current = getCurrent()
        super().__init__(mainWindow=self.mainWindow, name=self.plugin.name)
        self.frameWidgets = FrameBase(parent=self.mainWidget, guiObject=self)
        self.widgetDefinitions = self.getWidgetDefinitions()
        self.frameWidgets.initWidgets(self.widgetDefinitions)

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

    def _closeModule(self):
        self.plugin.close()
        super()._closeModule()