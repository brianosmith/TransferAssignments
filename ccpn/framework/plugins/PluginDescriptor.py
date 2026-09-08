"""

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
__dateModified__ = "$dateModified: 2025-08-13 12:18:38 +0100 (Wed, August 13, 2025) $"
__version__ = "$Revision: 3.3.3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu  $"
__date__ = "$Date: 2025-08-06 15:08:39 +0100 (Wed, August 06, 2025) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.util.traits.CcpNmrJson import Constants, update, CcpNmrJson
from ccpn.util.traits.CcpNmrTraits import Unicode, Dict, List, Bool, Int, Float
from collections import defaultdict, OrderedDict
from ccpn.framework.plugins import pluginNamespaces as pluginVariables
from ccpn.util.Path import aPath
from ccpn.util.Logging import getLogger

class PluginDescriptor(CcpNmrJson):
    """
    The Plugin Metadata json file descriptor.
    Represents the metadata for a plugin, loaded from 'plugin_descriptor.json'.
    This defines the valid json descriptor file for a plugin to be discovered and work properly. You can create a template from the PluginManager,
    simply call the method  'createPluginDescriptorFileTemplate(path)'
    """

    # ~~~~~~ Required Fields ~~~~~~~~~
    name = Unicode(allow_none=False, default_value='My CcpNmr Plugin').tag(info='The unique name of the plugin.')
    version = Unicode(allow_none=False, default_value='').tag(info='Version string of the plugin.')
    author = Unicode(allow_none=False, default_value='').tag(info='Author of the plugin.')
    entryPoint = Unicode(allow_none=False, default_value='').tag(info='Dotted path to the callable or module.')

    # ~~~~~ Loading Behaviour ~~~~~
    loadLevel = Int(allow_none=False, default_value=0).tag(info='When the plugin should be loaded: "0:STARTUP", "1:UI", "2:ON-DEMAND".')

    # ~~~~~~ Optional Fields ~~~~~~~~~
    url = Unicode(allow_none=True, default_value='').tag(info='URL (e.g., GitHub or HTTP) where the plugin package can be downloaded.')
    type = Unicode(allow_none=True, default_value='Gui Module').tag(info='Declares what kind of plugin this is (e.g., function, popup).')
    description = Unicode(allow_none=True, default_value='').tag(info='Short description of the plugin.' )
    enabledByDefault = Bool(allow_none=False, default_value=True).tag(info='Whether the plugin should be enabled by default.')
    tags = List(Unicode(), default_value=[]).tag(info='List of tags or categories for the plugin.')

    # ~~~~~ UI Integration ~~~~~

    menuTitle = Unicode(allow_none=True, default_value='').tag( info='The menu title that will appear on the Plugins Menu. If load level is 3 and Gui module or Popup')
    menuShortcut = Unicode(allow_none=True, default_value='').tag(info='Keyboard shortcut (e.g. "P+E") if applicable.')
    menuIcon = Unicode(allow_none=True, default_value='').tag(info='Path to an icon file relative to plugin root.')
    menuTooltip = Unicode(allow_none=True, default_value='').tag(info='Tooltip or hover text for the plugin menu item.')

    # ~~~~~~ Internal Plugin Fields  ~~~~~~~~~
    _isInternalPlugin = Bool(allow_none=False, default_value=False).tag(info='True if is a built-in CcpNmr plugin')

    # ~~~~~~ Internal System Fields  ~~~~~~~~~

    _JSON_FILE = None
    classVersion = 1.0
    saveAllTraitsToJson = True

    def __init__(self, filePath):
        super().__init__()
        if filePath is not None:
            self._JSON_FILE = filePath
            self.loadFromFile(self._JSON_FILE)
            self.rootDir: aPath = filePath.parent  # base for relative entry points

    def loadFromFile(self, filePath):
        if filePath is None:
            return
        self.restore(filePath)

    def _encode(self):
        """
        Serialise this object into a dictionary of {trait: value} for JSON storage,
        to facilitate user readability and ease of manual editing if required.

        The traits are ordered according to their order defined in the class,
        with the special `_metadata` trait (Constants.METADATA) always placed last in the output.

        Ordering the traits in this way ensures:
          - Consistent and predictable key order in the saved JSON, matching the class definition.
          - Improved human readability when viewing or editing plugin metadata files.
          - The `_metadata` block is visually separated at the end of the file, making it easier
            to spot versioning and provenance information without interrupting the main data section.

        """
        # get all traits that need saving to json
        traitsToEncode = [Constants.METADATA]
        for trait in self.keys():
            _saveTraitToJson = self.trait_metadata(traitname=trait, key='saveToJson', default=None)
            if _saveTraitToJson is None:
                _saveTraitToJson = bool(self.saveAllTraitsToJson)

            if _saveTraitToJson:
                traitsToEncode.append(trait)

        # create a dict of trait: value
        dataDict = {}
        for trait in traitsToEncode:
            handler = self._getJsonHandler(trait)
            if handler is not None:
                dataDict[trait] = handler().encode(self, trait)
            else:
                dataDict[trait] = getattr(self, trait)
        items = [(val._traitOrder, key) for key, val in self.class_traits().items()]
        sorted_items = sorted(items, key=lambda x: (x[0] == 0, x[0]))
        orderedDataDict = OrderedDict((key, dataDict[key]) for _, key in sorted_items)
        return orderedDataDict

    def saveToFile(self, filePath=None):
        """
        :param filePath: A valid path
        :return: the filepath where the json has been saved
        """
        validName = pluginVariables.PLUGIN_DESCRIPTOR_FILE_NAME
        filePath = aPath(filePath)
        if filePath.is_dir():
            filePath = filePath / validName
        if not filePath.name == validName:
            getLogger().warning(f'Plugin descriptor file name has to be of a valid name. Replaced {filePath.name} with {validName}')
            filePath = filePath.filepath / validName
        self.save(filePath)
        return filePath

    def getIconPath(self):
        """Get the absolute Icon Path if defined in the Descriptor """
        if not self.menuIcon:
            return
        iconRelPath = aPath(self.menuIcon)
        absPath = self.rootDir / iconRelPath
        return absPath




PluginDescriptor.register()
