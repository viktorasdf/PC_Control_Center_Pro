
from collections import deque

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPen, QFont
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QHBoxLayout, QSizePolicy, QWidget, QPushButton


BG_CARD = "#0a1428"
BG_CARD_2 = "#0d1a31"
BORDER = "#1d3152"
TEXT = "#f4f7ff"
MUTED = "#8ea3bd"
GRID = "#1a2d49"

TRANSLATIONS = {
    "ru": {"performance":"Общая производительность","stable":"Система работает\nстабильно","optimize":"Оптимизировать","unavailable":"Данные недоступны","excellent":"Отлично","good":"Хорошо","normal":"Нормально","attention":"Внимание","resources":"Краткий обзор ресурсов","more":"Подробнее  ›","realtime":"Мониторинг в реальном времени","open_monitoring":"Открыть мониторинг  ›","recommendations":"Найдено {count} рекомендаций","sec":"сек"},
    "en": {"performance":"Overall performance","stable":"System is running\nstably","optimize":"Optimize","unavailable":"Data unavailable","excellent":"Excellent","good":"Good","normal":"Normal","attention":"Attention","resources":"Resource overview","more":"Details  ›","realtime":"Real-time monitoring","open_monitoring":"Open monitoring  ›","recommendations":"{count} recommendations found","sec":"sec"},
    "uk": {"performance":"Загальна продуктивність","stable":"Система працює\nстабільно","optimize":"Оптимізувати","unavailable":"Дані недоступні","excellent":"Відмінно","good":"Добре","normal":"Нормально","attention":"Увага","resources":"Короткий огляд ресурсів","more":"Детальніше  ›","realtime":"Моніторинг у реальному часі","open_monitoring":"Відкрити моніторинг  ›","recommendations":"Знайдено {count} рекомендацій","sec":"сек"},
    "de": {"performance":"Gesamtleistung","stable":"System läuft\nstabil","optimize":"Optimieren","unavailable":"Daten nicht verfügbar","excellent":"Ausgezeichnet","good":"Gut","normal":"Normal","attention":"Achtung","resources":"Ressourcenübersicht","more":"Details  ›","realtime":"Echtzeitüberwachung","open_monitoring":"Überwachung öffnen  ›","recommendations":"{count} Empfehlungen gefunden","sec":"Sek."},
    "it": {"performance":"Prestazioni complessive","stable":"Il sistema funziona\nstabilmente","optimize":"Ottimizza","unavailable":"Dati non disponibili","excellent":"Eccellente","good":"Buono","normal":"Normale","attention":"Attenzione","resources":"Panoramica risorse","more":"Dettagli  ›","realtime":"Monitoraggio in tempo reale","open_monitoring":"Apri monitoraggio  ›","recommendations":"{count} raccomandazioni trovate","sec":"sec"},
    "es": {"performance":"Rendimiento general","stable":"El sistema funciona\ncon normalidad","optimize":"Optimizar","unavailable":"Datos no disponibles","excellent":"Excelente","good":"Bien","normal":"Normal","attention":"Atención","resources":"Resumen de recursos","more":"Detalles  ›","realtime":"Monitorización en tiempo real","open_monitoring":"Abrir monitorización  ›","recommendations":"Se encontraron {count} recomendaciones","sec":"s"},
    "fr": {"performance":"Performances globales","stable":"Le système fonctionne\nnormalement","optimize":"Optimiser","unavailable":"Données indisponibles","excellent":"Excellent","good":"Bon","normal":"Normal","attention":"Attention","resources":"Aperçu des ressources","more":"Détails  ›","realtime":"Surveillance en temps réel","open_monitoring":"Ouvrir la surveillance  ›","recommendations":"{count} recommandations trouvées","sec":"s"},
}

def _tr(language, key, **kwargs):
    language = str(language or "ru").lower().strip()
    if language not in TRANSLATIONS:
        language = "ru"
    return TRANSLATIONS[language].get(key, key).format(**kwargs)



