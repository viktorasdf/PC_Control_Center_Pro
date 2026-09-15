
from PySide6.QtCore import QThread, Signal

from app.services.ai_analyzer import AIAnalyzer


class AIWorker(QThread):
    """
    Фоновый worker для AIAnalyzer.

    Выполняет AI-анализ в отдельном потоке,
    чтобы не блокировать GUI.
    """

    result_ready = Signal(dict)
    error = Signal(str)

    def __init__(self, analyzer=None, parent=None):
        super().__init__(parent)

        self.analyzer = analyzer or AIAnalyzer()

        self._stop_requested = False
        self._shutdown_started = False

    # ==========================================================
    # RUN
    # ==========================================================

    def run(self):
        """
        Выполняет AI-анализ в отдельном потоке.
        """

        try:
            if self._stop_requested:
                return

            result = self.analyzer.analyze()

            # --------------------------------------------------
            # Приложение уже начало закрываться.
            # Результат больше нельзя передавать в Dashboard.
            # --------------------------------------------------

            if self._shutdown_started or self._stop_requested:
                print(
                    "[AIWorker] "
                    "Result ignored because shutdown started"
                )
                return

            # --------------------------------------------------
            # Проверяем результат.
            # --------------------------------------------------

            if not isinstance(result, dict):
                print(
                    "[AIWorker] Invalid AI result type"
                )
                return

            # --------------------------------------------------
            # Передаём результат в Dashboard.
            # --------------------------------------------------

            self.result_ready.emit(result)

        except Exception as exc:
            print(
                f"[AIWorker] Error: {exc}"
            )

            if not self._stop_requested:
                self.error.emit(str(exc))

        finally:
            print(
                "[AIWorker] Thread stopped"
            )

    # ==========================================================
    # REQUEST STOP
    # ==========================================================

    def request_stop(self):
        """
        Запрашивает остановку worker.

        Принудительно поток не завершаем.
        AIAnalyzer должен естественно закончить текущий анализ.
        """

        self._stop_requested = True
        self._shutdown_started = True

    # ==========================================================
    # STOP
    # ==========================================================

    def stop(self, timeout=15000):
        """
        Останавливает worker и ждёт его естественного завершения.

        timeout указывается в миллисекундах.
        """

        if not self.isRunning():
            return True

        print(
            "[AIWorker] Stop requested"
        )

        self.request_stop()

        print(
            "[AIWorker] Waiting for thread..."
        )

        finished = self.wait(timeout)

        if finished:
            print(
                "[AIWorker] Thread stopped"
            )
            return True

        print(
            "[AIWorker] WARNING: "
            f"thread did not finish within "
            f"{timeout / 1000:.0f} seconds"
        )

        return False

    # ==========================================================
    # SHUTDOWN
    # ==========================================================

    def shutdown(self, timeout=15000):
        """
        Алиас для stop().
        """

        return self.stop(timeout=timeout)
