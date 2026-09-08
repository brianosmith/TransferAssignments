from __future__ import annotations


"""
A utility for executing external processes via the command-line shell

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
__dateModified__ = "$dateModified: 2025-08-14 17:51:40 +0100 (Thu, August 14, 2025) $"
__version__ = "$Revision: 3.3.3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu  $"
__date__ = "$Date: 2025-08-06 15:08:39 +0100 (Wed, August 06, 2025) $"

#=========================================================================================
# Start of code
#=========================================================================================

import json
import shlex
import subprocess
import time
import os
from dataclasses import dataclass
from ccpn.util.Path import aPath
from typing import Any, Iterable, Mapping, Optional, Sequence, Union


StrPath = Union[str, aPath]

@dataclass(slots=True)
class ExternalRunResult:
    """Lightweight result container for external runs."""
    args: list[str]
    returncode: int
    stdout: str | bytes | None
    stderr: str | bytes | None
    cwd: aPath
    duration_s: float

    def ok(self) -> bool:
        return self.returncode == 0


class ExternalProcessRunner:
    """
    A tool for executing external processes on the command-line shell.
    Features:
      • Explicit tool path, default args, working directory, and env overlay
      • Synchronous `run()` with captured stdout/stderr and timeout
      • Non‑blocking `popen()` for streaming/GUI scenarios
      • Helpers to parse JSON outputs and inspect filesystem artefacts
      • Pure stdlib (subprocess, pathlib); no event loop assumptions

    Typical use:
        runner = ExternalProcessRunner("/usr/bin/ffmpeg", workDir="~/tmp", env={"LC_ALL": "C"})
        res = runner.run(["-version"])
        if res.ok(): print(res.stdout)

    Notes:
      • Do not pass untrusted strings to `shell=True`.
      • Use `popen()` if you need incremental reading without blocking the UI.
    """

    def __init__(self, tool: StrPath, *,
                 defaultArgs: Optional[Sequence[str]] = None,
                 workDir: Optional[StrPath] = None,
                 env: Optional[Mapping[str, str]] = None,
                 shell: bool = False,
                 ) -> None:

        self.tool = str(tool)
        self.defaultArgs: list[str] = list(defaultArgs or [])
        self.workDir = aPath(workDir).expanduser().resolve() if workDir else os.getcwd()
        self.env: dict[str, str] = dict(env or {})
        self.shell = shell  # keep False unless you know you need a shell

    # ----------------------
    # Public API
    # ----------------------

    def run(self, args: Optional[Sequence[str]] = None, *,
            inputData: Optional[Union[str, bytes]] = None,
            text: bool = True,
            timeout: Optional[float] = None,
            check: bool = False,
            captureOutput: bool = True,
            extraEnv: Optional[Mapping[str, str]] = None,
            cwd: Optional[StrPath] = None,
            ) -> ExternalRunResult:
        """
        Run the tool to completion and capture output.

        :param args: Extra arguments appended after `defaultArgs`.
        :param inputData: Data to send to stdin (str/bytes depending on `text`).
        :param text: If True, decode to str (locale); else keep bytes.
        :param timeout: Seconds before killing the process (None = no timeout).
        :param check: If True, raise CalledProcessError on non‑zero exit.
        :param captureOutput: If False, inherit parent stdio.
        :param extraEnv: Per‑call environment overlay.
        :param cwd: Per‑call working directory (defaults to runner.workDir).
        :return: ExternalRunResult.
        """
        cmd = self._buildCommand(args)
        runEnv = self._mergedEnv(extraEnv)
        runCwd = aPath(cwd).expanduser().resolve() if cwd else self.workDir

        start = time.perf_counter()
        if captureOutput:
            cp = subprocess.run(
                    cmd,
                    cwd=str(runCwd),
                    env=runEnv,
                    input=inputData,
                    text=text,
                    timeout=timeout,
                    shell=self.shell,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    )
        else:
            cp = subprocess.run(
                    cmd,
                    cwd=str(runCwd),
                    env=runEnv,
                    input=inputData,
                    text=text,
                    timeout=timeout,
                    shell=self.shell,
                    )
        dur = time.perf_counter() - start

        if check and cp.returncode != 0:
            # Preserve output on exception for diagnostics
            err = subprocess.CalledProcessError(
                    cp.returncode, cmd, output=getattr(cp, "stdout", None), stderr=getattr(cp, "stderr", None)
                    )
            raise err

        return ExternalRunResult(
                args=[str(a) for a in (cmd if isinstance(cmd, list) else [cmd])],
                returncode=cp.returncode,
                stdout=getattr(cp, "stdout", None),
                stderr=getattr(cp, "stderr", None),
                cwd=runCwd,
                duration_s=dur,
                )

    def popen(
            self,
            args: Optional[Sequence[str]] = None,
            *,
            text: bool = True,
            extraEnv: Optional[Mapping[str, str]] = None,
            cwd: Optional[StrPath] = None,
            stdout: int = subprocess.PIPE,
            stderr: int = subprocess.PIPE,
            stdin: int = subprocess.PIPE,
            bufsize: int = 1,
            ) -> subprocess.Popen:
        """
        Launch the tool without waiting. Caller is responsible for reading pipes.

        :return: subprocess.Popen
        """
        cmd = self._buildCommand(args)
        runEnv = self._mergedEnv(extraEnv)
        runCwd = aPath(cwd).expanduser().resolve() if cwd else self.workDir
        return subprocess.Popen(
                cmd,
                cwd=str(runCwd),
                env=runEnv,
                text=text,
                shell=self.shell,
                stdout=stdout,
                stderr=stderr,
                stdin=stdin,
                bufsize=bufsize,
                )

    # ----------------------
    # Parsing / filesystem helpers
    # ----------------------

    @staticmethod
    def readJson(path: StrPath) -> Any:
        with open(aPath(path), "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def listFiles(path: StrPath, *, pattern: str = "*") -> list[aPath]:
        p = aPath(path)
        return [q for q in p.glob(pattern) if q.is_file()]

    @staticmethod
    def listDirs(path: StrPath) -> list[aPath]:
        p = aPath(path)
        return [q for q in p.iterdir() if q.is_dir()]

    # ----------------------
    # Private utilities
    # ----------------------

    def _buildCommand(self, args: Optional[Sequence[str]]) -> list[str] | str:
        """Return argv list unless `shell=True`, in which case return a shell string."""
        argv: list[str] = [self.tool, *self.defaultArgs, *(args or [])]
        return " ".join(shlex.quote(x) for x in argv) if self.shell else argv

    def _mergedEnv(self, extra: Optional[Mapping[str, str]]) -> dict[str, str]:
        env = dict(self.env)
        if extra:
            env.update(extra)
        # Inherit parent env last, unless you prefer the opposite;
        # flip the order if you want runner.env to override parent.
        parent = dict(subprocess.os.environ)
        parent.update(env)
        return parent


if __name__ == "__main__":
    # Example: run `ls -l` in the user's home directory on macOS
    print("\n[Example 1] ls -l in HOME (sync)")
    home = aPath(__file__).parent
    r1 = ExternalProcessRunner("/bin/ls", defaultArgs=["-l"], workDir=home)
    res1 = r1.run()
    print("cmd      :", " ".join(res1.args))
    print("rc       :", res1.returncode)
    print("cwd      :", res1.cwd)
    print("duration :", f"{res1.duration_s:.3f}s")
    print("stdout   :", (res1.stdout or "").splitlines()[:3], "...")  # show a few lines

    # --- Example 2:  Non-blocking external tool run that writes to a file

    # Prepare output directory
    out_dir = home / "tmp_ext"
    out_dir.mkdir(exist_ok=True)

    # Command: echo "Hello" > out_dir/output.txt
    runner = ExternalProcessRunner("/bin/sh", defaultArgs=["-c"], workDir=out_dir)
    script = f'echo "Hello from external tool" > "{out_dir}/output.txt"'

    # Start process (non-blocking)
    proc = runner.popen([script], text=True)

    print("[Main] External tool started; We can do other work while the External tool is running...")


    # --- Example 3: streaming async (popen) with shell script --------------
    # Uses /bin/sh -c to print ticks; demonstrates non-blocking read of stdout.
    import time, sys


    print("\n[Example 3] streaming (async) with popen + shell")
    script = 'for i in 1 2 3 4 5; do echo "tick $i"; sleep 0.25; done'
    sh_runner = ExternalProcessRunner("/bin/sh", defaultArgs=["-c"], shell=False)  # pass script as arg, no shell=True needed
    proc = sh_runner.popen([script], text=True)

    # Non-blocking-ish line-by-line read (blocks per-read if no data; good enough for demo)
    for line in proc.stdout:  # type: ignore[union-attr]
        sys.stdout.write(f"[out] {line}")
        sys.stdout.flush()
    err = proc.stderr.read() if proc.stderr else ""
    rc = proc.wait()
    print(f"[Example 3] rc={rc}, stderr={(err or '<empty>').strip()}")

    # --- Example 4: custom environment -------------------------------------
    print("\n[Example 4] custom environment (MY_VAR)")
    runner_custom_env = ExternalProcessRunner(
            "/usr/bin/env",
            env={"MY_VAR": "hello-from-runner"},
            workDir=home,
            )
    res4 = runner_custom_env.run()
    # show only MY_VAR
    my_var = next((ln for ln in (res4.stdout or "").splitlines() if ln.startswith("MY_VAR=")), "<MY_VAR not found>")
    print("MY_VAR   :", my_var)
    print("\nAll examples finished.")
