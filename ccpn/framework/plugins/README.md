# Plugin System Overview

This plugin system is **descriptor-driven** and **discovery-based** - **declarative**, not prescriptive.

Unlike traditional plugin architectures that rely on subclassing or registering specific classes, this system uses a lightweight, flexible model where each plugin is defined by a descriptor, the `plugin_descriptor.json` file, and the whole plugin can take various forms — from a single function to a full UI component.

🔁 Philosophy

We don’t tell users how to build their plugin.
Users tell us what their plugin does — and we make it work.

✅ Benefits
•	Maximum freedom for plugin developers
•	Loose coupling between core and plugin code
•	Simple, explicit integration
•	Scales well across plugin types
•	Minimal friction to start using it

## ✨ Key Concepts

- **Descriptor-driven:** Each plugin is declared using a `plugin_descriptor.json` file.
- **Discovery-based:** The system scans plugin directories to locate and load plugins dynamically.
- **No ABC required:** Plugins do not need to inherit from a base class or follow a strict interface, but we provide templates
- **Extremely flexible:** A plugin can be a module, a function, a UI widget, or even just an action.

## 📦 What Is a Plugin?

A plugin is any self-contained Python code that provides functionality and is described by a `plugin_descriptor.json` file.

A plugin can be:

- ✅ A public method (e.g., `myplugin.export_data`)
- ✅ A module with a `run()` function
- ✅ A popup GUI window
- ✅ A context menu item
- ✅ Any callable Python object

## Create Your First Plugin:  Minimal Plugin Structure

To create a valid plugin, the following minimal structure is required:
myplugin/
├── plugin_descriptor.json   # Required: declares the plugin
├── plugin.py                        # Required: defines the entry point (can be empty or callable)
├── README.md                 # Optional but Recommended: describes the plugin’s purpose and usage
├── LICENSE                       # Optional but Recommended: defines licensing for distribution

### 🔑 Required Files

- **`plugin_descriptor.json`**
  Describes the plugin’s name, entry point, and metadata.
  Example:

  ```json
  {
    "name": "MyPlugin",
    "entryPoint": "plugin.run",
    "version": "0.0.1",
    "author": "Bob"
  }
  ```
- **`plugin.py`**
  Makes the plugin a Python package. Can be empty, or contain the `entryPoint` function directly:

  ```python
  def run(**kwargs):
      print("Plugin executed with", kwargs)
  ```

## 🔁 Plugin `loadLevel` Comparison


| Level | `loadLevel` | When It Loads                 | Intended Use                        | When Entry Point Executes       |
| ----- | ----------- | ----------------------------- | ----------------------------------- | ------------------------------- |
| 0     | `startup`   | During application startup    | Core services, patchers, observers  | Immediately at startup          |
| 1     | `ui`        | After UI is initialised       | Panels, UI components, integrations | After UI is ready (auto)        |
| 2     | `onDemand`  | When user explicitly triggers | Scripts, tools, export actions      | When user triggers (menu/click) |

> All plugins are **discovered** at startup via their `plugin_descriptor.json`,
> but only those matching the current `loadLevel` are **loaded and executed**.


## CCPN code Plugin management file structure

  ```python
  ccpn/
└─ framework/
      └─ plugins/
            ├─ pluginNamespaces.py
            ├─ PluginDescriptor.py
            ├─ PluginLoader.py
            ├─ PluginScanner.py
            ├─ PluginManager.py
            ├─ PluginBase.py
            ├─ PluginUiBase.py
            ├─ hookHub.py            #pluggy integration
            └─ external/
                ├─ externalToolRunner.py
                └─ toolJob.py         # runner + (optional) watcher coordination---
  ```
