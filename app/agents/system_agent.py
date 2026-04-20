"""
SystemAgent — controls the local machine safely.
Can run scripts, manage files, check system status, control applications, send notifications.
All script execution is validated against an allowlist before running.
"""
from __future__ import annotations

import logging
import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.agents.base import AgentResponse, BaseAgent

LOGGER = logging.getLogger(__name__)

# ── Allowed directories for script execution ───────────────────────────────
_ALLOWED_SCRIPT_ROOTS = [
    Path("C:/dev"),
    Path("C:/Users/Admin/scripts"),
    Path(os.path.expanduser("~/scripts")),
]

# ── Allowed script extensions ──────────────────────────────────────────────
_ALLOWED_EXTENSIONS = {".py", ".bat"}

# ── Max file size for read_file (1 MB) ────────────────────────────────────
_MAX_READ_BYTES = 1_048_576

# ── Allowed directories for file read/write ───────────────────────────────
_ALLOWED_FILE_ROOTS: list[Path] = [
    Path("C:/dev").resolve(),
    Path("C:/Users/Admin/Documents").resolve(),
    Path("C:/Users/Admin/Desktop").resolve(),
    Path(os.path.expanduser("~/Downloads")).resolve(),
]

def _is_path_allowed(p: Path) -> bool:
    """Return True if the resolved path is under an allowed root."""
    try:
        resolved = p.resolve()
        return any(
            str(resolved).startswith(str(root))
            for root in _ALLOWED_FILE_ROOTS
        )
    except Exception:
        return False

# ── Optional psutil ────────────────────────────────────────────────────────
try:
    import psutil as _psutil
    _PSUTIL_AVAILABLE = True
except ImportError:
    _psutil = None  # type: ignore[assignment]
    _PSUTIL_AVAILABLE = False

# ── Optional plyer (cross-platform notifications) ─────────────────────────
try:
    from plyer import notification as _plyer_notification
    _PLYER_AVAILABLE = True
except ImportError:
    _plyer_notification = None  # type: ignore[assignment]
    _PLYER_AVAILABLE = False

# ── Windows toast via win10toast ──────────────────────────────────────────
try:
    from win10toast import ToastNotifier as _ToastNotifier
    _WIN10TOAST_AVAILABLE = True
except ImportError:
    _ToastNotifier = None  # type: ignore[assignment]
    _WIN10TOAST_AVAILABLE = False


