
# -*- coding: utf-8 -*-

import platform
import psutil
import subprocess
import os
import sys
import winreg
from pathlib import Path

from PySide6.QtCore import QTimer, Qt, QSettings
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QListWidget,
    QListWidgetItem,
    QStackedWidget,
    QLabel,
    QFrame,
    QApplication,
    QPushButton,
    QSizePolicy,
    QDialog,
    QCheckBox,
    QComboBox,
    QDialogButtonBox,
    QSpinBox,
)

from app.pages.dashboard import DashboardPage
from app.pages.monitoring import MonitoringPage
from app.pages.hardware_page import HardwarePage
from app.pages.storage import StoragePage
from app.pages.network import NetworkPage
from app.pages.placeholder import PlaceholderPage
from app.pages.tools import ToolsPage
from app.pages.ai_assistant_page import AIAssistantPage
from app.pages.optimize import OptimizePage

from app.services.gpu_worker import GPUWorker
from app.services.disk_worker import DiskWorker


# ==============================================================
# COLORS
# ==============================================================

BG = "#050b18"
SIDEBAR = "#070d25"
CARD = "#091528"
BORDER = "#182c4a"
TEXT = "#f4f7ff"
MUTED = "#8ea3bd"
BLUE = "#168cff"
GREEN = "#79ff21"
PURPLE = "#a970ff"


# ==============================================================
# TOP BAR
# ==============================================================

class TopBar(QFrame):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setMinimumHeight(62)
        self.setMaximumHeight(78)

        self.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Preferred,
        )

        self.setStyleSheet(
            f"""
            QFrame {{
                background: {CARD};
                border: 1px solid {BORDER};
                border-radius: 12px;
            }}
            """
        )

        lay = QHBoxLayout(self)

        lay.setContentsMargins(
            16,
            6,
            10,
            6,
        )

        lay.setSpacing(8)

        self.items = {}

        for key, title, value, color in (
            ("windows", "Windows 11 Pro", "22H2", BLUE),
            ("cpu", "CPU", "—", "#22d3ee"),
            ("gpu", "GPU", "—", GREEN),
            ("ram", "RAM", "—", "#b8e820"),
        ):

            box = QVBoxLayout()
            box.setSpacing(1)

            title_label = QLabel(title)

            title_label.setStyleSheet(
                f"""
                color:{TEXT};
                font-size:13px;
                font-weight:800;
                background:transparent;
                border:none;
                """
            )

            value_label = QLabel(value)

            value_label.setStyleSheet(
                f"""
                color:{MUTED};
                font-size:10px;
                background:transparent;
                border:none;
                """
            )

            box.addWidget(title_label)
            box.addWidget(value_label)

            lay.addLayout(
                box,
                1,
            )

            self.items[key] = value_label

            if key != "ram":

                sep = QFrame()

                sep.setFrameShape(
                    QFrame.VLine
                )

                sep.setStyleSheet(
                    "color:#172b47;"
                )

                lay.addWidget(sep)

        lay.addStretch(1)

        self.wifi_button = self._make_top_button(
            "Wi-Fi",
            "#17aaff",
            58,
        )

        self.sound_button = self._make_top_button(
            "🔊",
            "#f4f7ff",
            38,
        )

        self.extra_button = self._make_top_button(
            "⚡",
            "#17aaff",
            38,
        )

        lay.addWidget(self.wifi_button)
        lay.addWidget(self.sound_button)
        lay.addWidget(self.extra_button)

        # ----------------------------------------------------------
        # WINDOW CONTROL BUTTONS
        # ----------------------------------------------------------

        # Отдельный фиксированный контейнер.
        # Благодаря ему кнопки — □ × всегда остаются справа.
        self.window_buttons = QWidget()

        self.window_buttons.setFixedSize(
            118,
            40,
        )

        self.window_buttons.setSizePolicy(
            QSizePolicy.Fixed,
            QSizePolicy.Fixed,
        )

        window_lay = QHBoxLayout(
            self.window_buttons
        )

        window_lay.setContentsMargins(
            2,
            3,
            2,
            3,
        )

        window_lay.setSpacing(4)

        self.min_button = self._make_window_button(
            "—"
        )

        self.max_button = self._make_window_button(
            "□"
        )

        self.close_button = self._make_window_button(
            "×",
            close=True,
        )

        self.min_button.clicked.connect(
            lambda: self.window().showMinimized()
        )

        self.max_button.clicked.connect(
            self._toggle_maximize
        )

        self.close_button.clicked.connect(
            lambda: self.window().close()
        )

        window_lay.addWidget(
            self.min_button
        )

        window_lay.addWidget(
            self.max_button
        )

        window_lay.addWidget(
            self.close_button
        )

        # Контейнер всегда находится в крайней правой части TopBar.
        lay.addWidget(
            self.window_buttons
        )

    # ----------------------------------------------------------

    def _make_top_button(
        self,
        text,
        color,
        width,
    ):

        button = QPushButton(text)

        button.setFixedSize(
            width,
            34,
        )

        button.setCursor(
            Qt.PointingHandCursor
        )

        button.setStyleSheet(
            f"""
            QPushButton {{
                color:{color};
                background:transparent;
                border:1px solid transparent;
                border-radius:8px;
                font-size:15px;
                font-weight:800;
                padding:0;
            }}

            QPushButton:hover {{
                background:#10203a;
                border:1px solid #214267;
            }}

            QPushButton:pressed {{
                background:#162b49;
            }}
            """
        )

        return button

    # ----------------------------------------------------------

    def _make_window_button(
        self,
        text,
        close=False,
    ):

        button = QPushButton(text)

        button.setFixedSize(
            34,
            34,
        )

        button.setCursor(
            Qt.PointingHandCursor
        )

        normal = (
            "#ff6475"
            if close
            else "#8ea3bd"
        )

        hover = (
            "#dc2626"
            if close
            else "#1b3354"
        )

        button.setStyleSheet(
            f"""
            QPushButton {{
                color:{normal};
                background:transparent;
                border:1px solid transparent;
                border-radius:8px;
                font-size:20px;
                font-weight:800;
                padding:0;
            }}

            QPushButton:hover {{
                color:#ffffff;
                background:{hover};
                border:1px solid #31547d;
            }}

            QPushButton:pressed {{
                color:#ffffff;
                background:#12243d;
            }}
            """
        )

        return button

    # ----------------------------------------------------------

    def _toggle_maximize(self):

        window = self.window()

        if window.isMaximized():

            window.showNormal()

            self.max_button.setText(
                "□"
            )

        else:

            window.showMaximized()

            self.max_button.setText(
                "❐"
            )

    # ----------------------------------------------------------

    def _short(
        self,
        text,
        limit=22,
    ):

        text = str(
            text or "—"
        )

        if len(text) <= limit:
            return text

        return (
            text[:limit - 1]
            + "…"
        )


# ==============================================================
# SIDEBAR
# ==============================================================

class Sidebar(QFrame):

    def __init__(
        self,
        menu,
        parent=None,
    ):

        super().__init__(parent)

        self.setMinimumWidth(
            210
        )

        self.setMaximumWidth(
            264
        )

        self.setSizePolicy(
            QSizePolicy.Preferred,
            QSizePolicy.Expanding,
        )

        self.setStyleSheet(
            f"""
            QFrame {{
                background: {SIDEBAR};
                border-right: 1px solid #152642;
            }}
            """
        )

        lay = QVBoxLayout(self)

        lay.setContentsMargins(
            12,
            18,
            12,
            12,
        )

        lay.setSpacing(8)

        # ----------------------------------------------------------
        # LOGO
        # ----------------------------------------------------------

        logo = QHBoxLayout()

        mark = QLabel("⬢")

        mark.setStyleSheet(
            """
            color:#168cff;
            font-size:34px;
            background:transparent;
            border:none;
            """
        )

        logo.addWidget(mark)

        titlebox = QVBoxLayout()

        title = QLabel(
            "PC Control Center Pro"
        )

        title.setStyleSheet(
            f"""
            color:{TEXT};
            font-size:17px;
            font-weight:800;
            background:transparent;
            border:none;
            """
        )

        sub = QLabel(
            "Ваш компьютер под контролем"
        )

        sub.setStyleSheet(
            f"""
            color:{MUTED};
            font-size:9px;
            background:transparent;
            border:none;
            """
        )

        titlebox.addWidget(title)
        titlebox.addWidget(sub)

        logo.addLayout(titlebox)

        lay.addLayout(logo)

        lay.addSpacing(16)

        self.menu = menu

        lay.addWidget(menu)

        lay.addStretch()

        # ----------------------------------------------------------
        # BOTTOM
        # ----------------------------------------------------------

        self.settings_button = QPushButton("⚙  Настройки")
        self.about_button = QPushButton("ⓘ  О программе")
        self.theme_button = QPushButton("☼  Светлая тема")

        for button in (self.settings_button, self.about_button, self.theme_button):
            button.setCursor(Qt.PointingHandCursor)
            button.setMinimumHeight(34)
            button.setStyleSheet(
                f"""
                QPushButton {{
                    color:{TEXT};
                    font-size:11px;
                    text-align:left;
                    padding:7px 10px;
                    background:transparent;
                    border:1px solid transparent;
                    border-radius:8px;
                }}
                QPushButton:hover {{
                    background:#10203a;
                    border:1px solid #214267;
                }}
                """
            )
            lay.addWidget(button)

        ver = QLabel(
            "PC Control Center Pro v1.0"
        )

        ver.setStyleSheet(
            f"""
            color:{MUTED};
            font-size:9px;
            padding:6px 10px;
            background:transparent;
            border:none;
            """
        )

        lay.addWidget(ver)


# ==============================================================
# MAIN WINDOW
# ==============================================================

