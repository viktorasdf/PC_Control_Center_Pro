import platform

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
    get_system_info,
)

from app.services.gpu_info import get_gpu_info


class HardwarePage(QWidget):

    SUPPORTED_LANGUAGES = ("ru", "uk", "en")

    TRANSLATIONS = {
        "ru": {
            "hardware": "\u041e\u0431\u043e\u0440\u0443\u0434\u043e\u0432\u0430\u043d\u0438\u0435",
            "hardware_subtitle": "\u0418\u043d\u0444\u043e\u0440\u043c\u0430\u0446\u0438\u044f \u043e\u0431 \u043e\u0431\u043e\u0440\u0443\u0434\u043e\u0432\u0430\u043d\u0438\u0438 \u043a\u043e\u043c\u043f\u044c\u044e\u0442\u0435\u0440\u0430",
            "system": "\u0421\u0438\u0441\u0442\u0435\u043c\u0430",
            "windows_computer": "Windows / \u041a\u043e\u043c\u043f\u044c\u044e\u0442\u0435\u0440",
            "loading": "\u0417\u0430\u0433\u0440\u0443\u0437\u043a\u0430...",
            "model": "\u041c\u043e\u0434\u0435\u043b\u044c",
            "cores": "\u042f\u0434\u0440\u0430",
            "threads": "\u041f\u043e\u0442\u043e\u043a\u0438",
            "total": "\u0412\u0441\u0435\u0433\u043e",
            "used": "\u0418\u0441\u043f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u043d\u043e",
            "usage": "\u0417\u0430\u0433\u0440\u0443\u0437\u043a\u0430",
            "vendor": "\u041f\u0440\u043e\u0438\u0437\u0432\u043e\u0434\u0438\u0442\u0435\u043b\u044c",
            "memory": "\u041f\u0430\u043c\u044f\u0442\u044c",
            "driver": "\u0414\u0440\u0430\u0439\u0432\u0435\u0440",
            "computer": "\u041a\u043e\u043c\u043f\u044c\u044e\u0442\u0435\u0440",
            "release": "\u0412\u0435\u0440\u0441\u0438\u044f",
            "architecture": "\u0410\u0440\u0445\u0438\u0442\u0435\u043a\u0442\u0443\u0440\u0430",
        },
        "uk": {
            "hardware": "\u041e\u0431\u043b\u0430\u0434\u043d\u0430\u043d\u043d\u044f",
            "hardware_subtitle": "\u0406\u043d\u0444\u043e\u0440\u043c\u0430\u0446\u0456\u044f \u043f\u0440\u043e \u043e\u0431\u043b\u0430\u0434\u043d\u0430\u043d\u043d\u044f \u043a\u043e\u043c\u043f'\u044e\u0442\u0435\u0440\u0430",
            "system": "\u0421\u0438\u0441\u0442\u0435\u043c\u0430",
            "windows_computer": "Windows / \u041a\u043e\u043c\u043f\u0027\u044e\u0442\u0435\u0440",
            "loading": "\u0417\u0430\u0432\u0430\u043d\u0442\u0430\u0436\u0435\u043d\u043d\u044f...",
            "model": "\u041c\u043e\u0434\u0435\u043b\u044c",
            "cores": "\u042f\u0434\u0440\u0430",
            "threads": "\u041f\u043e\u0442\u043e\u043a\u0438",
            "total": "\u0412\u0441\u044c\u043e\u0433\u043e",
            "used": "\u0412\u0438\u043a\u043e\u0440\u0438\u0441\u0442\u0430\u043d\u043e",
            "usage": "\u0417\u0430\u0432\u0430\u043d\u0442\u0430\u0436\u0435\u043d\u043d\u044f",
            "vendor": "\u0412\u0438\u0440\u043e\u0431\u043d\u0438\u043a",
            "memory": "\u041f\u0430\u043c\u0027\u044f\u0442\u044c",
            "driver": "\u0414\u0440\u0430\u0439\u0432\u0435\u0440",
            "computer": "\u041a\u043e\u043c\u0027\u044e\u0442\u0435\u0440",
            "release": "\u0412\u0435\u0440\u0441\u0456\u044f",
            "architecture": "\u0410\u0440\u0445\u0456\u0442\u0435\u043a\u0442\u0443\u0440\u0430",
        },
        "en": {
            "hardware": "Hardware",
            "hardware_subtitle": "Computer hardware information",
            "system": "System",
            "windows_computer": "Windows / Computer",
            "loading": "Loading...",
            "model": "Model",
            "cores": "Cores",
            "threads": "Threads",
            "total": "Total",
            "used": "Used",
            "usage": "Usage",
            "vendor": "Vendor",
            "memory": "Memory",
            "driver": "Driver",
            "computer": "Computer",
            "release": "Release",
            "architecture": "Architecture",
        },
    }

    def _tr(self, key):
        return self.TRANSLATIONS.get(
            self.ui_language,
            self.TRANSLATIONS["ru"]
        ).get(key, key)

    def __init__(self):
        super().__init__()

        self.ui_language = "ru"

        self.main_layout = QVBoxLayout(self)

        self.main_layout.setContentsMargins(
            35, 30, 35, 30
        )

        self.main_layout.setSpacing(20)

        # ==========================
        # HEADER
        # ==========================

        self.title_label = QLabel(self._tr("hardware"))

        self.title_label.setStyleSheet(
            "font-size:30px;font-weight:bold;"
        )

        self.subtitle_label = QLabel(
            self._tr("hardware_subtitle")
        )

        self.subtitle_label.setStyleSheet(
            "font-size:16px;color:#909090;"
        )

        self.main_layout.addWidget(self.title_label)
        self.main_layout.addWidget(self.subtitle_label)

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

        self.system_title_label = QLabel(self._tr("system"))

        self.system_title_label.setStyleSheet(
            "font-size:20px;font-weight:bold;"
        )

        self.main_layout.addWidget(
            self.system_title_label
        )

        self.system_card = self.create_card(
            "Windows / Computer"
        )

        self.main_layout.addWidget(
            self.system_card
        )

        self.main_layout.addStretch()

        self.set_language(self.ui_language)

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
        card.title_label = title_label

        return card

    def set_language(self, language):
        language = str(language or "ru").lower().strip()

        if language not in self.SUPPORTED_LANGUAGES:
            language = "ru"

        self.ui_language = language

        try:
            self.title_label.setText(
                self._tr("hardware")
            )

            self.subtitle_label.setText(
                self._tr("hardware_subtitle")
            )

            self.system_title_label.setText(
                self._tr("system")
            )

            self.cpu_card.title_label.setText("CPU")
            self.gpu_card.title_label.setText("GPU")
            self.ram_card.title_label.setText("RAM")

            self.system_card.title_label.setText(
                self._tr("windows_computer")
            )

            self.update_hardware()

            print(
                "[HardwarePage] Language:",
                self.ui_language
            )

        except Exception as exc:
            print(
                "[HardwarePage] Language update error:",
                exc
            )

    def update_hardware(self):

        # ==========================
        # CPU
        # ==========================

        cpu = get_cpu_info()

        cpu_text = (
            f"{self._tr('model')}: {cpu.get('name', 'Unknown')}\n"
            f"{self._tr('cores')}: {cpu.get('cores', 0)}\n"
            f"{self._tr('threads')}: {cpu.get('threads', 0)}"
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
            f"{self._tr('total')}: {total:.1f} GB\n"
            f"{self._tr('used')}: {used:.1f} GB\n"
            f"{self._tr('usage')}: {memory['percent']:.0f}%"
        )

        self.ram_card.info_label.setText(
            ram_text
        )

        # ==========================
        # GPU
        # ==========================

        gpu = get_gpu_info()

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

        gpu_text = (
            f"{self._tr('model')}: {gpu_name}\n"
            f"{self._tr('vendor')}: {vendor}\n"
            f"{self._tr('memory')}: {memory_total:.1f} GB\n"
            f"{self._tr('driver')}: {driver}"
        )

        self.gpu_card.info_label.setText(
            gpu_text
        )

        # ==========================
        # SYSTEM
        # ==========================

        system = get_system_info()

        system_text = (
            f"{self._tr('computer')}: {system.get('computer', 'Unknown')}\n"
            f"{self._tr('system')}: {system.get('system', 'Unknown')}\n"
            f"{self._tr('release')}: {system.get('release', 'Unknown')}\n"
            f"{self._tr('architecture')}: {system.get('machine', 'Unknown')}"
        )

        self.system_card.info_label.setText(
            system_text
        )