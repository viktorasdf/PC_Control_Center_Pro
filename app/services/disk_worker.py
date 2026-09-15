
from PySide6.QtCore import QThread, Signal

from app.services.disk_info import get_disk_info


class DiskWorker(QThread):

    disk_ready = Signal(dict)

    def __init__(self, path="C:\\", parent=None):
        super().__init__(parent)

        self.path = path
        self._running = True
        self._last_log_signature = None

    # ==========================================================
    # RUN
    # ==========================================================

    def run(self):

        print("[DiskWorker] Started")

        while self._running:

            try:

                data = get_disk_info(
                    self.path
                )

                if not isinstance(
                    data,
                    dict
                ):
                    data = {
                        "activity": 0.0,
                        "read": 0.0,
                        "write": 0.0,
                        "space": 0.0,
                        "total": 0,
                        "used": 0,
                        "free": 0,
                    }

                # Метрики диска обновляются постоянно, но в консоль их не
                # выводим: даже небольшая активность меняется почти каждый тик.
                # В лог попадают только старт/остановка worker и ошибки.

                self.disk_ready.emit(
                    data
                )

            except Exception as exc:

                print(
                    "[DiskWorker] ERROR:",
                    repr(exc)
                )

                self.disk_ready.emit(
                    {
                        "activity": 0.0,
                        "read": 0.0,
                        "write": 0.0,
                        "space": 0.0,
                        "total": 0,
                        "used": 0,
                        "free": 0,
                        "error": str(exc),
                    }
                )

            # ==================================================
            # 1 SECOND UPDATE
            # ==================================================

            for _ in range(10):

                if not self._running:
                    break

                self.msleep(100)

        print("[DiskWorker] Thread finished")

    # ==========================================================
    # STOP
    # ==========================================================

    def stop(self):

        print(
            "[DiskWorker] stop() called"
        )

        self._running = False

        if self.isRunning():

            print(
                "[DiskWorker] Waiting for thread..."
            )

            finished = self.wait(
                5000
            )

            if finished:

                print(
                    "[DiskWorker] Thread stopped"
                )

            else:

                print(
                    "[DiskWorker] WARNING: "
                    "thread did not stop"
                )

        else:

            print(
                "[DiskWorker] Thread already stopped"
            )

        return not self.isRunning()