class CardFrame(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("CardFrame")
        self.setStyleSheet(
            f"""
            QFrame#CardFrame {{
                background: {BG_CARD};
                border: 1px solid {BORDER};
                border-radius: 14px;
            }}
            """
        )

    def set_theme(self, light: bool):
        """Apply light/dark theme to the dashboard card."""
        card_bg = "#ffffff" if light else "#0a1428"
        card_border = "#d6e0ea" if light else "#1d3152"

        self.setStyleSheet(
            f"""
            QFrame#CardFrame {{
                background: {card_bg};
                border: 1px solid {card_border};
                border-radius: 14px;
            }}
            """
        )


class CircularGauge(QWidget):
    def __init__(self, title="", color="#22d3ee", value=None, parent=None):
        super().__init__(parent)

        self.title = title
        self.color = QColor(color)
        self.value = value
        self.subtitle = ""

        self.setMinimumSize(118, 118)
        self.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding
        )
        self.value_label = QLabel(self)
        self.value_label.setAlignment(Qt.AlignCenter)
        self.value_label.setStyleSheet(
            """
            QLabel {
                color: #f4f7ff;
                background: transparent;
                border: none;
                font-size: 20px;
                font-weight: bold;
            }
            """
        )
        self.value_label.setText(
            f"{self.value:.0f}%" if self.value is not None else "—"
        )
        self.value_label.raise_()

    def setValue(self, value, subtitle=""):
        if value is None:
            self.value = None
        else:
            try:
                value = float(value)
                self.value = max(0.0, min(100.0, value))
            except (TypeError, ValueError):
                self.value = None

        self.subtitle = subtitle

        self.value_label.setText(
            f"{self.value:.0f}%" if self.value is not None else "—"
        )
        self.value_label.raise_()

        print(
            f"[CircularGauge] {self.title}: "
            f"value={self.value!r}, subtitle={self.subtitle!r}"
        )

        self.update()

    def set_title(self, title):
        self.title = str(title)
        self.update()
    def resizeEvent(self, event):
        super().resizeEvent(event)

        label_width = min(self.width(), 90)
        label_height = 40

        self.value_label.setGeometry(
            (self.width() - label_width) // 2,
            (self.height() - label_height) // 2 - 2,
            label_width,
            label_height
        )

        self.value_label.raise_()
        self.update()



    def paintEvent(self, event):
        p = QPainter(self)
        print(
            f"[CircularGauge PAINT] "
            f"title={self.title!r}, "
            f"value={self.value!r}, "
            f"size={self.width()}x{self.height()}"
        )
        p.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()

        light = getattr(self, "_light_theme", False)

        if light:
            text_color = QColor("#172033")
            muted_color = QColor("#64748b")
            background_color = QColor("#d6e0ea")
        else:
            text_color = QColor("#f4f7ff")
            muted_color = QColor("#8ea3bd")
            background_color = QColor("#1b2b47")

        # Размер круга
        size = min(w, h) - 18
        x = (w - size) / 2
        y = (h - size) / 2

        from PySide6.QtCore import QRectF

        rect = QRectF(x, y, size, size)

        # -----------------------------
        # Фоновая дуга
        # -----------------------------
        p.setPen(
            QPen(
                background_color,
                10,
                Qt.SolidLine,
                Qt.RoundCap
            )
        )

        p.drawArc(
            rect,
            0,
            360 * 16
        )

        # -----------------------------
        # Значение
        # -----------------------------
        if self.value is not None:
            p.setPen(
                QPen(
                    self.color,
                    10,
                    Qt.SolidLine,
                    Qt.RoundCap
                )
            )

            p.drawArc(
                rect,
                140 * 16,
                int(-self.value * 3.6 * 16)
            )

            value_text = f"{self.value:.0f}%"

        else:
            value_text = "N/A"

        

        # -----------------------------
        # Название
        # -----------------------------
        title_rect = QRectF(
            x,
            y + size * 0.67,
            size,
            22
        )

        p.setPen(muted_color)

        title_font = QFont("Segoe UI")
        title_font.setPointSize(9)
        p.setFont(title_font)

        p.drawText(
            title_rect,
            Qt.AlignCenter,
            self.title
        )

        # -----------------------------
        # Подпись
        # -----------------------------
        if self.subtitle:
            subtitle_rect = QRectF(
                x,
                y + size * 0.82,
                size,
                20
            )

            p.setPen(self.color)

            subtitle_font = QFont("Segoe UI")
            subtitle_font.setBold(True)
            subtitle_font.setPointSize(8)
            p.setFont(subtitle_font)

            p.drawText(
                subtitle_rect,
                Qt.AlignCenter,
                self.subtitle
            )

        p.end()


