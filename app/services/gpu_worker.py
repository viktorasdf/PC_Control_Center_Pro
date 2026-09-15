from PySide6.QtCore import QThread, Signal

from app.services.gpu_info import get_gpu_info


class GPUWorker(QThread):
    gpu_ready = Signal(dict)

    def __init__(self, interval=1.0, parent=None):
        # Совместимость с вызовами GPUWorker(parent)
        if not isinstance(interval, (int, float)):
            if parent is None:
                parent = interval
            interval = 1.0

        super().__init__(parent)

        self.interval = max(0.2, float(interval))
        self._running = True

    def stop(self):
        self._running = False

        if self.isRunning():
            self.requestInterruption()

    def run(self):
        while self._running and not self.isInterruptionRequested():
            try:
                gpu = get_gpu_info(include_usage=True)

                if isinstance(gpu, dict):
                    self.gpu_ready.emit(gpu)

            except Exception as exc:
                print("[GPUWorker] ERROR:", repr(exc))

                self.gpu_ready.emit({
                    "name": "Unknown GPU",
                    "usage": 0.0,
                    "usage_3d": 0.0,
                    "usage_compute": 0.0,
                    "usage_video_decode": 0.0,
                    "usage_video_encode": 0.0,
                    "memory_total": 0,
                    "memory_used": 0,
                    "memory_percent": 0,
                    "temperature": None,
                    "vendor": "Unknown",
                })

            if (
                self._running
                and not self.isInterruptionRequested()
            ):
                self.msleep(int(self.interval * 1000))