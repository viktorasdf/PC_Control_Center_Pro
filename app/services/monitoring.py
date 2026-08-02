import time
import psutil


class SystemMonitor:
    """
    Сбор показателей системы для мониторинга в реальном времени.
    """

    def __init__(self, history_size=60):
        self.history_size = history_size

        self.cpu_history = []
        self.ram_history = []
        self.download_history = []
        self.upload_history = []

        self.last_time = time.time()

        counters = psutil.net_io_counters()

        self.last_bytes_recv = counters.bytes_recv
        self.last_bytes_sent = counters.bytes_sent

    def update(self):
        """
        Снимает новый набор показателей.
        """

        current_time = time.time()

        # ==============================================
        # CPU
        # ==============================================

        cpu = psutil.cpu_percent(
            interval=None
        )

        # ==============================================
        # RAM
        # ==============================================

        memory = psutil.virtual_memory()

        ram = memory.percent

        # ==============================================
        # NETWORK
        # ==============================================

        counters = psutil.net_io_counters()

        elapsed = current_time - self.last_time

        if elapsed <= 0:
            elapsed = 1

        download_speed = (
            counters.bytes_recv
            - self.last_bytes_recv
        ) / elapsed

        upload_speed = (
            counters.bytes_sent
            - self.last_bytes_sent
        ) / elapsed

        # ==============================================
        # SAVE CURRENT VALUES
        # ==============================================

        self.cpu_history.append(cpu)
        self.ram_history.append(ram)

        self.download_history.append(
            download_speed
        )

        self.upload_history.append(
            upload_speed
        )

        # ==============================================
        # LIMIT HISTORY
        # ==============================================

        self.cpu_history = (
            self.cpu_history[-self.history_size:]
        )

        self.ram_history = (
            self.ram_history[-self.history_size:]
        )

        self.download_history = (
            self.download_history[
                -self.history_size:
            ]
        )

        self.upload_history = (
            self.upload_history[
                -self.history_size:
            ]
        )

        # ==============================================
        # UPDATE BASE VALUES
        # ==============================================

        self.last_time = current_time

        self.last_bytes_recv = (
            counters.bytes_recv
        )

        self.last_bytes_sent = (
            counters.bytes_sent
        )

        return {
            "cpu": cpu,
            "ram": ram,
            "download": download_speed,
            "upload": upload_speed,
        }

    @staticmethod
    def bytes_to_mbps(value):
        """
        Перевод байт/сек в мегабит/сек.
        """

        return (
            value * 8
        ) / (
            1024 * 1024
        )

    @staticmethod
    def bytes_to_mb(value):
        """
        Перевод байт в мегабайты.
        """

        return value / (
            1024 * 1024
        )