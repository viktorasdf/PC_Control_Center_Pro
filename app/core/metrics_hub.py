from PySide6.QtCore import QObject, Signal


class MetricsHub(QObject):
    """
    Центральное хранилище текущих системных метрик.

    MetricsHub НИЧЕГО не измеряет.

    Его задача:

        Worker
           ↓
        MetricsHub
           ↓
        Dashboard / Monitoring / AIWorker

    Workers являются источниками данных.
    MetricsHub хранит последнее полученное состояние.
    """

    metrics_updated = Signal(dict)

    cpu_updated = Signal(dict)
    ram_updated = Signal(dict)
    gpu_updated = Signal(dict)
    disk_updated = Signal(dict)
    network_updated = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)

        # ======================================================
        # CURRENT DATA
        # ======================================================

        self._metrics = {
            "cpu": {},
            "ram": {},
            "gpu": {},
            "disk": {},
            "network": [],
        }

    # ==========================================================
    # CPU
    # ==========================================================

    def update_cpu(self, data):
        """
        Получает новые данные от CPUWorker.
        """

        if not isinstance(data, dict):
            return

        self._metrics["cpu"] = dict(data)

        self.cpu_updated.emit(
            dict(self._metrics["cpu"])
        )

        self._emit_metrics()

    # ==========================================================
    # RAM
    # ==========================================================

    def update_ram(self, data):
        """
        Получает новые данные от RAMWorker.
        """

        if not isinstance(data, dict):
            return

        self._metrics["ram"] = dict(data)

        self.ram_updated.emit(
            dict(self._metrics["ram"])
        )

        self._emit_metrics()

    # ==========================================================
    # GPU
    # ==========================================================

    def update_gpu(self, data):
        """
        Получает новые данные от GPUWorker.
        """

        if not isinstance(data, dict):
            return

        self._metrics["gpu"] = dict(data)

        self.gpu_updated.emit(
            dict(self._metrics["gpu"])
        )

        self._emit_metrics()

    # ==========================================================
    # DISK
    # ==========================================================

    def update_disk(self, data):
        """
        Получает новые данные от DiskWorker.
        """

        if not isinstance(data, dict):
            return

        self._metrics["disk"] = dict(data)

        self.disk_updated.emit(
            dict(self._metrics["disk"])
        )

        self._emit_metrics()

    # ==========================================================
    # NETWORK
    # ==========================================================

    def update_network(self, data):
        """
        Получает новые данные от NetworkWorker.
        """

        if not isinstance(data, list):
            return

        # Создаём копию списка.
        self._metrics["network"] = [
            dict(item)
            for item in data
            if isinstance(item, dict)
        ]

        self.network_updated.emit(
            [
                dict(item)
                for item in self._metrics["network"]
            ]
        )

        self._emit_metrics()

    # ==========================================================
    # SNAPSHOT
    # ==========================================================

    def get_metrics(self):
        """
        Возвращает копию текущих метрик.

        Внешний код не получает прямой доступ
        к внутреннему состоянию MetricsHub.
        """

        return {
            "cpu": dict(
                self._metrics["cpu"]
            ),

            "ram": dict(
                self._metrics["ram"]
            ),

            "gpu": dict(
                self._metrics["gpu"]
            ),

            "disk": dict(
                self._metrics["disk"]
            ),

            "network": [
                dict(item)
                for item in self._metrics["network"]
            ],
        }

    # ==========================================================
    # INTERNAL EMIT
    # ==========================================================

    def _emit_metrics(self):
        """
        Передаёт единый snapshot всем подписчикам.
        """

        self.metrics_updated.emit(
            self.get_metrics()
        )