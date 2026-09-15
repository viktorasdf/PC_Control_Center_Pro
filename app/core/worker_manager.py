from PySide6.QtCore import QObject, Signal

from app.workers.cpu_worker import CPUWorker
from app.workers.ram_worker import RAMWorker
from app.workers.gpu_worker import GPUWorker
from app.workers.disk_worker import DiskWorker
from app.workers.network_worker import NetworkWorker

from app.core.metrics_hub import MetricsHub


class WorkerManager(QObject):
    """
    Центральный менеджер всех системных workers.

    WorkerManager отвечает только за:

        создание workers
        запуск workers
        подключение сигналов
        остановку workers

    WorkerManager НЕ собирает метрики самостоятельно.
    """

    started = Signal()
    stopped = Signal()

    def __init__(
        self,
        parent=None,
    ):
        super().__init__(parent)

        # ======================================================
        # METRICS HUB
        # ======================================================

        self.metrics = MetricsHub(
            self
        )

        # ======================================================
        # WORKERS
        # ======================================================

        self.cpu_worker = CPUWorker(
            interval_ms=1000,
            parent=self,
        )

        self.ram_worker = RAMWorker(
            interval_ms=1000,
            parent=self,
        )

        self.gpu_worker = GPUWorker(
            parent=self,
        )

        self.disk_worker = DiskWorker(
            path="C:\\",
            parent=self,
        )

        self.network_worker = NetworkWorker(
            interval_ms=2000,
            parent=self,
        )

        self._workers = [
            self.cpu_worker,
            self.ram_worker,
            self.gpu_worker,
            self.disk_worker,
            self.network_worker,
        ]

        self._running = False

        # ======================================================
        # SIGNALS → METRICS HUB
        # ======================================================

        self.cpu_worker.cpu_ready.connect(
            self.metrics.update_cpu
        )

        self.ram_worker.ram_ready.connect(
            self.metrics.update_ram
        )

        self.gpu_worker.gpu_ready.connect(
            self.metrics.update_gpu
        )

        self.disk_worker.disk_ready.connect(
            self.metrics.update_disk
        )

        self.network_worker.network_ready.connect(
            self.metrics.update_network
        )

    # ==========================================================
    # START
    # ==========================================================

    def start(self):
        """
        Запускает все системные workers.
        """

        if self._running:

            print(
                "[WorkerManager] "
                "Already running"
            )

            return

        print(
            "[WorkerManager] Starting workers..."
        )

        self._running = True

        for worker in self._workers:

            if not worker.isRunning():

                print(
                    "[WorkerManager] Starting:",
                    worker.__class__.__name__,
                )

                worker.start()

        self.started.emit()

        print(
            "[WorkerManager] "
            "All workers started"
        )

    # ==========================================================
    # GET METRICS
    # ==========================================================

    def get_metrics(self):
        """
        Возвращает текущий snapshot системы.
        """

        return self.metrics.get_metrics()

    # ==========================================================
    # STOP
    # ==========================================================

    def stop(self):
        """
        Корректно останавливает все workers.

        Сначала просим каждый worker завершиться,
        затем ждём его завершения.
        """

        if not self._running:

            print(
                "[WorkerManager] "
                "Already stopped"
            )

            return True

        print(
            "[WorkerManager] "
            "Stopping workers..."
        )

        self._running = False

        success = True

        # ======================================================
        # STOP REQUEST
        # ======================================================

        for worker in self._workers:

            try:

                if worker.isRunning():

                    print(
                        "[WorkerManager] Stopping:",
                        worker.__class__.__name__,
                    )

                    worker.stop()

            except Exception as exc:

                success = False

                print(
                    "[WorkerManager] "
                    f"Stop error "
                    f"{worker.__class__.__name__}:",
                    repr(exc),
                )

        # ======================================================
        # VERIFY
        # ======================================================

        for worker in self._workers:

            if worker.isRunning():

                success = False

                print(
                    "[WorkerManager] WARNING:",
                    worker.__class__.__name__,
                    "is still running",
                )

        if success:

            print(
                "[WorkerManager] "
                "All workers stopped"
            )

        else:

            print(
                "[WorkerManager] "
                "Some workers failed to stop"
            )

        self.stopped.emit()

        return success