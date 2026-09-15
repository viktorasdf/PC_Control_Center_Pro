from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
)

from app.services.system_info import (
    get_cpu_info,
    get_memory_info,
    get_system_info,АА
)

from app.services.gpu_info import get_cached_gpu_info


class HardwarePage(QWidget):

    def __init__(self):
        super().__init__()

        self.main_layout = QVBoxLayout(self)

        self.main_layout.setContentsMargins(
            35, 30, 35, 30
        )

        self.main_layout.setSpacing(20)

        # ==========================
        # HEADER
        # ==========================

        title = QLabel("Hardware")

        title.setStyleSheet(
            "font-size:30px;font-weight:bold;"
        )

        subtitle = QLabel(
            "Computer hardware information"
        )

        subtitle.setStyleSheet(
            "font-size:16px;color:#909090;"
        )

        self.main_layout.addWidget(title)
        self.main_layout.addWidget(subtitle)

        # ==========================
        # CARDS
        # ==========================

        cards = QHBoxLayout()
        cards.setSpacing(15)

        self.cpu_card = self.create_card(
            "CPU"
        )

        self.gpu_card = self.create_card(
            "GPU"
        )

        self.ram_card = self.create_card(
            "RAM"
        )

        cards.addWidget(self.cpu_card)
        cards.addWidget(self.gpu_card)
        cards.addWidget(self.ram_card)

        self.main_layout.addLayout(cards)

        # ==========================
        # SYSTEM
        # ==========================

        system_title = QLabel("System")

        system_title.setStyleSheet(
            "font-size:20px;font-weight:bold;"
        )

        self.main_layout.addWidget(
            system_title
        )

        self.system_card = self.create_card(
            "Windows / Computer"
        )

        self.main_layout.addWidget(
            self.system_card
        )

        self.main_layout.addStretch()

        self.update_hardware()

    def create_card(self, title):

        card = QFrame()

        card.setObjectName("HardwareCard")

        card.setMinimumHeight(150)

        layout = QVBoxLayout(card)

        layout.setContentsMargins(
            20, 15, 20, 15
        )

        layout.setSpacing(8)

        title_label = QLabel(title)

        title_label.setStyleSheet(
            "font-size:18px;font-weight:bold;"
        )

        info = QLabel("Loading...")

        info.setWordWrap(True)

        info.setStyleSheet(
            "font-size:14px;color:#d0d0d0;"
        )

        layout.addWidget(title_label)
        layout.addWidget(info)

        card.info_label = info

        return card

    def update_hardware(self):

        # ==========================
        # CPU
        # ==========================

        cpu = get_cpu_info()

        cpu_text = (
            f"Model: {cpu.get('name', 'Unknown')}\n"
            f"Cores: {cpu.get('cores', 0)}\n"
            f"Threads: {cpu.get('threads', 0)}"
        )

        self.cpu_card.info_label.setText(
            cpu_text
        )

        # ==========================
        # RAM
        # ==========================

        memory = get_memory_info()

        total = memory["total"] / (1024 ** 3)
        used = memory["used"] / (1024 ** 3)

        ram_text = (
            f"Total: {total:.1f} GB\n"
            f"Used: {used:.1f} GB\n"
            f"Usage: {memory['percent']:.0f}%"
        )

        self.ram_card.info_label.setText(
            ram_text
        )

        # ==========================
        # GPU
        # ==========================

        gpu = get_cached_gpu_info()

        gpu_name = gpu.get(
            "name",
            "Unknown GPU"
        )

        vendor = gpu.get(
            "vendor",
            "Unknown"
        )

        memory_total = gpu.get(
            "memory_total",
            0
        )

        driver = gpu.get(
            "driver",
            "Unknown"
        )

        gpu_usage = gpu.get(
            "usage",
            0
        )

        gpu_text = (
            f"Model: {gpu_name}\n"
            f"Vendor: {vendor}\n"
            f"Memory: {memory_total:.1f} GB\n"
            f"Driver: {driver}\n"
            f"Usage: {gpu_usage:.0f}%"
        )

        self.gpu_card.info_label.setText(
            gpu_text
        )

        # ==========================
        # SYSTEM
        # ==========================

        system = get_system_info()

        system_text = (
            f"Computer: {system.get('computer', 'Unknown')}\n"
            f"System: {system.get('system', 'Unknown')}\n"
            f"Release: {system.get('release', 'Unknown')}\n"
            f"Architecture: {system.get('machine', 'Unknown')}"
        )

        self.system_card.info_label.setText(
            system_text
        )