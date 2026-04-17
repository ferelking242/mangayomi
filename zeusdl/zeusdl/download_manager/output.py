import json
import sys
import time
from typing import Optional


class OutputFormatter:
    """Handles all output for ZeusDL — both JSON-progress mode and terminal dashboard."""

    def __init__(self, json_mode: bool = False, no_interactive: bool = False):
        self.json_mode = json_mode
        self.no_interactive = no_interactive
        self._last_render_time: float = 0.0

    def emit_progress(
        self,
        task_id: str,
        status: str,
        progress: float = 0.0,
        speed: Optional[float] = None,
        eta: Optional[int] = None,
        downloaded_bytes: int = 0,
        total_bytes: Optional[int] = None,
        filename: Optional[str] = None,
        error: Optional[str] = None,
    ) -> None:
        if self.json_mode:
            payload: dict = {
                "id": task_id,
                "status": status,
                "progress": round(progress, 2),
                "speed": speed,
                "eta": eta,
                "downloaded_bytes": downloaded_bytes,
                "total_bytes": total_bytes,
                "filename": filename,
            }
            if error:
                payload["error"] = error
            print(json.dumps(payload), flush=True)

    def emit_event(self, event: str, data: dict) -> None:
        if self.json_mode:
            payload = {"event": event, **data}
            print(json.dumps(payload), flush=True)

    def format_speed(self, bps: Optional[float]) -> str:
        if bps is None:
            return "---"
        if bps >= 1_048_576:
            return f"{bps / 1_048_576:.1f}MB/s"
        if bps >= 1024:
            return f"{bps / 1024:.1f}KB/s"
        return f"{bps:.0f}B/s"

    def format_eta(self, eta: Optional[int]) -> str:
        if eta is None:
            return "--:--"
        m, s = divmod(eta, 60)
        h, m = divmod(m, 60)
        if h:
            return f"{h:02d}:{m:02d}:{s:02d}"
        return f"{m:02d}:{s:02d}"

    def render_dashboard(self, tasks: list) -> None:
        if self.json_mode or self.no_interactive:
            return
        now = time.time()
        if now - self._last_render_time < 0.25:
            return
        self._last_render_time = now

        lines = []
        lines.append("\033[2J\033[H")
        lines.append("  \033[1;36mZeusDL Download Manager\033[0m")
        lines.append("  " + "─" * 52)

        if not tasks:
            lines.append("  No downloads in queue.")
        else:
            for i, task in enumerate(tasks, 1):
                state_colors = {
                    "waiting": "\033[33m",
                    "downloading": "\033[32m",
                    "paused": "\033[35m",
                    "completed": "\033[34m",
                    "error": "\033[31m",
                    "cancelled": "\033[90m",
                }
                color = state_colors.get(task.state.value, "\033[0m")
                reset = "\033[0m"

                name = (task.filename or task.url)[-42:]
                bar_fill = int(task.progress / 100 * 20)
                bar = "█" * bar_fill + "░" * (20 - bar_fill)

                speed_str = self.format_speed(task.speed)
                eta_str = self.format_eta(task.eta)

                lines.append(
                    f"  [{i}] {color}{task.state.value.upper():12s}{reset} {name}"
                )
                if task.state.value == "downloading":
                    lines.append(
                        f"      [{bar}] {task.progress:5.1f}%  {speed_str}  ETA {eta_str}"
                    )
                elif task.state.value == "error" and task.error_message:
                    lines.append(f"      \033[31m{task.error_message[:60]}\033[0m")

        lines.append("")
        lines.append("  \033[90m[p] Pause  [r] Resume  [s] Stop  [q] Quit\033[0m")
        sys.stdout.write("\n".join(lines) + "\n")
        sys.stdout.flush()
