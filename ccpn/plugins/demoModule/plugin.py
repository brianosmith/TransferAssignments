import sys

from ccpn.api import PluginBase, PluginGUIModule
from collections import OrderedDict as od
import ccpn.ui.gui.widgets.PulldownListsForObjects as objectPulldowns
import ccpn.ui.gui.widgets.CompoundWidgets as compoundWidget

SettingsWidgetFixedWidths = (200, 350, 350)

SOURCE_PEAKLIST = 'SOURCE_PEAKLIST'
RUN_BUTTON = 'RUN_BUTTON'


class DemoGuiModule(PluginGUIModule):
    """A class to create the GUI element of the plugin as a GuiModule """

    def getWidgetDefinitions(self) :
        """
        An OrderedDict describing the GUI widgets for this plugin.
        Each entry defines one widget, keyed by its variable name, with metadata
        such as label, type (class, not instance), and keyword arguments for
        initialisation. The order controls how widgets are displayed in the GUI.
        :return: OrderedDict of widgets defs
        """
        self.widgetDefinitions = od((
            (SOURCE_PEAKLIST,
             {'label': 'PeakList',
              'tipText': 'Select a PeakList',
              'callBack': None,
              'type': objectPulldowns.PeakListPulldown,
              'kwds': {'labelText': 'PeakList',
                       'tipText': 'Select a PeakList',
                       'filterFunction': None,
                       'showSelectName':True,
                       'objectName': SOURCE_PEAKLIST,
                       'fixedWidths': SettingsWidgetFixedWidths}}),

            (RUN_BUTTON,
             {'label'   : 'Run The Plugin',
              'tipText' : 'Run The Plugin',
              'callBack': self._runCallback,
              'type'    : compoundWidget.ButtonCompoundWidget,
              '_init'   : None,
              'kwds'    : {'labelText'  : 'Run',
                           'text'       : 'Execute',  # this is the Button name
                           'hAlign'     : 'left',
                           'tipText'    : 'Run The Plugin',
                           'fixedWidths': SettingsWidgetFixedWidths}}),
            ))
        return self.widgetDefinitions



class MyCcpnModule(PluginBase):
    def __init__(self,  descriptor, application):
        """
             Plugin initialisation. Called automatically by the PluginManager.

             Framework-provided arguments:
                   :param descriptor: Metadata object describing the plugin (name, version, entry point, etc.).
                   :param application: Reference to the main application instance, used to access
                                       shared services such as project data, managers, and configuration.
             Notes:
               - These parameters are injected by the plugin manager and are not intended to be supplied by end users.
        """
        super().__init__(descriptor, application)
        self.ui = DemoGuiModule # we need to attach the Gui element here. See class above

    def run(self, *args, **kwargs):
        """
        Default entry point for executing a plugin action.
        This method is called automatically when the user clicks *Run* in the plugin’s GUI if there is a GUI element.
        By default this method does nothing. Subclasses should override it
        to implement the plugin’s behaviour. Typical uses include:

          • Running an external command or script via the provided process runner
          • Attaching a file watcher to monitor results and feed them back into the project
          • Performing a direct action on the current project (e.g. adding, updating, or analysing data)

        The keyword arguments (`kwargs`) are automatically populated from
        the plugin’s GUI layer, based on the widgets defined in
        `getWidgetDefinitions()`. Each widget contributes its value under
        the symbolic name you assigned there.
        """
        sys.stdout.write(f"\n Run method called with arguments: {kwargs}")