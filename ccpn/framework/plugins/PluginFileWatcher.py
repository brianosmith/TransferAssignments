from __future__ import annotations


"""
    A file watcher system for external plugins.
    
    Provides a unified wrapper interface around different backend file-watcher
    implementations. Currently uses a Qt-based watcher that requires a running
    QApplication. Designed for future extension to alternative backends such as
    Watchdog for headless, non-Qt environments.
    See below for full docs. 

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
__dateModified__ = "$dateModified: 2025-08-18 13:10:29 +0100 (Mon, August 18, 2025) $"
__version__ = "$Revision: 3.3.3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu  $"
__date__ = "$Date: 2025-08-06 15:08:39 +0100 (Wed, August 06, 2025) $"

#=========================================================================================
# Start of code
#=========================================================================================


import time
from typing import Any, Callable, Iterable, Optional, TypeAlias, TypedDict
from contextlib import contextmanager
from PyQt5.QtCore import QFileSystemWatcher, QTimer
from ccpn.util.Path import aPath, Path



# =========================
# Wrapper (public entry)
# =========================

class PluginFileWatcher:
    """
        Create a file/directory watcher for a plugin.

        The watcher observes the given paths and reports meaningful changes (create, delete,
        modify) via a callback. Name filters are applied to files; directories are always
        considered (then their children are filtered). When recursive mode is enabled,
        subdirectories are also watched up to a maximum depth. Optionally, changes detected
        in deep subfolders can be “bubbled up” and reported as a single event at the root.

        :param application:
            The running application instance. A Qt event loop must be available (QApplication).
            In headless “NoUi” mode this watcher is not supported.

        :param plugin:
            Human‑readable name of the owning plugin. Included in every callback payload.

        :param paths:
            Iterable of paths (files and/or directories) to watch. Directories are watched
            non‑recursively by default; set ``recursive=True`` to include subdirectories.

        :param callback:
            Function invoked on change events. Signature:
            ``callback(info: dict) -> None`` where ``info`` contains:
                - ``timestamp`` (float): time.time()
                - ``plugin`` (str): plugin name
                - ``path`` (str): path of the directory or file where the change was detected
                - ``kind`` (str): "dir" or "file"
                - ``changed`` (dict): sets of names under keys "created", "deleted", "modified"
                - ``exists`` (bool): whether the path still exists at emit time
                - ``entryCount`` (int|None): number of direct children (dirs only)
                - ``totalSize`` (int|None): sum of file sizes among direct children (dirs only)
                - ``size`` (int|None): file size (files only)
                - ``mtime_ns`` (int|None): last modified time in nanoseconds

        :param delaySeconds:
            Stabilisation delay (quiet time) before emitting a change after the OS signal
            arrives. Helps coalesce bursts during saves/copies. Default: 0.4 seconds.

        :param notify:
            Optional logger/printer for internal status messages, called as ``notify(str)``.

        :param includeSuffixes:
            Optional set of lowercase file suffixes to include (e.g. {".txt", ".json"}).
            If provided, only files with these suffixes are reported. Directories are not
            filtered by suffix.

        :param excludeSuffixes:
            Optional set of lowercase file suffixes to exclude (e.g. {".tmp", ".log"}).
            Applied after ``includeSuffixes``. Directories are not filtered by suffix.

        :param ignoreHidden:
            If ``True`` (default), ignore hidden names (dot‑files like ``.foo``).

        :param ignoreNames:
            Optional set of exact names to ignore (e.g. {".DS_Store", "Thumbs.db"}).
            System junk files are ignored by default; your entries are added to that list.

        :param eventFilter:
            Optional predicate ``(info: dict) -> bool``. If provided and it returns ``False``
            for an event payload, the event is dropped (final veto hook).

        :param recursive:
            If ``True``, watch subdirectories as well. New subdirectories created later are
            armed automatically. Be mindful of very large trees and OS watcher limits.

        :param maxDepth:
            Maximum recursion depth when ``recursive=True``. ``0`` means only the root
            directory itself; ``1`` includes its direct children, etc. Default: 5.

        :param bubbleUp:
            If ``True``, changes in subdirectories are also emitted as an event at the
            original root path, with names prefixed by their relative subpath
            (e.g. ``"sub/inner/file.txt"``). This simplifies consumers that only want to
            listen at the root level.

        :param trackDirectories:
            If ``True`` (default), directory names are included in the ``changed`` sets for directory events.
            If ``False``, only file names are reported; directory name changes are omitted.

        :param dirEventsRequireIncludedFiles:
            If ``True``, directory events are only emitted when at least one file passes the current include/exclude filters.
            Pure directory changes (creation/deletion/rename) or changes caused only by non-matching files are suppressed.

        :raises RuntimeError:
            If ``application`` is ``None`` or if running in a headless “NoUi” environment.

        Behaviour notes:
            - Suffix filters apply to files only; directories always pass filtering so that
              their eligible children can be considered.
            - Simply opening a folder in a file manager does not trigger notifications unless
              it results in actual creates/deletes/modifications after filtering.
            - Use ``suspendEvents()`` as a context manager to silence callbacks during
              bulk writes you perform programmatically.
        """


    def __init__(
        self,
        application,
        *,
        plugin: str,
        paths: Optional[Iterable[aPath]] = None,
        callback: Optional[callable] = None,
        delaySeconds: float = 0.4,
        notify: Optional[Callable[[str], None]] = None,
        includeSuffixes: Optional[set[str]] = None,
        excludeSuffixes: Optional[set[str]] = None,
        ignoreHidden: bool = True,
        ignoreNames: Optional[set[str]] = None,
        eventFilter: Optional[callable] = None,
        recursive: bool = False,
        maxDepth: int = 5,
        bubbleUp: bool = False,
        trackDirectories: bool = True,
        dirEventsRequireIncludedFiles: bool = False,
    ) -> None:
        params = {k: v for k, v in locals().items() if k != "self"}

        if application is None:
            raise RuntimeError("An application must be set for the file watcher to work")

        if getattr(getattr(application, "args", None), "interface", None) == "NoUi":
            raise RuntimeError("This feature has not yet been implemented")

        self._impl = QtPluginFileWatcher(**params)

    def __getattr__(self, name: str):
        return getattr(self._impl, name)


# =========================
# Base (ABC-lite contract)
# =========================
class PluginFileWatcherBase:
    PathLike: TypeAlias = str | Path

    class ChangeInfo(TypedDict, total=False):
        timestamp: float
        plugin: str
        path: str
        kind: str  # "file" | "dir"
        changed: dict[str, set[str]]  # {"created","deleted","modified"} (names only)
        exists: bool
        entryCount: int | None
        totalSize: int | None
        size: int | None
        mtime_ns: int | None

    ChangeCallback: TypeAlias = Callable[[ChangeInfo], None]
    EventFilter:   TypeAlias = Callable[[ChangeInfo], bool]

    def __init__(
        self,
        application,
        *,
        plugin: str,
        paths: Optional[Iterable[PathLike]] = None,
        callback: Optional[ChangeCallback] = None,
        delaySeconds: float = 0.4,
        notify: Optional[Callable[[str], None]] = None,
        includeSuffixes: Optional[set[str]] = None,  # e.g. {".txt",".json"}
        excludeSuffixes: Optional[set[str]] = None,  # e.g. {".tmp",".log"}
        ignoreHidden: bool = True,                   # skip dot-files by default
        ignoreNames: Optional[set[str]] = None,      # e.g. {".DS_Store"}
        eventFilter: Optional[EventFilter] = None,   # final veto hook
        bubbleUp: bool = False,
        recursive: bool = False,
        maxDepth: int = 5,
        trackDirectories: bool = True,
        dirEventsRequireIncludedFiles: bool = False,
    ) -> None:
        self.application = application
        self.plugin = plugin
        self._suspended = False
        self._paths = list(paths or [])
        self._callback = callback
        self._delaySeconds = delaySeconds
        self._bubbleUp = bool(bubbleUp)
        self._notify = notify or (lambda _m: None)

        # filters
        self._include = {s.lower() for s in includeSuffixes} if includeSuffixes else None
        self._exclude = {s.lower() for s in excludeSuffixes} if excludeSuffixes else set()
        self._ignoreHidden = bool(ignoreHidden)
        self._ignoreNames = {".DS_Store", "Icon\r", "Thumbs.db"} | set(ignoreNames or ())
        self._eventFilter = eventFilter

        # recursion controls
        self._recursive = bool(recursive)
        self._maxDepth = int(maxDepth)

        # directory event policy
        self._trackDirectories = bool(trackDirectories)
        self._dirEventsRequireIncludedFiles = bool(dirEventsRequireIncludedFiles)

    # abstract-ish API
    def watchPaths(self, paths: Iterable[PathLike]) -> None: ...
    def addPath(self, path: PathLike) -> None: ...
    def removePath(self, path: PathLike) -> None: ...
    def clear(self) -> None: ...
    def stop(self) -> None: ...
    def isWatching(self, path: PathLike) -> bool: ...

    @contextmanager
    def suspendEvents(self):
        was_suspended = self._suspended
        self._suspended = True
        try:
            yield
        finally:
            self._suspended = was_suspended

    def _emitChange(self, info: dict):
        if not self._suspended and self._callback:
            self._callback(info)

    # -------- filter helpers --------
    def _acceptName(self, name: str, *, isDir: bool) -> bool:
        if self._ignoreHidden and name.startswith("."):
            return False
        if name in self._ignoreNames or name.startswith("._"):
            return False
        if not isDir:
            suffix = aPath(name).suffix.lower()
            if self._include is not None and suffix not in self._include:
                return False
            if suffix in self._exclude:
                return False
        return True

    def _acceptPath(self, p: aPath) -> bool:
        if p.is_file():
            return self._acceptName(p.name, isDir=False)
        return True

    def _maybeEmit(self, info: ChangeInfo) -> None:
        if self._eventFilter and not self._eventFilter(info):
            return
        if self._callback:
            try:
                self._callback(info)
            except Exception as e:
                self._notify(f"[PluginFileWatcher] callback error: {e}")


# =========================
# Qt backend (QFileSystemWatcher + delay + diffs + recursion)
# =========================
class QtPluginFileWatcher(PluginFileWatcherBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._fsw = QFileSystemWatcher()
        self._fsw.fileChanged.connect(self._onFileChanged)
        self._fsw.directoryChanged.connect(self._onDirChanged)

        self._debounceMs = int(max(0.0, self._delaySeconds) * 1000)
        self._timers: dict[aPath, QTimer] = {}

        # snapshots
        # value: (mtime_ns, size) where size=-1 marks a directory
        self._dirSnapshots: dict[aPath, dict[str, tuple[int, int]]] = {}
        self._fileState: dict[aPath, tuple[bool, int, int]] = {}  # (exists, size, mtime_ns)

        # recursion book-keeping
        self._watchedDirs: set[aPath] = set()
        self._roots: set[aPath] = set()

        if self._paths:
            self.watchPaths(self._paths)

    # --- public API ---
    def watchPaths(self, paths: Iterable[PluginFileWatcherBase.PathLike]) -> None:
        for p in paths:
            P = aPath(p).resolve()
            self._ensureTimer(P)
            if P.is_dir():
                self._roots.add(P)
                if self._recursive:
                    self._armDirRecursive(P)
                else:
                    self._armDir(P)
            else:
                self._armFile(P)

    def addPath(self, path: PluginFileWatcherBase.PathLike) -> None:
        self.watchPaths([path])

    def removePath(self, path: PluginFileWatcherBase.PathLike) -> None:
        P = aPath(path).resolve()
        self._stopTimer(P)
        sP = str(P)
        if sP in self._fsw.files():
            self._fsw.removePath(sP)
        if sP in self._fsw.directories():
            self._fsw.removePath(sP)
        self._dirSnapshots.pop(P, None)
        self._fileState.pop(P, None)
        self._watchedDirs.discard(P)
        self._roots.discard(P)

    def clear(self) -> None:
        files = self._fsw.files()
        dirs = self._fsw.directories()
        if files:
            self._fsw.removePaths(files)
        if dirs:
            self._fsw.removePaths(dirs)
        for t in self._timers.values():
            t.stop()
            t.deleteLater()
        self._timers.clear()
        self._dirSnapshots.clear()
        self._fileState.clear()
        self._watchedDirs.clear()
        self._roots.clear()

    def clear(self) -> None:
        files = self._fsw.files()
        dirs = self._fsw.directories()
        if files:
            self._fsw.removePaths(files)
        if dirs:
            self._fsw.removePaths(dirs)
        # Disconnect (ok if already disconnected)
        try:
            self._fsw.fileChanged.disconnect()
        except Exception:
            pass
        try:
            self._fsw.directoryChanged.disconnect()
        except Exception:
            pass
        # Kill timers
        for t in self._timers.values():
            try:
                t.stop(); t.deleteLater()
            except Exception:
                pass
        self._timers.clear()
        # Reset bookkeeping
        self._dirSnapshots.clear()
        self._fileState.clear()
        self._watchedDirs.clear()
        self._roots.clear()


    def stop(self) -> None:
        """Full teardown (call when you’re done for good)."""
        self.clear()
        try:
            self._fsw.deleteLater()
        except Exception:
            pass


    def isWatching(self, path: PluginFileWatcherBase.PathLike) -> bool:
        sP = str(aPath(path).resolve())
        return sP in self._fsw.files() or sP in self._fsw.directories()

    # --- arming helpers ---
    def _armDir(self, D: aPath) -> None:
        sD = str(D)
        if sD not in self._fsw.directories():
            try:
                self._fsw.addPath(sD)
            except Exception:
                pass
        self._dirSnapshots[D] = self._snapshotDir(D) if D.exists() else {}
        self._watchedDirs.add(D)

    def _iterDirs(self, root: aPath, *, depth: int) -> Iterable[aPath]:
        if not root.exists() or not root.is_dir():
            return []
        out: list[aPath] = []
        stack: list[tuple[aPath, int]] = [(root, depth)]
        while stack:
            d, lvl = stack.pop()
            out.append(d)
            if lvl >= self._maxDepth:
                continue
            try:
                for child in d.iterdir():
                    if child.is_dir() and self._acceptName(child.name, isDir=True):
                        stack.append((child, lvl + 1))
            except FileNotFoundError:
                pass
        return out

    def _armDirRecursive(self, root: aPath) -> None:
        for d in self._iterDirs(root, depth=0):
            sD = str(d)
            if sD not in self._fsw.directories():
                try:
                    self._fsw.addPath(sD)
                except Exception:
                    pass
            if d not in self._dirSnapshots:
                self._dirSnapshots[d] = self._snapshotDir(d) if d.exists() else {}
            self._watchedDirs.add(d)

    def _armFile(self, P: aPath) -> None:
        self._fileState[P] = self._probeFile(P)
        if P.exists() and P.is_file() and str(P) not in self._fsw.files():
            try:
                self._fsw.addPath(str(P))
            except Exception:
                pass
        parent = P.parent
        if parent.is_dir() and str(parent) not in self._fsw.directories():
            try:
                self._fsw.addPath(str(parent))
            except Exception:
                pass
            self._dirSnapshots.setdefault(parent, self._snapshotDir(parent))
            self._watchedDirs.add(parent)

    def _findRootFor(self, p: aPath) -> Optional[aPath]:
        sp = str(p)
        for r in self._roots:
            sr = str(r)
            if sp == sr or sp.startswith(sr + "/") or sp.startswith(sr + "\\"):
                return r
        return None

    # --- Qt slots + debounce ---
    def _onDirChanged(self, changedPath: str) -> None:
        P = aPath(changedPath).resolve()
        self._ensureTimer(P).start(self._debounceMs)

        # re-arm any watched files under this dir
        for F in list(self._fileState.keys()):
            if F.parent == P and F.exists() and str(F) not in self._fsw.files():
                try:
                    self._fsw.addPath(str(F))
                except Exception:
                    pass

        # keep recursive watches in sync
        if self._recursive and P.exists() and P.is_dir():
            self._reconcileSubtree(P)

    def _onFileChanged(self, changedPath: str) -> None:
        P = aPath(changedPath).resolve()
        self._ensureTimer(P).start(self._debounceMs)
        if not P.exists():  # keep last known to emit 'deleted'
            ex, sz, mt = self._fileState.get(P, (False, 0, 0))
            self._fileState[P] = (False, sz, mt)

    def _ensureTimer(self, P: aPath) -> QTimer:
        t = self._timers.get(P)
        if t:
            return t
        t = QTimer()
        t.setSingleShot(True)
        t.setInterval(self._debounceMs)
        t.timeout.connect(lambda p=P: self._emitFor(p))
        self._timers[P] = t
        return t

    def _stopTimer(self, P: aPath) -> None:
        t = self._timers.pop(P, None)
        if t:
            t.stop()
            t.deleteLater()

    # --- reconcile subtree (recursive) ---
    def _reconcileSubtree(self, root: aPath) -> None:
        current = set(self._iterDirs(root, depth=0))
        # add new dirs
        toAdd = current - self._watchedDirs
        if toAdd:
            try:
                self._fsw.addPaths([str(d) for d in toAdd])
            except Exception:
                pass
            for d in toAdd:
                self._watchedDirs.add(d)
                self._dirSnapshots.setdefault(d, self._snapshotDir(d) if d.exists() else {})
        # remove dirs that disappeared beneath root
        def _isUnder(candidate: aPath, top: aPath) -> bool:
            return str(candidate).startswith(str(top))
        toRemove = {d for d in self._watchedDirs if _isUnder(d, root)} - current
        if toRemove:
            drop = [str(d) for d in toRemove if str(d) in self._fsw.directories()]
            if drop:
                try:
                    self._fsw.removePaths(drop)
                except Exception:
                    pass
            for d in toRemove:
                self._watchedDirs.discard(d)
                self._dirSnapshots.pop(d, None)

    # --- emit payload (with filters applied) ---
    def _emitFor(self, P: aPath) -> None:
        now = time.time()

        # directory branch
        if P.is_dir() or P in self._dirSnapshots:
            exists = P.exists() and P.is_dir()
            old = self._dirSnapshots.get(P, {})
            new = self._snapshotDir(P) if exists else {}

            created, deleted, modified = self._diff(old, new)

            # classify and filter using size=-1 marker (dirs) vs files
            def _is_dir_from(map_, name):  # size == -1 => directory
                return (map_.get(name, (0, -1))[1] == -1)

            # keep separate buckets for files/dirs so we can apply policy
            created_files  = {n for n in created  if not _is_dir_from(new, n)  and self._acceptName(n, isDir=False)}
            created_dirs   = {n for n in created  if     _is_dir_from(new, n)  and self._acceptName(n, isDir=True)}
            deleted_files  = {n for n in deleted  if not _is_dir_from(old, n)  and self._acceptName(n, isDir=False)}
            deleted_dirs   = {n for n in deleted  if     _is_dir_from(old, n)  and self._acceptName(n, isDir=True)}
            modified_files = {n for n in modified if not _is_dir_from(new or old, n) and self._acceptName(n, isDir=False)}
            modified_dirs  = {n for n in modified if     _is_dir_from(new or old, n) and self._acceptName(n, isDir=True)}

            # immediately arm new sub-dirs when recursive
            if self._recursive:
                for n in created_dirs:
                    self._armDirRecursive(P / n)

            # apply directory event policy
            if not self._trackDirectories:
                # drop dir names entirely (files only)
                created_dirs = deleted_dirs = modified_dirs = set()

            if self._dirEventsRequireIncludedFiles:
                has_file_change = bool(created_files or deleted_files or modified_files)
                if not has_file_change:
                    # no interesting files changed; suppress this dir event
                    self._dirSnapshots[P] = new if exists else {}
                    return

            created_all  = created_files  | created_dirs
            deleted_all  = deleted_files  | deleted_dirs
            modified_all = modified_files | modified_dirs

            if not (created_all or deleted_all or modified_all):
                self._dirSnapshots[P] = new if exists else {}
                return

            self._dirSnapshots[P] = new if exists else {}
            info: PluginFileWatcherBase.ChangeInfo = {
                "timestamp": now,
                "plugin": self.plugin,
                "path": str(P),
                "kind": "dir",
                "changed": {"created": created_all, "deleted": deleted_all, "modified": modified_all},
                "exists": exists,
                "entryCount": len(new) if exists else 0,
                "totalSize": sum(sz for (_, sz) in new.values() if sz >= 0) if exists else 0,
                "mtime_ns": (P.stat().st_mtime_ns if exists else None),
            }

            if self._bubbleUp:
                root = self._findRootFor(P)
                if root and root != P:
                    rel_prefix = str(P.relative_to(root))
                    def _prefixed(names: set[str]) -> set[str]:
                        return {f"{rel_prefix}/{n}" for n in names}
                    bubbled = {
                        "timestamp": info["timestamp"],
                        "plugin": info["plugin"],
                        "path": str(root),
                        "kind": "dir",
                        "changed": {
                            "created": _prefixed(created_all),
                            "deleted": _prefixed(deleted_all),
                            "modified": _prefixed(modified_all),
                        },
                        "exists": True,
                        "entryCount": info.get("entryCount"),
                        "totalSize": info.get("totalSize"),
                        "mtime_ns": info.get("mtime_ns"),
                    }
                    self._maybeEmit(bubbled)
                    return

            self._maybeEmit(info)
            return

        # file branch
        prev = self._fileState.get(P, (False, 0, 0))
        cur  = self._probeFile(P)
        self._fileState[P] = cur

        if P.exists() and P.is_file() and not self._acceptPath(P):
            return

        created  = {P.name} if (not prev[0] and cur[0]) else set()
        deleted  = {P.name} if (prev[0] and not cur[0]) else set()
        modified = {P.name} if (prev[0] and cur[0] and (prev[1] != cur[1] or prev[2] != cur[2])) else set()

        info: PluginFileWatcherBase.ChangeInfo = {
            "timestamp": now,
            "plugin": self.plugin,
            "path": str(P),
            "kind": "file",
            "changed": {"created": created, "deleted": deleted, "modified": modified},
            "exists": cur[0],
            "size": cur[1] if cur[0] else None,
            "mtime_ns": cur[2] if cur[0] else None,
        }

        if self._bubbleUp:
            root = self._findRootFor(P)
            if root and root != P:
                rel_prefix = str(P.parent.relative_to(root)) if P.parent != root else ""
                def _prefixed(names: set[str]) -> set[str]:
                    if not names:
                        return names
                    return {f"{rel_prefix}/{n}"} if rel_prefix else names
                bubbled = {
                    "timestamp": info["timestamp"],
                    "plugin": info["plugin"],
                    "path": str(root),
                    "kind": "dir",
                    "changed": {
                        "created": _prefixed(created),
                        "deleted": _prefixed(deleted),
                        "modified": _prefixed(modified),
                    },
                    "exists": True,
                    "entryCount": None,
                    "totalSize": None,
                    "mtime_ns": info.get("mtime_ns"),
                }
                self._maybeEmit(bubbled)
                return

        self._maybeEmit(info)

    # --- snapshots / diffs / probes ---
    def _snapshotDir(self, D: aPath) -> dict[str, tuple[int, int]]:
        snap: dict[str, tuple[int, int]] = {}
        try:
            for c in D.iterdir():
                if c.is_dir():
                    name = c.name
                    if not self._acceptName(name, isDir=True):
                        continue
                    st = c.stat()
                    snap[name] = (st.st_mtime_ns, -1)
                elif c.is_file():
                    name = c.name
                    if not self._acceptName(name, isDir=False):
                        continue
                    st = c.stat()
                    snap[name] = (st.st_mtime_ns, st.st_size)
        except FileNotFoundError:
            pass
        return snap

    @staticmethod
    def _diff(
        old: dict[str, tuple[int, int]],
        new: dict[str, tuple[int, int]]
    ) -> tuple[set[str], set[str], set[str]]:
        ok, nk = set(old), set(new)
        created  = nk - ok
        deleted  = ok - nk
        modified = {k for k in (ok & nk) if old[k] != new[k]}
        return created, deleted, modified

    @staticmethod
    def _probeFile(P: aPath) -> tuple[bool, int, int]:
        if P.exists() and P.is_file():
            st = P.stat()
            return True, int(st.st_size), int(st.st_mtime_ns)
        return False, 0, 0


if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication

    def onChange(info: PluginFileWatcherBase.ChangeInfo):
        print(f"[{info['plugin']}] Change detected:")
        print(f"  Path: {info['path']}")
        print(f"  Kind: {info['kind']}")
        print(f"  Exists: {info['exists']}")
        print(f"  Changed: {info['changed']}")
        print()

    app = QApplication(sys.argv)

    watchedDir = aPath(__file__).parent
    watcher = PluginFileWatcher(
        app,
        plugin="TestPlugin",
        paths=[watchedDir],
        callback=onChange,
        delaySeconds=0.5,
        includeSuffixes={".txt"},      # only file types of interest
        excludeSuffixes={".log"},
        ignoreHidden=True,
        recursive=True,                # watch subdirs
        maxDepth=4,                    # limit recursion
        bubbleUp=True,                 # bubble deep changes to root
        dirEventsRequireIncludedFiles=True,  # <- suppress dir events unless a matching file changed
        trackDirectories=False,  # <- and don’t include dir names in the changed sets
        )

    with watcher.suspendEvents():
        ...

    print(f"Watching {watchedDir} (recursive, depth<=4). Press Ctrl+C to quit.")
    sys.exit(app.exec_())