class SystemAgent(BaseAgent):
    """Controls the local Windows machine — scripts, files, status, notifications."""

    name = "SystemAgent"
    description = (
        "Gives JARVIS hands on the local machine — runs scripts, reads/writes files, "
        "checks system resources, lists directories, and sends desktop notifications."
    )
    capabilities = [
        "Get CPU, RAM, and disk usage",
        "List running processes",
        "Run allowed Python or batch scripts",
        "Open desktop applications",
        "Read and write local files",
        "List directory contents",
        "Send Windows desktop notifications",
    ]

    def __init__(self) -> None:
        super().__init__()

    # ── Public agent interface ──────────────────────────────────────────────

    def handle(self, query: str, context: Optional[Dict[str, Any]] = None) -> AgentResponse:
        """Route system queries to the correct sub-handler."""
        context = context or {}
        q = query.lower()

        # System status
        if any(kw in q for kw in ["cpu", "memory", "ram", "disk", "system status", "resource"]):
            result = self.get_system_status()
            content = _format_system_status(result)
            return AgentResponse(agent=self.name, content=content, data=result, status="success")

        # Processes
        if any(kw in q for kw in ["process", "running", "task manager"]):
            result = self.list_processes()
            procs = result.get("processes", [])
            lines = [f"Top {len(procs)} processes by CPU:"]
            for p in procs[:10]:
                lines.append(f"  {p['name']:30s}  CPU: {p['cpu_percent']:5.1f}%  RAM: {p['memory_mb']:.0f} MB")
            return AgentResponse(
                agent=self.name,
                content="\n".join(lines),
                data=result,
                status="success",
            )

        # Run script
        if any(kw in q for kw in ["run script", "execute script", "run the", "start script"]):
            path = context.get("script_path") or context.get("path", "")
            if not path:
                return AgentResponse(
                    agent=self.name,
                    content="Please provide the script path in the request context.",
                    status="error",
                )
            result = self.run_script(path)

        # Open application
        elif any(kw in q for kw in ["open", "launch", "start"]) and context.get("app_name"):
            result = self.open_application(context["app_name"])

        # Notification
        elif any(kw in q for kw in ["notify", "notification", "alert me", "send me"]):
            title = context.get("title", "JARVIS")
            message = context.get("message") or query
            result = self.send_notification(title, message)

        # List directory
        elif any(kw in q for kw in ["list", "directory", "folder", "files in"]):
            path = context.get("path", ".")
            result = self.list_directory(path)

        # Read file
        elif any(kw in q for kw in ["read file", "show file", "contents of"]):
            path = context.get("path", "")
            if not path:
                return AgentResponse(
                    agent=self.name,
                    content="Please provide the file path in the request context.",
                    status="error",
                )
            result = self.read_file(path)

        # Create / write file
        elif any(kw in q for kw in ["create file", "write file", "save file"]):
            path = context.get("path", "")
            content_text = context.get("content", "")
            if not path:
                return AgentResponse(
                    agent=self.name,
                    content="Please provide the file path in the request context.",
                    status="error",
                )
            result = self.create_file(path, content_text)

        else:
            # Default: system status
            result = self.get_system_status()

        if isinstance(result, dict) and "error" in result:
            return AgentResponse(agent=self.name, content=result["error"], status="error")

        content = result.get("message") or result.get("output") or str(result)
        return AgentResponse(agent=self.name, content=content, data=result, status="success")

    # ── Core system methods ─────────────────────────────────────────────────

    def run_script(self, script_path: str) -> Dict[str, Any]:
        """Execute a Python or batch script (allowlisted paths only)."""
        p = Path(script_path).resolve()

        # Security: check extension
        if p.suffix.lower() not in _ALLOWED_EXTENSIONS:
            return {"error": f"Script type not allowed: {p.suffix}. Only .py and .bat files."}

        # Security: check path is under an allowed root
        allowed = any(
            str(p).startswith(str(root.resolve())) for root in _ALLOWED_SCRIPT_ROOTS
        )
        if not allowed:
            allowed_str = ", ".join(str(r) for r in _ALLOWED_SCRIPT_ROOTS)
            return {"error": f"Script path not in allowlist. Allowed roots: {allowed_str}"}

        if not p.exists():
            return {"error": f"Script not found: {script_path}"}

        try:
            if p.suffix.lower() == ".py":
                cmd = [sys.executable, str(p)]
            else:
                cmd = [str(p)]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
                cwd=str(p.parent),
            )
            return {
                "message": f"Script executed: {p.name}",
                "stdout": result.stdout[:2000],
                "stderr": result.stderr[:500],
                "return_code": result.returncode,
                "script_path": str(p),
                "type": "script_run",
            }
        except subprocess.TimeoutExpired:
            return {"error": f"Script timed out after 60 seconds: {script_path}"}
        except Exception as exc:
            LOGGER.exception("run_script failed: %s", exc)
            return {"error": f"Script execution failed: {exc}"}

    def open_application(self, app_name: str) -> Dict[str, Any]:
        """Open a desktop application by name."""
        # Map common friendly names to executable commands
        app_map = {
            "notepad": "notepad.exe",
            "calculator": "calc.exe",
            "paint": "mspaint.exe",
            "browser": "start chrome",
            "chrome": "start chrome",
            "firefox": "start firefox",
            "edge": "start msedge",
            "explorer": "explorer.exe",
            "file explorer": "explorer.exe",
            "task manager": "taskmgr.exe",
            "cmd": "cmd.exe",
            "terminal": "wt.exe",
        }
        normalized = app_name.lower()
        if normalized not in app_map:
            return {"error": f"Application '{app_name}' is not in the allowed list. "
                    f"Allowed: {', '.join(sorted(app_map.keys()))}"}
        exe = app_map[normalized]
        # Strip the "start " prefix — we use ShellExecute / Popen with a list instead
        if exe.startswith("start "):
            exe = exe[6:].strip()
        try:
            if platform.system() == "Windows":
                # os.startfile uses ShellExecute — safe, no shell=True needed
                os.startfile(exe)
            else:
                subprocess.Popen([exe])
            return {
                "message": f"Opened: {app_name}",
                "app": app_name,
                "type": "open_application",
            }
        except Exception as exc:
            LOGGER.exception("open_application failed: %s", exc)
            return {"error": f"Could not open {app_name}: {exc}"}

    def get_system_status(self) -> Dict[str, Any]:
        """Return CPU, RAM, disk usage, and uptime."""
        if not _PSUTIL_AVAILABLE:
            return {"error": "psutil not installed. Run: pip install psutil"}
        try:
            cpu_percent = _psutil.cpu_percent(interval=1)
            mem = _psutil.virtual_memory()
            disk = _psutil.disk_usage("/")
            uptime_secs = None
            try:
                import time
                boot_time = _psutil.boot_time()
                uptime_secs = int(time.time() - boot_time)
            except Exception:
                pass

            return {
                "cpu_percent": cpu_percent,
                "cpu_cores": _psutil.cpu_count(),
                "ram_total_gb": round(mem.total / 1e9, 2),
                "ram_used_gb": round(mem.used / 1e9, 2),
                "ram_percent": mem.percent,
                "disk_total_gb": round(disk.total / 1e9, 2),
                "disk_used_gb": round(disk.used / 1e9, 2),
                "disk_percent": disk.percent,
                "uptime_seconds": uptime_secs,
                "type": "system_status",
            }
        except Exception as exc:
            LOGGER.exception("get_system_status failed: %s", exc)
            return {"error": f"System status check failed: {exc}"}

    def list_processes(self, top_n: int = 20) -> Dict[str, Any]:
        """Return a list of running processes sorted by CPU usage."""
        if not _PSUTIL_AVAILABLE:
            return {"error": "psutil not installed. Run: pip install psutil"}
        try:
            procs = []
            for proc in _psutil.process_iter(["pid", "name", "cpu_percent", "memory_info", "status"]):
                try:
                    info = proc.info
                    mem_mb = info["memory_info"].rss / 1e6 if info.get("memory_info") else 0.0
                    procs.append({
                        "pid": info["pid"],
                        "name": info["name"],
                        "cpu_percent": info["cpu_percent"] or 0.0,
                        "memory_mb": round(mem_mb, 1),
                        "status": info["status"],
                    })
                except (_psutil.NoSuchProcess, _psutil.AccessDenied):
                    pass
            procs.sort(key=lambda x: x["cpu_percent"], reverse=True)
            return {
                "processes": procs[:top_n],
                "total_count": len(procs),
                "type": "process_list",
            }
        except Exception as exc:
            LOGGER.exception("list_processes failed: %s", exc)
            return {"error": f"Process listing failed: {exc}"}

    def create_file(self, path: str, content: str) -> Dict[str, Any]:
        """Write content to a file (creates parent dirs if needed)."""
        try:
            p = Path(path)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")
            return {
                "message": f"File created: {path} ({len(content)} bytes)",
                "path": str(p.absolute()),
                "size_bytes": len(content.encode("utf-8")),
                "type": "file_create",
            }
        except Exception as exc:
            LOGGER.exception("create_file failed: %s", exc)
            return {"error": f"File creation failed: {exc}"}

    def read_file(self, path: str) -> Dict[str, Any]:
        """Read a file and return its contents (max 1 MB)."""
        try:
            p = Path(path)
            if not _is_path_allowed(p):
                return {"error": f"Access denied: '{path}' is outside the allowed directories."}
            if not p.exists():
                return {"error": f"File not found: {path}"}
            size = p.stat().st_size
            if size > _MAX_READ_BYTES:
                return {"error": f"File too large to read ({size / 1e6:.1f} MB). Limit is 1 MB."}
            content = p.read_text(encoding="utf-8", errors="replace")
            return {
                "content": content,
                "message": f"Read {size} bytes from {path}",
                "path": str(p.absolute()),
                "size_bytes": size,
                "type": "file_read",
            }
        except Exception as exc:
            LOGGER.exception("read_file failed: %s", exc)
            return {"error": f"File read failed: {exc}"}

    def list_directory(self, path: str = ".") -> Dict[str, Any]:
        """List contents of a directory."""
        try:
            p = Path(path)
            if not p.exists():
                return {"error": f"Directory not found: {path}"}
            if not p.is_dir():
                return {"error": f"Not a directory: {path}"}
            entries = []
            for item in sorted(p.iterdir(), key=lambda x: (x.is_file(), x.name.lower())):
                try:
                    stat = item.stat()
                    entries.append({
                        "name": item.name,
                        "type": "file" if item.is_file() else "directory",
                        "size_bytes": stat.st_size if item.is_file() else None,
                    })
                except Exception:
                    entries.append({"name": item.name, "type": "unknown", "size_bytes": None})
            return {
                "path": str(p.absolute()),
                "entries": entries,
                "count": len(entries),
                "message": f"{len(entries)} items in {path}",
                "type": "directory_listing",
            }
        except Exception as exc:
            LOGGER.exception("list_directory failed: %s", exc)
            return {"error": f"Directory listing failed: {exc}"}

    def send_notification(self, title: str, message: str, duration: int = 5) -> Dict[str, Any]:
        """Send a Windows desktop notification."""
        # Attempt 1: win10toast
        if _WIN10TOAST_AVAILABLE and _ToastNotifier is not None:
            try:
                toaster = _ToastNotifier()
                toaster.show_toast(
                    title,
                    message,
                    duration=duration,
                    threaded=True,
                )
                return {
                    "message": f"Notification sent via win10toast: {title}",
                    "title": title,
                    "body": message,
                    "type": "notification",
                }
            except Exception as exc:
                LOGGER.warning("win10toast failed: %s", exc)

        # Attempt 2: plyer
        if _PLYER_AVAILABLE and _plyer_notification is not None:
            try:
                _plyer_notification.notify(
                    title=title,
                    message=message,
                    timeout=duration,
                )
                return {
                    "message": f"Notification sent via plyer: {title}",
                    "title": title,
                    "body": message,
                    "type": "notification",
                }
            except Exception as exc:
                LOGGER.warning("plyer notification failed: %s", exc)

        # Attempt 3: Windows PowerShell toast (no deps)
        if platform.system() == "Windows":
            try:
                # Escape single quotes to prevent PowerShell injection
                safe_title = str(title).replace("'", "''").replace("`", "``")[:128]
                safe_message = str(message).replace("'", "''").replace("`", "``")[:256]
                ps_script = (
                    f"[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, "
                    f"ContentType = WindowsRuntime] > $null; "
                    f"$template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent("
                    f"[Windows.UI.Notifications.ToastTemplateType]::ToastText02); "
                    f"$textNodes = $template.GetElementsByTagName('text'); "
                    f"$textNodes.Item(0).AppendChild($template.CreateTextNode('{safe_title}')) > $null; "
                    f"$textNodes.Item(1).AppendChild($template.CreateTextNode('{safe_message}')) > $null; "
                    f"$toast = [Windows.UI.Notifications.ToastNotification]::new($template); "
                    f"[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('JARVIS').Show($toast)"
                )
                subprocess.run(
                    ["powershell", "-NoProfile", "-Command", ps_script],
                    capture_output=True,
                    timeout=10,
                )
                return {
                    "message": f"Notification sent via PowerShell: {title}",
                    "title": title,
                    "body": message,
                    "type": "notification",
                }
            except Exception as exc:
                LOGGER.warning("PowerShell toast failed: %s", exc)

        LOGGER.warning("No notification backend available. Install plyer or win10toast.")
        return {
            "message": f"Notification logged (no desktop backend): {title} — {message}",
            "title": title,
            "body": message,
            "type": "notification",
            "warning": "No desktop notification backend available",
        }


# ── Internal formatters ─────────────────────────────────────────────────────

def _format_system_status(status: Dict[str, Any]) -> str:
    if "error" in status:
        return status["error"]
    lines = [
        f"CPU: {status.get('cpu_percent', '?')}% ({status.get('cpu_cores', '?')} cores)",
        f"RAM: {status.get('ram_used_gb', '?')} GB / {status.get('ram_total_gb', '?')} GB ({status.get('ram_percent', '?')}%)",
        f"Disk: {status.get('disk_used_gb', '?')} GB / {status.get('disk_total_gb', '?')} GB ({status.get('disk_percent', '?')}%)",
    ]
    if status.get("uptime_seconds"):
        h, r = divmod(int(status["uptime_seconds"]), 3600)
        m, _ = divmod(r, 60)
        lines.append(f"Uptime: {h}h {m}m")
    return "\n".join(lines)
