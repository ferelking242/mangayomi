import json
import os
import time
from typing import List
from .task import DownloadTask, TaskState


class SessionManager:
    """Persist queue state to disk so downloads survive restarts."""

    def __init__(self, session_file: str):
        self.session_file = session_file

    def save(self, tasks: List[DownloadTask]) -> None:
        data = {
            "version": 1,
            "saved_at": time.time(),
            "tasks": [t.to_session_dict() for t in tasks],
        }
        tmp = self.session_file + ".tmp"
        try:
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            os.replace(tmp, self.session_file)
        except OSError:
            pass

    def load(self) -> List[DownloadTask]:
        if not os.path.exists(self.session_file):
            return []
        try:
            with open(self.session_file, encoding="utf-8") as f:
                data = json.load(f)
            tasks = []
            for d in data.get("tasks", []):
                task = DownloadTask.from_session_dict(d)
                if task.state == TaskState.DOWNLOADING:
                    task.state = TaskState.WAITING
                tasks.append(task)
            return tasks
        except (json.JSONDecodeError, KeyError, OSError):
            return []
