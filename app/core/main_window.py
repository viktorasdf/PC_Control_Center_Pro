from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QStackedWidget,
)

from app.pages.dashboard import DashboardPage
from app.pages.monitoring import MonitoringPage
from app.pages.hardware import HardwarePage
from app.pages.storage import StoragePage
from app.pages.network import NetworkPage


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("PC Control Center Pro")
        self.resize(1400, 850)

        central = QWidget()
        self.setCentralWidget(central)

        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)

        self.menu = QListWidget()
        self.menu.setFixedWidth(220)

        pages = [
            "Dashboard",
            "Monitoring",
            "Hardware",
            "Storage",
            "Network",
        ]

        for page in pages:
            self.menu.addItem(QListWidgetItem(page))

        layout.addWidget(self.menu)

        self.stack = QStackedWidget()
        layout.addWidget(self.stack)

        self.dashboard = DashboardPage()
        self.monitoring = MonitoringPage()
        self.hardware = HardwarePage()
        self.storage = StoragePage()
        self.network = NetworkPage()

        self.stack.addWidget(self.dashboard)
        self.stack.addWidget(self.monitoring)
        self.stack.addWidget(self.hardware)
        self.stack.addWidget(self.storage)
        self.stack.addWidget(self.network)

        self.menu.currentRowChanged.connect(self.stack.setCurrentIndex)
        self.menu.setCurrentRow(0)

        # Первичная загрузка данных Dashboard
        if hasattr(self.dashboard, "update_dashboard"):
            self.dashboard.update_dashboard()