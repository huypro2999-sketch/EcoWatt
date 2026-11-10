import os
import sys
import ctypes
from ctypes import wintypes
import customtkinter as ctk

# Ensure working directory is the script/executable directory
if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

os.chdir(BASE_DIR)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from power_engine import PowerEngine
from config import ConfigManager
from tray_manager import TrayManager

# Appearance setup
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

import threading

# Win32 Single Instance Mutex & IPC Event
MUTEX_NAME = "Global\\EcoWatt_SingleInstance_Mutex_b5fcdf98"
EVENT_NAME = "Global\\EcoWatt_RestoreEvent_b5fcdf98"
ERROR_ALREADY_EXISTS = 183

def check_single_instance():
    try:
        mutex = ctypes.windll.kernel32.CreateMutexW(None, False, MUTEX_NAME)
        if ctypes.windll.kernel32.GetLastError() == ERROR_ALREADY_EXISTS:
            # Another instance is already running! Signal it to restore
            signal_existing_instance()
            return None
        return mutex
    except Exception:
        return True

def create_restore_event():
    try:
        return ctypes.windll.kernel32.CreateEventW(None, False, False, EVENT_NAME)
    except Exception:
        return None

def signal_existing_instance():
    try:
        EVENT_MODIFY_STATE = 0x0002
        h_event = ctypes.windll.kernel32.OpenEventW(EVENT_MODIFY_STATE, False, EVENT_NAME)
        if h_event:
            ctypes.windll.kernel32.SetEvent(h_event)
            ctypes.windll.kernel32.CloseHandle(h_event)
        
        # Also bring window to front directly via Win32 API
        hwnd = ctypes.windll.user32.FindWindowW(None, "EcoWatt - Tổng Điện Năng Laptop")
        if hwnd:
            SW_RESTORE = 9
            ctypes.windll.user32.ShowWindow(hwnd, SW_RESTORE)
            ctypes.windll.user32.SetForegroundWindow(hwnd)
    except Exception:
        pass

