from __future__ import annotations

from PySide6.QtCore import QThread, Signal

from app.services.cleanup_service import (
    scan_temp_files,
    delete_temp_files,
)


class CleanupWorker(QThread):
    """
    Выполняет операции очистки во внешнем потоке,
    чтобы не блокировать GUI.
    """

    scan_finished = Signal(dict)
    delete_finished = Signal(dict)
    error = Signal(str)

    def __init__(
        self,
        operation: str,
        parent=None,
    ):
        super().__init__(parent)

        self.operation = operation
        self._stop_requested = False

    # ==========================================================
    # STOP REQUEST
    # ==========================================================

    def request_stop(self):
        self._stop_requested = True

    # ==========================================================
    # RUN
    # ==========================================================

    def run(self):

        if self._stop_requested:
            return

        try:

            if self.operation == "scan":

                print(
                    "[CleanupWorker] "
                    "Starting scan..."
                )

                result = scan_temp_files()

                if self._stop_requested:
                    print(
                        "[CleanupWorker] "
                        "Scan result ignored because shutdown started"
                    )
                    return

                if not isinstance(result, dict):
                    result = {}

                self.scan_finished.emit(result)

                print(
                    "[CleanupWorker] "
                    "Scan finished"
                )

                return

            if self.operation == "delete":

                print(
                    "[CleanupWorker] "
                    "Starting delete..."
                )

                result = delete_temp_files(
                    dry_run=False
                )

                if self._stop_requested:
                    print(
                        "[CleanupWorker] "
                        "Delete result ignored because shutdown started"
                    )
                    return

                if not isinstance(result, dict):
                    result = {}

                self.delete_finished.emit(result)

                print(
                    "[CleanupWorker] "
                    "Delete finished"
                )

                return

            raise ValueError(
                f"Unknown cleanup operation: "
                f"{self.operation}"
            )

        except Exception as exc:

            if not self._stop_requested:

                self.error.emit(
                    str(exc)
                )

    # ==========================================================
    # STOP
    # ==========================================================

    def stop(
        self,
        timeout=15000,
    ):

        self.request_stop()

        if not self.isRunning():
            return True

        print(
            "[CleanupWorker] "
            "Stop requested"
        )

        print(
            "[CleanupWorker] "
            "Waiting for thread..."
        )

        finished = self.wait(
            timeout
        )

        if finished:

            print(
                "[CleanupWorker] "
                "Thread stopped"
            )

            return True

        print(
            "[CleanupWorker] WARNING: "
            "thread did not finish within "
            f"{timeout / 1000:.0f} seconds"
        )

        return False