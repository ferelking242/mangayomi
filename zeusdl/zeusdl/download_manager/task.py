import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class TaskState(str, Enum):
    WAITING = "waiting"
    DOWNLOADING = "downloading"
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"
    CANCELLED = "cancelled"


@dataclass
class DownloadTask:
    url: str
    task_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    state: TaskState = TaskState.WAITING
    output_dir: str = "."
    format_spec: str = "bestvideo+bestaudio/best"
    limit_rate: Optional[str] = None
    retries: int = 10
    extra_args: list = field(default_factory=list)

    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    finished_at: Optional[float] = None

    filename: Optional[str] = None
    progress: float = 0.0
    speed: Optional[float] = None
    eta: Optional[int] = None
    downloaded_bytes: int = 0
    total_bytes: Optional[int] = None
    error_message: Optional[str] = None
    pid: Optional[int] = None

    def to_dict(self) -> dict:
        return {
            "id": self.task_id,
            "url": self.url,
            "status": self.state.value,
            "progress": round(self.progress, 1),
            "speed": self.speed,
            "eta": self.eta,
            "downloaded_bytes": self.downloaded_bytes,
            "total_bytes": self.total_bytes,
            "filename": self.filename,
            "error": self.error_message,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
        }

    def to_session_dict(self) -> dict:
        d = self.to_dict()
        d.update({
            "output_dir": self.output_dir,
            "format_spec": self.format_spec,
            "limit_rate": self.limit_rate,
            "retries": self.retries,
            "extra_args": self.extra_args,
        })
        return d

    @classmethod
    def from_session_dict(cls, d: dict) -> "DownloadTask":
        task = cls(
            url=d["url"],
            task_id=d["id"],
            output_dir=d.get("output_dir", "."),
            format_spec=d.get("format_spec", "bestvideo+bestaudio/best"),
            limit_rate=d.get("limit_rate"),
            retries=d.get("retries", 10),
            extra_args=d.get("extra_args", []),
        )
        state_str = d.get("status", "waiting")
        if state_str in (TaskState.COMPLETED.value, TaskState.ERROR.value, TaskState.CANCELLED.value):
            task.state = TaskState(state_str)
        else:
            task.state = TaskState.WAITING
        task.filename = d.get("filename")
        task.progress = d.get("progress", 0.0)
        task.downloaded_bytes = d.get("downloaded_bytes", 0)
        task.total_bytes = d.get("total_bytes")
        task.created_at = d.get("created_at", time.time())
        task.started_at = d.get("started_at")
        task.finished_at = d.get("finished_at")
        return task
