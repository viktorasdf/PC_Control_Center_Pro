import platform

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
)

from app.services.system_info import (
    get_cpu_info,
    get_memory_info,
    get_system_info,
)

from app.services.gpu_info import (
    get_cached_gpu_info,
)

from app.widgets.dashboard_widgets import CardFrame


SUPPORTED_LANGUAGES = ("ru", "uk", "en", "de", "it", "es", "fr")

TRANSLATIONS = {
    "ru": {
        "hardware": "\u0410\u043f\u043f\u0430\u0440\u0430\u0442\u043d\u043e\u0435 \u043e\u0431\u0435\u0441\u043f\u0435\u0447\u0435\u043d\u0438\u0435",
        "hardware_description": "\u0418\u043d\u0444\u043e\u0440\u043c\u0430\u0446\u0438\u044f \u043e \u043a\u043e\u043c\u043f\u043e\u043d\u0435\u043d\u0442\u0430\u0445 \u043a\u043e\u043c\u043f\u044c\u044e\u0442\u0435\u0440\u0430",
        "loading": "\u0417\u0430\u0433\u0440\u0443\u0437\u043a\u0430...",
        "detecting_gpu": "\u041e\u043f\u0440\u0435\u0434\u0435\u043b\u0435\u043d\u0438\u0435 GPU...",
        "waiting": "\u041e\u0436\u0438\u0434\u0430\u043d\u0438\u0435...",
        "unknown": "\u041d\u0435\u0438\u0437\u0432\u0435\u0441\u0442\u043d\u043e",
        "model": "\u041c\u043e\u0434\u0435\u043b\u044c",
        "manufacturer": "\u041f\u0440\u043e\u0438\u0437\u0432\u043e\u0434\u0438\u0442\u0435\u043b\u044c",
        "vram": "VRAM",
        "driver": "\u0414\u0440\u0430\u0439\u0432\u0435\u0440",
        "usage": "\u0418\u0441\u043f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u043d\u0438\u0435",
        "cores": "\u042f\u0434\u0440\u0430",
        "threads": "\u041f\u043e\u0442\u043e\u043a\u0438",
        "total": "\u0412\u0441\u0435\u0433\u043e",
        "used": "\u0418\u0441\u043f\u043e\u043b\u044c\u0437\u0443\u0435\u0442\u0441\u044f",
        "computer": "\u041a\u043e\u043c\u043f\u044c\u044e\u0442\u0435\u0440",
        "system": "\u0421\u0438\u0441\u0442\u0435\u043c\u0430",
        "architecture": "\u0410\u0440\u0445\u0438\u0442\u0435\u043a\u0442\u0443\u0440\u0430",
        "processor": "\u041f\u0440\u043e\u0446\u0435\u0441\u0441\u043e\u0440",
        "gpu_error": "\u041e\u0448\u0438\u0431\u043a\u0430 GPU",
        "cpu_error": "\u041e\u0448\u0438\u0431\u043a\u0430 CPU",
        "ram_error": "\u041e\u0448\u0438\u0431\u043a\u0430 RAM",
        "system_error": "\u041e\u0448\u0438\u0431\u043a\u0430 \u0441\u0438\u0441\u0442\u0435\u043c\u044b",
    },

    "uk": {
        "hardware": "\u0410\u043f\u0430\u0440\u0430\u0442\u043d\u0435 \u0437\u0430\u0431\u0435\u0437\u043f\u0435\u0447\u0435\u043d\u043d\u044f",
        "hardware_description": "\u0406\u043d\u0444\u043e\u0440\u043c\u0430\u0446\u0456\u044f \u043f\u0440\u043e \u043a\u043e\u043c\u043f'\u044e\u0442\u0435\u0440\u043d\u0456 \u043a\u043e\u043c\u043f\u043e\u043d\u0435\u043d\u0442\u0438",
        "loading": "\u0417\u0430\u0432\u0430\u043d\u0442\u0430\u0436\u0435\u043d\u043d\u044f...",
        "detecting_gpu": "\u0412\u0438\u0437\u043d\u0430\u0447\u0435\u043d\u043d\u044f GPU...",
        "waiting": "\u041e\u0447\u0456\u043a\u0443\u0432\u0430\u043d\u043d\u044f...",
        "unknown": "\u041d\u0435\u0432\u0456\u0434\u043e\u043c\u043e",
        "model": "\u041c\u043e\u0434\u0435\u043b\u044c",
        "manufacturer": "\u0412\u0438\u0440\u043e\u0431\u043d\u0438\u043a",
        "vram": "VRAM",
        "driver": "\u0414\u0440\u0430\u0439\u0432\u0435\u0440",
        "usage": "\u0412\u0438\u043a\u043e\u0440\u0438\u0441\u0442\u0430\u043d\u043d\u044f",
        "cores": "\u042f\u0434\u0440\u0430",
        "threads": "\u041f\u043e\u0442\u043e\u043a\u0438",
        "total": "\u0412\u0441\u044c\u043e\u0433\u043e",
        "used": "\u0412\u0438\u043a\u043e\u0440\u0438\u0441\u0442\u0430\u043d\u043e",
        "computer": "\u041a\u043e\u043c\u043f'\u044e\u0442\u0435\u0440",
        "system": "\u0421\u0438\u0441\u0442\u0435\u043c\u0430",
        "architecture": "\u0410\u0440\u0445\u0456\u0442\u0435\u043a\u0442\u0443\u0440\u0430",
        "processor": "\u041f\u0440\u043e\u0446\u0435\u0441\u043e\u0440",
        "gpu_error": "\u041f\u043e\u043c\u0438\u043b\u043a\u0430 GPU",
        "cpu_error": "\u041f\u043e\u043c\u0438\u043b\u043a\u0430 CPU",
        "ram_error": "\u041f\u043e\u043c\u0438\u043b\u043a\u0430 RAM",
        "system_error": "\u041f\u043e\u043c\u0438\u043b\u043a\u0430 \u0441\u0438\u0441\u0442\u0435\u043c\u0438",
    },

    "en": {
        "hardware": "Hardware",
        "hardware_description": "Information about computer components",
        "loading": "Loading...",
        "detecting_gpu": "Detecting GPU...",
        "waiting": "Waiting...",
        "unknown": "Unknown",
        "model": "Model",
        "manufacturer": "Manufacturer",
        "vram": "VRAM",
        "driver": "Driver",
        "usage": "Usage",
        "cores": "Cores",
        "threads": "Threads",
        "total": "Total",
        "used": "Used",
        "computer": "Computer",
        "system": "System",
        "architecture": "Architecture",
        "processor": "Processor",
        "gpu_error": "GPU error",
        "cpu_error": "CPU error",
        "ram_error": "RAM error",
        "system_error": "System error",
    },

    "de": {
        "hardware": "Hardware",
        "hardware_description": "Informationen \u00fcber die Computerkomponenten",
        "loading": "Wird geladen...",
        "detecting_gpu": "GPU wird erkannt...",
        "waiting": "Warten...",
        "unknown": "Unbekannt",
        "model": "Modell",
        "manufacturer": "Hersteller",
        "vram": "VRAM",
        "driver": "Treiber",
        "usage": "Auslastung",
        "cores": "Kerne",
        "threads": "Threads",
        "total": "Gesamt",
        "used": "Verwendet",
        "computer": "Computer",
        "system": "System",
        "architecture": "Architektur",
        "processor": "Prozessor",
        "gpu_error": "GPU-Fehler",
        "cpu_error": "CPU-Fehler",
        "ram_error": "RAM-Fehler",
        "system_error": "Systemfehler",
    },

    "it": {
        "hardware": "Hardware",
        "hardware_description": "Informazioni sui componenti del computer",
        "loading": "Caricamento...",
        "detecting_gpu": "Rilevamento GPU...",
        "waiting": "Attendere...",
        "unknown": "Sconosciuto",
        "model": "Modello",
        "manufacturer": "Produttore",
        "vram": "VRAM",
        "driver": "Driver",
        "usage": "Utilizzo",
        "cores": "Core",
        "threads": "Thread",
        "total": "Totale",
        "used": "Utilizzato",
        "computer": "Computer",
        "system": "Sistema",
        "architecture": "Architettura",
        "processor": "Processore",
        "gpu_error": "Errore GPU",
        "cpu_error": "Errore CPU",
        "ram_error": "Errore RAM",
        "system_error": "Errore di sistema",
    },

    "es": {
        "hardware": "Hardware",
        "hardware_description": "Informaci\u00f3n sobre los componentes del ordenador",
        "loading": "Cargando...",
        "detecting_gpu": "Detectando GPU...",
        "waiting": "Esperando...",
        "unknown": "Desconocido",
        "model": "Modelo",
        "manufacturer": "Fabricante",
        "vram": "VRAM",
        "driver": "Controlador",
        "usage": "Uso",
        "cores": "N\u00facleos",
        "threads": "Hilos",
        "total": "Total",
        "used": "Usado",
        "computer": "Ordenador",
        "system": "Sistema",
        "architecture": "Arquitectura",
        "processor": "Procesador",
        "gpu_error": "Error de GPU",
        "cpu_error": "Error de CPU",
        "ram_error": "Error de RAM",
        "system_error": "Error del sistema",
    },

    "fr": {
        "hardware": "Mat\u00e9riel",
        "hardware_description": "Informations sur les composants de l\u2019ordinateur",
        "loading": "Chargement...",
        "detecting_gpu": "D\u00e9tection du GPU...",
        "waiting": "En attente...",
        "unknown": "Inconnu",
        "model": "Mod\u00e8le",
        "manufacturer": "Fabricant",
        "vram": "VRAM",
        "driver": "Pilote",
        "usage": "Utilisation",
        "cores": "C\u0153urs",
        "threads": "Threads",
        "total": "Total",
        "used": "Utilis\u00e9",
        "computer": "Ordinateur",
        "system": "Syst\u00e8me",
        "architecture": "Architecture",
        "processor": "Processeur",
        "gpu_error": "Erreur GPU",
        "cpu_error": "Erreur CPU",
        "ram_error": "Erreur RAM",
        "system_error": "Erreur syst\u00e8me",
    },
}