class PerformanceGauge(CardFrame):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.ui_language = "ru"
        self._recommendation_count = 2

        # ==================================================
        # MAIN GAUGE
        # ==================================================
        self.gauge = CircularGauge("", "#22d3ee")
        self.gauge.setMinimumSize(150, 150)

        # ==================================================
        # STATUS
        # ==================================================
        self.status = QLabel()
        self.status.setStyleSheet(
            "color:#22e889;"
            "font-size:15px;"
            "font-weight:800;"
            "background:transparent;"
            "border:none;"
        )

        self.recommend = QLabel()
        self.recommend.setStyleSheet(
            "color:#28a8ff;"
            "font-size:11px;"
            "font-weight:600;"
            "background:transparent;"
            "border:none;"
        )

        # ==================================================
        # OPTIMIZE BUTTON
        # ==================================================
        self.optimize = QPushButton()
        self.optimize.setCursor(Qt.PointingHandCursor)
        self.optimize.setMinimumHeight(42)
        self.optimize.setFocusPolicy(Qt.NoFocus)

        self.optimize.setStyleSheet(
            """
            QPushButton {
                color: white;
                background: #075be8;
                border: 1px solid #1686ff;
                border-radius: 10px;
                padding: 7px 12px;
                font-size: 12px;
                font-weight: 800;
            }

            QPushButton:hover {
                background: #1264ef;
            }

            QPushButton:pressed {
                background: #063fae;
            }

            QPushButton:disabled {
                color: #718096;
                background: #172235;
                border: 1px solid #263750;
            }
            """
        )

        # ==================================================
        # CARD LAYOUT
        # ==================================================
        body = QVBoxLayout(self)
        body.setContentsMargins(
            18,
            11,
            18,
            14,
        )
        body.setSpacing(8)

        # ==================================================
        # HEADER
        # ==================================================
        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 0)

        self.header = QLabel()
        self.header.setStyleSheet(
            "color:#f4f7ff;"
            "font-size:17px;"
            "font-weight:700;"
            "background:transparent;"
            "border:none;"
        )

        header_row.addWidget(self.header)
        header_row.addStretch()

        body.addLayout(header_row)

        # ==================================================
        # CONTENT
        # ==================================================
        content = QHBoxLayout()
        content.setContentsMargins(0, 0, 0, 0)
        content.setSpacing(14)

        # Gauge container
        self.gauge_panel = QFrame()
        self.gauge_panel.setStyleSheet(
            """
            QFrame {
                background: #071225;
                border: 1px solid #162a47;
                border-radius: 11px;
            }
            """
        )

        gauge_layout = QVBoxLayout(self.gauge_panel)
        gauge_layout.setContentsMargins(3, 3, 3, 3)
        gauge_layout.addWidget(self.gauge)

        content.addWidget(
            self.gauge_panel,
            0,
        )

        # Information area
        self.info_panel = QFrame()
        self.info_panel.setStyleSheet(
            """
            QFrame {
                background: #071225;
                border: 1px solid #162a47;
                border-radius: 11px;
            }
            """
        )

        info_layout = QVBoxLayout(self.info_panel)
        info_layout.setContentsMargins(
            13,
            11,
            13,
            11,
        )
        info_layout.setSpacing(7)

        self.stable = QLabel()
        self.stable.setStyleSheet(
            "color:#f4f7ff;"
            "font-size:15px;"
            "font-weight:700;"
            "background:transparent;"
            "border:none;"
        )

        info_layout.addWidget(self.stable)
        info_layout.addWidget(self.status)
        info_layout.addWidget(self.recommend)

        info_layout.addStretch()

        info_layout.addWidget(self.optimize)

        content.addWidget(
            self.info_panel,
            1,
        )

        body.addLayout(
            content,
            1,
        )

        self.set_language(
            getattr(
                self,
                "ui_language",
                "ru",
            )
        )

    def set_theme(self, light: bool):
        """Apply light/dark theme to the performance card."""

        super().set_theme(light)

        panel_bg = "#f8fafc" if light else "#071225"
        panel_border = "#d6e0ea" if light else "#162a47"
        text_color = "#172033" if light else "#f4f7ff"

        panel_style = (
            "QFrame {"
            f"background:{panel_bg};"
            f"border:1px solid {panel_border};"
            "border-radius:11px;"
            "}"
        )

        self.gauge_panel.setStyleSheet(panel_style)
        self.info_panel.setStyleSheet(panel_style)

        self.header.setStyleSheet(
            f"color:{text_color};"
            "font-size:17px;"
            "font-weight:700;"
            "background:transparent;"
            "border:none;"
        )

        self.stable.setStyleSheet(
            f"color:{text_color};"
            "font-size:15px;"
            "font-weight:700;"
            "background:transparent;"
            "border:none;"
        )

    def set_language(self, language):
        self.ui_language = str(
            language or "ru"
        ).lower().strip()

        if self.ui_language not in TRANSLATIONS:
            self.ui_language = "ru"

        self.header.setText(
            _tr(
                self.ui_language,
                "performance",
            )
        )

        self.stable.setText(
            _tr(
                self.ui_language,
                "stable",
            )
        )

        self.optimize.setText(
            _tr(
                self.ui_language,
                "optimize",
            )
        )

        self._refresh_status()

        self.recommend.setText(
            _tr(
                self.ui_language,
                "recommendations",
                count=self._recommendation_count,
            )
        )

    def _refresh_status(self):
        value = self.gauge.value

        if value is None:
            self.status.setText(
                _tr(
                    self.ui_language,
                    "unavailable",
                )
            )

            self.status.setStyleSheet(
                "color:#f0a43b;"
                "font-size:15px;"
                "font-weight:800;"
                "background:transparent;"
                "border:none;"
            )

            return

        if value >= 75:
            text, color = "excellent", "#22e889"
        elif value >= 50:
            text, color = "good", "#22d3ee"
        elif value >= 25:
            text, color = "normal", "#f3c64f"
        else:
            text, color = "attention", "#ff7a66"

        self.status.setText(
            _tr(
                self.ui_language,
                text,
            )
        )

        self.status.setStyleSheet(
            f"color:{color};"
            "font-size:15px;"
            "font-weight:800;"
            "background:transparent;"
            "border:none;"
        )

    def setValue(self, value):
        self.gauge.setValue(value)
        self._refresh_status()

    def set_recommendations(self, count):
        try:
            self._recommendation_count = max(
                0,
                int(count),
            )
        except (TypeError, ValueError):
            self._recommendation_count = 0

        self.recommend.setText(
            _tr(
                self.ui_language,
                "recommendations",
                count=self._recommendation_count,
            )
        )

