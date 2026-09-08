from __future__ import annotations

"""
PluginLoader
------------
Utility functions for importing plugin modules and resolving entry points
specified in plugin descriptors. Used by PluginManager at runtime.


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


import importlib, sys, types
from typing import Any, Optional, Tuple

class PluginLoader:
    """
    Resolve a plugin entry point into a live Python object (module, function,
    class, or attribute) using setuptools-style syntax.

    Entry-point syntax (for `plugin_descriptor.json`)
    -------------------------------------------------
        <module>[:<attr>[.<subattr>...]]

    Examples:
        • Module only
            "entryPoint": "myplugin.plugin"

        • Function in module
            "entryPoint": "myplugin.plugin:run"

        • Class in module
            "entryPoint": "myplugin.plugin:MyClass"

        • Unbound method in a class
            "entryPoint": "myplugin.plugin:MyClass.run"

    Rules:
        • The part before `:` must be an importable module path.
        • `:` separates the module from the first attribute.
        • `.` traverses deeper attributes.
        • If `:` is omitted, the imported module is returned.

    Behaviour:
        • Returns modules, functions, classes, or attributes.
        • For class methods, this returns an *unbound* attribute.
        • Raises ValueError / ImportError / AttributeError for invalid input.

    Security:
        • Only resolve trusted entry points. Importing a module executes code.
    """
    classVersion = 1.0

    # ---------- public API ----------

    @staticmethod
    def resolveForDescriptor(descriptor: "PluginDescriptor") -> Any:
        """
        Resolve `descriptor.entryPoint`.

        :param descriptor: PluginDescriptor exposing `entryPoint: str`
        :return: The resolved Python object.
        :raises ValueError, ImportError, AttributeError
        """
        if not getattr(descriptor, "entryPoint", None):
            raise ValueError("Descriptor has no 'entryPoint'.")

        return PluginLoader.resolveEntryPoint(descriptor.entryPoint)

    @staticmethod
    def resolveEntryPoint(entryPoint: str, *, baseDir: Optional[str] = None) -> Any:
        """
        Resolve a setuptools-style entry point string.

        :param entryPoint: Entry point string
        :param baseDir: Ignored in setuptools-style resolution
        :return: The resolved Python object
        """
        if not entryPoint or not isinstance(entryPoint, str):
            raise ValueError("Entry point must be a non-empty string.")

        modulePath, attrChain = PluginLoader._splitModuleAndAttrs(entryPoint)

        module = importlib.import_module(modulePath)

        return PluginLoader._traverse(module, attrChain) if attrChain else module

    # ---------- internals ----------

    @staticmethod
    def _splitModuleAndAttrs(spec: str) -> Tuple[str, str]:
        """
        Split an entry point into (module, attrChain).
        """
        parts = spec.split(":", 1)
        return parts[0], parts[1] if len(parts) > 1 else ""

    @staticmethod
    def _traverse(obj: Any, chain: str) -> Any:
        """
        Traverse a dotted attribute chain on `obj`.
        """
        current = obj
        for part in chain.split("."):
            if not part:
                raise ValueError("Empty segment in attribute chain.")
            current = getattr(current, part)
        return current

    @staticmethod
    def _purgeModules(packageOrModule: str) -> None:
        """
        Remove a package/module and its submodules from sys.modules.

        Example:
            'myplugin' → drop 'myplugin' and 'myplugin.*'
        """
        prefix = packageOrModule + "."
        to_drop = [
            m for m in list(sys.modules)
            if m == packageOrModule or m.startswith(prefix)
            ]
        for m in to_drop:
            mod = sys.modules.get(m)
            # NOTE (future): if plugins need cleanup, define a __plugin_teardown__()
            # function inside the module to release resources (threads, files, etc.)
            sys.modules.pop(m, None)
