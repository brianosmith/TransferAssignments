"""
 A module  that contains only reusable namespaces

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
__dateModified__ = "$dateModified: 2025-08-12 19:40:43 +0100 (Tue, August 12, 2025) $"
__version__ = "$Revision: 3.3.3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu  $"
__date__ = "$Date: 2025-08-06 15:08:39 +0100 (Wed, August 06, 2025) $"
#=========================================================================================
# Start of code
#=========================================================================================

# ~~~ File naming
PLUGIN_DESCRIPTOR_FILE_NAME = 'plugin_descriptor.json'

# ~~~ Supported plugin types
PLUGIN_TYPE_FUNCTION     = 'function'
PLUGIN_TYPE_MODULE       = 'module'
PLUGIN_TYPE_MENU_ITEM    = 'menuItem'
PLUGIN_TYPE_POPUP        = 'popup'
PLUGIN_TYPE_PROCESSOR    = 'processor'
PLUGIN_TYPE_CONTEXT_ITEM = 'contextItem'
PLUGIN_TYPE_TOOLBAR      = 'toolbar'
PLUGIN_TYPE_PANEL        = 'panel'
PLUGIN_TYPE_UNKNOWN      = 'unknown'

# ~~~ Loading plugin types
PLUGIN_LOAD_STARTUP   = 'STARTUP'
PLUGIN_LOAD_UI   = 'UI'
PLUGIN_LOAD_ONDEMAND   = 'ON-DEMAND'

DESCRIPTOR = 'descriptor'
ENTRY = 'entry'
MODULE = 'module' # this is used for a Python Library module . Not  to be confused with the "ccpn gui module" nomenclature !
RESOLVED_ENTRY_POINT = 'resolvedEntryPoint'
ENABLED_PLUGINS = 'enabledPlugins'
DISABLED_PLUGINS = 'disabledPlugins'

AUTHOR = 'author'
ENABLED_BY_DEFAULT = 'enabledByDefault'