class HardwarePage(QWidget):

    def _tr(self, key):
        return TRANSLATIONS.get(
            self.ui_language,
            TRANSLATIONS["ru"],
        ).get(
            key,
            TRANSLATIONS["ru"].get(key, key),
        )

    def set_language(self, language):
        language = str(language or "ru").lower().strip()

        if language not in SUPPORTED_LANGUAGES:
            language = "ru"

        self.ui_language = language

        try:
            if hasattr(self, "title_label"):
                self.title_label.setText(
                    self._tr("hardware")
                )

            if hasattr(self, "description_label"):
                self.description_label.setText(
                    self._tr("hardware_description")
                )

            if hasattr(self, "cpu") and hasattr(
                self.cpu, "title_label"
            ):
                self.cpu.title_label.setText("CPU")

            if hasattr(self, "gpu") and hasattr(
                self.gpu, "title_label"
            ):
                self.gpu.title_label.setText("GPU")

            if hasattr(self, "ram") and hasattr(
                self.ram, "title_label"
            ):
                self.ram.title_label.setText("RAM")

            if hasattr(self, "system") and hasattr(
                self.system, "title_label"
            ):
                self.system.title_label.setText(
                    self._tr("system")
                )

            # Immediately refresh dynamic hardware text
            # in the selected language.
            self.update_hardware()
            self.update_gpu()

            print(
                "[HardwarePage] Language:",
                self.ui_language
            )

        except Exception as exc:
            print(
                "[HardwarePage] Language update error:",
                exc
            )

    def __init__(self, parent=None):

        self.ui_language = "ru"

        super().__init__(parent)

        self.setObjectName("HardwarePage")

        self.setStyleSheet(
            """
            QWidget#HardwarePage {
                background: #050b18;
            }

            QLabel {
                color: #f4f7ff;
            }
            """
        )

        # ====================================================
        # BUILD UI
        # ====================================================

        self._build_ui()

        # ====================================================
        # INITIAL HARDWARE DATA
        # ====================================================

        self.update_hardware()

        # ====================================================
        # HARDWARE TIMER
        # CPU + RAM
        # ====================================================

        self.hardware_timer = QTimer(self)

        self.hardware_timer.timeout.connect(
            self.update_hardware
        )

        self.hardware_timer.start(1000)

        # ====================================================
        # GPU TIMER
        # GPU cache
        # ====================================================

        self.gpu_timer = QTimer(self)

        self.gpu_timer.timeout.connect(
            self.update_gpu
        )

        self.gpu_timer.start(1000)

        # Первое обновление GPU сразу
        self.update_gpu()

    # ========================================================
    # UPDATE GPU
    # ========================================================

    def update_gpu(self):
        try:
            gpu = get_cached_gpu_info() or {}

            if not gpu:
                self.gpu.info.setText(
                    self._tr("detecting_gpu")
                )
                return

            gpu_name = gpu.get(
                "name",
                "Unknown GPU",
            )
            vendor = gpu.get(
                "vendor",
                "Unknown",
            )
            memory_total = float(
                gpu.get(
                    "memory_total",
                    gpu.get(
                        "memory",
                        0,
                    ),
                )
                or 0
            )

            if memory_total > 1024 * 1024:
                memory_total = (
                    memory_total
                    / (1024 ** 3)
                )

            driver = gpu.get(
                "driver",
                "Unknown",
            )
            usage = gpu.get(
                "usage",
                None,
            )

            if usage is None:
                usage_text = self._tr("waiting")
            else:
                usage_text = (
                    f"{float(usage):.1f}%"
                )

            self.gpu.info.setText(
                f"{self._tr('model')}: {gpu_name}\n"
                f"{self._tr('manufacturer')}: {vendor}\n"
                f"{self._tr('vram')}: {memory_total:.1f} GB\n"
                f"{self._tr('driver')}: {driver}\n"
                f"{self._tr('usage')}: {usage_text}"
            )

        except Exception as exc:
            self.gpu.info.setText(
                f"{self._tr('gpu_error')}: {exc}"
            )

    def _label(
        self,
        text,
        size=12,
        color="#f4f7ff",
        bold=False,
    ):

        label = QLabel(text)

        label.setStyleSheet(
            f"""
            color: {color};
            font-size: {size}px;
            font-weight: {"800" if bold else "400"};
            background: transparent;
            border: none;
            """
        )

        label.setWordWrap(True)

        return label

    # ========================================================
    # CARD
    # ========================================================

    def _card(self, title, accent):
        card = CardFrame()

        layout = QVBoxLayout(card)

        layout.setContentsMargins(
            18,
            14,
            18,
            14,
        )

        layout.setSpacing(7)

        title_label = self._label(
            title,
            17,
            accent,
            True,
        )

        layout.addWidget(title_label)

        info = self._label(
            self._tr("loading"),
            10,
            "#c4d0df",
        )

        layout.addWidget(info)

        card.info = info
        card.title_label = title_label
        card.card_title = title

        return card

    def _build_ui(self):

        root = QVBoxLayout(self)

        root.setContentsMargins(
            14,
            12,
            14,
            12,
        )

        root.setSpacing(12)

        # ====================================================
        # TITLE
        self.title_label = self._label(
            "\u0410\u043f\u043f\u0430\u0440\u0430\u0442\u043d\u043e\u0435 \u043e\u0431\u0435\u0441\u043f\u0435\u0447\u0435\u043d\u0438\u0435",
            28,
            "#f4f7ff",
            True,
        )

        root.addWidget(self.title_label)

        # DESCRIPTION
        self.description_label = self._label(
            "\u0418\u043d\u0444\u043e\u0440\u043c\u0430\u0446\u0438\u044f \u043e \u043a\u043e\u043c\u043f\u043e\u043d\u0435\u043d\u0442\u0430\u0445 \u043a\u043e\u043c\u043f\u044c\u044e\u0442\u0435\u0440\u0430",
            11,
            "#8ea3bd",
        )

        root.addWidget(self.description_label)

        # MAIN CARDS
        # ====================================================

        row = QHBoxLayout()

        row.setSpacing(12)

        self.cpu = self._card(
            "CPU",
            "#22d3ee",
        )

        self.gpu = self._card(
            "GPU",
            "#a970ff",
        )

        self.ram = self._card(
            "RAM",
            "#22e889",
        )

        row.addWidget(
            self.cpu,
            1,
        )

        row.addWidget(
            self.gpu,
            1,
        )

        row.addWidget(
            self.ram,
            1,
        )

        root.addLayout(row)

        # ====================================================
        # SYSTEM CARD
        # ====================================================

        self.system = self._card(
            "Windows / System",
            "#168cff",
        )

        root.addWidget(
            self.system
        )

        # ====================================================
        # STRETCH
        # ====================================================

        root.addStretch()

    # ========================================================
    # UPDATE HARDWARE
    # CPU + RAM + SYSTEM
    # ========================================================

    def update_hardware(self):
        try:
            cpu = get_cpu_info() or {}

            cpu_name = cpu.get(
                "name",
                "Unknown CPU",
            )

            cores = cpu.get(
                "cores",
                0,
            )

            threads = cpu.get(
                "threads",
                0,
            )

            usage = float(
                cpu.get(
                    "usage",
                    0,
                )
                or 0
            )

            self.cpu.info.setText(
                f"{self._tr('model')}: {cpu_name}\n"
                f"{self._tr('cores')}: {cores}\n"
                f"{self._tr('threads')}: {threads}\n"
                f"{self._tr('usage')}: {usage:.0f}%"
            )

        except Exception as exc:
            self.cpu.info.setText(
                f"{self._tr('cpu_error')}: {exc}"
            )

        try:
            memory = get_memory_info() or {}

            total = (
                float(
                    memory.get(
                        "total",
                        0,
                    )
                    or 0
                )
                / (1024 ** 3)
            )

            used = (
                float(
                    memory.get(
                        "used",
                        0,
                    )
                    or 0
                )
                / (1024 ** 3)
            )

            percent = float(
                memory.get(
                    "percent",
                    0,
                )
                or 0
            )

            self.ram.info.setText(
                f"{self._tr('total')}: {total:.1f} GB\n"
                f"{self._tr('used')}: {used:.1f} GB\n"
                f"{self._tr('usage')}: {percent:.0f}%"
            )

        except Exception as exc:
            self.ram.info.setText(
                f"{self._tr('ram_error')}: {exc}"
            )

        try:
            system = get_system_info() or {}

            computer = system.get(
                "computer",
                "Unknown",
            )

            system_name = system.get(
                "system",
                "Unknown",
            )

            release = system.get(
                "release",
                "",
            )

            architecture = system.get(
                "machine",
                "Unknown",
            )

            processor = (
                system.get(
                    "processor",
                    None,
                )
                or platform.processor()
                or "Unknown"
            )

            self.system.info.setText(
                f"{self._tr('computer')}: {computer}\n"
                f"{self._tr('system')}: {system_name} {release}\n"
                f"{self._tr('architecture')}: {architecture}\n"
                f"{self._tr('processor')}: {processor}"
            )

        except Exception as exc:
            self.system.info.setText(
                f"{self._tr('system_error')}: {exc}"
            )

