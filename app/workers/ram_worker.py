from PySide6.QtCore import QThread, Signal

from app.services.ram_info import get_ram_info


class RAMWorker(QThread):
    """
    Фоновый worker для мониторинга RAM.
    """

    ram_ready = Signal(dict)

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
            "[RAMWorker] Thread started"
        )

        self._running = True

        while self._running:

            try:

                data = get_ram_info()

                if not isinstance(
                    data,
                    dict,
                ):
                    data = {
                        "usage": 0.0,
                        "total": 0.0,
                        "used": 0.0,
                        "available": 0.0,
                        "free": 0.0,
                        "total_gb": 0.0,
                        "used_gb": 0.0,
                        "available_gb": 0.0,
                        "free_gb": 0.0,
                    }

                self.ram_ready.emit(
                    data
                )

            except Exception as exc:

                print(
                    "[RAMWorker] ERROR:",
                    repr(exc),
                )

                self.ram_ready.emit({
                    "usage": 0.0,
                    "total": 0.0,
                    "used": 0.0,
                    "available": 0.0,
                    "free": 0.0,
                    "total_gb": 0.0,
                    "used_gb": 0.0,
                    "available_gb": 0.0,
                    "free_gb": 0.0,
                    "error": str(exc),
                })

            elapsed = 0

            while (
                self._running
                and elapsed < self.interval_ms
            ):

                self.msleep(100)

                elapsed += 100

        print(
            "[RAMWorker] Thread stopped"
        )

    # ==========================================================
    # STOP
    # ==========================================================

    def stop(self):

        print(
            "[RAMWorker] stop() called"
        )

        self._running = False

        if not self.isRunning():

            print(
                "[RAMWorker] Thread already stopped"
            )

            return True

        finished = self.wait(
            5000
        )

        if finished:

            print(
                "[RAMWorker] Thread stopped"
            )

        else:

            print(
                "[RAMWorker] WARNING: "
                "thread did not stop"
            )

        return not self.isRunning()