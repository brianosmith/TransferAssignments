"""
PluginManager: Descriptor-based plugin system

This manager handles discovery and activation of plugins using JSON descriptors.
Plugins do not need to inherit from a base class or follow a strict interface.

Supported plugin types:
    - Python functions (via dotted entryPoint)
    - Modules with `run()` functions
    - UI components
    - Menu/context actions
    - Any callable object declared in plugin_descriptor.json

See plugins/README.md for structure, examples, and best practices.

"""

#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2026"
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
__dateModified__ = "$dateModified: 2026-03-03 16:05:23 +0000 (Tue, March 03, 2026) $"
__version__ = "$Revision: 3.5.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu  $"
__date__ = "$Date: 2025-08-06 15:08:39 +0100 (Wed, August 06, 2025) $"
#=========================================================================================
# Start of code
#=========================================================================================

import sys
import importlib, sys, types
import io
import zipfile
import requests
from functools import partial
from types import ModuleType
from typing import Any, Callable, Dict, List, Optional
from ccpn.util.Path import aPath, fetchDir
from ccpn.framework.Preferences import Preferences
from ccpn.util.Logging import getLogger
from ccpn.framework.PathsAndUrls import pluginPath, userCcpnPath
from ccpn.framework.plugins.PluginDescriptor import PluginDescriptor
from ccpn.framework.plugins.PluginLoader import PluginLoader
from ccpn.framework.plugins import pluginNamespaces as pluginVariables
from ccpn.framework.plugins.PluginBase import PluginBase
from ccpn.framework.plugins.PluginExternalToolRunner import ExternalProcessRunner
from ccpn.framework.plugins.PluginFileWatcher import PluginFileWatcher