class EcoWattApp(ctk.CTk):
    def __init__(self, mutex_handle, restore_event=None):
        super().__init__()
        self.mutex_handle = mutex_handle
        self.restore_event = restore_event
        self._running = True

        # Load Configuration
        self.config = ConfigManager()
        self.engine = PowerEngine(evn_rate=self.config.get("evn_rate", 2500))

        # States
        self.is_expanded = False
        self.is_mini = False
        self.is_settings_open = False
        self.always_on_top = self.config.get("always_on_top", False)

        # Window Settings
        self.title("EcoWatt - Tổng Điện Năng Laptop")
        self.geometry("400x345")
        self.resizable(False, False)
        self.configure(fg_color="#111215")

        if self.always_on_top:
            self.attributes("-topmost", True)

        # Fonts
        self.font_title = ctk.CTkFont(family="Segoe UI", size=15, weight="bold")
        self.font_big_num = ctk.CTkFont(family="Segoe UI", size=48, weight="bold")
        self.font_unit = ctk.CTkFont(family="Segoe UI", size=18, weight="bold")
        self.font_badge = ctk.CTkFont(family="Segoe UI", size=12, weight="bold")
        self.font_body = ctk.CTkFont(family="Segoe UI", size=12)
        self.font_small = ctk.CTkFont(family="Segoe UI", size=11)
        self.font_bold_sm = ctk.CTkFont(family="Segoe UI", size=11, weight="bold")

        # Build UI
        self.build_ui()

        # Build Tray Manager
        self.tray = TrayManager(
            on_show_window=self.show_window_from_tray,
            on_toggle_mini=self.toggle_mini_mode,
            on_toggle_autostart=self.toggle_autostart,
            on_quit=self.quit_app,
            config_manager=self.config
        )
        self.tray.start()

        # Start Restore Event Listener Thread
        if self.restore_event:
            self._ipc_thread = threading.Thread(target=self._restore_listener_loop, daemon=True)
            self._ipc_thread.start()

        # Intercept window close (X)
        self.protocol("WM_DELETE_WINDOW", self.on_window_close)

        # Telemetry update loop
        self.update_telemetry()

    def _restore_listener_loop(self):
        WAIT_OBJECT_0 = 0
        while self._running and self.restore_event:
            try:
                res = ctypes.windll.kernel32.WaitForSingleObject(self.restore_event, 500)
                if res == WAIT_OBJECT_0:
                    self.after(0, self.show_window_from_tray)
            except Exception:
                break

    def build_ui(self):
        # 1. Header Frame
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=16, pady=(14, 6))

        self.app_title = ctk.CTkLabel(
            self.header_frame,
            text="⚡ EcoWatt",
            font=self.font_title,
            text_color="#f4f4f5"
        )
        self.app_title.pack(side="left")

        # Right buttons on header: Settings, Mini, Pin
        self.settings_btn = ctk.CTkButton(
            self.header_frame,
            text="⚙️",
            width=32,
            height=26,
            fg_color="#24262f",
            hover_color="#363945",
            text_color="#a1a1aa",
            font=self.font_small,
            command=self.toggle_settings
        )
        self.settings_btn.pack(side="right", padx=(6, 0))

        self.pin_btn = ctk.CTkButton(
            self.header_frame,
            text="📌 Đã ghim" if self.always_on_top else "📌 Ghim",
            width=62,
            height=26,
            fg_color="#0284c7" if self.always_on_top else "#24262f",
            hover_color="#0369a1" if self.always_on_top else "#363945",
            text_color="#ffffff" if self.always_on_top else "#a1a1aa",
            font=self.font_small,
            command=self.toggle_always_on_top
        )
        self.pin_btn.pack(side="right", padx=(6, 0))

        self.mini_btn = ctk.CTkButton(
            self.header_frame,
            text="🗗 Mini",
            width=54,
            height=26,
            fg_color="#24262f",
            hover_color="#363945",
            text_color="#a1a1aa",
            font=self.font_small,
            command=self.toggle_mini_mode
        )
        self.mini_btn.pack(side="right")

        # 2. Hero Card (Main Display)
        self.hero_card = ctk.CTkFrame(self, fg_color="#181a20", corner_radius=14, border_width=1, border_color="#282a33")
        self.hero_card.pack(fill="x", padx=16, pady=6)

        # Status Bar inside Hero Card
        self.status_bar = ctk.CTkFrame(self.hero_card, fg_color="transparent")
        self.status_bar.pack(fill="x", padx=16, pady=(12, 0))

        self.power_badge = ctk.CTkLabel(
            self.status_bar,
            text="⚡ Đang cắm sạc",
            font=self.font_badge,
            fg_color="#1e293b",
            text_color="#38bdf8",
            corner_radius=6,
            padx=8,
            pady=2
        )
        self.power_badge.pack(side="left")

        self.cost_label = ctk.CTkLabel(
            self.status_bar,
            text="~35 đ / giờ",
            font=self.font_small,
            text_color="#a1a1aa"
        )
        self.cost_label.pack(side="right")

        # Large Watt Display
        self.num_container = ctk.CTkFrame(self.hero_card, fg_color="transparent")
        self.num_container.pack(pady=(4, 0))

        self.watt_label = ctk.CTkLabel(
            self.num_container,
            text="--.-",
            font=self.font_big_num,
            text_color="#10b981"
        )
        self.watt_label.pack(side="left")

        self.unit_label = ctk.CTkLabel(
            self.num_container,
            text=" W",
            font=self.font_unit,
            text_color="#71717a"
        )
        self.unit_label.pack(side="left", padx=(2, 0), pady=(14, 0))

        # Status Category Badge
        self.category_label = ctk.CTkLabel(
            self.hero_card,
            text="🟢 Tiết kiệm • Tác vụ nhẹ",
            font=self.font_small,
            text_color="#10b981"
        )
        self.category_label.pack(pady=(2, 4))

        # Subtitle info
        self.sub_info_label = ctk.CTkLabel(
            self.hero_card,
            text="Pin: --% • Cắm sạc",
            font=self.font_small,
            text_color="#94a3b8"
        )
        self.sub_info_label.pack(pady=(0, 12))

        # 3. Accordion Button
        self.expand_btn = ctk.CTkButton(
            self,
            text="Chi tiết linh kiện  ▼",
            fg_color="#20222a",
            hover_color="#2b2d38",
            text_color="#e4e4e7",
            font=self.font_small,
            height=32,
            corner_radius=8,
            command=self.toggle_expand
        )
        self.expand_btn.pack(fill="x", padx=16, pady=(8, 4))

        # 4. Detail Frame (Accordion content)
        self.detail_frame = ctk.CTkFrame(self, fg_color="#16171d", corner_radius=12, border_width=1, border_color="#272932")
        self.cpu_row = self._create_component_row(self.detail_frame, "🖥️ CPU", "#38bdf8")
        self.gpu_row = self._create_component_row(self.detail_frame, "🎮 GPU", "#a855f7")
        self.screen_row = self._create_component_row(self.detail_frame, "💡 Màn hình", "#eab308")
        self.board_row = self._create_component_row(self.detail_frame, "⚙️ Bo mạch & Khác", "#64748b")

        # 5. Settings Frame (Modal drawer)
        self.settings_frame = ctk.CTkFrame(self, fg_color="#16171d", corner_radius=12, border_width=1, border_color="#272932")
        self._build_settings_ui(self.settings_frame)

    def _create_component_row(self, parent, title, color):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", padx=12, pady=6)

        header = ctk.CTkFrame(frame, fg_color="transparent")
        header.pack(fill="x")

        lbl_title = ctk.CTkLabel(header, text=title, font=self.font_bold_sm, text_color="#f4f4f5")
        lbl_title.pack(side="left")

        lbl_val = ctk.CTkLabel(header, text="0.0 W", font=self.font_bold_sm, text_color=color)
        lbl_val.pack(side="right")

        progress = ctk.CTkProgressBar(frame, height=5, progress_color=color, fg_color="#27272a")
        progress.pack(fill="x", pady=(4, 2))
        progress.set(0.1)

        sub_info = ctk.CTkLabel(frame, text="--", font=ctk.CTkFont(size=10), text_color="#71717a", anchor="w")
        sub_info.pack(fill="x")

        return {
            "val_label": lbl_val,
            "progress": progress,
            "sub_info": sub_info
        }

    def _build_settings_ui(self, parent):
        lbl = ctk.CTkLabel(parent, text="⚙️ Cài đặt ứng dụng", font=self.font_bold_sm, text_color="#f4f4f5")
        lbl.pack(anchor="w", padx=14, pady=(10, 6))

        # Switch: Autostart
        self.sw_autostart = ctk.CTkSwitch(
            parent,
            text="Khởi động cùng Windows",
            font=self.font_small,
            command=self._on_switch_autostart
        )
        self.sw_autostart.pack(anchor="w", padx=14, pady=4)
        if self.config.get("autostart", False):
            self.sw_autostart.select()

        # Switch: Minimize to tray on close
        self.sw_min_tray = ctk.CTkSwitch(
            parent,
            text="Thu nhỏ về khay hệ thống khi đóng (X)",
            font=self.font_small,
            command=self._on_switch_min_tray
        )
        self.sw_min_tray.pack(anchor="w", padx=14, pady=4)
        if self.config.get("minimize_to_tray", True):
            self.sw_min_tray.select()

        # EVN Rate input
        evn_frame = ctk.CTkFrame(parent, fg_color="transparent")
        evn_frame.pack(fill="x", padx=14, pady=(6, 12))

        lbl_rate = ctk.CTkLabel(evn_frame, text="Giá điện (đ/kWh):", font=self.font_small, text_color="#a1a1aa")
        lbl_rate.pack(side="left")

        self.entry_rate = ctk.CTkEntry(evn_frame, width=80, height=26, font=self.font_small)
        self.entry_rate.pack(side="left", padx=8)
        self.entry_rate.insert(0, str(self.config.get("evn_rate", 2500)))

        btn_save_rate = ctk.CTkButton(
            evn_frame,
            text="Lưu",
            width=45,
            height=26,
            font=self.font_small,
            fg_color="#0284c7",
            hover_color="#0369a1",
            command=self._save_evn_rate
        )
        btn_save_rate.pack(side="left")

    def _on_switch_autostart(self):
        val = bool(self.sw_autostart.get())
        self.config.set("autostart", val)

    def _on_switch_min_tray(self):
        val = bool(self.sw_min_tray.get())
        self.config.set("minimize_to_tray", val)

    def _save_evn_rate(self):
        try:
            val = int(self.entry_rate.get().strip())
            self.config.set("evn_rate", val)
            self.engine.set_evn_rate(val)
        except Exception:
            pass

    def toggle_settings(self):
        self.is_settings_open = not self.is_settings_open
        if self.is_settings_open:
            if self.is_expanded:
                self.toggle_expand()
            self.settings_frame.pack(fill="both", expand=True, padx=16, pady=(4, 12))
            self.geometry("400x530")
            self.settings_btn.configure(fg_color="#0284c7", text_color="#ffffff")
        else:
            self.settings_frame.pack_forget()
            self.geometry("400x345")
            self.settings_btn.configure(fg_color="#24262f", text_color="#a1a1aa")

    def toggle_expand(self):
        self.is_expanded = not self.is_expanded
        if self.is_expanded:
            if self.is_settings_open:
                self.toggle_settings()
            self.detail_frame.pack(fill="both", expand=True, padx=16, pady=(4, 12))
            self.geometry("400x595")
            self.expand_btn.configure(text="Thu gọn chi tiết  ▲")
        else:
            self.detail_frame.pack_forget()
            self.geometry("400x345")
            self.expand_btn.configure(text="Chi tiết linh kiện  ▼")

    def toggle_always_on_top(self):
        self.always_on_top = not self.always_on_top
        self.attributes("-topmost", self.always_on_top)
        self.config.set("always_on_top", self.always_on_top)
        if self.always_on_top:
            self.pin_btn.configure(fg_color="#0284c7", text_color="#ffffff", text="📌 Đã ghim")
        else:
            self.pin_btn.configure(fg_color="#24262f", text_color="#a1a1aa", text="📌 Ghim")

    def toggle_mini_mode(self):
        # Can be called from UI or from Tray
        self.after(0, self._toggle_mini_mode_impl)

    def _toggle_mini_mode_impl(self):
        self.is_mini = not self.is_mini
        if self.is_mini:
            # Hide standard window frames
            if self.is_expanded:
                self.detail_frame.pack_forget()
            if self.is_settings_open:
                self.settings_frame.pack_forget()
            self.expand_btn.pack_forget()
            self.hero_card.pack_forget()
            self.header_frame.pack_forget()

            # Compact floating widget
            self.geometry("265x66")
            self.attributes("-topmost", True)
            self.overrideredirect(True)

            self.mini_frame = ctk.CTkFrame(self, fg_color="#181a20", corner_radius=12, border_width=1, border_color="#38bdf8")
            self.mini_frame.pack(fill="both", expand=True, padx=2, pady=2)

            self.mini_lbl = ctk.CTkLabel(self.mini_frame, text="⚡ -- W", font=ctk.CTkFont(size=16, weight="bold"), text_color="#10b981")
            self.mini_lbl.pack(side="left", padx=12)

            self.mini_restore_btn = ctk.CTkButton(
                self.mini_frame, text="✕", width=28, height=24, fg_color="transparent", hover_color="#282a33", command=self.toggle_mini_mode
            )
            self.mini_restore_btn.pack(side="right", padx=6)

            self.mini_frame.bind("<Button-1>", self._start_drag)
            self.mini_frame.bind("<B1-Motion>", self._on_drag)
        else:
            if hasattr(self, 'mini_frame'):
                self.mini_frame.destroy()
            self.overrideredirect(False)
            self.attributes("-topmost", self.always_on_top)

            # Rebuild standard layout
            self.header_frame.pack(fill="x", padx=16, pady=(14, 6))
            self.hero_card.pack(fill="x", padx=16, pady=6)
            self.expand_btn.pack(fill="x", padx=16, pady=(8, 4))
            if self.is_expanded:
                self.detail_frame.pack(fill="both", expand=True, padx=16, pady=(4, 12))
                self.geometry("400x595")
            elif self.is_settings_open:
                self.settings_frame.pack(fill="both", expand=True, padx=16, pady=(4, 12))
                self.geometry("400x530")
            else:
                self.geometry("400x345")

    def _start_drag(self, event):
        self._drag_x = event.x
        self._drag_y = event.y

    def _on_drag(self, event):
        x = self.winfo_x() + (event.x - self._drag_x)
        y = self.winfo_y() + (event.y - self._drag_y)
        self.geometry(f"+{x}+{y}")

    def show_window_from_tray(self):
        self.after(0, self._show_window_impl)

    def _show_window_impl(self):
        if self.is_mini:
            self._toggle_mini_mode_impl()
        self.deiconify()
        self.lift()
        self.focus_force()

    def toggle_autostart(self):
        cur = self.config.get("autostart", False)
        self.config.set("autostart", not cur)
        if hasattr(self, 'sw_autostart'):
            if not cur:
                self.sw_autostart.select()
            else:
                self.sw_autostart.deselect()

    def update_telemetry(self):
        data = self.engine.get_data()
        total_w = data["total_watts"]

        # Dynamic Color coding
        if total_w < 20.0:
            color = "#10b981"  # Emerald Green
            category = "🟢 Tiết kiệm • Tác vụ văn phòng / lướt web"
        elif total_w < 45.0:
            color = "#f59e0b"  # Amber Yellow
            category = "🟡 Tải vừa phải • Làm việc đa nhiệm / Đồ họa nhẹ"
        else:
            color = "#ef4444"  # Red
            category = "🔴 Tải cao • Gaming / Render đồ họa"

        self.watt_label.configure(text=f"{total_w:.1f}", text_color=color)
        self.category_label.configure(text=category, text_color=color)

        # Power Status
        if data["is_plugged"]:
            self.power_badge.configure(
                text="⚡ Đang cắm sạc",
                fg_color="#1e293b",
                text_color="#38bdf8"
            )
            self.sub_info_label.configure(text=f"Pin: {data['bat_percent']}% • Đang dùng nguồn điện AC")
        else:
            time_str = ""
            if data["bat_seconds"]:
                hours = int(data["bat_seconds"] // 3600)
                mins = int((data["bat_seconds"] % 3600) // 60)
                time_str = f" • Còn ~{hours}h {mins}m"
            self.power_badge.configure(
                text="🔋 Đang dùng pin",
                fg_color="#064e3b",
                text_color="#34d399"
            )
            self.sub_info_label.configure(text=f"Pin: {data['bat_percent']}%{time_str}")

        # Cost
        self.cost_label.configure(text=f"~{data['cost_per_hour_vnd']} đ / giờ")

        # Mini mode label if active
        if self.is_mini and hasattr(self, 'mini_lbl'):
            icon = "⚡" if data["is_plugged"] else "🔋"
            self.mini_lbl.configure(text=f"{icon} {total_w:.1f} W ({data['bat_percent']}%)", text_color=color)

        # Update Tray Icon
        self.tray.update(
            watts=total_w,
            is_plugged=data["is_plugged"],
            bat_percent=data["bat_percent"],
            cpu_percent=data["cpu_percent"]
        )

        # Update details if expanded
        if self.is_expanded:
            safe_total = max(total_w, 0.1)

            # CPU
            cpu_w = data["cpu_watts"]
            cpu_ratio = min(cpu_w / safe_total, 1.0)
            self.cpu_row["val_label"].configure(text=f"{cpu_w:.1f} W ({int(cpu_ratio*100)}%)")
            self.cpu_row["progress"].set(cpu_ratio)
            self.cpu_row["sub_info"].configure(
                text=f"{data['cpu_name']} • Tải {data['cpu_percent']}% • {data['cpu_freq_ghz']} GHz"
            )

            # GPU
            gpu_w = data["gpu_watts"]
            gpu_ratio = min(gpu_w / safe_total, 1.0)
            self.gpu_row["val_label"].configure(text=f"{gpu_w:.1f} W ({int(gpu_ratio*100)}%)")
            self.gpu_row["progress"].set(gpu_ratio)
            self.gpu_row["sub_info"].configure(text=f"Đồ họa • Tải {data['gpu_percent']}%")

            # Screen
            screen_w = data["screen_watts"]
            screen_ratio = min(screen_w / safe_total, 1.0)
            self.screen_row["val_label"].configure(text=f"{screen_w:.1f} W ({int(screen_ratio*100)}%)")
            self.screen_row["progress"].set(screen_ratio)
            self.screen_row["sub_info"].configure(text=f"Độ sáng: {data['screen_brightness']}%")

            # Board
            board_w = data["board_watts"]
            board_ratio = min(board_w / safe_total, 1.0)
            self.board_row["val_label"].configure(text=f"{board_w:.1f} W ({int(board_ratio*100)}%)")
            self.board_row["progress"].set(board_ratio)
            self.board_row["sub_info"].configure(text=f"RAM {data['mem_percent']}% • Bo mạch, Quạt, SSD")

        # Repeat update after 1000ms
        self.after(1000, self.update_telemetry)

    def on_window_close(self):
        if self.config.get("minimize_to_tray", True):
            self.withdraw()
            if self.config.get("first_run_notification", True):
                self.tray.notify(
                    "EcoWatt vẫn đang chạy ngầm",
                    "Ứng dụng đã thu nhỏ xuống khay Taskbar để tiếp tục theo dõi lượng điện."
                )
                self.config.set("first_run_notification", False)
        else:
            self.quit_app()

    def quit_app(self):
        self._running = False
        self.engine.stop()
        self.tray.stop()
        if self.restore_event:
            try:
                ctypes.windll.kernel32.CloseHandle(self.restore_event)
            except Exception:
                pass
        if self.mutex_handle and self.mutex_handle != True:
            try:
                ctypes.windll.kernel32.CloseHandle(self.mutex_handle)
            except Exception:
                pass
        self.destroy()
        sys.exit(0)

if __name__ == "__main__":
    mutex = check_single_instance()
    if not mutex:
        # Another instance is already running; it was signaled to restore to front
        sys.exit(0)

    restore_event = create_restore_event()
    app = EcoWattApp(mutex, restore_event)
    app.mainloop()
