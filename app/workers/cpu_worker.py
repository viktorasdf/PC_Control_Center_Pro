from PySide6.QtCore import QThread, Signal

from app.services.cpu_info import get_cpu_info


class CPUWorker(QThread):
    """
    Фоновый worker для мониторинга CPU.
    """

    cpu_ready = Signal(dict)

    def __init__(
        self,
        interval_ms=1000,
        parent=None,
    ):
        super().__init__(parent)

        self.interval_ms = max(
            100,
            int(interval_ms),
        )

        self._running = False

    # ==========================================================
    # RUN
    # ==========================================================

    def run(self):

        print(
            "[CPUWorker] Thread started"
        )

        self._running = True

        while self._running:

            try:

                data = get_cpu_info()

                if not isinstance(
                    data,
                    dict,
                ):
                    data = {
                        "usage": 0.0,
                        "cores": 0,
                        "threads": 0,
                        "frequency_current": 0.0,
                        "frequency_min": 0.0,
                        "frequency_max": 0.0,
                        "load_1m": 0.0,
                        "load_5m": 0.0,
                        "load_15m": 0.0,
                    }

                self.cpu_ready.emit(
                    data
                )

            except Exception as exc:

                print(
                    "[CPUWorker] ERROR:",
                    repr(exc),
                )

                self.cpu_ready.emit({
                    "usage": 0.0,
                    "cores": 0,
                    "threads": 0,
                    "frequency_current": 0.0,
                    "frequency_min": 0.0,
                    "frequency_max": 0.0,
                    "load_1m": 0.0,
                    "load_5m": 0.0,
                    "load_15m": 0.0,
                    "error": str(exc),
                })

            # --------------------------------------------------
            # Interruptible sleep
            # --------------------------------------------------

            elapsed = 0

            while (
                self._running
                and elapsed < self.interval_ms
            ):

                self.msleep(100)

                elapsed += 100

        print(
            "[CPUWorker] Thread stopped"
        )

    # ==========================================================
    # STOP
    # ==========================================================

    def stop(self):

        print(
            "[CPUWorker] stop() called"
        )

        self._running = False

        if not self.isRunning():

            print(
                "[CPUWorker] Thread already stopped"
            )

            return True

        finished = self.wait(
            5000
        )

        if finished:

            print(
                "[CPUWorker] Thread stopped"
            )

        else:

            print(
                "[CPUWorker] WARNING: "
                "thread did not stop"
            )

        return not self.isRunning()