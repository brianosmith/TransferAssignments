"""
 A module needed to create the object that scans the plugin directory for valid plugins.
 PluginScanner → Discovery only
    •	Walks the directory structure.
    •	Looks for required files (metadataFile.json).
    •	Optionally validates metadata format.
    •	Returns metadata and paths, but does not import or execute any plugin code.

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
__dateModified__ = "$dateModified: 2025-08-12 19:40:42 +0100 (Tue, August 12, 2025) $"
__version__ = "$Revision: 3.3.3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu  $"
__date__ = "$Date: 2025-08-06 15:08:39 +0100 (Wed, August 06, 2025) $"
#=========================================================================================
# Start of code
#=========================================================================================


from typing import List, Dict, Any
import json
from ccpn.util.Path import aPath, fetchDir
from ccpn.util.Logging import getLogger
from ccpn.framework.plugins import pluginNamespaces as pluginVariables
from ccpn.framework.plugins.PluginDescriptor import PluginDescriptor

class PluginScanner:
    """
    Scans a plugin directory and identifies valid plugins
    based on the presence of required files such as 'plugin_descriptor.json' .
    Note: this object only job is to discover plugin and to load the metadata, NOT to load the plugin in the main program. the PluginManager will do the loading etc.
    """
    classVersion = 1.0

    def __init__(self, pluginDir: str) -> None:
        self.pluginDir = aPath(pluginDir)
        self.metadataFilename = pluginVariables.PLUGIN_DESCRIPTOR_FILE_NAME

    def scan(self) -> List[PluginDescriptor]:
        """
        Scan the plugin directory for valid plugins.
        It is a dry, passive, read-only operation.
        It just reads metadata files, parses them, validates them, and logs failures.
        Returns: List of metadata dictionaries for valid plugins.
        """
        foundPlugins = []
        for entry in self.pluginDir.iterdir():
            if entry.is_dir():
                metadataPath = entry / self.metadataFilename
                if metadataPath.is_file():
                    getLogger().info(f"[PluginScanner] found metadata in {metadataPath}. Ready to load")
                    try:
                        descriptor = self._loadMetadata(metadataPath)
                        foundPlugins.append(descriptor)
                        getLogger().info(f"[PluginScanner] loaded {descriptor}.")

                    except Exception as e:
                        getLogger().warning(f"[PluginScanner] Invalid metadata in {metadataPath}: {e}. This Plugin won't be loaded")
        return foundPlugins

    def _loadMetadata(self, metadataPath: aPath) -> PluginDescriptor:
        """
        Load plugin metadata from a JSON file.
        :param metadataPath:  Path to the metadata JSON file.
        :return: the valid pluginDescriptor
        """
        pluginDescriptor = PluginDescriptor(metadataPath)
        return pluginDescriptor

