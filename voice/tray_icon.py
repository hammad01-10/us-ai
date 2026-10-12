import threading
from PIL import Image, ImageDraw
import pystray

from core.autostart import disable_autostart, enable_autostart, is_autostart_enabled
from memory import memory


def _create_tray_image(state="active"):
    """Generates a sleek, high-resolution AI assistant icon for the Windows taskbar tray."""
    size = 64
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    # Outer ambient glow
    accent = "#60F5FF" if state == "active" else "#FF6B6B"
    deep = "#122D65" if state == "active" else "#5A1E1E"

    draw.ellipse((4, 4, 60, 60), fill=deep, outline=accent, width=2)
    draw.ellipse((12, 12, 52, 52), fill="#0B132B")
    draw.ellipse((20, 20, 44, 44), fill=accent)
    draw.ellipse((24, 24, 38, 38), fill="#FFFFFF")

    return image


class AssistantTray:
    """Manages the Windows taskbar notification area tray icon and context menu."""

    def __init__(self, on_open_hud=None, on_exit=None, on_toggle_mic=None):
        self.on_open_hud = on_open_hud
        self.on_exit = on_exit
        self.on_toggle_mic = on_toggle_mic
        self.mic_muted = False
        self._icon = None
        self._thread = None

    def _build_menu(self):
        def _get_status_text(item):
            return "🔴 Mic Muted" if self.mic_muted else "🟢 Status: Listening"

        def _get_autostart_text(item):
            return "✓ Autostart on Windows Boot" if is_autostart_enabled() else "  Enable Autostart on Boot"

        def _get_response_style_text(item):
            style = memory.get_response_style().title()
            return f"✓ Response: {style}" if style else "Response: Brief"

        def _handle_autostart_toggle(icon, item):
            if is_autostart_enabled():
                disable_autostart()
            else:
                enable_autostart()
            icon.menu = self._build_menu()

        def _handle_toggle_mic(icon, item):
            self.mic_muted = not self.mic_muted
            icon.icon = _create_tray_image("muted" if self.mic_muted else "active")
            icon.menu = self._build_menu()
            if self.on_toggle_mic:
                self.on_toggle_mic(self.mic_muted)

        def _handle_set_style(style):
            def _set(icon, item):
                memory.set_response_style(style)
                icon.menu = self._build_menu()
            return _set

        def _handle_open_hud(icon, item):
            if self.on_open_hud:
                self.on_open_hud()

        def _handle_exit(icon, item):
            icon.stop()
            if self.on_exit:
                self.on_exit()

        return pystray.Menu(
            pystray.MenuItem(_get_status_text, None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("💬 Open US AI Assistant", _handle_open_hud, default=True),
            pystray.MenuItem("🎙️ Mute / Unmute Microphone", _handle_toggle_mic),
            pystray.MenuItem("⚡ Brief mode", _handle_set_style("brief")),
            pystray.MenuItem("🧠 Detailed mode", _handle_set_style("detailed")),
            pystray.MenuItem("🤫 Quiet mode", _handle_set_style("quiet")),
            pystray.MenuItem(_get_response_style_text, None, enabled=False),
            pystray.MenuItem(_get_autostart_text, _handle_autostart_toggle),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("❌ Exit US AI", _handle_exit),
        )

    def start(self):
        """Starts the system tray icon in a dedicated daemon thread."""
        img = _create_tray_image("active")
        self._icon = pystray.Icon(
            "US_AI",
            img,
            "US AI Desktop Assistant",
            menu=self._build_menu(),
        )

        def _run():
            try:
                self._icon.run()
            except Exception as exc:
                print(f"Tray icon error: {exc}")

        self._thread = threading.Thread(target=_run, name="tray-icon-thread", daemon=True)
        self._thread.start()

    def set_mic_muted(self, muted):
        """Synchronizes the tray menu and icon with the assistant microphone state."""
        self.mic_muted = bool(muted)
        if self._icon is not None:
            self._icon.icon = _create_tray_image("muted" if self.mic_muted else "active")
            self._icon.menu = self._build_menu()

    def stop(self):
        if self._icon is not None:
            try:
                self._icon.stop()
            except Exception:
                pass
            self._icon = None
