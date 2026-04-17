import os
import re
import subprocess
import sys
import threading
import time
from typing import Callable, Dict, List, Optional

from .output import OutputFormatter
from .session import SessionManager
from .task import DownloadTask, TaskState

# ── Auth integration (optional — gracefully disabled if auth module missing) ──
try:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from zeusdl.auth import SessionGuard
    _AUTH_AVAILABLE = True
except Exception:
    SessionGuard = None  # type: ignore
    _AUTH_AVAILABLE = False

# Auth errors patterns that warrant a re-login retry
_AUTH_ERROR_PATTERNS = re.compile(
    r"(403 Forbidden|401 Unauthorized|login required|"
    r"not logged in|members only|subscription required|"
    r"HTTP Error 40[13])",
    re.IGNORECASE,
)

PYTHON3 = sys.executable


def _find_zeusdl_module() -> str:
    """Return the root directory that contains the zeusdl package."""
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.dirname(here)


class DownloadQueueManager:
    """
    Manages a queue of download tasks.

    Architecture
    ─────────────
    • Each task runs ZeusDL as a subprocess with --json-progress.
    • Pause = SIGSTOP, Resume = SIGCONT (POSIX).
      On Windows, the subprocess is simply killed and restarted
      (Windows does not support SIGSTOP).
    • The manager runs a scheduler thread that starts new workers as
      slots become available.
    """

    def __init__(
        self,
        max_concurrent: int = 3,
        output_formatter: Optional[OutputFormatter] = None,
        session_file: Optional[str] = None,
        on_update: Optional[Callable[[DownloadTask], None]] = None,
        auth_verbose: bool = False,
    ):
        self.max_concurrent = max_concurrent
        self.formatter = output_formatter or OutputFormatter()
        self.session_mgr = SessionManager(session_file) if session_file else None
        self.on_update = on_update
        self._guard: Optional[SessionGuard] = (
            SessionGuard(verbose=auth_verbose) if _AUTH_AVAILABLE else None
        )

        self._tasks: Dict[str, DownloadTask] = {}
        self._order: List[str] = []
        self._lock = threading.Lock()
        self._workers: Dict[str, threading.Thread] = {}
        self._procs: Dict[str, subprocess.Popen] = {}

        self._running = False
        self._scheduler_thread: Optional[threading.Thread] = None

    # ──────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────

    def add(self, task: DownloadTask) -> DownloadTask:
        with self._lock:
            self._tasks[task.task_id] = task
            self._order.append(task.task_id)
        self._save_session()
        return task

    def pause(self, task_id: str) -> bool:
        with self._lock:
            task = self._tasks.get(task_id)
            if not task or task.state != TaskState.DOWNLOADING:
                return False
            proc = self._procs.get(task_id)
            if proc and proc.poll() is None:
                try:
                    if sys.platform != "win32":
                        import signal
                        proc.send_signal(signal.SIGSTOP)
                    else:
                        proc.terminate()
                except (ProcessLookupError, PermissionError):
                    pass
            task.state = TaskState.PAUSED
        self._notify(task)
        self._save_session()
        return True

    def resume(self, task_id: str) -> bool:
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return False
            if task.state == TaskState.PAUSED:
                proc = self._procs.get(task_id)
                if proc and proc.poll() is None and sys.platform != "win32":
                    import signal
                    try:
                        proc.send_signal(signal.SIGCONT)
                        task.state = TaskState.DOWNLOADING
                        self._notify(task)
                        return True
                    except (ProcessLookupError, PermissionError):
                        pass
                task.state = TaskState.WAITING
                self._notify(task)
                self._save_session()
                return True
        return False

    def cancel(self, task_id: str) -> bool:
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return False
            proc = self._procs.get(task_id)
            if proc and proc.poll() is None:
                try:
                    proc.terminate()
                except (ProcessLookupError, PermissionError):
                    pass
            task.state = TaskState.CANCELLED
        self._notify(task)
        self._save_session()
        return True

    def get_task(self, task_id: str) -> Optional[DownloadTask]:
        return self._tasks.get(task_id)

    def list_tasks(self) -> List[DownloadTask]:
        with self._lock:
            return [self._tasks[tid] for tid in self._order if tid in self._tasks]

    def start(self) -> None:
        self._running = True
        if self.session_mgr:
            loaded = self.session_mgr.load()
            for task in loaded:
                if task.task_id not in self._tasks:
                    self._tasks[task.task_id] = task
                    self._order.append(task.task_id)
        self._scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self._scheduler_thread.start()

    def stop(self) -> None:
        self._running = False
        with self._lock:
            for task_id, proc in list(self._procs.items()):
                task = self._tasks.get(task_id)
                if task and task.state == TaskState.DOWNLOADING:
                    task.state = TaskState.WAITING
                try:
                    proc.terminate()
                except Exception:
                    pass
        self._save_session()

    def wait(self) -> None:
        while True:
            with self._lock:
                active = [
                    t for t in self._tasks.values()
                    if t.state in (TaskState.WAITING, TaskState.DOWNLOADING)
                ]
            if not active:
                break
            time.sleep(0.5)

    # ──────────────────────────────────────────────
    # Scheduler
    # ──────────────────────────────────────────────

    def _scheduler_loop(self) -> None:
        while self._running:
            self._tick()
            time.sleep(0.3)

    def _tick(self) -> None:
        with self._lock:
            active_count = sum(
                1 for t in self._tasks.values()
                if t.state == TaskState.DOWNLOADING
            )
            slots = self.max_concurrent - active_count
            if slots <= 0:
                return
            for tid in self._order:
                if slots <= 0:
                    break
                task = self._tasks.get(tid)
                if task and task.state == TaskState.WAITING:
                    task.state = TaskState.DOWNLOADING
                    task.started_at = time.time()
                    slots -= 1
                    t = threading.Thread(target=self._run_worker, args=(task,), daemon=True)
                    self._workers[tid] = t
                    t.start()

    # ──────────────────────────────────────────────
    # Worker
    # ──────────────────────────────────────────────

    def _auth_args_for(self, url: str, force_refresh: bool = False) -> List[str]:
        """Return ZeusDL CLI flags for authentication (cookies or username)."""
        if self._guard is None:
            return []
        try:
            ctx = self._guard.ensure(url, force_refresh=force_refresh)
            if ctx.method == "cookies" and ctx.cookie_file:
                return ["--cookies", str(ctx.cookie_file)]
            if ctx.method == "password":
                cred = ctx.ydl_opts
                if cred.get("username"):
                    return ["--username", cred["username"], "--password", cred["password"]]
        except Exception as exc:
            print(f"[queue] auth guard error: {exc}", file=sys.stderr)
        return []

    def _build_args(self, task: DownloadTask, auth_flags: Optional[List[str]] = None) -> List[str]:
        zeusdl_root = _find_zeusdl_module()
        args = [PYTHON3, "-m", "zeusdl"]
        args += ["--newline", "--no-colors", "--no-warnings"]
        args += ["-f", task.format_spec]
        args += ["-o", os.path.join(task.output_dir, "%(title)s.%(ext)s")]
        args += ["--continue"]
        if task.limit_rate:
            args += ["-r", task.limit_rate]
        args += ["--retries", str(task.retries)]
        if auth_flags:
            args += auth_flags
        args += task.extra_args
        args += ["--", task.url]
        return args

    def _run_worker(self, task: DownloadTask) -> None:
        # ── Auth: ensure fresh cookies before starting ─────────────────
        auth_flags = self._auth_args_for(task.url)
        args = self._build_args(task, auth_flags=auth_flags)
        zeusdl_root = _find_zeusdl_module()
        env = os.environ.copy()
        env["PYTHONPATH"] = zeusdl_root + os.pathsep + env.get("PYTHONPATH", "")

        proc = None
        try:
            proc = subprocess.Popen(
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=zeusdl_root,
                env=env,
                bufsize=1,
            )
            with self._lock:
                if self._tasks.get(task.task_id) and self._tasks[task.task_id].state == TaskState.DOWNLOADING:
                    self._procs[task.task_id] = proc
                    task.pid = proc.pid
                else:
                    proc.terminate()
                    return

            self._notify(task)

            for line in proc.stdout:
                with self._lock:
                    current_state = self._tasks.get(task.task_id, task).state
                if current_state == TaskState.CANCELLED:
                    proc.terminate()
                    break
                self._parse_progress_line(task, line.strip())

            proc.wait()
            stderr_output = proc.stderr.read() if proc.stderr else ""

            # ── Auth-error retry: re-login once on 401/403 ─────────────
            if (
                proc.returncode != 0
                and self._guard is not None
                and _AUTH_ERROR_PATTERNS.search(stderr_output)
            ):
                with self._lock:
                    retry_state = self._tasks.get(task.task_id, task).state
                if retry_state not in (TaskState.CANCELLED, TaskState.PAUSED):
                    print(
                        f"[queue] auth error detected for {task.task_id} — "
                        f"re-logging in and retrying once",
                        file=sys.stderr,
                    )
                    fresh_auth = self._auth_args_for(task.url, force_refresh=True)
                    retry_args = self._build_args(task, auth_flags=fresh_auth)
                    with self._lock:
                        task.error_message = None
                    try:
                        retry_proc = subprocess.Popen(
                            retry_args,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True,
                            cwd=_find_zeusdl_module(),
                            env=env,
                            bufsize=1,
                        )
                        with self._lock:
                            self._procs[task.task_id] = retry_proc
                            task.pid = retry_proc.pid
                        for line in retry_proc.stdout:
                            self._parse_progress_line(task, line.strip())
                        retry_proc.wait()
                        retry_stderr = retry_proc.stderr.read() if retry_proc.stderr else ""
                        proc = retry_proc
                        stderr_output = retry_stderr
                    except Exception as retry_exc:
                        stderr_output = str(retry_exc)
            # ───────────────────────────────────────────────────────────

            with self._lock:
                current = self._tasks.get(task.task_id, task)
                if current.state in (TaskState.CANCELLED, TaskState.PAUSED):
                    pass
                elif proc.returncode == 0:
                    current.state = TaskState.COMPLETED
                    current.finished_at = time.time()
                    current.progress = 100.0
                else:
                    current.state = TaskState.ERROR
                    current.finished_at = time.time()
                    current.error_message = stderr_output.strip()[-200:] if stderr_output else "Unknown error"

            self._notify(task)
            self._save_session()

        except Exception as exc:
            with self._lock:
                task.state = TaskState.ERROR
                task.error_message = str(exc)
                task.finished_at = time.time()
            self._notify(task)
        finally:
            with self._lock:
                self._procs.pop(task.task_id, None)

    # ──────────────────────────────────────────────
    # Progress parsing
    # ──────────────────────────────────────────────

    _PROGRESS_RE = re.compile(
        r"\[download\]\s+"
        r"(?P<pct>[\d.]+)%\s+of\s+~?(?P<total>[\d.]+(?:Ki?B|Mi?B|Gi?B|B))"
        r"(?:\s+at\s+(?P<speed>[\d.]+(?:Ki?B|Mi?B|Gi?B|B)/s))?"
        r"(?:\s+ETA\s+(?P<eta>[\d:]+))?",
        re.IGNORECASE,
    )
    _DEST_RE = re.compile(r"\[download\] Destination:\s+(.+)$")

    @staticmethod
    def _parse_size(s: str) -> float:
        s = s.strip()
        for suffix, mult in [("GiB", 1073741824), ("MiB", 1048576), ("KiB", 1024),
                              ("GB", 1000000000), ("MB", 1000000), ("KB", 1000), ("B", 1)]:
            if s.endswith(suffix):
                return float(s[: -len(suffix)]) * mult
        return 0.0

    @staticmethod
    def _parse_eta(s: str) -> int:
        parts = list(map(int, s.split(":")))
        if len(parts) == 3:
            return parts[0] * 3600 + parts[1] * 60 + parts[2]
        if len(parts) == 2:
            return parts[0] * 60 + parts[1]
        return parts[0]

    def _parse_progress_line(self, task: DownloadTask, line: str) -> None:
        m = self._DEST_RE.match(line)
        if m:
            task.filename = os.path.basename(m.group(1).strip())
            return

        m = self._PROGRESS_RE.search(line)
        if m:
            pct = float(m.group("pct"))
            total_str = m.group("total")
            speed_str = m.group("speed")
            eta_str = m.group("eta")

            total_bytes = self._parse_size(total_str) if total_str else None
            speed = self._parse_size(speed_str.replace("/s", "")) if speed_str else None
            eta = self._parse_eta(eta_str) if eta_str else None
            downloaded = int(total_bytes * pct / 100) if total_bytes else 0

            with self._lock:
                task.progress = pct
                task.speed = speed
                task.eta = eta
                task.downloaded_bytes = downloaded
                task.total_bytes = int(total_bytes) if total_bytes else None

            self.formatter.emit_progress(
                task_id=task.task_id,
                status=task.state.value,
                progress=pct,
                speed=speed,
                eta=eta,
                downloaded_bytes=downloaded,
                total_bytes=int(total_bytes) if total_bytes else None,
                filename=task.filename,
            )
            self._notify(task)

    # ──────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────

    def _notify(self, task: DownloadTask) -> None:
        if self.on_update:
            try:
                self.on_update(task)
            except Exception:
                pass

    def _save_session(self) -> None:
        if self.session_mgr:
            tasks = self.list_tasks()
            self.session_mgr.save(tasks)