class PluginManager:
    """
    Manages discovery, registration, and lifecycle of plugins. Headless.

    Features:
        - Discovers plugins in a directory.
        - Loads plugins dynamically.
        - Tracks enabled/disabled.
         - Initialises enabled plugins.
        - Publishes and subscribes to events.
        - install from url (github etc)

    Plugin Load Workflow:
        1.	Discover descriptors — Scan for plugin_descriptor.json
        2.	Check enabled state —  check preferences for disabled and enabled. Use enabledByDefault  for first time
        3.	Resolve entry point and load the plugin — Import and validate the entryPoint
        4.	Store Load plugin — Store in the registry dict with metadata and loaded module
        5.	Integrate / initialise — start or hook into UI, menus, pipelines, etc.

    """

    classVersion = 1.0

    def __init__(self, application, autoLoad=True) -> None:
        """
        Initialise the Plugin Manager.
        """
        self.application = application
        self.preferences = self._getUserPreferences()
        self.ccpnPluginsDirPath = aPath(pluginPath)
        self._userPluginsDirPath: Optional[aPath] = None  # Dynamically set. See property below
        self._registerPluginRootPath(self.userPluginsPath)
        self._registerPluginRootPath(self.ccpnPluginsDirPath)

        # Utility Tools
        self.externalProcessRunner = ExternalProcessRunner
        self.fileWatcher = PluginFileWatcher

        # Plugin Load Workflow
        # ~~ Discover descriptors
        self._descriptors: dict[str, PluginDescriptor] = {}
        self.discoverPlugins()

        #  ~~ Set AutoEnabled in CCPN Preferences/Plugins unless they were previously disabled by the user
        self._setAutoEnabledToPreferences()

        #  ~~ Load from Resolved entry points
        self._registeredPlugins: dict[str, dict[str, Any]] = {} # it’s a dictionary of plugin records see "pluginRegistry" property
        if autoLoad:
            self._loadPlugins(level=0)

    # ----------------------
    # Public API
    # ----------------------

    @property
    def pluginRegistry(self) -> dict[str, dict[str, Any]]:
        """
        Read-only access to the registry of all successfully loaded plugins.

        Each plugin record contains:
            - 'descriptor': The PluginDescriptor object with metadata
            - 'entry':      The resolved plugin object (function/class/etc.)
            - 'module':     The imported module

        :return: A dictionary mapping plugin names to their plugin records.
        """
        return self._registeredPlugins

    def createPluginDescriptorFileTemplate(self, filePath) -> None:
        """
        Create a template plugin descriptor file with default values.
        :param filePath: Path where the descriptor file will be created.
        :return: None
        """
        from ccpn.framework.plugins.PluginDescriptor import PluginDescriptor
        handler = PluginDescriptor(None)
        handler.saveToFile(filePath=filePath)

    def installPluginFromUrl(self, url: str) -> aPath:
        """
        Download and install a plugin from a remote ZIP URL into the user plugins path.
        Then rediscover plugins so the new one is available.
        """
        pluginPath = self._downloadAndExtract(url, self.userPluginsPath)

        # Re-run discovery so the new plugin gets picked up
        self.discoverPlugins(internal=False, external=True)

        return pluginPath

    def discoverPlugins(self, internal: bool = True, external: bool = True) -> dict:
        """
        Discover available plugins and collect their descriptors.

        This method scans the configured plugin directories for valid plugin
        descriptor files (e.g., ``plugin.json``) using the :class:`PluginScanner`.

        Args:
        :param internal:  If ``True``, scan the internal (built‑in) plugins directory
                located at :attr:`ccpnPluginsDirPath`.
        :param external: If ``True``, scan the external (user‑installed) plugins
                directory located at :attr:`userPluginsPath`.

        Notes:
            - This method only discovers and collects plugin descriptors.
              It does not import or initialise the plugin modules.
            - The descriptors returned by :class:`PluginScanner` can be used
              later by the plugin manager to validate and load plugins.
            - Both internal and external scans may be enabled simultaneously.
        """
        from ccpn.framework.plugins.PluginScanner import PluginScanner
        self._descriptors.clear()
        descriptors = []
        if internal:
            descriptors = PluginScanner(self.ccpnPluginsDirPath).scan()
            _ = [setattr(d, '_isInternalPlugin', True) for d in descriptors]

        if external:
            descriptors += PluginScanner(self.userPluginsPath).scan()
        for descriptor in descriptors:
            self._descriptors[descriptor.name] = descriptor
        return self._descriptors

    def loadPlugin(self, name: str) -> None:
        """
        Load an enabled plugin by name.
        """
        return self._loadPluginByName(name)


    def isLoaded(self, name: str) -> bool:
        """

        Check if a plugin is currently enabled.
        """

        return True if self.pluginRegistry.get(name) else False

    def enablePluginOnPreferences(self, name, enabled:bool):
        self._setPluginEnabledInPreferences(name, enabled=enabled)
        self._registerLazyMenus(self.application.mainWindow)

    def getEnabledPlugins(self):
        return self._getPluginListFromPreferences(pluginVariables.ENABLED_PLUGINS)

    def getDisabledPlugins(self):
        return self._getPluginListFromPreferences(pluginVariables.DISABLED_PLUGINS)

    def isEnabled(self, name):
        return name in self.getEnabledPlugins()

    @property
    def userPluginsPath(self) -> aPath:
        path = self._userPluginsDirPath or self._getUserPluginsPath()
        return aPath(path)

    @userPluginsPath.setter
    def userPluginsPath(self, path:str):
        self._userPluginsDirPath = path




    # ------------------------------------------------------------------------------------------------------
    # Private Methods
    # ------------------------------------------------------------------------------------------------------

    ## ~~~ Loading helpers ~~~~


    def _registerLazyMenus(self, mainWindow):
        from ccpn.ui.gui.widgets.Menu import PLUGINSMENU, CCPNPLUGINSMENU

        userPluginsSubMenu = mainWindow.searchMenuAction(PLUGINSMENU)
        internalPluginsSubMenu = mainWindow.searchMenuAction(CCPNPLUGINSMENU)
        userPluginsSubMenu.clear() #clear all to don't mess with ordering or complex checking
        internalPluginsSubMenu.clear()
        for pluginName, pluginDescriptor in self._descriptors.items():
            _isInternalPlugin = pluginDescriptor._isInternalPlugin
            isEnabled = self.isEnabled(pluginName)
            menuTitle = pluginDescriptor.menuTitle
            if not menuTitle:
                continue
            if _isInternalPlugin:
                action = internalPluginsSubMenu.addAction(menuTitle, partial(self._menuActionCallback, pluginName))
            else:
                action = userPluginsSubMenu.addAction(menuTitle,  partial(self._menuActionCallback, pluginName))

            action.setEnabled(isEnabled)

    def _menuActionCallback(self, pluginName, *args):
        """On menu item clicked lazy load the plugin if not already loaded
        and show the ui if any otherwise run the run method"""

        self.loadPlugin(pluginName)
        # create the instance
        # run the show if it has UI or the run methods
        loadedRegistry = self.loadPlugin(pluginName) or {}
        if not loadedRegistry:
            getLogger().warning('Plugin not registered or found')
            return

        resolvedClass = loadedRegistry.get(pluginVariables.RESOLVED_ENTRY_POINT)
        descriptor = loadedRegistry.get(pluginVariables.DESCRIPTOR)

        if issubclass(resolvedClass, PluginBase):
            plugin = resolvedClass(descriptor, self.application)
            plugin.show()

    def _loadPlugins(self, level:int):
        if not self._descriptors:
            return
        getLogger().info(f"Loading level {level} plugins:\n")
        for pluginName in self._descriptors:
            descriptor = self._descriptors[pluginName]
            if descriptor.loadLevel == level:
                self._loadPluginByName(pluginName)


    def _loadPluginByName(self, pluginName: str):
        if pluginName in self.pluginRegistry:
            return self.pluginRegistry[pluginName]
        usersEnabledPlugins = self.getEnabledPlugins()
        usersDisablePlugins = self.getDisabledPlugins()

        descriptor = self._descriptors.get(pluginName)
        if not descriptor:
            return
        enabledByDefault = descriptor.enabledByDefault
        if enabledByDefault and pluginName in usersDisablePlugins:
            getLogger().debug('Cannot load a User-disabled plugin even if is enabledByDefault')
            return
        if enabledByDefault or descriptor.name in usersEnabledPlugins:
            if pluginRecord := self._loadFromDescriptor(descriptor):
                self.pluginRegistry[descriptor.name] = pluginRecord
                return pluginRecord


    def unloadPlugin(self, pluginName: str, setEnable:bool=True) -> None:
        """
        Unload a plugin by name.
        Best‑effort unload:
          1) call shutdown hooks
          2) unhook UI/watchers/etc. NIY
          3) purge sys.modules for the plugin package/submodules
          4) drop registry entry
        """
        reg = self.pluginRegistry.get(pluginName)
        if not reg:
            getLogger().warning(f"Plugin '{pluginName}' is not currently loaded.")
            return

        # 1) shutdown hooks
        obj = reg.get(pluginVariables.RESOLVED_ENTRY_POINT)
        try:
            if hasattr(obj, "close") and callable(obj.close):
                obj.close()
        except Exception as e:
            getLogger().warning(f"[PluginManager] {pluginName}.close() raised: {e}")

        # 2) TODO: unhook everything attached by the plugin like
        #    - disconnect Qt signals / remove menus & actions
        #    - stop file watchers, timers, threads, subprocesses
        #    - unregister event/notifier subscriptions,  hooks
        #    - revert monkey patches if any

        # 3) purge modules by entry point’s module name
        descriptor = reg.get(pluginVariables.DESCRIPTOR)
        if descriptor:
            try:
                modulePath, attrChain = PluginLoader._splitModuleAndAttrs(descriptor.entryPoint)
                PluginLoader._purgeModules(modulePath)
            except Exception as e:
                getLogger().warning(f"[PluginManager] purge skipped for '{pluginName}': {e}")

        # 4) drop registry entry
        self.pluginRegistry.pop(pluginName, None)

        #  5) disable it
        self._setPluginEnabledInPreferences(pluginName, enabled=setEnable)


    def reloadPlugin(self, pluginName: str, *, setEnabled: bool = True) -> Optional[dict[str, Any]]:
        """
        Full reload from entryPoint string:
          - unload
          - import fresh
          - (optionally) instantiate/initialise
          - re‑register record
        Returns the new registry record or None on failure.
        """
        descr = self._descriptors.get(pluginName)
        if not descr:
            raise RuntimeError(f"Reload failed: '{pluginName}' not found")
        reg = self.pluginRegistry.get(pluginName)

        if not reg: # never loaded before
            return self._loadPluginByName(pluginName)
        # unload first
        try:
            self.unloadPlugin(pluginName)
        except Exception as e:
            getLogger().warning(f"[PluginManager] unload before reload failed for '{pluginName}': {e}")

        # Load fresh
        self.discoverPlugins()
        return self._loadPluginByName(pluginName)


    def _registerPluginRootPath(self, pluginRoot: aPath) -> None:
        """
        Ensure the given top-level pluginRoot directory is on sys.path.
        This allows importing plugins as packages, e.g.:
            from myPlugin import plugin
        :param pluginRoot: Path to the directory that contains all plugin packages.
        """
        pathStr = str(pluginRoot.resolve())
        if pathStr not in sys.path:
            sys.path.insert(0, pathStr)

    def _loadFromDescriptor(self, descriptor) -> Optional[dict[str, Any]]:
        """
        Load and optionally initialise a plugin from its descriptor.

        Splits the process into:
          - Importing the module
          - Resolving the entry point
        Returns a structured plugin record for storage.

        :param descriptor: PluginDescriptor with at least 'name' and 'entryPoint'
        :return: A dict with 'entry', 'module', 'descriptor', or None on failure.
        """
        name = descriptor.name

        try:
        # if True:
            resolvedEntryPoint = PluginLoader.resolveForDescriptor(descriptor)
            getLogger().info(f"\u2003{name} loaded. \n")

            return {
                pluginVariables.DESCRIPTOR   : descriptor,
                pluginVariables.RESOLVED_ENTRY_POINT:  resolvedEntryPoint,
                }

        except Exception as e:
            getLogger().warning(f"Failed to load plugin '{name}': {e}")
            return None

    def _downloadAndExtract(self, url: str, targetDir: aPath) -> Optional[aPath]:
        """
        Download a ZIP archive from the given URL and extract it into targetDir.
        Only returns the extracted plugin root if it contains plugin_descriptor.json.

        :param url: Direct link to the ZIP file (e.g., GitHub archive URL).
        :param targetDir: Directory where the plugin should be extracted.
        :return: Path to the extracted plugin directory, or None if invalid.
        :raises Exception: On download or extraction failure.
        """
        targetDir.mkdir(parents=True, exist_ok=True)

        # Download
        resp = requests.get(url, stream=True)
        resp.raise_for_status()

        # Extract into targetDir
        with zipfile.ZipFile(io.BytesIO(resp.content)) as z:
            z.extractall(targetDir)

        # Detect plugin folder (GitHub zips often contain a single top-level dir)
        extractedDirs = sorted(
                [d for d in targetDir.iterdir() if d.is_dir()],
                key=lambda p: p.stat().st_mtime,
                reverse=True
                )

        for folder in extractedDirs:
            if (folder / pluginVariables.PLUGIN_DESCRIPTOR_FILE_NAME).exists():
                return folder

        return None




    ## ~~~ Preferences helpers ~~~~

    def _getUserPreferences(self):
        """
        Fetch Preferences from the loading application or from file.
        """
        if self.application is not None:
            return self.application.preferences
        try:
            preferences = Preferences(None)._getUserPreferences()
            return preferences
        except Exception as err:
            getLogger().warning('Unable to load user preferences.')

    def _getUserPluginsPath(self) -> Optional[str]:
        """
        Resolve the user plugin path from preferences if available.
        Returns:
            The path from preferences.general.userPluginPath, or fetch default if not set.
        """
        if not self.preferences or not hasattr(self.preferences, "general"):
            return None
        userPluginPath = getattr(self.preferences.general, "userPluginPath", None)
        if userPluginPath is None or not aPath(userPluginPath).exists():
            userPluginPath = fetchDir(userCcpnPath, 'plugins')
            setattr(self.preferences.general, "userPluginPath", userPluginPath)
        return userPluginPath

    def _getPluginListFromPreferences(self, key: str) -> list[str]:
        """
        Generic getter for plugin lists from preferences.

        :param key: Either 'enabledPlugins' or 'disabledPlugins'
        :return: List of plugin names, or empty list if unavailable
        """
        foundDescriptors = list(self._descriptors.keys())
        pluginsPrefs = getattr(self.preferences, "plugins", None)
        foundInPreferences = list(getattr(pluginsPrefs, key, [])) if pluginsPrefs else []
        return [i for i in foundInPreferences if i in foundDescriptors]

    def _setPluginEnabledInPreferences(self, name: str, enabled: bool) -> None:
        """
        Set plugin as enabled or disabled in preferences. Ensures mutual exclusivity.

        :param name: Plugin name
        :param enabled: True to enable, False to disable
        """
        if name not in self._descriptors:
            raise ValueError('Cannot enable/disable a non available Plugin')
        pluginsPrefs = getattr(self.preferences, "plugins", None)
        if not pluginsPrefs:
            return

        for lst in (pluginsPrefs.enabledPlugins, pluginsPrefs.disabledPlugins):
            if name in lst:
                lst.remove(name)

        target = pluginsPrefs.enabledPlugins if enabled else pluginsPrefs.disabledPlugins
        target.append(name)

    def _setAutoEnabledToPreferences(self):
        """We need to ensure the plugins with the descriptors defined as AutoEnabled are set as enabled in the preferences list. Note a plugin could have been seen before and already disabled by the user, in that case
         it will appear in preferences as disabled"""
        autoEnabledList = [i for i in self._descriptors if self._descriptors[i].enabledByDefault]
        disabledList = self.getDisabledPlugins()
        for i in autoEnabledList:
            if i not in disabledList:
                self._setPluginEnabledInPreferences(i, True)


# m = PluginManager()
