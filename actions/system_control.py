import ctypes
import os
import platform
import subprocess
import threading
import time
from datetime import datetime
from pathlib import Path


# ============================================================
# WINDOWS VIRTUAL KEY CODES
# ============================================================
VK_VOLUME_MUTE = 0xAD
VK_VOLUME_DOWN = 0xAE
VK_VOLUME_UP = 0xAF
VK_MEDIA_NEXT_TRACK = 0xB0
VK_MEDIA_PREV_TRACK = 0xB1
VK_MEDIA_STOP = 0xB2
VK_MEDIA_PLAY_PAUSE = 0xB3
KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP = 0x0002


def _send_win_key(vk_code):
    """Presses and releases a virtual key on Windows."""
    user32 = ctypes.windll.user32
    user32.keybd_event(vk_code, 0, KEYEVENTF_EXTENDEDKEY, 0)
    time.sleep(0.05)
    user32.keybd_event(vk_code, 0, KEYEVENTF_EXTENDEDKEY | KEYEVENTF_KEYUP, 0)


# ============================================================
# VOLUME CONTROL
# ============================================================
def volume_up(steps=3):
    """Increases master volume."""
    system = platform.system()
    if system == "Windows":
        for _ in range(steps):
            _send_win_key(VK_VOLUME_UP)
            time.sleep(0.03)
        return "Turned volume up."
    elif system == "Linux":
        subprocess.run(["amixer", "-D", "pulse", "sset", "Master", f"{steps * 5}%+"], capture_output=True)
        return "Turned volume up."
    return "Volume control is not supported on this operating system."


def volume_down(steps=3):
    """Decreases master volume."""
    system = platform.system()
    if system == "Windows":
        for _ in range(steps):
            _send_win_key(VK_VOLUME_DOWN)
            time.sleep(0.03)
        return "Turned volume down."
    elif system == "Linux":
        subprocess.run(["amixer", "-D", "pulse", "sset", "Master", f"{steps * 5}%-"], capture_output=True)
        return "Turned volume down."
    return "Volume control is not supported on this operating system."


def volume_mute():
    """Toggles volume mute."""
    system = platform.system()
    if system == "Windows":
        _send_win_key(VK_VOLUME_MUTE)
        return "Toggled mute."
    elif system == "Linux":
        subprocess.run(["amixer", "-D", "pulse", "sset", "Master", "toggle"], capture_output=True)
        return "Toggled mute."
    return "Mute control is not supported on this operating system."


# ============================================================
# MEDIA PLAYBACK CONTROLS
# ============================================================
def media_play_pause():
    """Toggles media play/pause."""
    system = platform.system()
    if system == "Windows":
        _send_win_key(VK_MEDIA_PLAY_PAUSE)
        return "Toggled media playback."
    elif system == "Linux":
        subprocess.run(["playerctl", "play-pause"], capture_output=True)
        return "Toggled media playback."
    return "Media control is not supported on this operating system."


def media_next():
    """Skips to next track."""
    system = platform.system()
    if system == "Windows":
        _send_win_key(VK_MEDIA_NEXT_TRACK)
        return "Skipped to next track."
    elif system == "Linux":
        subprocess.run(["playerctl", "next"], capture_output=True)
        return "Skipped to next track."
    return "Media control is not supported on this operating system."


def media_previous():
    """Returns to previous track."""
    system = platform.system()
    if system == "Windows":
        _send_win_key(VK_MEDIA_PREV_TRACK)
        return "Skipped to previous track."
    elif system == "Linux":
        subprocess.run(["playerctl", "previous"], capture_output=True)
        return "Skipped to previous track."
    return "Media control is not supported on this operating system."


# ============================================================
# SYSTEM STATUS & TOOLS
# ============================================================
class _SYSTEM_POWER_STATUS(ctypes.Structure):
    _fields_ = [
        ("ACLineStatus", ctypes.c_byte),
        ("BatteryFlag", ctypes.c_byte),
        ("BatteryLifePercent", ctypes.c_byte),
        ("SystemStatusFlag", ctypes.c_byte),
        ("BatteryLifeTime", ctypes.c_ulong),
        ("BatteryFullLifeTime", ctypes.c_ulong),
    ]


