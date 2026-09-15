from collections import deque

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
)

from app.widgets.graph_widget import GraphWidget


class MonitoringPage(QWidget):

    def __init__(
        self,
        gpu_worker=None,
        disk_worker=None,
        parent=None,
    ):
        super().__init__(parent)

        self.setObjectName(
            "MonitoringPage"
        )

        # ======================================================
        # LANGUAGE
        # ======================================================

        self.ui_language = "ru"

        # ======================================================
        # WORKERS
        # ======================================================

        self.gpu_worker = gpu_worker
        self.disk_worker = disk_worker

        # ======================================================
        # HISTORY
        # ======================================================

        self.gpu_values = deque(
            maxlen=60
        )

        self.disk_values = deque(
            maxlen=60
        )

        # ======================================================
        # UI
        # ======================================================

        self._build_ui()

        # ======================================================
        # LANGUAGE INITIALIZATION
        # ======================================================

        self.set_language(self.ui_language)

        # ======================================================
        # SIGNALS
        # ======================================================

        if self.gpu_worker is not None:

            try:

                self.gpu_worker.gpu_ready.connect(
                    self.update_gpu
                )

                print(
                    "[MonitoringPage] "
                    "GPU signal connected"
                )

            except Exception as exc:

                print(
                    "[MonitoringPage] "
                    f"GPU signal connection error: {exc}"
                )

        if self.disk_worker is not None:

            try:

                self.disk_worker.disk_ready.connect(
                    self.update_disk
                )

                print(
                    "[MonitoringPage] "
                    "Disk signal connected"
                )

            except Exception as exc:

                print(
                    "[MonitoringPage] "
                    f"Disk signal connection error: {exc}"
                )

    # ==========================================================
    # LANGUAGE
    # ==========================================================

    SUPPORTED_LANGUAGES = {"ru", "en", "uk", "de", "it", "es", "fr"}

    TRANSLATIONS = {
        "monitoring": {
            "ru": "\u041c\u043e\u043d\u0438\u0442\u043e\u0440\u0438\u043d\u0433",
            "en": "Monitoring",
            "uk": "\u041c\u043e\u043d\u0456\u0442\u043e\u0440\u0438\u043d\u0433",
            "de": "Monitoring",
            "it": "Monitoraggio",
            "es": "Monitoreo",
            "fr": "Surveillance",
        },

        "monitoring_subtitle": {
            "ru": "\u041c\u043e\u043d\u0438\u0442\u043e\u0440\u0438\u043d\u0433 \u0440\u0435\u0441\u0443\u0440\u0441\u043e\u0432 \u043a\u043e\u043c\u043f\u044c\u044e\u0442\u0435\u0440\u0430 \u0432 \u0440\u0435\u0430\u043b\u044c\u043d\u043e\u043c \u0432\u0440\u0435\u043c\u0435\u043d\u0438",
            "en": "Real-time computer resource monitoring",
            "uk": "\u041c\u043e\u043d\u0456\u0442\u043e\u0440\u0438\u043d\u0433 \u0440\u0435\u0441\u0443\u0440\u0441\u0456\u0432 \u043a\u043e\u043c\u043f\u2019\u044e\u0442\u0435\u0440\u0430 \u0432 \u0440\u0435\u0430\u043b\u044c\u043d\u043e\u043c\u0443 \u0447\u0430\u0441\u0456",
            "de": "Echtzeit-\u00dcberwachung der Computerressourcen",
            "it": "Monitoraggio delle risorse del computer in tempo reale",
            "es": "Monitoreo de los recursos del ordenador en tiempo real",
            "fr": "Surveillance des ressources de l\u2019ordinateur en temps r\u00e9el",
        },

        "gpu_usage": {
            "ru": "GPU Usage",
            "en": "GPU Usage",
            "uk": "GPU Usage",
            "de": "GPU-Auslastung",
            "it": "Utilizzo GPU",
            "es": "Uso de GPU",
            "fr": "Utilisation du GPU",
        },

        "gpu_total": {
            "ru": "\u041e\u0431\u0449\u0430\u044f \u0437\u0430\u0433\u0440\u0443\u0437\u043a\u0430 GPU",
            "en": "Total GPU usage",
            "uk": "\u0417\u0430\u0433\u0430\u043b\u044c\u043d\u0435 \u0437\u0430\u0432\u0430\u043d\u0442\u0430\u0436\u0435\u043d\u043d\u044f GPU",
            "de": "Gesamtauslastung der GPU",
            "it": "Utilizzo totale della GPU",
            "es": "Uso total de la GPU",
            "fr": "Utilisation totale du GPU",
        },

        "gpu_3d": {
            "ru": "3D engine",
            "en": "3D engine",
            "uk": "3D engine",
            "de": "3D-Engine",
            "it": "Motore 3D",
            "es": "Motor 3D",
            "fr": "Moteur 3D",
        },

        "video_decode": {
            "ru": "\u0414\u0435\u043a\u043e\u0434\u0438\u0440\u043e\u0432\u0430\u043d\u0438\u0435 \u0432\u0438\u0434\u0435\u043e",
            "en": "Video decoding",
            "uk": "\u0414\u0435\u043a\u043e\u0434\u0443\u0432\u0430\u043d\u043d\u044f \u0432\u0456\u0434\u0435\u043e",
            "de": "Videodekodierung",
            "it": "Decodifica video",
            "es": "Decodificaci\u00f3n de v\u00eddeo",
            "fr": "D\u00e9codage vid\u00e9o",
        },

        "compute": {
            "ru": "GPU \u0432\u044b\u0447\u0438\u0441\u043b\u0435\u043d\u0438\u044f",
            "en": "GPU compute",
            "uk": "GPU \u043e\u0431\u0447\u0438\u0441\u043b\u0435\u043d\u043d\u044f",
            "de": "GPU-Berechnungen",
            "it": "Calcolo GPU",
            "es": "C\u00e1lculo de GPU",
            "fr": "Calcul GPU",
        },

        "disk_activity": {
            "ru": "Активность диска",
            "en": "Disk Activity",
            "uk": "Активність диска",
            "de": "Festplattenaktivit\u00e4t",
            "it": "Attivit\u00e0 del disco",
            "es": "Actividad del disco",
            "fr": "Activit\u00e9 du disque",
        },

          "current_activity": {
              "ru": "Текущая активность",
              "en": "Current activity",
              "uk": "Поточна активність",
              "de": "Aktuelle Aktivität",
              "it": "Attività corrente",
              "es": "Actividad actual",
              "fr": "Activité actuelle",
          },

        "read_speed": {
            "ru": "\u0421\u043a\u043e\u0440\u043e\u0441\u0442\u044c \u0447\u0442\u0435\u043d\u0438\u044f",
            "en": "Read speed",
            "uk": "\u0428\u0432\u0438\u0434\u043a\u0456\u0441\u0442\u044c \u0447\u0438\u0442\u0430\u043d\u043d\u044f",
            "de": "Lesegeschwindigkeit",
            "it": "Velocit\u00e0 di lettura",
            "es": "Velocidad de lectura",
            "fr": "Vitesse de lecture",
        },

        "write_speed": {
            "ru": "\u0421\u043a\u043e\u0440\u043e\u0441\u0442\u044c \u0437\u0430\u043f\u0438\u0441\u0438",
            "en": "Write speed",
            "uk": "\u0428\u0432\u0438\u0434\u043a\u0456\u0441\u0442\u044c \u0437\u0430\u043f\u0438\u0441\u0443",
            "de": "Schreibgeschwindigkeit",
            "it": "Velocit\u00e0 di scrittura",
            "es": "Velocidad de escritura",
            "fr": "Vitesse d\u2019\u00e9criture",
        },

        "disk_space_used": {
            "ru": "\u0417\u0430\u043d\u044f\u0442\u043e \u043c\u0435\u0441\u0442\u0430",
            "en": "Space used",
            "uk": "\u0417\u0430\u0439\u043d\u044f\u0442\u043e \u043c\u0456\u0441\u0446\u044f",
            "de": "Belegter Speicherplatz",
            "it": "Spazio utilizzato",
            "es": "Espacio utilizado",
            "fr": "Espace utilis\u00e9",
        },

        "monitoring_active": {
            "ru": "\u041c\u043e\u043d\u0438\u0442\u043e\u0440\u0438\u043d\u0433 \u0430\u043a\u0442\u0438\u0432\u0435\u043d",
            "en": "Monitoring active",
            "uk": "\u041c\u043e\u043d\u0456\u0442\u043e\u0440\u0438\u043d\u0433 \u0430\u043a\u0442\u0438\u0432\u043d\u0438\u0439",
            "de": "\u00dcberwachung aktiv",
            "it": "Monitoraggio attivo",
            "es": "Monitoreo activo",
            "fr": "Surveillance active",
        },

        "gpu_monitoring_active": {
            "ru": "GPU \u043c\u043e\u043d\u0438\u0442\u043e\u0440\u0438\u043d\u0433 \u0430\u043a\u0442\u0438\u0432\u0435\u043d",
            "en": "GPU monitoring active",
            "uk": "\u041c\u043e\u043d\u0456\u0442\u043e\u0440\u0438\u043d\u0433 GPU \u0430\u043a\u0442\u0438\u0432\u043d\u0438\u0439",
            "de": "GPU-\u00dcberwachung aktiv",
            "it": "Monitoraggio GPU attivo",
            "es": "Monitoreo de GPU activo",
            "fr": "Surveillance du GPU active",
        },

        "gpu_disk_monitoring_active": {
            "ru": "\u041c\u043e\u043d\u0438\u0442\u043e\u0440\u0438\u043d\u0433 GPU + Disk \u0430\u043a\u0442\u0438\u0432\u0435\u043d",
            "en": "GPU + Disk monitoring active",
            "uk": "\u041c\u043e\u043d\u0456\u0442\u043e\u0440\u0438\u043d\u0433 GPU + Disk \u0430\u043a\u0442\u0438\u0432\u043d\u0438\u0439",
            "de": "GPU- und Festplatten\u00fcberwachung aktiv",
            "it": "Monitoraggio GPU + disco attivo",
            "es": "Monitoreo de GPU y disco activo",
            "fr": "Surveillance du GPU et du disque active",
        },
    }

    def _tr(self, text):
        lang = getattr(self, "ui_language", "ru")
        if lang not in self.SUPPORTED_LANGUAGES:
            lang = "ru"

        return self.TRANSLATIONS.get(
            text,
            {}
        ).get(
            lang,
            text
        )

    def set_language(self, language):
        language = str(language or "ru").lower().strip()

        if language not in self.SUPPORTED_LANGUAGES:
            language = "ru"

        self.ui_language = language

        try:
            if hasattr(self, "title_label"):
                self.title_label.setText(
                    self._tr("monitoring")
                )

            if hasattr(self, "subtitle_label"):
                self.subtitle_label.setText(
                    self._tr("monitoring_subtitle")
                )

            if hasattr(self, "gpu_title_label"):
                self.gpu_title_label.setText(
                    self._tr("gpu_usage")
                )

            if hasattr(self, "status_label"):
                self.status_label.setText(
                    "\u25cf " + self._tr("monitoring_active")
                )

            # GPU cards
            if hasattr(self, "gpu_card"):
                self.gpu_card["title_label"].setText("GPU")
                self.gpu_card["description_label"].setText(
                    self._tr("gpu_total")
                )

            if hasattr(self, "gpu_3d_card"):
                self.gpu_3d_card["title_label"].setText("GPU 3D")
                self.gpu_3d_card["description_label"].setText(
                    self._tr("gpu_3d")
                )

            if hasattr(self, "video_card"):
                self.video_card["title_label"].setText("Video Decode")
                self.video_card["description_label"].setText(
                    self._tr("video_decode")
                )

            if hasattr(self, "compute_card"):
                self.compute_card["title_label"].setText("Compute")
                self.compute_card["description_label"].setText(
                    self._tr("compute")
                )
            if hasattr(self, "disk_title_label"):
                self.disk_title_label.setText(
                    self._tr("disk_activity")
                )  

            # Disk cards
            if hasattr(self, "disk_activity_card"):
                self.disk_activity_card["title_label"].setText(
                    self._tr("disk_activity")
                )
                self.disk_activity_card["description_label"].setText(
                    self._tr("current_activity")
                )

            if hasattr(self, "disk_read_card"):
                self.disk_read_card["title_label"].setText(
                    self._tr("read_speed")
                )
                self.disk_read_card["description_label"].setText(
                    self._tr("read_speed")
                )

            if hasattr(self, "disk_write_card"):
                self.disk_write_card["title_label"].setText(
                    self._tr("write_speed")
                )
                self.disk_write_card["description_label"].setText(
                    self._tr("write_speed")
                )

            if hasattr(self, "disk_space_card"):
                self.disk_space_card["title_label"].setText(
                    "Disk Space"
                )
                self.disk_space_card["description_label"].setText(
                    self._tr("disk_space_used")
                )

            print(
                "[MonitoringPage] Language:",
                self.ui_language
            )

        except Exception as exc:
            print(
                "[MonitoringPage] Language update error:",
                exc
            )

    # ==========================================================
    # THEME
    # ==========================================================

    def set_theme(self, light=False):
        """Переключает MonitoringPage между тёмной и светлой темой."""
        light = bool(light)
        light_to_dark = {
            "#F5F7FB": "#070B1A",
            "#FFFFFF": "#0D162B",
            "#D9E2F0": "#1D3152",
            "#172033": "#F8FAFC",
            "#607089": "#8FA2BF",
            "#42526B": "#AEBBD0",
        }
        dark_to_light = {v: k for k, v in light_to_dark.items()}
        mapping = dark_to_light if light else light_to_dark

        for widget in [self] + self.findChildren(QWidget):
            try:
                qss = widget.styleSheet()
                if not qss:
                    continue
                for source, target in mapping.items():
                    qss = qss.replace(source, target)
                    qss = qss.replace(source.lower(), target)
                widget.setStyleSheet(qss)
            except RuntimeError:
                pass

        self._theme_light = light

    # ==========================================================
    # UI
    # ==========================================================

    def _build_ui(self):

        self.setStyleSheet("""
            QWidget#MonitoringPage {
                background-color: #F5F7FB;
            }

            QLabel {
                color: #172033;
            }

            QFrame {
                background-color: #FFFFFF;
                border: 1px solid #D9E2F0;
                border-radius: 12px;
            }
        """)

        layout = QVBoxLayout(
            self
        )

        layout.setContentsMargins(
            24,
            24,
            24,
            24,
        )

        layout.setSpacing(
            18
        )

        # ======================================================
        # HEADER
        # ======================================================

        self.title_label = QLabel(
            "Мониторинг"
        )

        self.title_label.setStyleSheet("""
            QLabel {
                color: #172033;
                background: transparent;
                border: none;
                font-size: 28px;
                font-weight: 700;
            }
        """)

        self.subtitle_label = QLabel(
            "Мониторинг ресурсов компьютера "
            "в реальном времени"
        )

        self.subtitle_label.setStyleSheet("""
            QLabel {
                color: #607089;
                background: transparent;
                border: none;
                font-size: 13px;
            }
        """)

        layout.addWidget(self.title_label)
        layout.addWidget(self.subtitle_label)

        # ======================================================
        # GPU CARDS
        # ======================================================

        gpu_cards = QHBoxLayout()

        gpu_cards.setSpacing(
            14
        )

        self.gpu_card = self._create_card(
            "GPU",
            "#22D3EE",
            "Общая загрузка GPU"
        )

        self.gpu_3d_card = self._create_card(
            "GPU 3D",
            "#3B82F6",
            "3D engine"
        )

        self.video_card = self._create_card(
            "Video Decode",
            "#A855F7",
            "Декодирование видео"
        )

        self.compute_card = self._create_card(
            "Compute",
            "#F97316",
            "GPU вычисления"
        )

        gpu_cards.addWidget(
            self.gpu_card["frame"]
        )

        gpu_cards.addWidget(
            self.gpu_3d_card["frame"]
        )

        gpu_cards.addWidget(
            self.video_card["frame"]
        )

        gpu_cards.addWidget(
            self.compute_card["frame"]
        )

        layout.addLayout(
            gpu_cards
        )

        # ======================================================
        # DISK CARDS
        # ======================================================

        disk_cards = QHBoxLayout()

        disk_cards.setSpacing(
            14
        )

        self.disk_activity_card = self._create_card(
            self._tr("disk_activity"),
          "#F5C542",
            "Текущая активность"
        )

        self.disk_read_card = self._create_card(
            self._tr("read_speed"),
            "#22C55E",
            "Скорость чтения"
        )

        self.disk_write_card = self._create_card(
            self._tr("write_speed"),
            "#F97316",
            "Скорость записи"
        )

        self.disk_space_card = self._create_card(
            "Disk Space",
            "#EF4444",
            "Занято места"
        )

        disk_cards.addWidget(
            self.disk_activity_card["frame"]
        )

        disk_cards.addWidget(
            self.disk_read_card["frame"]
        )

        disk_cards.addWidget(
            self.disk_write_card["frame"]
        )

        disk_cards.addWidget(
            self.disk_space_card["frame"]
        )

        layout.addLayout(
            disk_cards
        )

        # ======================================================
        # GPU GRAPH
        # ======================================================

        gpu_graph_frame = QFrame()

        gpu_graph_frame.setObjectName(
            "GPUGraphFrame"
        )

        gpu_graph_frame.setStyleSheet("""
            QFrame#GPUGraphFrame {
                background-color: #FFFFFF;
                border: 1px solid #D9E2F0;
                border-radius: 12px;
            }
        """)

        gpu_graph_layout = QVBoxLayout(
            gpu_graph_frame
        )

        gpu_graph_layout.setContentsMargins(
            18,
            16,
            18,
            18,
        )

        gpu_graph_layout.setSpacing(
            8
        )

        gpu_header = QHBoxLayout()

        self.gpu_title_label = QLabel(
            "GPU Usage"
        )

        self.gpu_title_label.setStyleSheet("""
            QLabel {
                color: #172033;
                background: transparent;
                border: none;
                font-size: 18px;
                font-weight: 700;
            }
        """)

        self.gpu_graph_current = QLabel(
            "N/A"
        )

        self.gpu_graph_current.setStyleSheet("""
            QLabel {
                color: #22D3EE;
                background: transparent;
                border: none;
                font-size: 18px;
                font-weight: 700;
            }
        """)

        gpu_header.addWidget(
            self.gpu_title_label
        )

        gpu_header.addStretch()

        gpu_header.addWidget(
            self.gpu_graph_current
        )

        gpu_graph_layout.addLayout(
            gpu_header
        )

        self.gpu_graph = GraphWidget(
            title="",
            minimum_value=0,
            maximum_value=100,
        )

        gpu_graph_layout.addWidget(
            self.gpu_graph
        )

        layout.addWidget(
            gpu_graph_frame,
            1
        )

        # ======================================================
        # DISK GRAPH
        # ======================================================

        disk_graph_frame = QFrame()

        disk_graph_frame.setObjectName(
            "DiskGraphFrame"
        )

        disk_graph_frame.setStyleSheet("""
            QFrame#DiskGraphFrame {
                background-color: #FFFFFF;
                border: 1px solid #D9E2F0;
                border-radius: 12px;
            }
        """)

        disk_graph_layout = QVBoxLayout(
            disk_graph_frame
        )

        disk_graph_layout.setContentsMargins(
            18,
            16,
            18,
            18,
        )

        disk_graph_layout.setSpacing(
            8
        )

        disk_header = QHBoxLayout()

        self.disk_title_label = QLabel(
            self._tr("disk_activity")
        )

        self.disk_title_label.setStyleSheet("""
            QLabel {
                color: #172033;
                background: transparent;
                border: none;
                font-size: 18px;
                font-weight: 700;
            }
        """)

        self.disk_graph_current = QLabel(
            "N/A"
        )

        self.disk_graph_current.setStyleSheet("""
            QLabel {
                color: #F5C542;
                background: transparent;
                border: none;
                font-size: 18px;
                font-weight: 700;
            }
        """)

        disk_header.addWidget(
            self.disk_title_label
        )

        disk_header.addStretch()

        disk_header.addWidget(
            self.disk_graph_current
        )

        disk_graph_layout.addLayout(
            disk_header
        )

        self.disk_graph = GraphWidget(
            title="",
            minimum_value=0,
            maximum_value=100,
        )

        disk_graph_layout.addWidget(
            self.disk_graph
        )

        layout.addWidget(
            disk_graph_frame,
            1
        )

        # ======================================================
        # STATUS
        # ======================================================

        status_frame = QFrame()

        status_frame.setObjectName(
            "MonitoringStatus"
        )

        status_frame.setStyleSheet("""
            QFrame#MonitoringStatus {
                background-color: #FFFFFF;
                border: 1px solid #D9E2F0;
                border-radius: 10px;
            }
        """)

        status_layout = QHBoxLayout(
            status_frame
        )

        status_layout.setContentsMargins(
            15,
            10,
            15,
            10,
        )

        self.status_label = QLabel(
            "● Мониторинг активен"
        )

        self.status_label.setStyleSheet("""
            QLabel {
                color: #22C55E;
                background: transparent;
                border: none;
                font-size: 12px;
                font-weight: 600;
            }
        """)

        status_layout.addWidget(
            self.status_label
        )

        status_layout.addStretch()

        self.info_label = QLabel(
            "GPU: 1.5 сек.  |  Disk: 1 сек."
        )

        self.info_label.setStyleSheet("""
            QLabel {
                color: #607089;
                background: transparent;
                border: none;
                font-size: 11px;
            }
        """)

        status_layout.addWidget(
            self.info_label
        )

        layout.addWidget(
            status_frame
        )

    # ==========================================================
    # CARD
    # ==========================================================

    def _create_card(
        self,
        title,
        accent,
        description,
    ):

        frame = QFrame()

        frame.setMinimumHeight(
            125
        )

        frame.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border: 1px solid #D9E2F0;
                border-radius: 12px;
            }
        """)

        layout = QVBoxLayout(
            frame
        )

        layout.setContentsMargins(
            18,
            16,
            18,
            14,
        )

        layout.setSpacing(
            4
        )

        title_label = QLabel(
            title
        )

        title_label.setStyleSheet("""
            QLabel {
                color: #42526B;
                background: transparent;
                border: none;
                font-size: 13px;
                font-weight: 600;
            }
        """)

        value_label = QLabel(
            "N/A"
        )

        value_label.setMinimumHeight(
            40
        )

        value_label.setStyleSheet(
            f"""
            QLabel {{
                color: {accent};
                background: transparent;
                border: none;
                font-size: 30px;
                font-weight: 800;
            }}
            """
        )

        description_label = QLabel(
            description
        )

        description_label.setStyleSheet("""
            QLabel {
                color: #607089;
                background: transparent;
                border: none;
                font-size: 11px;
            }
        """)

        description_label.setWordWrap(
            True
        )

        layout.addWidget(
            title_label
        )

        layout.addWidget(
            value_label
        )

        layout.addWidget(
            description_label
        )

        return {
            "frame": frame,
            "value": value_label,
            "title_label": title_label,
            "description_label": description_label,
            "title": title,
            "description": description,
        }

    # ==========================================================
    # FORMAT PERCENT
    # ==========================================================

    def _format_percent(
        self,
        value,
    ):

        if value is None:
            return "N/A"

        try:

            value = float(
                value
            )

        except (
            ValueError,
            TypeError,
        ):

            return "N/A"

        value = max(
            0.0,
            min(
                100.0,
                value,
            )
        )

        return f"{value:.1f}%"

    # ==========================================================
    # FORMAT SPEED
    # ==========================================================

    def _format_speed(
        self,
        value,
    ):

        if value is None:
            return "N/A"

        try:

            value = float(
                value
            )

        except (
            ValueError,
            TypeError,
        ):

            return "N/A"

        if value < 0:
            value = 0.0

        if value >= 1024:

            return (
                f"{value / 1024:.1f} GB/s"
            )

        return (
            f"{value:.1f} MB/s"
        )

    # ==========================================================
    # GPU UPDATE
    # ==========================================================

    def update_gpu(
        self,
        gpu,
    ):

        if not isinstance(
            gpu,
            dict,
        ):
            return

        usage = gpu.get(
            "usage"
        )

        usage_3d = gpu.get(
            "usage_3d"
        )

        video_decode = gpu.get(
            "usage_video_decode"
        )

        compute = gpu.get(
            "usage_compute"
        )

        self.gpu_card["value"].setText(
            self._format_percent(
                usage
            )
        )

        self.gpu_3d_card["value"].setText(
            self._format_percent(
                usage_3d
            )
        )

        self.video_card["value"].setText(
            self._format_percent(
                video_decode
            )
        )

        self.compute_card["value"].setText(
            self._format_percent(
                compute
            )
        )

        if usage is None:

            self.gpu_graph_current.setText(
                "N/A"
            )

            return

        try:

            value = float(
                usage
            )

        except (
            ValueError,
            TypeError,
        ):

            return

        value = max(
            0.0,
            min(
                100.0,
                value,
            )
        )

        self.gpu_graph_current.setText(
            f"{value:.1f}%"
        )

        self.gpu_values.append(
            value
        )

        self.gpu_graph.set_values(
            list(
                self.gpu_values
            )
        )

        self.status_label.setText(
            "\u25cf " + self._tr("gpu_monitoring_active")
        )

    # ==========================================================
    # DISK UPDATE
    # ==========================================================

    def update_disk(
        self,
        disk,
    ):

        if not isinstance(
            disk,
            dict,
        ):
            return

        activity = disk.get(
            "activity"
        )

        read = disk.get(
            "read"
        )

        write = disk.get(
            "write"
        )

        space = disk.get(
            "space"
        )

        self.disk_activity_card["value"].setText(
            self._format_percent(
                activity
            )
        )

        self.disk_read_card["value"].setText(
            self._format_speed(
                read
            )
        )

        self.disk_write_card["value"].setText(
            self._format_speed(
                write
            )
        )

        self.disk_space_card["value"].setText(
            self._format_percent(
                space
            )
        )

        if activity is None:

            self.disk_graph_current.setText(
                "N/A"
            )

            return

        try:

            value = float(
                activity
            )

        except (
            ValueError,
            TypeError,
        ):

            return

        value = max(
            0.0,
            min(
                100.0,
                value,
            )
        )

        self.disk_graph_current.setText(
            f"{value:.1f}%"
        )

        self.disk_values.append(
            value
        )

        self.disk_graph.set_values(
            list(
                self.disk_values
            )
        )

        self.status_label.setText(
            "\u25cf " + self._tr("gpu_disk_monitoring_active")
        )

    # ==========================================================
    # SHUTDOWN
    # ==========================================================

    def shutdown(self):

        print(
            "[Monitoring] Shutdown started"
        )

        # ------------------------------------------------------
        # ВАЖНО:
        #
        # GPUWorker и DiskWorker теперь принадлежат MainWindow.
        #
        # Поэтому MonitoringPage НЕ останавливает их.
        #
        # MainWindow сам отвечает за остановку workers.
        # ------------------------------------------------------

        print(
            "[Monitoring] Workers owned by MainWindow"
        )

        print(
            "[Monitoring] Shutdown complete"
        )

    # ==========================================================
    # CLOSE EVENT
    # ==========================================================

    def closeEvent(
        self,
        event,
    ):

        self.shutdown()

        event.accept()