class ResourceOverview(CardFrame):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.gauges = {}
        self.ui_language = "ru"

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 10, 16, 12)
        layout.setSpacing(7)

        # --------------------------------------------------
        # HEADER
        # --------------------------------------------------
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)

        self.title = QLabel()
        self.title.setStyleSheet(
            "color:#f4f7ff;"
            "font-size:17px;"
            "font-weight:700;"
            "background:transparent;"
            "border:none;"
        )

        self.more = QLabel()
        self.more.setStyleSheet(
            "color:#168cff;"
            "font-size:11px;"
            "font-weight:600;"
            "background:transparent;"
            "border:none;"
        )

        header.addWidget(self.title)
        header.addStretch()
        header.addWidget(self.more)
        layout.addLayout(header)

        # --------------------------------------------------
        # RESOURCE CARDS
        # --------------------------------------------------
        row = QHBoxLayout()
        row.setSpacing(8)

        resources = [
            ("CPU", "#22d3ee"),
            ("GPU", "#a970ff"),
            ("RAM", "#22e889"),
            ("Диск", "#f3a83b"),
        ]

        for name, color in resources:
            panel = QFrame()
            panel.setObjectName("ResourceMiniCard")
            panel.setStyleSheet(
                "QFrame#ResourceMiniCard {"
                "background:#071225;"
                "border:1px solid #162a47;"
                "border-radius:10px;"
                "}"
            )

            panel_layout = QVBoxLayout(panel)
            panel_layout.setContentsMargins(3, 3, 3, 3)
            panel_layout.setSpacing(0)

            gauge = CircularGauge(name, color)
            gauge.setMinimumSize(118, 125)
            gauge.setSizePolicy(
                QSizePolicy.Expanding,
                QSizePolicy.Expanding
            )

            panel_layout.addWidget(gauge)
            row.addWidget(panel, 1)

            self.gauges[name] = gauge

        layout.addLayout(row, 1)

        self.set_language(self.ui_language)

    def set_theme(self, light: bool):
        """Apply light/dark theme to the resource overview card."""

        super().set_theme(light)

        card_bg = "#f8fafc" if light else "#071225"
        card_border = "#d6e0ea" if light else "#162a47"
        text_color = "#172033" if light else "#f4f7ff"

        self.title.setStyleSheet(
            f"color:{text_color};"
            "font-size:17px;"
            "font-weight:700;"
            "background:transparent;"
            "border:none;"
        )

        mini_card_style = (
            "QFrame#ResourceMiniCard {"
            f"background:{card_bg};"
            f"border:1px solid {card_border};"
            "border-radius:10px;"
            "}"
        )

        for panel in self.findChildren(QFrame, "ResourceMiniCard"):
            panel.setStyleSheet(mini_card_style)

    def set_language(self, language):
        self.ui_language = str(language or "ru").lower().strip()

        if self.ui_language not in TRANSLATIONS:
            self.ui_language = "ru"

        self.title.setText(
            _tr(self.ui_language, "resources")
        )

        self.more.setText(
            _tr(self.ui_language, "more")
        )

        disk_title = {
            "ru": "Диск",
            "en": "Disk",
            "uk": "Диск",
            "de": "Datenträger",
            "it": "Disco",
            "es": "Disco",
            "fr": "Disque",
        }[self.ui_language]

        self.gauges["Диск"].set_title(disk_title)

        self.update()

    def set_values(self, cpu, gpu, ram, disk, subtitles=None):
        subtitles = subtitles or {}

        for name, value in [
            ("CPU", cpu),
            ("GPU", gpu),
            ("RAM", ram),
            ("Диск", disk),
        ]:
            self.gauges[name].setValue(
                value,
                subtitles.get(name, "")
            )