class _MEMORYSTATUSEX(ctypes.Structure):
    _fields_ = [
        ("dwLength", ctypes.c_ulong),
        ("dwMemoryLoad", ctypes.c_ulong),
        ("ullTotalPhys", ctypes.c_ulonglong),
        ("ullAvailPhys", ctypes.c_ulonglong),
        ("ullTotalPageFile", ctypes.c_ulonglong),
        ("ullAvailPageFile", ctypes.c_ulonglong),
        ("ullTotalVirtual", ctypes.c_ulonglong),
        ("ullAvailVirtual", ctypes.c_ulonglong),
        ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
    ]


def get_system_status():
    """Returns a natural language summary of system battery and memory usage."""
    system = platform.system()
    parts = []

    if system == "Windows":
        # Memory
        mem = _MEMORYSTATUSEX()
        mem.dwLength = ctypes.sizeof(_MEMORYSTATUSEX)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(mem)):
            used_pct = mem.dwMemoryLoad
            total_gb = round(mem.ullTotalPhys / (1024**3), 1)
            avail_gb = round(mem.ullAvailPhys / (1024**3), 1)
            parts.append(f"RAM usage is at {used_pct}% ({avail_gb} GB free out of {total_gb} GB).")

        # Battery / Power
        power = _SYSTEM_POWER_STATUS()
        if ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(power)):
            pct = power.BatteryLifePercent
            ac = power.ACLineStatus
            if pct != -1 and pct <= 100:
                charging_text = "plugged in" if ac == 1 else "on battery"
                parts.append(f"Battery is at {pct}%, currently {charging_text}.")
            elif ac == 1:
                parts.append("Device is plugged into AC power.")

        parts.append(f"Operating system is Windows {platform.release()}.")
    else:
        parts.append(f"Running on {system}.")

    return " ".join(parts) if parts else "System status is healthy."


def lock_screen():
    """Locks the workstation."""
    system = platform.system()
    if system == "Windows":
        ctypes.windll.user32.LockWorkStation()
        return "Screen locked."
    elif system == "Linux":
        subprocess.run(["xdg-screensaver", "lock"], capture_output=True)
        return "Screen locked."
    return "Locking screen is not supported on this system."


