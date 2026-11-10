import os
import pystray
from PIL import Image, ImageDraw, ImageFont

class TrayManager:
    def __init__(self, on_show_window, on_toggle_mini, on_toggle_autostart, on_quit, config_manager):
        self.on_show_window = on_show_window
        self.on_toggle_mini = on_toggle_mini
        self.on_toggle_autostart = on_toggle_autostart
        self.on_quit = on_quit
        self.config = config_manager

        self.last_val_int = -1
        self.icon = None
        self._font_path = self._find_best_font()
        self._init_tray()

    def _find_best_font(self):
        candidates = [
            r"C:\Windows\Fonts\segoeuib.ttf",
            r"C:\Windows\Fonts\arialbd.ttf",
            r"C:\Windows\Fonts\tahomabd.ttf",
        ]
        for c in candidates:
            if os.path.exists(c):
                return c
        return None

    def _generate_icon_image(self, watts):
        # 64x64 RGBA canvas
        img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Dynamic Color
        if watts < 20.0:
            fill_color = (16, 185, 129, 255)   # #10b981 Emerald
        elif watts < 45.0:
            fill_color = (245, 158, 11, 255)   # #f59e0b Amber
        else:
            fill_color = (239, 68, 68, 255)    # #ef4444 Red

        # Draw rounded rectangle icon
        draw.rounded_rectangle([2, 2, 62, 62], radius=15, fill=fill_color)

        val_int = int(round(watts))
        text = f"{val_int}W" if val_int < 100 else f"{val_int}"

        # Choose best font size to fit neatly
        font_size = 28 if len(text) <= 2 else (24 if len(text) == 3 else 20)
        try:
            if self._font_path:
                font = ImageFont.truetype(self._font_path, font_size)
            else:
                font = ImageFont.load_default()
        except Exception:
            font = ImageFont.load_default()

        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        x = (64 - tw) / 2
        y = (64 - th) / 2 - 4
        draw.text((x, y), text, fill=(255, 255, 255, 255), font=font)
        return img

    def _create_menu(self):
        autostart_checked = self.config.get("autostart", False)
        return pystray.Menu(
            pystray.MenuItem("⚡ EcoWatt Power Monitor", None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Mở giao diện chính", lambda: self.on_show_window(), default=True),
            pystray.MenuItem("Chế độ Mini Widget", lambda: self.on_toggle_mini()),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "Khởi động cùng Windows",
                lambda: self.on_toggle_autostart(),
                checked=lambda item: self.config.get("autostart", False)
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Thoát", lambda: self.on_quit())
        )

    def _init_tray(self):
        initial_img = self._generate_icon_image(15.0)
        self.icon = pystray.Icon(
            "EcoWatt",
            initial_img,
            "EcoWatt: Đang khởi động...",
            menu=self._create_menu()
        )

    def start(self):
        if self.icon:
            self.icon.run_detached()

    def update(self, watts, is_plugged, bat_percent, cpu_percent):
        if not self.icon:
            return

        val_int = int(round(watts))
        # Update image only when whole number changes (saves redraw cycles)
        if val_int != self.last_val_int:
            self.last_val_int = val_int
            self.icon.icon = self._generate_icon_image(watts)

        # Update hover tooltip
        power_src = "⚡ Sạc" if is_plugged else "🔋 Pin"
        tooltip = f"EcoWatt: {watts:.1f} W ({power_src} {bat_percent}% | CPU {int(cpu_percent)}%)"
        self.icon.title = tooltip

    def notify(self, title, message):
        try:
            if self.icon:
                self.icon.notify(message, title)
        except Exception:
            pass

    def stop(self):
        if self.icon:
            try:
                self.icon.stop()
            except Exception:
                pass