class RealtimeGraph(CardFrame):
    def __init__(self, parent=None):
        self.ui_language = "ru"
        super().__init__(parent)

        self.series = {
            "CPU": deque(maxlen=60),
            "GPU": deque(maxlen=60),
            "RAM": deque(maxlen=60),
            "Диск": deque(maxlen=60),
        }

        self.colors = {
            "CPU": QColor("#168cff"),
            "GPU": QColor("#22e889"),
            "RAM": QColor("#f3a83b"),
            "Диск": QColor("#9b5cff"),
        }

        self.setMinimumHeight(210)
        self.set_language(self.ui_language)

    def set_theme(self, light: bool):
        """Apply light/dark theme to the realtime graph."""

        super().set_theme(light)

        self._light_theme = light
        self.update()

    def set_language(self, language):
        self.ui_language = str(language or "ru").lower().strip()

        if self.ui_language not in TRANSLATIONS:
            self.ui_language = "ru"

        self.update()

    def _series_title(self, name):
        if name != "Диск":
            return name

        return {
            "ru": "Диск",
            "en": "Disk",
            "uk": "Диск",
            "de": "Datenträger",
            "it": "Disco",
            "es": "Disco",
            "fr": "Disque",
        }[self.ui_language]

    def _time_label(self, seconds):
        unit = _tr(self.ui_language, "sec")

        if seconds:
            return f"-{seconds} {unit}"

        return f"0 {unit}"

    def add(self, values):
        for name in self.series:
            v = values.get(name)

            if v is None:
                if self.series[name]:
                    v = self.series[name][-1]
                else:
                    continue

            try:
                v = max(0.0, min(100.0, float(v)))
            except (TypeError, ValueError):
                continue

            self.series[name].append(v)

        self.update()
    
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()

        light = getattr(self, "_light_theme", False)

        if light:
            bg = QColor("#f8fafc")
            grid = QColor("#d6e0ea")
            text = QColor("#172033")
            muted = QColor("#64748b")
        else:
            bg = QColor("#071225")
            grid = QColor("#142642")
            text = QColor("#f4f7ff")
            muted = QColor("#8ea3bd")

        p.fillRect(0, 0, w, h, bg)

        left = 42
        right = 12
        top = 12
        bottom = 28

        graph_w = max(1, w - left - right)
        graph_h = max(1, h - top - bottom)

        # -----------------------------
        # Сетка
        # -----------------------------
        p.setPen(QPen(grid, 1))

        for i in range(5):
            y = top + int(graph_h * i / 4)
            p.drawLine(left, y, w - right, y)

        for i in range(6):
            x = left + int(graph_w * i / 5)
            p.drawLine(x, top, x, h - bottom)

        # -----------------------------
        # Шкала 0-100%
        # -----------------------------
        p.setPen(muted)
        p.setFont(QFont("Segoe UI", 8))

        for value in (100, 75, 50, 25, 0):
            y = top + int(graph_h * (100 - value) / 100)

            p.drawText(
                2,
                y - 7,
                left - 8,
                16,
                Qt.AlignRight | Qt.AlignVCenter,
                str(value),
            )

        # -----------------------------
        # Время
        # -----------------------------
        p.setPen(muted)
        p.setFont(QFont("Segoe UI", 8))

        for i in range(6):
            x = left + int(graph_w * i / 5)
            seconds = (5 - i) * 10

            if seconds:
                label = f"-{seconds} {_tr(self.ui_language, 'sec')}"
            else:
                label = f"0 {_tr(self.ui_language, 'sec')}"

            p.drawText(
                x - 25,
                h - bottom + 5,
                50,
                18,
                Qt.AlignCenter,
                label,
            )

        # -----------------------------
        # Графики
        # -----------------------------
        has_data = False

        for name, series in self.series.items():

            if not series:
                continue

            points = list(series)

            if not points:
                continue

            has_data = True

            color = self.colors.get(
                name,
                QColor("#22d3ee"),
            )

            pen = QPen(
                color,
                2,
                Qt.SolidLine,
                Qt.RoundCap,
                Qt.RoundJoin,
            )

            p.setPen(pen)

            if len(points) == 1:
                value = max(
                    0.0,
                    min(100.0, float(points[0]))
                )

                x = left + graph_w // 2

                y = top + int(
                    graph_h * (100.0 - value) / 100.0
                )

                p.drawPoint(x, y)

            else:
                step = graph_w / float(
                    max(1, len(points) - 1)
                )

                previous_value = max(
                    0.0,
                    min(100.0, float(points[0]))
                )

                previous_x = left

                previous_y = top + int(
                    graph_h
                    * (100.0 - previous_value)
                    / 100.0
                )

                for index in range(1, len(points)):

                    try:
                        value = float(points[index])
                    except (TypeError, ValueError):
                        value = 0.0

                    value = max(
                        0.0,
                        min(100.0, value)
                    )

                    x = left + int(step * index)

                    y = top + int(
                        graph_h
                        * (100.0 - value)
                        / 100.0
                    )

                    p.drawLine(
                        previous_x,
                        previous_y,
                        x,
                        y,
                    )

                    previous_x = x
                    previous_y = y

        # -----------------------------
        # Если данных ещё нет
        # -----------------------------
        if not has_data:
            p.setPen(muted)
            p.setFont(QFont("Segoe UI", 9))

            p.drawText(
                0,
                0,
                w,
                h,
                Qt.AlignCenter,
                "No data",
            )

        p.end()