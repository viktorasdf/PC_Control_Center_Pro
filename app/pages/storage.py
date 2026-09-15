import psutil

from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QProgressBar,
)


class StoragePage(QWidget):

    SUPPORTED_LANGUAGES = (
        "ru",
        "uk",
        "en",
        "de",
        "it",
        "es",
        "fr",
    )

    TRANSLATIONS = {
        "ru": {
    "storage": "Хранилище",
    "subtitle": "Дисковое пространство и использование хранилища",
    "used": "Использовано",
    "free": "Свободно",
    "total": "Всего",
    "used_percent": "% использовано",
        },
        "uk": {
    "storage": "Сховище",
    "subtitle": "Дисковий простір та використання сховища",
    "used": "Використано",
    "free": "Вільно",
    "total": "Всього",
    "used_percent": "% використано",
        },
        "en": {
            "storage": "Storage",
            "subtitle": "Disk space and storage usage",
            "used": "Used",
            "free": "Free",
            "total": "Total",
            "used_percent": "% used",
        },
        "de": {
            "storage": "Speicher",
            "subtitle": "Festplattenspeicher und Speichernutzung",
            "used": "Belegt",
            "free": "Frei",
            "total": "Gesamt",
            "used_percent": "% verwendet",
        },
        "it": {
            "storage": "Archiviazione",
            "subtitle": "Spazio su disco e utilizzo dell'archiviazione",
            "used": "Utilizzato",
            "free": "Libero",
            "total": "Totale",
            "used_percent": "% utilizzato",
        },
        "es": {
            "storage": "Almacenamiento",
            "subtitle": "Espacio en disco y uso del almacenamiento",
            "used": "Usado",
            "free": "Libre",
            "total": "Total",
            "used_percent": "% utilizado",
        },
        "fr": {
            "storage": "Stockage",
            "subtitle": "Espace disque et utilisation du stockage",
            "used": "Utilisé",
            "free": "Libre",
            "total": "Total",
            "used_percent": "% utilisé",
        },
    }

    def __init__(self):
        self.ui_language = "ru"

        super().__init__()

        self.main_layout = QVBoxLayout(self)

        self.main_layout.setContentsMargins(
            35, 30, 35, 30
        )

        self.main_layout.setSpacing(20)

        # ==========================
        # HEADER
        # ==========================

        self.title_label = QLabel(
            self._tr("storage")
        )

        self.title_label.setStyleSheet(
            "font-size:30px;font-weight:bold;"
        )

        self.subtitle_label = QLabel(
            self._tr("subtitle")
        )

        self.subtitle_label.setStyleSheet(
            "font-size:16px;color:#909090;"
        )

        self.main_layout.addWidget(
            self.title_label
        )

        self.main_layout.addWidget(
            self.subtitle_label
        )

        # ==========================
        # DISKS
        # ==========================

        self.disks_layout = QVBoxLayout()

        self.disks_layout.setSpacing(15)

        self.main_layout.addLayout(
            self.disks_layout
        )

        self.main_layout.addStretch()

        self.update_storage()

    def create_disk_card(
        self,
        device,
        total,
        used,
        free,
        percent,
    ):

        card = QFrame()

        card.setObjectName("StorageCard")

        card.setMinimumHeight(150)

        layout = QVBoxLayout(card)

        layout.setContentsMargins(
            20, 15, 20, 15
        )

        layout.setSpacing(8)

        # --------------------------
        # TITLE
        # --------------------------

        title = QLabel(
            f"💾 {device}"
        )

        title.setStyleSheet(
            "font-size:20px;font-weight:bold;"
        )

        layout.addWidget(title)

        # --------------------------
        # INFO
        # --------------------------

        info = QLabel(
            f"{self._tr('used')}: {used:.1f} GB    "
            f"{self._tr('free')}: {free:.1f} GB    "
            f"{self._tr('total')}: {total:.1f} GB"
        )

        info.setProperty(
            "storage_info",
            True
        )

        info.setStyleSheet(
            "font-size:14px;"
        )

        layout.addWidget(info)

        # --------------------------
        # PROGRESS
        # --------------------------

        progress = QProgressBar()

        progress.setRange(0, 100)

        progress.setValue(
            int(percent)
        )

        progress.setTextVisible(True)

        progress.setFormat(
            f"{percent:.0f}{self._tr('used_percent')}"
        )

        progress.setMinimumHeight(22)

        layout.addWidget(progress)

        return card

    def _tr(self, key):
        language = getattr(
            self,
            "ui_language",
            "ru",
        )

        if language not in self.SUPPORTED_LANGUAGES:
            language = "ru"

        return self.TRANSLATIONS.get(
            language,
            self.TRANSLATIONS["ru"],
        ).get(
            key,
            self.TRANSLATIONS["ru"].get(
                key,
                key,
            ),
        )

    def set_language(self, language):
        language = str(
            language or "ru"
        ).lower().strip()

        if language not in self.SUPPORTED_LANGUAGES:
            language = "ru"

        self.ui_language = language

        if hasattr(self, "title_label"):
            self.title_label.setText(
                self._tr("storage")
            )

        if hasattr(self, "subtitle_label"):
            self.subtitle_label.setText(
                self._tr("subtitle")
            )

        self.update_storage()

        print(
            "[StoragePage] Language:",
            self.ui_language,
        )

    def update_storage(self):

        # Удаляем старые карточки

        while self.disks_layout.count():

            item = self.disks_layout.takeAt(0)

            widget = item.widget()

            if widget is not None:
                widget.deleteLater()

        # Получаем список дисков

        partitions = psutil.disk_partitions(
            all=False
        )

        for partition in partitions:

            device = partition.device

            try:

                usage = psutil.disk_usage(
                    device
                )

            except (
                PermissionError,
                OSError,
            ):
                continue

            total = (
                usage.total
                / (1024 ** 3)
            )

            used = (
                usage.used
                / (1024 ** 3)
            )

            free = (
                usage.free
                / (1024 ** 3)
            )

            percent = usage.percent

            card = self.create_disk_card(
                device,
                total,
                used,
                free,
                percent,
            )

            self.disks_layout.addWidget(
                card
            )
