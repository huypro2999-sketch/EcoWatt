import time
import threading
import ctypes
from ctypes import wintypes
import psutil
import wmi

class SYSTEM_POWER_STATUS(ctypes.Structure):
    _fields_ = [
        ('ACLineStatus', ctypes.c_byte),
        ('BatteryFlag', ctypes.c_byte),
        ('BatteryLifePercent', ctypes.c_byte),
        ('SystemStatusFlag', ctypes.c_byte),
        ('BatteryLifeTime', ctypes.c_ulong),
        ('BatteryFullLifeTime', ctypes.c_ulong),
    ]

class PowerEngine:
    def __init__(self, evn_rate=2500):
        self.evn_rate = evn_rate
        self.is_admin = self._check_admin()
        self.cpu_name = self._get_cpu_name()
        self.cpu_cores = psutil.cpu_count(logical=True)
        self.max_freq = 2000.0
        try:
            freq = psutil.cpu_freq()
            if freq and freq.max > 0:
                self.max_freq = freq.max
        except Exception:
            pass

        self._wmi = None
        self._wmi_lock = threading.Lock()
        
        # Telemetry Cache
        self.latest_data = {
            "total_watts": 12.0,
            "is_plugged": True,
            "bat_percent": 100,
            "bat_seconds": None,
            "cpu_watts": 5.0,
            "cpu_percent": 15.0,
            "cpu_freq_ghz": 1.8,
            "cpu_name": self.cpu_name,
            "gpu_watts": 1.5,
            "gpu_percent": 5.0,
            "screen_watts": 2.5,
            "screen_brightness": 70,
            "board_watts": 3.0,
            "mem_percent": 50.0,
            "is_admin": self.is_admin,
            "cost_per_hour_vnd": 30
        }
        
        self._running = True
        self._worker_thread = threading.Thread(target=self._telemetry_worker, daemon=True)
        self._worker_thread.start()

    def _check_admin(self):
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            return False

    def _get_cpu_name(self):
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0")
            name, _ = winreg.QueryValueEx(key, "ProcessorNameString")
            winreg.CloseKey(key)
            # Shorten name if too long
            clean = name.replace("Intel(R) Core(TM)", "Intel Core").replace("CPU @", "@").strip()
            return clean
        except Exception:
            return "Intel/AMD Processor"

    def _get_wmi(self):
        if self._wmi is None:
            try:
                import pythoncom
                pythoncom.CoInitialize()
                self._wmi = wmi.WMI(namespace="root/wmi")
            except Exception:
                self._wmi = None
        return self._wmi

    def _read_battery_and_screen(self):
        discharge_w = 0.0
        brightness = 70
        try:
            with self._wmi_lock:
                w = self._get_wmi()
                if w:
                    # Query battery status
                    bat_objs = w.BatteryStatus()
                    if bat_objs:
                        rate_mw = bat_objs[0].DischargeRate
                        if rate_mw and rate_mw > 0:
                            discharge_w = rate_mw / 1000.0

                    # Query brightness
                    b_objs = w.WmiMonitorBrightness()
                    if b_objs and b_objs[0].CurrentBrightness is not None:
                        brightness = int(b_objs[0].CurrentBrightness)
                        if brightness == 0:  # When 0 (sometimes external monitor), fallback to nominal 60%
                            brightness = 60
        except Exception:
            pass
        return discharge_w, brightness

    def _telemetry_worker(self):
        # Background loop polling every 1000ms
        while self._running:
            try:
                # 1. Battery OS API (Instant)
                sps = SYSTEM_POWER_STATUS()
                ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(sps))
                is_plugged = (sps.ACLineStatus == 1)
                percent = sps.BatteryLifePercent if sps.BatteryLifePercent <= 100 else 100
                bat_secs = sps.BatteryLifeTime if sps.BatteryLifeTime != 0xFFFFFFFF else None

                # 2. Direct WMI battery discharge & screen brightness
                discharge_w, brightness = self._read_battery_and_screen()

                # 3. CPU & RAM
                cpu_pct = psutil.cpu_percent(interval=None)
                cur_freq = self.max_freq
                try:
                    f = psutil.cpu_freq()
                    if f and f.current > 0:
                        cur_freq = f.current
                except Exception:
                    pass
                mem = psutil.virtual_memory()

                # 4. CPU Power Model (i7-8550U)
                # Idle is ~1.5W, TDP base is 15W, boost up to 25W+
                freq_ratio = min(max(cur_freq / self.max_freq, 0.4), 1.5)
                load_fraction = cpu_pct / 100.0
                cpu_watts = 1.6 + (14.0 * load_fraction * (freq_ratio ** 1.3))
                cpu_watts = round(min(max(cpu_watts, 1.4), 32.0), 1)

                # 5. Screen Power Model
                screen_watts = round(2.0 + (brightness / 100.0) * 6.5, 1)

                # 6. Motherboard, RAM, SSD, Fan
                board_watts = round(3.2 + (mem.percent / 100.0) * 2.2, 1)

                # 7. GPU Power (Integrated or Discrete)
                # Idle GPU is ~0.6W, active load scales up to 15W
                # We estimate lightweight GPU activity from CPU activity & RAM
                gpu_load = round(min(max(cpu_pct * 0.35, 1.0), 100.0), 1)
                gpu_watts = round(0.6 + (gpu_load / 100.0) * 8.0, 1)

                # Total calculation
                if not is_plugged and discharge_w > 0:
                    # Battery hardware sensor reports ground truth for whole laptop
                    total_watts = round(discharge_w, 1)
                    est_sum = cpu_watts + gpu_watts + screen_watts + board_watts
                    if est_sum > 0:
                        ratio = total_watts / est_sum
                        cpu_watts = round(cpu_watts * ratio, 1)
                        gpu_watts = round(gpu_watts * ratio, 1)
                        screen_watts = round(screen_watts * ratio, 1)
                        board_watts = round(max(total_watts - (cpu_watts + gpu_watts + screen_watts), 0.5), 1)
                else:
                    total_watts = round(cpu_watts + gpu_watts + screen_watts + board_watts, 1)

                # Electricity cost in VND
                cost_per_hour = int((total_watts / 1000.0) * self.evn_rate)

                self.latest_data = {
                    "total_watts": total_watts,
                    "is_plugged": is_plugged,
                    "bat_percent": percent,
                    "bat_seconds": bat_secs,
                    "cpu_watts": cpu_watts,
                    "cpu_percent": round(cpu_pct, 1),
                    "cpu_freq_ghz": round(cur_freq / 1000.0, 2),
                    "cpu_name": self.cpu_name,
                    "gpu_watts": gpu_watts,
                    "gpu_percent": gpu_load,
                    "screen_watts": screen_watts,
                    "screen_brightness": brightness,
                    "board_watts": board_watts,
                    "mem_percent": round(mem.percent, 1),
                    "is_admin": self.is_admin,
                    "cost_per_hour_vnd": max(cost_per_hour, 10)
                }
            except Exception as e:
                pass

            time.sleep(1.0)

    def get_data(self):
        return dict(self.latest_data)

    def set_evn_rate(self, rate):
        try:
            self.evn_rate = int(rate)
        except Exception:
            pass

    def stop(self):
        self._running = False
