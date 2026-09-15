from PySide6.QtCore import QThread, Signal

from app.services.network_info import get_network_info


class NetworkWorker(QThread):
    """
    Фоновый worker для мониторинга сетевых интерфейсов.
    """

    network_ready = Signal(list)

    def __init__(
        self,
        interval_ms=2000,
        parent=None,
    ):
        super().__init__(parent)

        self.interval_ms = max(
            500,
            int(interval_ms),
        )

        self._running = False

    # ==========================================================
    # RUN
    # ==========================================================

    def run(self):

        print(
            "[NetworkWorker] Thread started"
        )

        self._running = True

        while self._running:

            try:

                data = get_network_info()

                if not isinstance(
                    data,
                    list,
                ):
                    data = []

                self.network_ready.emit(
                    data
                )

            except Exception as exc:

                print(
                    "[NetworkWorker] ERROR:",
                    repr(exc),
                )

                self.network_ready.emit(
                    []
                )

            elapsed = 0

            while (
                self._running
                and elapsed < self.interval_ms
            ):

                self.msleep(100)

                elapsed += 100

        print(
            "[NetworkWorker] Thread stopped"
        )

    # ==========================================================
    # STOP
    # ==========================================================

    def stop(self):

        print(
            "[NetworkWorker] stop() called"
        )

        self._running = False

        if not self.isRunning():

            print(
                "[NetworkWorker] Thread already stopped"
            )

            return True

        finished = self.wait(
            5000
        )

        if finished:

            print(
                "[NetworkWorker] Thread stopped"
            )

        else:

            print(
                "[NetworkWorker] WARNING: "
                "thread did not stop"
            )

        return not self.isRunning()