class MainWindow(QMainWindow):

    def __init__(self):

        super().__init__()

        self._closing = False
        self._settings = QSettings("PCControlCenterPro", "PCControlCenterPro")
        stored_theme_mode = self._settings.value("theme/mode", "dark")
        if stored_theme_mode == "light":
            self._light_theme = True
        elif stored_theme_mode == "system":
            self._light_theme = QApplication.palette().window().color().lightness() >= 128
        else:
            self._light_theme = False
        self._refresh_interval = int(self._settings.value("system/refresh_interval", 1000, type=int))

        self.setWindowTitle(
            "PC Control Center Pro"
        )

        # ----------------------------------------------------------
        # WINDOW SIZE
        # ----------------------------------------------------------

        screen = QApplication.primaryScreen()

        available = (
            screen.availableGeometry()
            if screen
            else None
        )

        if available:

            target_w = min(
                1450,
                max(
                    980,
                    available.width() - 24,
                ),
            )

            target_h = min(
                900,
                max(
                    620,
                    available.height() - 24,
                ),
            )

            self.resize(
                target_w,
                target_h,
            )

            self.setMinimumSize(
                min(
                    980,
                    available.width(),
                ),
                min(
                    620,
                    available.height(),
                ),
            )

        else:

            self.resize(
                1280,
                720,
            )

            self.setMinimumSize(
                980,
                620,
            )

        # ----------------------------------------------------------
        # FRAMELESS WINDOW
        # ----------------------------------------------------------

        self.setWindowFlag(
            Qt.FramelessWindowHint,
            True,
        )

        self.setStyleSheet(
            f"""
            QMainWindow {{
                background:{BG};
            }}

            QWidget {{
                background:{BG};
                color:{TEXT};
            }}
            """
        )

        # ----------------------------------------------------------
        # CENTRAL
        # ----------------------------------------------------------

        central = QWidget()

        self.setCentralWidget(
            central
        )

        root = QHBoxLayout(
            central
        )

        root.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        root.setSpacing(0)

        # ----------------------------------------------------------
        # MENU
        # ----------------------------------------------------------

        self.menu = QListWidget()

        self.menu.setFrameShape(
            QFrame.NoFrame
        )

        self.menu.setFocusPolicy(
            Qt.NoFocus
        )

        self.menu.setFixedWidth(
            240
        )

        self.menu.setStyleSheet(
            f"""
            QListWidget {{
                background:transparent;
                border:none;
                color:{MUTED};
                padding:5px 0;
                outline:none;
                font-size:12px;
            }}

            QListWidget::item {{
                color:{TEXT};
                padding:11px 14px;
                margin:2px 6px;
                border-radius:10px;
                background:transparent;
            }}

            QListWidget::item:hover {{
                background:#10203a;
            }}

            QListWidget::item:selected {{
                background:#2548ff;
                color:white;
                border-left:3px solid #22d3ee;
                font-weight:800;
            }}
            """
        )

        items = [
            "⌂   Главная",
            "▣   Мониторинг",
            "⚙   Аппаратное обеспечение",
            "▤   Хранилище",
            "◎   Сеть",
            "✧   Оптимизация",
            "⚒   Инструменты",
            "🤖   AI Assistant",
        ]

        for text in items:

            self.menu.addItem(
                QListWidgetItem(text)
            )

        self.sidebar = Sidebar(
            self.menu
        )

        self.sidebar.settings_button.clicked.connect(self.show_settings)
        self.sidebar.about_button.clicked.connect(self.show_about)
        self.sidebar.theme_button.clicked.connect(self.toggle_theme)

        root.addWidget(
            self.sidebar
        )

        # ----------------------------------------------------------
        # CONTENT
        # ----------------------------------------------------------

        content = QWidget()

        cl = QVBoxLayout(
            content
        )

        cl.setContentsMargins(
            12,
            10,
            12,
            10,
        )

        cl.setSpacing(10)

        # ----------------------------------------------------------
        # TOP BAR
        # ----------------------------------------------------------

        self.topbar = TopBar()

        self.topbar.wifi_button.clicked.connect(self.open_wifi_settings)
        self.topbar.sound_button.clicked.connect(self.open_sound_settings)
        self.topbar.extra_button.clicked.connect(self.open_extra_tools)

        cl.addWidget(
            self.topbar
        )

        # ----------------------------------------------------------
        # STACK
        # ----------------------------------------------------------

        self.stack = QStackedWidget()

        cl.addWidget(
            self.stack,
            1,
        )

        root.addWidget(
            content,
            1,
        )

        # ----------------------------------------------------------
        # PAGES
        # ----------------------------------------------------------

        self.dashboard = DashboardPage(
            main_window=self
        )

        # ----------------------------------------------------------
        # GPU / DISK WORKERS
        # ----------------------------------------------------------

        self.gpu_worker = GPUWorker(
            self
        )

        self.disk_worker = DiskWorker(
            path="C:\\",
            parent=self
        )

        # ----------------------------------------------------------
        # MONITORING PAGE
        # ----------------------------------------------------------

        self.monitoring = MonitoringPage(
            gpu_worker=self.gpu_worker,
            disk_worker=self.disk_worker
        )

        # ----------------------------------------------------------
        # START WORKERS
        # ----------------------------------------------------------

        self.gpu_worker.start()

        print(
            "[MainWindow] GPUWorker started"
        )

        self.disk_worker.start()

        print(
            "[MainWindow] DiskWorker started"
        )

        # ----------------------------------------------------------
        # OTHER PAGES
        # ----------------------------------------------------------

        self.hardware = HardwarePage()

        self.storage = StoragePage()

        self.network = NetworkPage()

        self.optimize = OptimizePage()

        self.tools = ToolsPage(
            parent=self
        )

        self.ai_assistant = AIAssistantPage(
            parent=self
        )

        # ----------------------------------------------------------
        # ADD PAGES TO STACK
        # ----------------------------------------------------------

        self.pages = (
            self.dashboard,
            self.monitoring,
            self.hardware,
            self.storage,
            self.network,
            self.optimize,
            self.tools,
            self.ai_assistant,
        )

        for page in self.pages:

            self.stack.addWidget(
                page
            )

        print(
            "[MainWindow] Pages added:",
            self.stack.count()
        )

        # ----------------------------------------------------------
        # MENU CONNECTION
        # ----------------------------------------------------------

        self.menu.currentRowChanged.connect(
            self._change_page
        )

        self.menu.setCurrentRow(
            0
        )

        # ----------------------------------------------------------
        # TOP BAR TIMER
        # ----------------------------------------------------------

        self.top_timer = QTimer(
            self
        )

        self.top_timer.timeout.connect(
            self._update_topbar
        )

        self.top_timer.start(
            self._refresh_interval
        )

        self._update_topbar()

        # Apply the saved theme after the complete UI tree has been created.
        self.set_theme(self._light_theme)

        # Apply the saved interface language after the complete UI tree exists.
        self.set_language(
            self._settings.value("interface/language", "ru")
        )

        # Re-apply translations to dynamic page labels (AI/Optimize/Network)
        # after worker updates without requiring a restart.
        #self._language_refresh_timer = QTimer(self)
        #self._language_refresh_timer.timeout.connect(self._refresh_language_widgets)
        #self._language_refresh_timer.start(1000)

        self._center()

    # ==========================================================
    # RESIZE
    # ==========================================================

    def resizeEvent(
        self,
        event,
    ):

        super().resizeEvent(
            event
        )

        if hasattr(
            self,
            "sidebar",
        ):

            width = (
                218
                if self.width() < 1120
                else 264
            )

            self.sidebar.setFixedWidth(
                width
            )

        if hasattr(
            self,
            "menu",
        ):

            self.menu.setFixedWidth(
                194
                if self.width() < 1120
                else 240
            )

    # ==========================================================
    # PAGE CHANGE
    # ==========================================================

    def open_page(
        self,
        page,
    ):

        index = self.stack.indexOf(
            page
        )

        if index >= 0:

            self.menu.setCurrentRow(
                index
            )

            self.stack.setCurrentIndex(
                index
            )

    # ----------------------------------------------------------

    def _change_page(
        self,
        row,
    ):

        if (
            0 <= row
            < self.stack.count()
        ):

            self.stack.setCurrentIndex(
                row
            )

    # ==========================================================
    # TOP BAR UPDATE
    # ==========================================================

    def _update_topbar(self):

        if self._closing:
            return

        try:

            self.topbar.items["cpu"].setText(
                self.topbar._short(
                    platform.processor()
                    or "CPU",
                    20,
                )
            )

            # --------------------------------------------------
            # GPU
            # --------------------------------------------------

            from app.services.gpu_info import (
                get_cached_gpu_info,
            )

            gpu = (
                get_cached_gpu_info()
                or {}
            )

            gpu_name = gpu.get(
                "name",
                "Unknown GPU",
            )

            memory_total = gpu.get(
                "memory_total",
                0,
            )

            try:

                memory_total = float(
                    memory_total or 0
                )

            except (
                TypeError,
                ValueError,
            ):

                memory_total = 0.0

            self.topbar.items["gpu"].setText(
                f"{self.topbar._short(gpu_name, 18)}   "
                f"{memory_total:.1f} GB VRAM"
            )

            # --------------------------------------------------
            # RAM
            # --------------------------------------------------

            mem = psutil.virtual_memory()

            self.topbar.items["ram"].setText(
                f"{mem.total / (1024 ** 3):.1f} GB   "
                f"{int(mem.percent)}%"
            )

        except Exception as exc:

            print(
                f"[MainWindow] "
                f"Top bar update error: {exc}"
            )

    # ==========================================================
    # SETTINGS / ABOUT / QUICK ACTIONS
    # ==========================================================

    def show_settings(self):
        settings_texts = {
            "ru": {
                "window": "Настройки",
                "title": "Настройки PC Control Center Pro",
                "monitoring": "Мониторинг",
                "graphs": "Обновление графиков",
                "ai": "AI Assistant",
                "ai_enabled": "Включить AI Assistant по умолчанию",
                "language": "Язык",
                "startup": "Запуск вместе с Windows",
                "startup_enabled": "Запускать PC Control Center Pro вместе с Windows",
                "theme": "Тема",
                "theme_dark": "Тёмная",
                "theme_light": "Светлая",
                "theme_system": "Системная",
                "saving": "Сохранение",
                "autosave": "Автосохранение настроек",
                "hint": (
                    "Интервалы задаются в миллисекундах.\n"
                    "Мониторинг и графики настраиваются независимо.\n"
                    "Все изменения сохраняются в QSettings."
                ),
                "save": "Сохранить",
                "defaults": "По умолчанию",
                "cancel": "Отмена",
            },
            "en": {
                "window": "Settings",
                "title": "PC Control Center Pro Settings",
                "monitoring": "Monitoring",
                "graphs": "Graph updates",
                "ai": "AI Assistant",
                "ai_enabled": "Enable AI Assistant by default",
                "language": "Language",
                "startup": "Start with Windows",
                "startup_enabled": "Start PC Control Center Pro with Windows",
                "theme": "Theme",
                "theme_dark": "Dark",
                "theme_light": "Light",
                "theme_system": "System",
                "saving": "Saving",
                "autosave": "Auto-save settings",
                "hint": (
                    "Intervals are specified in milliseconds.\n"
                    "Monitoring and graphs are configured independently.\n"
                    "All changes are saved to QSettings."
                ),
                "save": "Save",
                "defaults": "Defaults",
                "cancel": "Cancel",
            },
            "uk": {
                "window": "Налаштування",
                "title": "Налаштування PC Control Center Pro",
                "monitoring": "Моніторинг",
                "graphs": "Оновлення графіків",
                "ai": "AI Assistant",
                "ai_enabled": "Увімкнути AI Assistant за замовчуванням",
                "language": "Мова",
                "startup": "Запуск разом із Windows",
                "startup_enabled": "Запускати PC Control Center Pro разом із Windows",
                "theme": "Тема",
                "theme_dark": "Темна",
                "theme_light": "Світла",
                "theme_system": "Системна",
                "saving": "Збереження",
                "autosave": "Автозбереження налаштувань",
                "hint": (
                    "Інтервали задаються в мілісекундах.\n"
                    "Моніторинг і графіки налаштовуються незалежно.\n"
                    "Усі зміни зберігаються в QSettings."
                ),
                "save": "Зберегти",
                "defaults": "За замовчуванням",
                "cancel": "Скасувати",
            },
            "de": {
                "window": "Einstellungen",
                "title": "PC Control Center Pro Einstellungen",
                "monitoring": "Überwachung",
                "graphs": "Diagrammaktualisierung",
                "ai": "AI Assistant",
                "ai_enabled": "AI Assistant standardmäßig aktivieren",
                "language": "Sprache",
                "startup": "Start mit Windows",
                "startup_enabled": "PC Control Center Pro mit Windows starten",
                "theme": "Design",
                "theme_dark": "Dunkel",
                "theme_light": "Hell",
                "theme_system": "System",
                "saving": "Speichern",
                "autosave": "Einstellungen automatisch speichern",
                "hint": (
                    "Intervalle werden in Millisekunden angegeben.\n"
                    "Überwachung und Diagramme werden unabhängig konfiguriert.\n"
                    "Alle Änderungen werden in QSettings gespeichert."
                ),
                "save": "Speichern",
                "defaults": "Standard",
                "cancel": "Abbrechen",
            },
            "it": {
                "window": "Impostazioni",
                "title": "Impostazioni PC Control Center Pro",
                "monitoring": "Monitoraggio",
                "graphs": "Aggiornamento grafici",
                "ai": "AI Assistant",
                "ai_enabled": "Abilita AI Assistant per impostazione predefinita",
                "language": "Lingua",
                "startup": "Avvio con Windows",
                "startup_enabled": "Avvia PC Control Center Pro con Windows",
                "theme": "Tema",
                "theme_dark": "Scuro",
                "theme_light": "Chiaro",
                "theme_system": "Sistema",
                "saving": "Salvataggio",
                "autosave": "Salvataggio automatico delle impostazioni",
                "hint": (
                    "Gli intervalli sono espressi in millisecondi.\n"
                    "Monitoraggio e grafici sono configurati separatamente.\n"
                    "Tutte le modifiche vengono salvate in QSettings."
                ),
                "save": "Salva",
                "defaults": "Predefiniti",
                "cancel": "Annulla",
            },
            "es": {
                "window": "Configuración",
                "title": "Configuración de PC Control Center Pro",
                "monitoring": "Monitorización",
                "graphs": "Actualización de gráficos",
                "ai": "AI Assistant",
                "ai_enabled": "Activar AI Assistant de forma predeterminada",
                "language": "Idioma",
                "startup": "Iniciar con Windows",
                "startup_enabled": "Iniciar PC Control Center Pro con Windows",
                "theme": "Tema",
                "theme_dark": "Oscuro",
                "theme_light": "Claro",
                "theme_system": "Sistema",
                "saving": "Guardado",
                "autosave": "Guardar automáticamente la configuración",
                "hint": (
                    "Los intervalos se indican en milisegundos.\n"
                    "La monitorización y los gráficos se configuran de forma independiente.\n"
                    "Todos los cambios se guardan en QSettings."
                ),
                "save": "Guardar",
                "defaults": "Predeterminados",
                "cancel": "Cancelar",
            },
            "fr": {
                "window": "Paramètres",
                "title": "Paramètres de PC Control Center Pro",
                "monitoring": "Surveillance",
                "graphs": "Mise à jour des graphiques",
                "ai": "AI Assistant",
                "ai_enabled": "Activer AI Assistant par défaut",
                "language": "Langue",
                "startup": "Démarrage avec Windows",
                "startup_enabled": "Démarrer PC Control Center Pro avec Windows",
                "theme": "Thème",
                "theme_dark": "Sombre",
                "theme_light": "Clair",
                "theme_system": "Système",
                "saving": "Enregistrement",
                "autosave": "Enregistrement automatique des paramètres",
                "hint": (
                    "Les intervalles sont indiqués en millisecondes.\n"
                    "La surveillance et les graphiques sont configurés indépendamment.\n"
                    "Toutes les modifications sont enregistrées dans QSettings."
                ),
                "save": "Enregistrer",
                "defaults": "Par défaut",
                "cancel": "Annuler",
            },
        }

        current_language = str(getattr(self, "_language", "ru")).lower()
        if current_language not in settings_texts:
            current_language = "ru"

        t = settings_texts[current_language]

        dialog = QDialog(self)
        dialog.setWindowTitle(t["window"])
        dialog.setMinimumSize(600, 650)

        if self._light_theme:
            dialog.setStyleSheet("""
                QDialog { background:#ffffff; color:#172033; }
                QLabel { color:#172033; }
                QCheckBox { color:#172033; spacing:8px; }
                QComboBox { background:#ffffff; color:#172033; border:1px solid #cbd5e1; padding:7px; border-radius:7px; }
                QComboBox QAbstractItemView { background:#ffffff; color:#172033; selection-background-color:#dbeafe; selection-color:#172033; }
                QPushButton { background:#168cff; color:white; border:none; border-radius:7px; padding:8px 18px; font-weight:700; }
            """)
        else:
            dialog.setStyleSheet("""
                QDialog { background:#091528; color:#f4f7ff; }
                QLabel { color:#f4f7ff; }
                QCheckBox { color:#f4f7ff; spacing:8px; }
                QComboBox { background:#10203a; color:#f4f7ff; border:1px solid #284466; padding:7px; border-radius:7px; }
                QComboBox QAbstractItemView { background:#10203a; color:#f4f7ff; selection-background-color:#2548ff; selection-color:white; }
                QPushButton { background:#168cff; color:white; border:none; border-radius:7px; padding:8px 18px; font-weight:700; }
            """)
        lay = QVBoxLayout(dialog)

        title = QLabel(t["title"])
        title.setStyleSheet("font-size:20px;font-weight:800;")
        lay.addWidget(title)

        def section(text):
            label = QLabel(text)
            label.setStyleSheet("font-size:13px;font-weight:700;margin-top:10px;")
            lay.addWidget(label)

        # Мониторинг
        section(t["monitoring"])
        monitoring = QComboBox()
        monitoring_values = [100, 250, 500, 1000, 2000, 5000]
        monitoring.addItems([f"{v} мс" for v in monitoring_values])
        current_monitor = int(self._settings.value("monitoring/interval_ms", 1000, type=int))
        monitoring.setCurrentIndex(monitoring_values.index(current_monitor) if current_monitor in monitoring_values else 3)
        lay.addWidget(monitoring)

        section(t["graphs"])
        graph = QComboBox()
        graph_values = [100, 250, 500, 1000, 2000]
        graph.addItems([f"{v} мс" for v in graph_values])
        current_graph = int(self._settings.value("graphs/interval_ms", 500, type=int))
        graph.setCurrentIndex(graph_values.index(current_graph) if current_graph in graph_values else 2)
        lay.addWidget(graph)

        # AI
        section(t["ai"])
        ai_enabled = QCheckBox(t["ai_enabled"])
        ai_enabled.setChecked(self._settings.value("ai/enabled", True, type=bool))
        lay.addWidget(ai_enabled)

        section(t["language"])
        
        language = QComboBox()
        language_items = [("Русский", "ru"), ("English", "en"), ("Українська", "uk"), ("Deutsch", "de"), ("Italiano", "it"), ("Español", "es"), ("Français", "fr")]
        for label, code in language_items:
            language.addItem(label, code)
        stored_language = str(getattr(self, "_language", self._settings.value("interface/language", "ru")))
        language.setCurrentIndex(next((i for i, (_, code) in enumerate(language_items) if code == stored_language), 0))
        lay.addWidget(language)

        # Запуск Windows
        section(t["startup"])
        startup = QCheckBox(t["startup_enabled"])
        startup.setChecked(self._settings.value("system/start_with_windows", False, type=bool))
        lay.addWidget(startup)

        # Тема
        section(t["theme"])
        theme = QComboBox()
        theme.addItems([t["theme_dark"], t["theme_light"], t["theme_system"]])
        stored_theme = self._settings.value("theme/mode", "dark")
        theme.setCurrentIndex({"dark": 0, "light": 1, "system": 2}.get(stored_theme, 0))
        lay.addWidget(theme)

        # Автосохранение
        section(t["saving"])
        autosave = QCheckBox(t["autosave"])
        autosave.setChecked(self._settings.value("system/autosave", True, type=bool))
        lay.addWidget(autosave)

        hint = QLabel(t["hint"])
        hint.setStyleSheet("color:#8ea3bd;line-height:1.4;")
        hint.setWordWrap(True)
        lay.addWidget(hint)
        lay.addStretch()

        buttons = QDialogButtonBox()
        save = buttons.addButton(t["save"], QDialogButtonBox.AcceptRole)
        defaults = buttons.addButton(t["defaults"], QDialogButtonBox.ResetRole)
        cancel = buttons.addButton(t["cancel"], QDialogButtonBox.RejectRole)

        def apply_startup(enabled):
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            value_name = "PC Control Center Pro"
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE):
                    pass
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
                    if enabled:
                        pythonw = Path(sys.executable).with_name("pythonw.exe")
                        exe = pythonw if pythonw.exists() else Path(sys.executable)
                        main_py = Path(__file__).resolve().parents[2] / "main.py"
                        command = f'"{exe}" "{main_py}"'
                        winreg.SetValueEx(key, value_name, 0, winreg.REG_SZ, command)
                    else:
                        try:
                            winreg.DeleteValue(key, value_name)
                        except FileNotFoundError:
                            pass
                return True
            except Exception as exc:
                print(f"[MainWindow] Startup setting error: {exc}")
                return False

        def apply_theme(mode):
            if mode == "light":
                self.set_theme(True)
            elif mode == "system":
                is_dark = QApplication.palette().window().color().lightness() < 128
                self.set_theme(not is_dark)
            else:
                self.set_theme(False)

        def save_settings():
            monitor_ms = monitoring_values[monitoring.currentIndex()]
            graph_ms = graph_values[graph.currentIndex()]
            theme_mode = ["dark", "light", "system"][theme.currentIndex()]
            self._settings.setValue("monitoring/interval_ms", monitor_ms)
            self._settings.setValue("graphs/interval_ms", graph_ms)
            self._settings.setValue("ai/enabled", ai_enabled.isChecked())
            self._settings.setValue("interface/language", language.currentData() or "ru")
            self._settings.setValue("system/start_with_windows", startup.isChecked())
            self._settings.setValue("theme/mode", theme_mode)
            self._settings.setValue("theme/light", theme_mode == "light")
            self._settings.setValue("system/autosave", autosave.isChecked())
            self._settings.setValue("system/refresh_interval", monitor_ms)
            self._refresh_interval = monitor_ms
            self.top_timer.setInterval(monitor_ms)
            if hasattr(self, "dashboard"):
                self.dashboard.timer.setInterval(monitor_ms)
                self.dashboard.ai_timer.setInterval(30000 if ai_enabled.isChecked() else 86400000)
            apply_theme(theme_mode)
            self.set_language(language.currentData() or "ru")
            if autosave.isChecked():
                self._settings.sync()
            apply_startup(startup.isChecked())
            dialog.accept()

        def restore_defaults():
            monitoring.setCurrentIndex(3)
            graph.setCurrentIndex(2)
            ai_enabled.setChecked(True)
            language.setCurrentIndex(0)
            startup.setChecked(False)
            theme.setCurrentIndex(0)
            autosave.setChecked(True)

        save.clicked.connect(save_settings)
        defaults.clicked.connect(restore_defaults)
        cancel.clicked.connect(dialog.reject)
        lay.addWidget(buttons)
        dialog.exec()


    def set_language(self, language):
        """Переключает язык интерфейса без перезапуска приложения."""

        print("\n" + "=" * 80)
        print("[LANG][CALLER] MainWindow.set_language()")
        print("[LANG][CALLER] requested:", repr(language))

        import traceback
        traceback.print_stack(limit=15)

        print("=" * 80 + "\n")

        language = str(language).lower()
        supported = {"ru", "en", "uk", "de", "it", "es", "fr"}
        if language not in supported:
            language = "ru"
        self._language = language
        self._settings.setValue("interface/language", language)

        # Один источник переводов: русский -> все поддерживаемые языки.
        # Благодаря этому можно переключаться между любыми языками без перезапуска.
        T = {
            "Ваш компьютер под контролем": {"en":"Your computer under control","uk":"Ваш комп'ютер під контролем","de":"Ihr Computer unter Kontrolle","it":"Il tuo computer sotto controllo","es":"Tu ordenador bajo control","fr":"Votre ordinateur sous contrôle"},
            "⚙  Настройки": {"en":"⚙  Settings","uk":"⚙  Налаштування","de":"⚙  Einstellungen","it":"⚙  Impostazioni","es":"⚙  Configuración","fr":"⚙  Paramètres"},
            "ⓘ  О программе": {"en":"ⓘ  About","uk":"ⓘ  Про програму","de":"ⓘ  Über das Programm","it":"ⓘ  Informazioni","es":"ⓘ  Acerca de","fr":"ⓘ  À propos"},
            "☼  Светлая тема": {"en":"☼  Light theme","uk":"☼  Світла тема","de":"☼  Helles Design","it":"☼  Tema chiaro","es":"☼  Tema claro","fr":"☼  Thème clair"},
            "☾  Тёмная тема": {"en":"☾  Dark theme","uk":"☾  Темна тема","de":"☾  Dunkles Design","it":"☾  Tema scuro","es":"☾  Tema oscuro","fr":"☾  Thème sombre"},
            "⌂   Главная": {"en":"⌂   Dashboard","uk":"⌂   Головна","de":"⌂   Dashboard","it":"⌂   Dashboard","es":"⌂   Panel","fr":"⌂   Tableau de bord"},
            "▣   Мониторинг": {"en":"▣   Monitoring","uk":"▣   Моніторинг","de":"▣   Überwachung","it":"▣   Monitoraggio","es":"▣   Monitorización","fr":"▣   Surveillance"},
            "⚙   Аппаратное обеспечение": {"en":"⚙   Hardware","uk":"⚙   Обладнання","de":"⚙   Hardware","it":"⚙   Hardware","es":"⚙   Hardware","fr":"⚙   Matériel"},
            "▤   Хранилище": {"en":"▤   Storage","uk":"▤   Сховище","de":"▤   Speicher","it":"▤   Archiviazione","es":"▤   Almacenamiento","fr":"▤   Stockage"},
            "◎   Сеть": {"en":"◎   Network","uk":"◎   Мережа","de":"◎   Netzwerk","it":"◎   Rete","es":"◎   Red","fr":"◎   Réseau"},
            "✧   Оптимизация": {"en":"✧   Optimize","uk":"✧   Оптимізація","de":"✧   Optimierung","it":"✧   Ottimizzazione","es":"✧   Optimización","fr":"✧   Optimisation"},
            "⚒   Инструменты": {"en":"⚒   Tools","uk":"⚒   Інструменти","de":"⚒   Werkzeuge","it":"⚒   Strumenti","es":"⚒   Herramientas","fr":"⚒   Outils"},
            "🤖   AI Assistant": {"ru":"🤖   AI-помощник","en":"🤖   AI Assistant","uk":"🤖   AI-помічник","de":"🤖   KI-Assistent","it":"🤖   Assistente AI","es":"🤖   Asistente de IA","fr":"🤖   Assistant IA"},
            "Информация о системе": {"en":"System information","uk":"Інформація про систему","de":"Systeminformationen","it":"Informazioni di sistema","es":"Información del sistema","fr":"Informations système"},
            "Материнская плата:  —": {"en":"Motherboard:  —","uk":"Материнська плата:  —","de":"Mainboard:  —","it":"Scheda madre:  —","es":"Placa base:  —","fr":"Carte mère :  —"},
            "Время работы:  —": {"en":"Uptime:  —","uk":"Час роботи:  —","de":"Betriebszeit:  —","it":"Tempo di attività:  —","es":"Tiempo de actividad:  —","fr":"Temps de fonctionnement :  —"},
            "Система:  —": {"en":"System:  —","uk":"Система:  —","de":"System:  —","it":"Sistema:  —","es":"Sistema:  —","fr":"Système :  —"},
            "Запуск:  —": {"en":"Launch:  —","uk":"Запуск:  —","de":"Start:  —","it":"Avvio:  —","es":"Inicio:  —","fr":"Démarrage :  —"},
            "ⓘ  Подробная информация": {"en":"ⓘ  Detailed information","uk":"ⓘ  Детальна інформація","de":"ⓘ  Detaillierte Informationen","it":"ⓘ  Informazioni dettagliate","es":"ⓘ  Información detallada","fr":"ⓘ  Informations détaillées"},
            "Мониторинг в реальном времени": {"en":"Real-time monitoring","uk":"Моніторинг у реальному часі","de":"Echtzeitüberwachung","it":"Monitoraggio in tempo reale","es":"Monitorización en tiempo real","fr":"Surveillance en temps réel"},
            "Открыть мониторинг  ›": {"en":"Open monitoring  ›","uk":"Відкрити моніторинг  ›","de":"Überwachung öffnen  ›","it":"Apri monitoraggio  ›","es":"Abrir monitorización  ›","fr":"Ouvrir la surveillance  ›"},
            "Краткий обзор ресурсов": {"en":"Resource overview","uk":"Огляд ресурсів","de":"Ressourcenübersicht","it":"Panoramica delle risorse","es":"Resumen de recursos","fr":"Aperçu des ressources"},
            "Подробнее  ›": {"en":"Details  ›","uk":"Докладніше  ›","de":"Details  ›","it":"Dettagli  ›","es":"Detalles  ›","fr":"Détails  ›"},
            "Быстрые действия": {"en":"Quick actions","uk":"Швидкі дії","de":"Schnellaktionen","it":"Azioni rapide","es":"Acciones rápidas","fr":"Actions rapides"},
            "Быстрая оптимизация": {"en":"Quick optimization","uk":"Швидка оптимізація","de":"Schnelloptimierung","it":"Ottimizzazione rapida","es":"Optimización rápida","fr":"Optimisation rapide"},
            "Улучшить систему в один клик": {"en":"Improve the system in one click","uk":"Покращити систему одним натисканням","de":"System mit einem Klick verbessern","it":"Migliora il sistema con un clic","es":"Mejora el sistema con un clic","fr":"Améliorer le système en un clic"},
            "Очистка": {"en":"Cleanup","uk":"Очищення","de":"Bereinigung","it":"Pulizia","es":"Limpieza","fr":"Nettoyage"},
            "Удалить временные файлы и мусор": {"en":"Delete temporary files and junk","uk":"Видалити тимчасові файли та сміття","de":"Temporäre Dateien und Datenmüll löschen","it":"Elimina file temporanei e spazzatura","es":"Eliminar archivos temporales y basura","fr":"Supprimer les fichiers temporaires et les fichiers inutiles"},
            "Автозагрузка": {"en":"Startup apps","uk":"Автозапуск","de":"Autostart","it":"Avvio automatico","es":"Inicio automático","fr":"Applications au démarrage"},
            "Управление автозагрузкой": {"en":"Manage startup apps","uk":"Керування автозапуском","de":"Autostart verwalten","it":"Gestisci app all'avvio","es":"Gestionar aplicaciones de inicio","fr":"Gérer les applications au démarrage"},
            "Безопасность": {"en":"Security","uk":"Безпека","de":"Sicherheit","it":"Sicurezza","es":"Seguridad","fr":"Sécurité"},
            "Проверить состояние системы": {"en":"Check system status","uk":"Перевірити стан системи","de":"Systemstatus prüfen","it":"Controlla lo stato del sistema","es":"Comprobar el estado del sistema","fr":"Vérifier l’état du système"},
            "Оптимизировать": {"en":"Optimize","uk":"Оптимізувати","de":"Optimieren","it":"Ottimizza","es":"Optimizar","fr":"Optimiser"},
            "Общая производительность": {"en":"Overall performance","uk":"Загальна продуктивність","de":"Gesamtleistung","it":"Prestazioni complessive","es":"Rendimiento general","fr":"Performances globales"},
            "Система работает\nстабильно": {"en":"System is working\nstably","uk":"Система працює\nстабільно","de":"System läuft\nstabil","it":"Il sistema funziona\nin modo stabile","es":"El sistema funciona\nde forma estable","fr":"Le système fonctionne\nstablement"},
            "Отлично": {"en":"Excellent","uk":"Відмінно","de":"Ausgezeichnet","it":"Eccellente","es":"Excelente","fr":"Excellent"},
            "Хорошо": {"en":"Good","uk":"Добре","de":"Gut","it":"Buono","es":"Bueno","fr":"Bon"},
            "Нормально": {"en":"Normal","uk":"Нормально","de":"Normal","it":"Normale","es":"Normal","fr":"Normal"},
            "Внимание": {"en":"Attention","uk":"Увага","de":"Achtung","it":"Attenzione","es":"Atención","fr":"Attention"},
            "Данные недоступны": {"en":"Data unavailable","uk":"Дані недоступні","de":"Daten nicht verfügbar","it":"Dati non disponibili","es":"Datos no disponibles","fr":"Données indisponibles"},
            "Диск": {"en":"Disk","uk":"Диск","de":"Datenträger","it":"Disco","es":"Disco","fr":"Disque"},
            "Настройки": {"en":"Settings","uk":"Налаштування","de":"Einstellungen","it":"Impostazioni","es":"Configuración","fr":"Paramètres"},
            "Настройки PC Control Center Pro": {"en":"PC Control Center Pro Settings","uk":"Налаштування PC Control Center Pro","de":"PC Control Center Pro Einstellungen","it":"Impostazioni di PC Control Center Pro","es":"Configuración de PC Control Center Pro","fr":"Paramètres de PC Control Center Pro"},
            "Мониторинг": {"en":"Monitoring","uk":"Моніторинг","de":"Überwachung","it":"Monitoraggio","es":"Monitorización","fr":"Surveillance"},
            "Обновление графиков": {"en":"Graph update interval","uk":"Інтервал оновлення графіків","de":"Aktualisierungsintervall der Diagramme","it":"Intervallo di aggiornamento dei grafici","es":"Intervalo de actualización de gráficos","fr":"Intervalle de mise à jour des graphiques"},
            "Язык": {"en":"Language","uk":"Мова","de":"Sprache","it":"Lingua","es":"Idioma","fr":"Langue"},
            "Русский": {"en":"Russian","uk":"Українська","de":"Deutsch","it":"Italiano","es":"Español","fr":"Français"},
            "Тема": {"en":"Theme","uk":"Тема","de":"Design","it":"Tema","es":"Tema","fr":"Thème"},
            "Тёмная": {"en":"Dark","uk":"Темна","de":"Dunkel","it":"Scuro","es":"Oscuro","fr":"Sombre"},
            "Светлая": {"en":"Light","uk":"Світла","de":"Hell","it":"Chiaro","es":"Claro","fr":"Clair"},
            "Системная": {"en":"System","uk":"Системна","de":"System","it":"Sistema","es":"Sistema","fr":"Système"},
            "Сохранение": {"en":"Saving","uk":"Збереження","de":"Speichern","it":"Salvataggio","es":"Guardado","fr":"Enregistrement"},
            "Автосохранение настроек": {"en":"Auto-save settings","uk":"Автозбереження налаштувань","de":"Einstellungen automatisch speichern","it":"Salvataggio automatico delle impostazioni","es":"Guardar ajustes automáticamente","fr":"Enregistrer automatiquement les paramètres"},
            "Сохранить": {"en":"Save","uk":"Зберегти","de":"Speichern","it":"Salva","es":"Guardar","fr":"Enregistrer"},
            "По умолчанию": {"en":"Defaults","uk":"За замовчуванням","de":"Standardwerte","it":"Predefiniti","es":"Predeterminados","fr":"Par défaut"},
            "Отмена": {"en":"Cancel","uk":"Скасувати","de":"Abbrechen","it":"Annulla","es":"Cancelar","fr":"Annuler"},
            "О программе": {"en":"About","uk":"Про програму","de":"Über das Programm","it":"Informazioni","es":"Acerca de","fr":"À propos"},
            "Закрыть": {"en":"Close","uk":"Закрити","de":"Schließen","it":"Chiudi","es":"Cerrar","fr":"Fermer"},
            "Раздел подготовлен для следующего этапа.": {"en":"This section is prepared for the next stage.","uk":"Цей розділ підготовлено для наступного етапу.","de":"Dieser Bereich ist für die nächste Phase vorbereitet.","it":"Questa sezione è pronta per la prossima fase.","es":"Esta sección está preparada para la siguiente etapa.","fr":"Cette section est prête pour l’étape suivante."},
            "Интервалы задаются в миллисекундах.\nМониторинг и графики настраиваются независимо.\nВсе изменения сохраняются в QSettings.": {"en":"Intervals are specified in milliseconds.\nMonitoring and graphs are configured independently.\nAll changes are saved to QSettings.","uk":"Інтервали задаються в мілісекундах.\nМоніторинг і графіки налаштовуються незалежно.\nУсі зміни зберігаються в QSettings.","de":"Intervalle werden in Millisekunden angegeben.\nÜberwachung und Diagramme werden unabhängig konfiguriert.\nAlle Änderungen werden in QSettings gespeichert.","it":"Gli intervalli sono espressi in millisecondi.\nMonitoraggio e grafici sono configurati separatamente.\nTutte le modifiche vengono salvate in QSettings.","es":"Los intervalos se especifican en milisegundos.\nLa monitorización y los gráficos se configuran por separado.\nTodos los cambios se guardan en QSettings.","fr":"Les intervalles sont indiqués en millisecondes.\nLa surveillance et les graphiques sont configurés séparément.\nToutes les modifications sont enregistrées dans QSettings."},
        }

        # Page-wide English translations for strings that are created by the
        # individual pages after the dashboard translation table was written.
        # The same entries also make dynamic values such as "Files: 12" work.
        page_en = {
            "Сеть":"Network", "Сетевые интерфейсы и подключение":"Network interfaces and connection",
            "Обновить":"Refresh", "Не определён":"Unknown", "Сетевые интерфейсы не найдены":"No network interfaces found",
            "● Неизвестно":"● Unknown", "● Включён":"● Enabled", "● Выключен":"● Disabled",
            "● Подключён":"● Connected", "● Отключён":"● Disconnected", "Подождите...":"Please wait...",
            "Изменение состояния Bluetooth...":"Changing Bluetooth state...", "Недоступно":"Unavailable",
            "Физический Bluetooth-адаптер не найден":"Physical Bluetooth adapter not found", "Повторить":"Retry",
            "Повторно определить состояние Bluetooth":"Detect Bluetooth state again", "Выключить":"Disable",
            "Выключить физический Bluetooth-адаптер":"Disable physical Bluetooth adapter", "Включить":"Enable",
            "Включить физический Bluetooth-адаптер":"Enable physical Bluetooth adapter",
            "Мониторинг":"Monitoring", "Мониторинг ресурсов компьютера в реальном времени":"Real-time computer resource monitoring",
            "Общая загрузка GPU":"Total GPU usage", "Декодирование видео":"Video decoding", "GPU вычисления":"GPU compute",
            "Текущая активность":"Current activity", "Скорость чтения":"Read speed", "Скорость записи":"Write speed",
            "Занято места":"Space used", "● Мониторинг активен":"● Monitoring active", "● GPU мониторинг активен":"● GPU monitoring active",
            "● Мониторинг GPU + Disk активен":"● GPU + Disk monitoring active",
            "Аппаратное обеспечение":"Hardware", "Информация о компонентах компьютера":"Computer component information",
            "Загрузка...":"Loading...", "Ожидание...":"Waiting...", "Определение GPU...":"Detecting GPU...",
            "Оптимизация":"Optimization", "Анализ состояния системы и безопасная оптимизация":"System health analysis and safe optimization",
            "⚡ Состояние системы":"⚡ System status", "🔍 Анализ":"🔍 Analysis", "Проверка системы...":"Checking system...",
            "🛠 Оптимизация":"🛠 Optimization", "Доступные операции будут выполняться только после подтверждения.":"Available operations will run only after confirmation.",
            "↻  Обновить анализ":"↻  Refresh analysis", "⚡  Быстрая оптимизация":"⚡  Quick optimization",
            "⌛  Сканирование...":"⌛  Scanning...", "Подтверждение оптимизации":"Optimization confirmation", "Продолжить?":"Continue?",
            "⌛  Очистка...":"⌛  Cleaning...", "Очистка системы":"System cleanup",
            "🧹  Очистка системы":"🧹  System cleanup", "Поиск временных файлов и безопасная очистка системы":"Find temporary files and safely clean the system",
            "Сканирование ещё не выполнялось":"No scan has been performed yet", "Файлы: —":"Files: —", "Папки: —":"Folders: —", "Объём: —":"Size: —", "Источники: —":"Sources: —",
            "🔍  Сканировать":"🔍  Scan", "🧹  Очистить":"🧹  Clean", "Сканировать":"Scan", "Очистить":"Clean",
            "Программа":"Program", "Источник":"Source", "Команда":"Command", "Тип":"Type", "Статус":"Status",
            "🔄  Обновить":"🔄  Refresh", "⛔  Отключить":"⛔  Disable", "✅  Включить":"✅  Enable",
            "🟢 Включено":"🟢 Enabled", "🔴 Отключено":"🔴 Disabled",
            "AI-помощник":"AI Assistant", "Интеллектуальный анализ состояния компьютера":"Intelligent computer health analysis",
            "Готов к анализу":"Ready for analysis", "Нажмите «Проанализировать ПК», чтобы проверить состояние системы.":"Click “Analyze PC” to check the system status.",
            "🤖 Проанализировать ПК":"🤖 Analyze PC", "Анализирую...":"Analyzing...", "Выполняется анализ...":"Analysis in progress...",
            "AI собирает информацию о состоянии компьютера.":"AI is collecting information about the computer.", "Выполняется анализ системы...":"System analysis in progress...",
            "Анализ завершён.":"Analysis completed.", "✓ Система работает нормально":"✓ System is working normally",
            "⚠ Требуется внимание":"⚠ Attention required", "✕ Обнаружена проблема":"✕ Problem detected", "✕ Ошибка анализа":"✕ Analysis error",
            "AI Assistant не смог выполнить анализ.":"AI Assistant could not complete the analysis.", "Состояние системы":"System status",
            "Рекомендации системы:":"System recommendations:", "Рекомендации AI:":"AI recommendations:", "Возможные причины":"Possible causes",
            "Рекомендация":"Recommendation", "Высокая нагрузка CPU":"High CPU load", "Высокое использование RAM":"High RAM usage",
            "На диске мало свободного места":"Low free disk space", "Критических проблем, требующих немедленной оптимизации, не обнаружено.":"No critical problems requiring immediate optimization were found.",
            "Временные файлы для удаления не найдены.":"No temporary files to delete were found.",
            "Автозагрузка":"Startup apps", "Безопасность":"Security", "Проверить":"Check", "Анализировать":"Analyze", "Открыть":"Open",
            "Системные инструменты":"System tools", "Откройте приложение ":"Open the application ", " вручную.":" manually.",
            "Повторно проверить":"Check again", "Последнее сканирование":"Last scan", "✓  Система защищена":"✓  System protected",
        }
        # Full translations for the individual application pages.
        # Dashboard already had its own translations; these entries cover
        # Monitoring, Hardware, Network, Optimize, Tools and AI Assistant.
        page_multi = {
            "Сеть": {"en":"Network","uk":"Мережа","de":"Netzwerk","it":"Rete","es":"Red","fr":"Réseau"},
            "Сетевые интерфейсы и подключение": {"en":"Network interfaces and connection","uk":"Мережеві інтерфейси та підключення","de":"Netzwerkschnittstellen und Verbindung","it":"Interfacce di rete e connessione","es":"Interfaces de red y conexión","fr":"Interfaces réseau et connexion"},
            "Обновить": {"en":"Refresh","uk":"Оновити","de":"Aktualisieren","it":"Aggiorna","es":"Actualizar","fr":"Actualiser"},
            "Не определён": {"en":"Unknown","uk":"Не визначено","de":"Unbekannt","it":"Sconosciuto","es":"Desconocido","fr":"Inconnu"},
            "Сетевые интерфейсы не найдены": {"en":"No network interfaces found","uk":"Мережеві інтерфейси не знайдено","de":"Keine Netzwerkschnittstellen gefunden","it":"Nessuna interfaccia di rete trovata","es":"No se encontraron interfaces de red","fr":"Aucune interface réseau trouvée"},
            "● Неизвестно": {"en":"● Unknown","uk":"● Невідомо","de":"● Unbekannt","it":"● Sconosciuto","es":"● Desconocido","fr":"● Inconnu"},
            "● Включён": {"en":"● Enabled","uk":"● Увімкнено","de":"● Aktiviert","it":"● Abilitato","es":"● Activado","fr":"● Activé"},
            "● Выключен": {"en":"● Disabled","uk":"● Вимкнено","de":"● Deaktiviert","it":"● Disabilitato","es":"● Desactivado","fr":"● Désactivé"},
            "● Подключён": {"en":"● Connected","uk":"● Підключено","de":"● Verbunden","it":"● Connesso","es":"● Conectado","fr":"● Connecté"},
            "● Отключён": {"en":"● Disconnected","uk":"● Відключено","de":"● Getrennt","it":"● Disconnesso","es":"● Desconectado","fr":"● Déconnecté"},
            "Подождите...": {"en":"Please wait...","uk":"Зачекайте...","de":"Bitte warten...","it":"Attendere...","es":"Espere...","fr":"Veuillez patienter..."},
            "Изменение состояния Bluetooth...": {"en":"Changing Bluetooth state...","uk":"Зміна стану Bluetooth...","de":"Bluetooth-Status wird geändert...","it":"Modifica dello stato Bluetooth...","es":"Cambiando el estado de Bluetooth...","fr":"Modification de l’état Bluetooth..."},
            "Недоступно": {"en":"Unavailable","uk":"Недоступно","de":"Nicht verfügbar","it":"Non disponibile","es":"No disponible","fr":"Indisponible"},
            "Физический Bluetooth-адаптер не найден": {"en":"Physical Bluetooth adapter not found","uk":"Фізичний Bluetooth-адаптер не знайдено","de":"Physischer Bluetooth-Adapter nicht gefunden","it":"Adattatore Bluetooth fisico non trovato","es":"No se encontró el adaptador Bluetooth físico","fr":"Adaptateur Bluetooth physique introuvable"},
            "Повторить": {"en":"Retry","uk":"Повторити","de":"Erneut versuchen","it":"Riprova","es":"Reintentar","fr":"Réessayer"},
            "Повторно определить состояние Bluetooth": {"en":"Detect Bluetooth state again","uk":"Повторно визначити стан Bluetooth","de":"Bluetooth-Status erneut erkennen","it":"Rileva nuovamente lo stato Bluetooth","es":"Detectar de nuevo el estado de Bluetooth","fr":"Détecter à nouveau l’état Bluetooth"},
            "Выключить": {"en":"Disable","uk":"Вимкнути","de":"Deaktivieren","it":"Disabilita","es":"Desactivar","fr":"Désactiver"},
            "Включить": {"en":"Enable","uk":"Увімкнути","de":"Aktivieren","it":"Abilita","es":"Activar","fr":"Activer"},
            "Мониторинг ресурсов компьютера в реальном времени": {"en":"Real-time computer resource monitoring","uk":"Моніторинг ресурсів комп’ютера в реальному часі","de":"Echtzeitüberwachung der Computerressourcen","it":"Monitoraggio delle risorse del computer in tempo reale","es":"Monitorización de recursos del ordenador en tiempo real","fr":"Surveillance des ressources de l’ordinateur en temps réel"},
            "Общая загрузка GPU": {"en":"Total GPU usage","uk":"Загальне використання GPU","de":"Gesamtauslastung der GPU","it":"Utilizzo totale della GPU","es":"Uso total de la GPU","fr":"Utilisation totale du GPU"},
            "Декодирование видео": {"en":"Video decoding","uk":"Декодування відео","de":"Videodekodierung","it":"Decodifica video","es":"Decodificación de vídeo","fr":"Décodage vidéo"},
            "GPU вычисления": {"en":"GPU compute","uk":"Обчислення GPU","de":"GPU-Berechnung","it":"Calcolo GPU","es":"Cómputo de GPU","fr":"Calcul GPU"},
            "Текущая активность": {"en":"Current activity","uk":"Поточна активність","de":"Aktuelle Aktivität","it":"Attività corrente","es":"Actividad actual","fr":"Activité actuelle"},
            "Скорость чтения": {"en":"Read speed","uk":"Швидкість читання","de":"Lesegeschwindigkeit","it":"Velocità di lettura","es":"Velocidad de lectura","fr":"Vitesse de lecture"},
            "Скорость записи": {"en":"Write speed","uk":"Швидкість запису","de":"Schreibgeschwindigkeit","it":"Velocità di scrittura","es":"Velocidad de escritura","fr":"Vitesse d’écriture"},
            "Занято места": {"en":"Space used","uk":"Зайнято місця","de":"Belegter Speicherplatz","it":"Spazio utilizzato","es":"Espacio utilizado","fr":"Espace utilisé"},
            "● Мониторинг активен": {"en":"● Monitoring active","uk":"● Моніторинг активний","de":"● Überwachung aktiv","it":"● Monitoraggio attivo","es":"● Monitorización activa","fr":"● Surveillance active"},
            "● GPU мониторинг активен": {"en":"● GPU monitoring active","uk":"● Моніторинг GPU активний","de":"● GPU-Überwachung aktiv","it":"● Monitoraggio GPU attivo","es":"● Monitorización de GPU activa","fr":"● Surveillance du GPU active"},
            "● Мониторинг GPU + Disk активен": {"en":"● GPU + Disk monitoring active","uk":"● Моніторинг GPU + Disk активний","de":"● GPU- und Datenträgerüberwachung aktiv","it":"● Monitoraggio GPU + disco attivo","es":"● Monitorización de GPU + disco activa","fr":"● Surveillance GPU + disque active"},
            "Аппаратное обеспечение": {"en":"Hardware","uk":"Обладнання","de":"Hardware","it":"Hardware","es":"Hardware","fr":"Matériel"},
            "Информация о компонентах компьютера": {"en":"Computer component information","uk":"Інформація про компоненти комп’ютера","de":"Informationen zu Computerkomponenten","it":"Informazioni sui componenti del computer","es":"Información de los componentes del ordenador","fr":"Informations sur les composants de l’ordinateur"},
            "Загрузка...": {"en":"Loading...","uk":"Завантаження...","de":"Wird geladen...","it":"Caricamento...","es":"Cargando...","fr":"Chargement..."},
            "Ожидание...": {"en":"Waiting...","uk":"Очікування...","de":"Warten...","it":"In attesa...","es":"Esperando...","fr":"En attente..."},
            "Определение GPU...": {"en":"Detecting GPU...","uk":"Визначення GPU...","de":"GPU wird erkannt...","it":"Rilevamento GPU...","es":"Detectando GPU...","fr":"Détection du GPU..."},
            "Оптимизация": {"en":"Optimization","uk":"Оптимізація","de":"Optimierung","it":"Ottimizzazione","es":"Optimización","fr":"Optimisation"},
            "Анализ состояния системы и безопасная оптимизация": {"en":"System health analysis and safe optimization","uk":"Аналіз стану системи та безпечна оптимізація","de":"Systemanalyse und sichere Optimierung","it":"Analisi dello stato del sistema e ottimizzazione sicura","es":"Análisis del estado del sistema y optimización segura","fr":"Analyse de l’état du système et optimisation sécurisée"},
            "⚡ Состояние системы": {"en":"⚡ System status","uk":"⚡ Стан системи","de":"⚡ Systemstatus","it":"⚡ Stato del sistema","es":"⚡ Estado del sistema","fr":"⚡ État du système"},
            "🔍 Анализ": {"en":"🔍 Analysis","uk":"🔍 Аналіз","de":"🔍 Analyse","it":"🔍 Analisi","es":"🔍 Análisis","fr":"🔍 Analyse"},
            "Проверка системы...": {"en":"Checking system...","uk":"Перевірка системи...","de":"System wird geprüft...","it":"Controllo del sistema...","es":"Comprobando el sistema...","fr":"Vérification du système..."},
            "🛠 Оптимизация": {"en":"🛠 Optimization","uk":"🛠 Оптимізація","de":"🛠 Optimierung","it":"🛠 Ottimizzazione","es":"🛠 Optimización","fr":"🛠 Optimisation"},
            "Доступные операции будут выполняться только после подтверждения.": {"en":"Available operations will run only after confirmation.","uk":"Доступні операції виконуватимуться лише після підтвердження.","de":"Verfügbare Vorgänge werden erst nach Bestätigung ausgeführt.","it":"Le operazioni disponibili verranno eseguite solo dopo la conferma.","es":"Las operaciones disponibles se ejecutarán solo después de la confirmación.","fr":"Les opérations disponibles ne seront exécutées qu’après confirmation."},
            "↻  Обновить анализ": {"en":"↻  Refresh analysis","uk":"↻  Оновити аналіз","de":"↻  Analyse aktualisieren","it":"↻  Aggiorna analisi","es":"↻  Actualizar análisis","fr":"↻  Actualiser l’analyse"},
            "⚡  Быстрая оптимизация": {"en":"⚡  Quick optimization","uk":"⚡  Швидка оптимізація","de":"⚡  Schnelloptimierung","it":"⚡  Ottimizzazione rapida","es":"⚡  Optimización rápida","fr":"⚡  Optimisation rapide"},
            "⌛  Сканирование...": {"en":"⌛  Scanning...","uk":"⌛  Сканування...","de":"⌛  Scan läuft...","it":"⌛  Scansione...","es":"⌛  Escaneando...","fr":"⌛  Analyse..."},
            "Подтверждение оптимизации": {"en":"Optimization confirmation","uk":"Підтвердження оптимізації","de":"Optimierungsbestätigung","it":"Conferma dell’ottimizzazione","es":"Confirmación de optimización","fr":"Confirmation de l’optimisation"},
            "Продолжить?": {"en":"Continue?","uk":"Продовжити?","de":"Fortfahren?","it":"Continuare?","es":"¿Continuar?","fr":"Continuer ?"},
            "⌛  Очистка...": {"en":"⌛  Cleaning...","uk":"⌛  Очищення...","de":"⌛  Bereinigung...","it":"⌛  Pulizia...","es":"⌛  Limpiando...","fr":"⌛  Nettoyage..."},
            "Очистка системы": {"en":"System cleanup","uk":"Очищення системи","de":"Systembereinigung","it":"Pulizia del sistema","es":"Limpieza del sistema","fr":"Nettoyage du système"},
            "🧹  Очистка системы": {"en":"🧹  System cleanup","uk":"🧹  Очищення системи","de":"🧹  Systembereinigung","it":"🧹  Pulizia del sistema","es":"🧹  Limpieza del sistema","fr":"🧹  Nettoyage du système"},
            "Поиск временных файлов и безопасная очистка системы": {"en":"Find temporary files and safely clean the system","uk":"Пошук тимчасових файлів та безпечне очищення системи","de":"Temporäre Dateien finden und das System sicher bereinigen","it":"Trova i file temporanei e pulisci il sistema in modo sicuro","es":"Buscar archivos temporales y limpiar el sistema de forma segura","fr":"Rechercher les fichiers temporaires et nettoyer le système en toute sécurité"},
            "Сканирование ещё не выполнялось": {"en":"No scan has been performed yet","uk":"Сканування ще не виконувалося","de":"Noch kein Scan durchgeführt","it":"Nessuna scansione eseguita","es":"Aún no se ha realizado ningún análisis","fr":"Aucune analyse n’a encore été effectuée"},
            "Файлы: —": {"en":"Files: —","uk":"Файли: —","de":"Dateien: —","it":"File: —","es":"Archivos: —","fr":"Fichiers : —"},
            "Папки: —": {"en":"Folders: —","uk":"Папки: —","de":"Ordner: —","it":"Cartelle: —","es":"Carpetas: —","fr":"Dossiers : —"},
            "Объём: —": {"en":"Size: —","uk":"Обсяг: —","de":"Größe: —","it":"Dimensione: —","es":"Tamaño: —","fr":"Taille : —"},
            "Источники: —": {"en":"Sources: —","uk":"Джерела: —","de":"Quellen: —","it":"Origini: —","es":"Fuentes: —","fr":"Sources : —"},
            "🔍  Сканировать": {"en":"🔍  Scan","uk":"🔍  Сканувати","de":"🔍  Scannen","it":"🔍  Scansiona","es":"🔍  Escanear","fr":"🔍  Analyser"},
            "🧹  Очистить": {"en":"🧹  Clean","uk":"🧹  Очистити","de":"🧹  Bereinigen","it":"🧹  Pulisci","es":"🧹  Limpiar","fr":"🧹  Nettoyer"},
            "Сканировать": {"en":"Scan","uk":"Сканувати","de":"Scannen","it":"Scansiona","es":"Escanear","fr":"Analyser"},
            "Очистить": {"en":"Clean","uk":"Очистити","de":"Bereinigen","it":"Pulisci","es":"Limpiar","fr":"Nettoyer"},
            "Программа": {"en":"Program","uk":"Програма","de":"Programm","it":"Programma","es":"Programa","fr":"Programme"},
            "Источник": {"en":"Source","uk":"Джерело","de":"Quelle","it":"Origine","es":"Origen","fr":"Source"},
            "Команда": {"en":"Command","uk":"Команда","de":"Befehl","it":"Comando","es":"Comando","fr":"Commande"},
            "Тип": {"en":"Type","uk":"Тип","de":"Typ","it":"Tipo","es":"Tipo","fr":"Type"},
            "Статус": {"en":"Status","uk":"Статус","de":"Status","it":"Stato","es":"Estado","fr":"État"},
            "🔄  Обновить": {"en":"🔄  Refresh","uk":"🔄  Оновити","de":"🔄  Aktualisieren","it":"🔄  Aggiorna","es":"🔄  Actualizar","fr":"🔄  Actualiser"},
            "⛔  Отключить": {"en":"⛔  Disable","uk":"⛔  Вимкнути","de":"⛔  Deaktivieren","it":"⛔  Disabilita","es":"⛔  Desactivar","fr":"⛔  Désactiver"},
            "✅  Включить": {"en":"✅  Enable","uk":"✅  Увімкнути","de":"✅  Aktivieren","it":"✅  Abilita","es":"✅  Activar","fr":"✅  Activer"},
            "🟢 Включено": {"en":"🟢 Enabled","uk":"🟢 Увімкнено","de":"🟢 Aktiviert","it":"🟢 Abilitato","es":"🟢 Activado","fr":"🟢 Activé"},
            "🔴 Отключено": {"en":"🔴 Disabled","uk":"🔴 Вимкнено","de":"🔴 Deaktiviert","it":"🔴 Disabilitato","es":"🔴 Desactivado","fr":"🔴 Désactivé"},
            "AI-помощник": {"en":"AI Assistant","uk":"AI-помічник","de":"KI-Assistent","it":"Assistente AI","es":"Asistente de IA","fr":"Assistant IA"},
            "Интеллектуальный анализ состояния компьютера": {"en":"Intelligent computer health analysis","uk":"Інтелектуальний аналіз стану комп’ютера","de":"Intelligente Analyse des Computerzustands","it":"Analisi intelligente dello stato del computer","es":"Análisis inteligente del estado del ordenador","fr":"Analyse intelligente de l’état de l’ordinateur"},
            "Готов к анализу": {"en":"Ready for analysis","uk":"Готовий до аналізу","de":"Bereit zur Analyse","it":"Pronto per l’analisi","es":"Listo para el análisis","fr":"Prêt pour l’analyse"},
            "Анализ завершён.": {"en":"Analysis completed.","uk":"Аналіз завершено.","de":"Analyse abgeschlossen.","it":"Analisi completata.","es":"Análisis completado.","fr":"Analyse terminée."},
            "✓ Система работает нормально": {"en":"✓ System is working normally","uk":"✓ Система працює нормально","de":"✓ System funktioniert normal","it":"✓ Il sistema funziona normalmente","es":"✓ El sistema funciona con normalidad","fr":"✓ Le système fonctionne normalement"},
            "⚠ Требуется внимание": {"en":"⚠ Attention required","uk":"⚠ Потрібна увага","de":"⚠ Aufmerksamkeit erforderlich","it":"⚠ È necessaria attenzione","es":"⚠ Atención requerida","fr":"⚠ Attention requise"},
            "✕ Обнаружена проблема": {"en":"✕ Problem detected","uk":"✕ Виявлено проблему","de":"✕ Problem erkannt","it":"✕ Problema rilevato","es":"✕ Problema detectado","fr":"✕ Problème détecté"},
            "Состояние системы": {"en":"System status","uk":"Стан системи","de":"Systemstatus","it":"Stato del sistema","es":"Estado del sistema","fr":"État du système"},
            "Рекомендации системы:": {"en":"System recommendations:","uk":"Рекомендації системи:","de":"Systemempfehlungen:","it":"Raccomandazioni di sistema:","es":"Recomendaciones del sistema:","fr":"Recommandations du système :"},
            "Возможные причины": {"en":"Possible causes","uk":"Можливі причини","de":"Mögliche Ursachen","it":"Possibili cause","es":"Posibles causas","fr":"Causes possibles"},
            "Рекомендации AI:": {"en":"AI recommendations:","uk":"Рекомендації AI:","de":"KI-Empfehlungen:","it":"Raccomandazioni AI:","es":"Recomendaciones de IA:","fr":"Recommandations de l’IA :"},
            "Рекомендация": {"en":"Recommendation","uk":"Рекомендація","de":"Empfehlung","it":"Raccomandazione","es":"Recomendación","fr":"Recommandation"},
            "Высокая нагрузка CPU": {"en":"High CPU load","uk":"Високе навантаження CPU","de":"Hohe CPU-Auslastung","it":"Elevato utilizzo della CPU","es":"Alta carga de CPU","fr":"Forte charge CPU"},
            "Высокое использование RAM": {"en":"High RAM usage","uk":"Високе використання RAM","de":"Hoher RAM-Verbrauch","it":"Elevato utilizzo della RAM","es":"Alto uso de RAM","fr":"Forte utilisation de la RAM"},
            "На диске мало свободного места": {"en":"Low free disk space","uk":"Мало вільного місця на диску","de":"Wenig freier Speicherplatz","it":"Poco spazio libero sul disco","es":"Poco espacio libre en el disco","fr":"Peu d’espace disque libre"},
            "Автозагрузка": {"en":"Startup apps","uk":"Автозапуск","de":"Autostart","it":"Avvio automatico","es":"Aplicaciones de inicio","fr":"Applications au démarrage"},
            "Безопасность": {"en":"Security","uk":"Безпека","de":"Sicherheit","it":"Sicurezza","es":"Seguridad","fr":"Sécurité"},
            "Проверить": {"en":"Check","uk":"Перевірити","de":"Prüfen","it":"Controlla","es":"Comprobar","fr":"Vérifier"},
            "Анализировать": {"en":"Analyze","uk":"Аналізувати","de":"Analysieren","it":"Analizza","es":"Analizar","fr":"Analyser"},
            "Открыть": {"en":"Open","uk":"Відкрити","de":"Öffnen","it":"Apri","es":"Abrir","fr":"Ouvrir"},
            "Системные инструменты": {"en":"System tools","uk":"Системні інструменти","de":"Systemwerkzeuge","it":"Strumenti di sistema","es":"Herramientas del sistema","fr":"Outils système"},
            "Повторно проверить": {"en":"Check again","uk":"Перевірити ще раз","de":"Erneut prüfen","it":"Controlla di nuovo","es":"Comprobar de nuevo","fr":"Vérifier à nouveau"},
            "Последнее сканирование": {"en":"Last scan","uk":"Останнє сканування","de":"Letzter Scan","it":"Ultima scansione","es":"Último análisis","fr":"Dernière analyse"},
            "✓  Система защищена": {"en":"✓  System protected","uk":"✓  Система захищена","de":"✓  System geschützt","it":"✓  Sistema protetto","es":"✓  Sistema protegido","fr":"✓  Système protégé"},
        }
        T.update(page_multi)

        # ????????? ?????? ??????? ????????? ??? ????????????? ??????????.
        self._language_translations = T

        for ru_text, en_text in page_en.items():
            T.setdefault(ru_text, {"en": en_text, "uk": ru_text, "de": ru_text, "it": ru_text, "es": ru_text, "fr": ru_text})

        # Build a reverse index so switching works from any currently displayed language.
        mapping = {}
        for ru_text, variants in T.items():
            mapping[ru_text] = variants.get(language, ru_text)
            for code, translated in variants.items():
                mapping[translated] = variants.get(language, ru_text)

        self._language_mapping = mapping

        # DEBUG: ????????? ???????? ????????????? ???????? ? ??????????.
        translated_count = 0
        missed_count = 0

        # ???????? ????????? ???? ??????? ??????????????.
        # ?????????? ??????? MainWindow ?? ?????? ?????? ?? ?????.
        managed_pages = set()

        for page in getattr(self, "pages", ()):
            if page is not None:
                managed_pages.add(page)

        dashboard = getattr(self, "dashboard", None)
        if dashboard is not None:
            managed_pages.add(dashboard)

        for widget in [self] + self.findChildren(QWidget):
            try:
                if not isinstance(widget, (QLabel, QPushButton)):
                    continue

                # ?????????, ??????????? ?? ?????? ????? ?? ???????.
                parent = widget
                skip = False

                while parent is not None:
                    if parent in managed_pages:
                        skip = True
                        break

                    parent = (
                        parent.parentWidget()
                        if hasattr(parent, "parentWidget")
                        else None
                    )

                if skip:
                    continue

                current_text = widget.text()

                # ?????????? ???????? ????.
                source = widget.property("_translation_source")

                # ???? ???? ??? ?? ??????????, ?????????? ???
                # ?? ?????? ??????? ?????????.
                if not source:
                    for ru_text, variants in T.items():
                        if current_text == ru_text:
                            source = ru_text
                            break

                        if current_text in variants.values():
                            source = ru_text
                            break

                    if source:
                        widget.setProperty(
                            "_translation_source",
                            source
                        )

                if not source:
                    continue

                variants = T.get(source)
                if not variants:
                    continue

                new_text = variants.get(language, source)

                if new_text != current_text:
                    translated_count += 1
                    widget.setText(new_text)

            except RuntimeError:
                pass

        print(
            f"[LANG][GLOBAL] language={language} "
            f"translated={translated_count} missed={missed_count}"
        )

        for index in range(self.menu.count()):
            item = self.menu.item(index)
            text = item.text()
            if text in mapping:
                item.setText(mapping[text])

        # Language selector itself uses native language names.
        for combo in self.findChildren(QComboBox):
            if combo.count() == 7 and combo.findText("Русский") >= 0:
                current_code = combo.currentData()
                combo.blockSignals(True)
                combo.clear()
                for label, code in [("Русский","ru"),("English","en"),("Українська","uk"),("Deutsch","de"),("Italiano","it"),("Español","es"),("Français","fr")]:
                    combo.addItem(label, code)
                idx = combo.findData(current_code or language)
                combo.setCurrentIndex(max(0, idx))
                combo.blockSignals(False)

        # ????????? ????????? ???? ?? ???? ?????????.
        for page in getattr(self, "pages", ()):
            try:
                if hasattr(page, "set_language"):
                    page.set_language(language)
            except Exception as exc:
                print(
                    "[MainWindow] Language update error:",
                    type(page).__name__,
                    exc
                )

        self._settings.sync()

    def _refresh_language_widgets(self):
        """????????? ????????? ?????? ??????????? ??????? MainWindow."""
        translations = getattr(self, "_language_translations", {})
        language = getattr(self, "_language", "ru")

        if not translations:
            return

        try:
            # ???????? ????????? ???? ??????? ??????????????.
            # MainWindow ???? ?? ???????????.
            managed_pages = set()

            for page in getattr(self, "pages", ()):
                if page is not None:
                    managed_pages.add(page)

            dashboard = getattr(self, "dashboard", None)
            if dashboard is not None:
                managed_pages.add(dashboard)

            for widget in [self] + self.findChildren(QWidget):
                try:
                    if not isinstance(widget, (QLabel, QPushButton)):
                        continue

                    # ?????????? ??? ???????, ????????????? ?????????.
                    parent = widget
                    skip = False

                    while parent is not None:
                        if parent in managed_pages:
                            skip = True
                            break

                        parent = (
                            parent.parentWidget()
                            if hasattr(parent, "parentWidget")
                            else None
                        )

                    if skip:
                        continue

                    current_text = widget.text()

                    # ?????????? ??????? ???? ???????.
                    source = widget.property("_translation_source")

                    # ???? ???? ??? ?? ???????? ? ?????????? ???
                    # ?? ?????? ??????? ?????????.
                    if not source:
                        for ru_text, variants in translations.items():
                            if current_text == ru_text:
                                source = ru_text
                                break

                            if current_text in variants.values():
                                source = ru_text
                                break

                        if source:
                            widget.setProperty(
                                "_translation_source",
                                source
                            )

                    if not source:
                        continue

                    variants = translations.get(source)
                    if not variants:
                        continue

                    new_text = variants.get(language, source)

                    if new_text != current_text:
                        widget.setText(new_text)

                except RuntimeError:
                    pass

        except RuntimeError:
            pass

    def show_about(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("О программе")
        dialog.setFixedSize(520, 330)

        light = bool(getattr(self, "_light_theme", False))
        if light:
            dialog.setStyleSheet("""
                QDialog { background:#ffffff; color:#172033; }
                QLabel { color:#172033; background:transparent; }
                QPushButton {
                    background:#168cff; color:#ffffff; border:none;
                    border-radius:8px; padding:9px 18px; font-weight:700;
                }
                QPushButton:hover { background:#2698ff; color:#ffffff; }
                QPushButton:pressed { background:#0f75d5; color:#ffffff; }
            """)
        else:
            dialog.setStyleSheet("""
                QDialog { background:#091528; color:#f4f7ff; }
                QLabel { color:#f4f7ff; background:transparent; }
                QPushButton {
                    background:#168cff; color:#ffffff; border:none;
                    border-radius:8px; padding:9px 18px; font-weight:700;
                }
                QPushButton:hover { background:#2698ff; }
                QPushButton:pressed { background:#0f75d5; }
            """)

        lay = QVBoxLayout(dialog)
        title = QLabel("PC Control Center Pro")
        title.setStyleSheet("font-size:24px;font-weight:900;color:#168cff;background:transparent;")
        lay.addWidget(title)
        version = QLabel("Dashboard 2.0")
        version.setStyleSheet("font-size:16px;font-weight:700;background:transparent;")
        lay.addWidget(version)
        text = QLabel("Центр управления и мониторинга Windows.\n\nМониторинг CPU, RAM, GPU, диска и сети,\nуправление Bluetooth, инструменты оптимизации и AI Assistant.")
        text.setWordWrap(True)
        lay.addWidget(text)
        lay.addStretch()
        close = QPushButton("Закрыть")
        close.clicked.connect(dialog.accept)
        lay.addWidget(close)
        dialog.exec()

    def _apply_theme_to_widget_tree(self, light):
        """Перекрашивает уже созданные страницы, включая локальные QSS."""
        # Full light-theme palette.  The source files intentionally keep their
        # dark QSS so dark mode remains unchanged; here we translate every
        # known dark surface/text token to the light design.
        dark_to_light = {
            # application/page surfaces
            "#050b18": "#f5f7fb",
            "#070b1a": "#f5f7fb",
            "#071020": "#f8fafc",
            "#091528": "#ffffff",
            "#0a1322": "#f1f5f9",
            "#0a1326": "#f1f5f9",
            "#0a1428": "#ffffff",
            "#0d162b": "#ffffff",
            "#0d1a31": "#f8fafc",
            "#0d1d34": "#f1f5f9",
            "#10203a": "#168cff",
            "#10233f": "#eef6ff",
            "#111827": "#ffffff",
            "#111d32": "#f8fafc",
            "#12243d": "#0f75d5",
            "#152642": "#e2e8f0",
            "#162945": "#dbe4ee",
            "#172235": "#f8fafc",
            "#182c4a": "#d4dee9",
            "#1a2d49": "#d8e1eb",
            "#1b2b47": "#d7e1eb",
            "#1b3154": "#e5edf6",
            "#1d3152": "#d6e0ea",
            "#214267": "#bfd0e2",
            "#263750": "#d5e0eb",
            "#284466": "#cbd5e1",
            "#0a1730": "#ffffff",
            # common text tokens
            "#f4f7ff": "#172033",
            "#f8fafc": "#172033",
            "#8ea3bd": "#64748b",
            "#8fa2bf": "#64748b",
            "#9096a3": "#64748b",
            "#718096": "#64748b",
            "#71839f": "#64748b",
            "#657895": "#64748b",
            "#52657e": "#64748b",
            "#aebbd0": "#52657a",
        }
        light_to_dark = {v: k for k, v in dark_to_light.items()}

        widgets = [self] + self.findChildren(QWidget)
        for widget in widgets:
            original = widget.property("_pcc_original_qss")
            if original is None:
                original = widget.styleSheet()
                widget.setProperty("_pcc_original_qss", original)

            if not original:
                continue

            if light:
                qss = original
                for old, new in dark_to_light.items():
                    qss = qss.replace(old, new)
            else:
                qss = original

            # Navigation buttons use a blue hover in light mode, never black.
            if light and isinstance(widget, QPushButton):
                qss = qss.replace("background:#e7edf5", "background:#168cff")
                qss = qss.replace("background: #e7edf5", "background: #168cff")
                if "QPushButton:hover" in qss and "color:" not in qss.split("QPushButton:hover", 1)[1].split("}", 1)[0]:
                    qss = qss.replace("QPushButton:hover {{", "QPushButton:hover {{ color:white;")
            if qss != widget.styleSheet():
                widget.setStyleSheet(qss)

    def set_theme(self, light):
        self._light_theme = bool(light)

        # Update colors used directly by QPainter-based dashboard widgets.
        try:
            import app.widgets.dashboard_widgets as dw
            dw.LIGHT_THEME = self._light_theme
            dw.BG_CARD = "#ffffff" if self._light_theme else "#0a1428"
            dw.BG_CARD_2 = "#f8fafc" if self._light_theme else "#0d1a31"
            dw.BORDER = "#d6e0ea" if self._light_theme else "#1d3152"
            dw.TEXT = "#172033" if self._light_theme else "#f4f7ff"
            dw.MUTED = "#64748b" if self._light_theme else "#8ea3bd"
            dw.GRID = "#d8e1eb" if self._light_theme else "#1a2d49"
        except Exception as exc:
            print(f"[MainWindow] Theme widget palette update failed: {exc}")

        # Remember the original QSS before applying theme substitutions.
        self._apply_theme_to_widget_tree(self._light_theme)
        language = str(
            getattr(self, "_language", "ru")
        ).lower()

        theme_dark = {
            "ru": "Тёмная тема",
            "uk": "Темна тема",
            "en": "Dark theme",
            "de": "Dunkles Design",
            "it": "Tema scuro",
            "es": "Tema oscuro",
            "fr": "Thème sombre",
        }

        theme_light = {
            "ru": "Светлая тема",
            "uk": "Світла тема",
            "en": "Light theme",
            "de": "Helles Design",
            "it": "Tema chiaro",
            "es": "Tema claro",
            "fr": "Thème clair",
        }
        # Dashboard AI helper has its own local QSS and must receive the theme too.
        # Without this call its original dark bubble/card remains visible in Light mode.
        if hasattr(self, "dashboard") and hasattr(self.dashboard, "set_theme"):
            self.dashboard.set_theme(self._light_theme)

        # Full AI Assistant page also has its own local QSS.
        if hasattr(self, "ai_assistant") and hasattr(self.ai_assistant, "set_theme"):
            self.ai_assistant.set_theme(self._light_theme)

        # MonitoringPage previously contained a permanently light palette.
        # Keep its cards consistent with the selected global theme.
        if hasattr(self, "monitoring") and hasattr(self.monitoring, "set_theme"):
            self.monitoring.set_theme(self._light_theme)

        if hasattr(self, "tools") and hasattr(self.tools, "set_theme"):
            self.tools.set_theme(self._light_theme)
            

        if self._light_theme:
            self.setStyleSheet("""
                QMainWindow, QWidget { background:#eef3f8; color:#172033; }
                QDialog { background:#ffffff; color:#172033; }
                QLabel { color:#172033; }
                QCheckBox { color:#172033; }
                QComboBox, QSpinBox, QLineEdit {
                    background:#ffffff; color:#172033;
                    border:1px solid #cbd5e1; border-radius:7px; padding:7px;
                }
                QComboBox QAbstractItemView {
                    background:#ffffff; color:#172033;
                    selection-background-color:#dbeafe; selection-color:#172033;
                    border:1px solid #cbd5e1;
                }
                QToolTip { background:#ffffff; color:#172033; border:1px solid #cbd5e1; }
            """)
            self.sidebar.setStyleSheet("""
                QFrame { background:#f7f9fc; border-right:1px solid #dbe3ec; }
            """)
            # Every sidebar control gets its own light stylesheet because child widgets
            # may have hard-coded dark QSS from the original dark design.
            for button in (self.sidebar.settings_button, self.sidebar.about_button, self.sidebar.theme_button):
                button.setStyleSheet("""
                    QPushButton { background:transparent; color:#52657a; border:1px solid transparent;
                                  border-radius:9px; padding:9px 12px; text-align:left; }
                    QPushButton:hover { background:#168cff; color:#ffffff; border-color:#168cff; }
                    QPushButton:pressed { background:#0f75d5; color:#ffffff; border-color:#0f75d5; }
                """)
            for label in self.sidebar.findChildren(QLabel):
                label.setStyleSheet("color:#172033;background:transparent;border:none;")
            self.sidebar.theme_button.setText(
                f"☾  {theme_dark.get(language, theme_dark['ru'])}"
            )
            # Navigation: white surface, blue selection and blue hover — never black.
            self.menu.setStyleSheet("""
                QListWidget { background:#f7f9fc; border:none; color:#172033; outline:none; }
                QListWidget::item { color:#172033; background:transparent; padding:11px 14px; margin:2px 6px; border-radius:10px; }
                QListWidget::item:hover { background:#168cff; color:#ffffff; }
                QListWidget::item:selected { background:#168cff; color:#ffffff; border-left:3px solid #22d3ee; font-weight:800; }
            """)
        else:
            self.setStyleSheet(f"QMainWindow{{background:{BG};}} QWidget{{background:{BG};color:{TEXT};}}")
            self.sidebar.setStyleSheet(f"QFrame{{background:{SIDEBAR};border-right:1px solid #152642;}}")
            self.sidebar.theme_button.setText(
                f"☼  {theme_light.get(language, theme_light['ru'])}"
            )

        # Repaint custom-drawn gauges/graphs immediately after a theme switch.
        for widget in self.findChildren(QWidget):
            try:
                widget.update()
            except Exception:
                pass

    def toggle_theme(self):
        self.set_theme(not self._light_theme)

    @staticmethod
    def _open_uri(uri):
        try:
            subprocess.Popen(["explorer.exe", uri], creationflags=subprocess.CREATE_NO_WINDOW)
        except Exception as exc:
            print(f"[MainWindow] Cannot open Windows settings: {exc}")

    def open_wifi_settings(self):
        print("[MainWindow] Opening Wi-Fi settings")
        self._open_uri("ms-settings:network-wifi")

    def open_sound_settings(self):
        print("[MainWindow] Opening sound settings")
        self._open_uri("ms-settings:sound")

    def open_extra_tools(self):
        print("[MainWindow] Opening Windows system settings")
        self._open_uri("ms-settings:about")

    # ==========================================================
    # CENTER
    # ==========================================================

    def _center(self):

        try:

            screen = self.screen()

            if screen:

                self.move(
                    screen.availableGeometry().center()
                    - self.frameGeometry().center()
                )

        except Exception:
            pass

    # ==========================================================
    # CLOSE
    # ==========================================================

    def closeEvent(
        self,
        event,
    ):

        if self._closing:

            event.accept()

            return

        self._closing = True

        print(
            "[MainWindow] Closing started"
        )
    def closeEvent(self, event):
        import traceback

        print("\n" + "=" * 70)
        print("[MainWindow] CLOSE CALL STACK")
        print("=" * 70)
        traceback.print_stack()
        print("=" * 70 + "\n")

        super().closeEvent(event)

        # ----------------------------------------------------------
        # STOP TOP BAR TIMER
        # ----------------------------------------------------------

        try:

            if (
                hasattr(
                    self,
                    "top_timer",
                )
                and self.top_timer is not None
            ):

                self.top_timer.stop()

        except Exception as exc:

            print(
                "[MainWindow] "
                f"Top timer shutdown error: {exc}"
            )

        # ----------------------------------------------------------
        # STOP BACKGROUND PAGES
        # ----------------------------------------------------------

        pages = (
            getattr(
                self,
                "monitoring",
                None,
            ),
            getattr(
                self,
                "dashboard",
                None,
            ),
        )

        for page in pages:

            if page is None:
                continue

            try:

                shutdown = getattr(
                    page,
                    "shutdown",
                    None,
                )

                if shutdown is not None:

                    print(
                        "[MainWindow] "
                        f"Shutting down "
                        f"{page.__class__.__name__}"
                    )

                    shutdown()

            except Exception as exc:

                print(
                    "[MainWindow] "
                    f"Shutdown error "
                    f"{page.__class__.__name__}: "
                    f"{exc}"
                )

        # ----------------------------------------------------------
        # PROCESS QUEUED QT EVENTS
        # ----------------------------------------------------------

        QApplication.processEvents()

        # ----------------------------------------------------------
        # STOP GPU WORKER
        # ----------------------------------------------------------

        try:

            if (
                hasattr(
                    self,
                    "gpu_worker",
                )
                and self.gpu_worker is not None
                and self.gpu_worker.isRunning()
            ):

                print(
                    "[MainWindow] "
                    "Stopping GPUWorker..."
                )

                self.gpu_worker.stop()

                print(
                    "[MainWindow] "
                    "Waiting for GPUWorker to finish..."
                )

                if not self.gpu_worker.wait(
                    10000
                ):

                    print(
                        "[MainWindow] WARNING: "
                        "GPUWorker did not stop "
                        "within 10 seconds"
                    )

                else:

                    print(
                        "[MainWindow] "
                        "GPUWorker stopped"
                    )

        except Exception as exc:

            print(
                "[MainWindow] "
                f"GPUWorker shutdown error: {exc}"
            )

        # ----------------------------------------------------------
        # STOP DISK WORKER
        # ----------------------------------------------------------

        try:

            if (
                hasattr(
                    self,
                    "disk_worker",
                )
                and self.disk_worker is not None
                and self.disk_worker.isRunning()
            ):

                print(
                    "[MainWindow] "
                    "Stopping DiskWorker..."
                )

                self.disk_worker.stop()

                print(
                    "[MainWindow] "
                    "Waiting for DiskWorker to finish..."
                )

                if not self.disk_worker.wait(
                    10000
                ):

                    print(
                        "[MainWindow] WARNING: "
                        "DiskWorker did not stop "
                        "within 10 seconds"
                    )

                else:

                    print(
                        "[MainWindow] "
                        "DiskWorker stopped"
                    )

        except Exception as exc:

            print(
                "[MainWindow] "
                f"DiskWorker shutdown error: {exc}"
            )

        # ----------------------------------------------------------
        # PROCESS QUEUED QT EVENTS
        # ----------------------------------------------------------

        QApplication.processEvents()
        QApplication.processEvents()

        # ----------------------------------------------------------
        # FINAL WORKER CHECK
        # ----------------------------------------------------------

        for page in pages:

            if page is None:
                continue

            try:

                worker = getattr(
                    page,
                    "worker",
                    None,
                )

                if (
                    worker is not None
                    and worker.isRunning()
                ):

                    print(
                        "[MainWindow] WARNING: "
                        f"{page.__class__.__name__} "
                        "worker still running"
                    )

                ai_worker = getattr(
                    page,
                    "ai_worker",
                    None,
                )

                if (
                    ai_worker is not None
                    and ai_worker.isRunning()
                ):

                    print(
                        "[MainWindow] WARNING: "
                        "AI worker still running"
                    )

            except Exception as exc:

                print(
                    "[MainWindow] "
                    f"Worker check error: {exc}"
                )

        print(
            "[MainWindow] Closing complete"
        )

        event.accept()