def take_screenshot():
    """Captures the screen and saves it into the user's Pictures folder."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pictures_dir = Path(os.environ.get("USERPROFILE", Path.home())) / "Pictures" / "Screenshots"
    pictures_dir.mkdir(parents=True, exist_ok=True)
    target_path = pictures_dir / f"Screenshot_{timestamp}.png"

    if platform.system() == "Windows":
        ps_script = f"""
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
$bounds = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
$bitmap = New-Object System.Drawing.Bitmap $bounds.Width, $bounds.Height
$graphics = [System.Drawing.Graphics]::FromImage($bitmap)
$graphics.CopyFromScreen($bounds.Location, [System.Drawing.Point]::Empty, $bounds.Size)
$bitmap.Save('{str(target_path).replace("'", "''")}')
$graphics.Dispose()
$bitmap.Dispose()
"""
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_script],
            capture_output=True,
            text=True,
        )
        if target_path.exists():
            return f"Screenshot saved to Pictures/Screenshots."
        return f"Failed to capture screenshot: {result.stderr.strip()}"
    return "Screenshot capture is currently only supported on Windows."


# ============================================================
# ACTIVE TIMER MANAGER
# ============================================================
class TimerManager:
    """Manages background countdown timers with voice/sound alerts."""

    def __init__(self):
        self._timers = {}
        self._counter = 1
        self._lock = threading.Lock()

    def set_timer(self, seconds, label=None):
        from voice.tts import speak

        with self._lock:
            timer_id = self._counter
            self._counter += 1

        label = label or f"Timer #{timer_id}"

        def _countdown():
            time.sleep(seconds)
            with self._lock:
                self._timers.pop(timer_id, None)
            try:
                alert_text = f"Ding ding ding! Your {label} is done!"
                print(f"\n[TIMER ALERT] {alert_text}")
                speak(alert_text)
            except Exception as exc:
                print(f"Timer alert error: {exc}")

        thread = threading.Thread(target=_countdown, daemon=True)
        thread.start()

        with self._lock:
            self._timers[timer_id] = {
                "label": label,
                "duration": seconds,
                "started": time.time(),
                "thread": thread,
            }

        mins = seconds // 60
        secs = seconds % 60
        duration_desc = ""
        if mins > 0:
            duration_desc += f"{mins} minute{'s' if mins > 1 else ''}"
        if secs > 0:
            if duration_desc:
                duration_desc += f" and {secs} second{'s' if secs > 1 else ''}"
            else:
                duration_desc = f"{secs} second{'s' if secs > 1 else ''}"

        return f"Timer set for {duration_desc}."

    def list_timers(self):
        with self._lock:
            if not self._timers:
                return "There are no active timers."
            items = []
            now = time.time()
            for tid, tinfo in self._timers.items():
                remaining = max(0, int(tinfo["duration"] - (now - tinfo["started"])))
                items.append(f"{tinfo['label']} ({remaining}s remaining)")
            return "Active timers: " + ", ".join(items)


timer_manager = TimerManager()


_SKIP_EXE = {
    "nvxdsync.exe", "nvvsvc.exe", "nvtray.exe", "svchost.exe", "taskhostw.exe",
    "unsecapp.exe", "dllhost.exe", "RuntimeBroker.exe", "SearchHost.exe",
    "StartMenuExperienceHost.exe", "dwm.exe", "csrss.exe", "winlogon.exe",
    "msedgewebview2.exe", "WavesSvc64.exe", "RtkAudUService64.exe",
    "fontdrvhost.exe", "ctfmon.exe", "conhost.exe", "sihost.exe",
    "TextInputHost.exe", "ShellExperienceHost.exe", "explorer.exe",
    "ApplicationFrameHost.exe",
}

_SKIP_TITLES = {
    "N/A", "DWM Notification Window", "", "OleMainThreadWndName", "OLEChannelWnd",
    "Task Host Window", "Search", "Start", "Windows Push Notifications Platform",
    "NotificationIconWindow", "RealtekAudioAdminBackgroundProcessClass",
    "RealtekAudioBackgroundProcessClass", "WavesFXConnection_Capture",
    "Rtc Video PnP Listener", "DDE Server Window", "New notification",
    "Default IME", "MSCTFIME UI", "UxdService", "NvSvc",
    "Microsoft OneDrive Sync Service",
}


def get_open_windows():
    """Returns a spoken summary of visible user-facing application windows."""
    if platform.system() != "Windows":
        return "Window listing is only supported on Windows."
    try:
        import csv, io as _io
        result = subprocess.run(
            ["tasklist", "/v", "/fo", "csv"],
            capture_output=True, text=True, timeout=5
        )
        reader = csv.DictReader(_io.StringIO(result.stdout))
        windows = []
        seen = set()
        for row in reader:
            title = row.get("Window Title", "").strip()
            exe = row.get("Image Name", "").strip().lower()
            session = row.get("Session Name", "").strip()
            if (
                session == "Console"
                and title
                and title not in _SKIP_TITLES
                and exe not in {e.lower() for e in _SKIP_EXE}
            ):
                key = title.lower()[:70]
                if key not in seen:
                    seen.add(key)
                    windows.append(title)

        if not windows:
            return "I don't see any user applications open right now."

        if len(windows) == 1:
            return f"You have {windows[0]} open."

        listed = ", ".join(windows[:-1])
        return f"I can see {len(windows)} windows open: {listed}, and {windows[-1]}."
    except Exception as exc:
        return f"I couldn't list open windows: {exc}"


def get_current_time_and_date():
    """Returns natural language time and date."""
    now = datetime.now()
    time_str = now.strftime("%I:%M %p").lstrip("0")
    date_str = now.strftime("%A, %B %d, %Y")
    return f"It is currently {time_str} on {date_str}."
