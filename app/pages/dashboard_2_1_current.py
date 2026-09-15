# ============================================================
# PC CONTROL CENTER PRO
# Dashboard 2.1
# ============================================================

from __future__ import annotations

import os
import time
from datetime import datetime
from typing import Any, Optional

import psutil

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QPushButton,
    QFrame,
    QSizePolicy,
    QProgressBar,
    QSpacerItem,
)


# ============================================================
# OPTIONAL PROJECT IMPORTS
# ============================================================

try:
    from app.services.monitoring import SystemMonitor
except Exception:
    SystemMonitor = None

try:
    from app.services.ai_analyzer import AIAnalyzer
except Exception:
    AIAnalyzer = None

try:
    from app.services.hardware_info import get_hardware_info
except Exception:
    get_hardware_info = None

try:
    from app.services.storage_info import get_storage_info
except Exception:
    get_storage_info = None

try:
    from app.services.network_info import get_network_info
except Exception:
    get_network_info = None


# ============================================================
# HELPERS
# ============================================================

def safe_float(value: Any, default: float = 0.0) -> float:
    """Convert value to float safely."""
    try:
        if value is None:
            return default

        if isinstance(value, str):
            value = value.replace("%", "").replace(",", ".").strip()

        return float(value)
    except Exception:
        return default


def clamp(value: float, minimum: float = 0.0, maximum: float = 100.0) -> float:
    return max(minimum, min(maximum, value))


def format_bytes(value: Any) -> str:
    """Human-readable byte value."""
    try:
        value = float(value)
    except Exception:
        return "N/A"

    units = ["B", "KB", "MB", "GB", "TB", "PB"]

    index = 0

    while value >= 1024 and index < len(units) - 1:
        value /= 1024
        index += 1

    if index == 0:
        return f"{value:.0f} {units[index]}"

    return f"{value:.1f} {units[index]}"


def format_speed(value: Any) -> str:
    """Human-readable network speed."""
    try:
        value = float(value)
    except Exception:
        return "0 B/s"

    if value < 1024:
        return f"{value:.0f} B/s"

    if value < 1024 ** 2:
        return f"{value / 1024:.1f} KB/s"

    if value < 1024 ** 3:
        return f"{value / 1024 ** 2:.1f} MB/s"

    return f"{value / 1024 ** 3:.1f} GB/s"


# ============================================================
# MINI GRAPH
# ============================================================

class MiniGraph(QWidget):
    """
    Lightweight graph widget.

    No external dependency on pyqtgraph.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.values = []
        self.maximum_points = 40

        self.setMinimumHeight(45)
        self.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed,
        )

    def add_value(self, value: float):
        value = clamp(safe_float(value))

        self.values.append(value)

        if len(self.values) > self.maximum_points:
            self.values.pop(0)

        self.update()

    def paintEvent(self, event):
        from PySide6.QtGui import QPainter, QPen, QPainterPath

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = self.rect()

        # Background
        painter.setPen(Qt.NoPen)

        # Grid
        pen = QPen()
        pen.setColor(Qt.GlobalColor.darkGray)
        pen.setWidth(1)

        painter.setPen(pen)

        for y in (0.25, 0.50, 0.75):
            yy = rect.height() * y
            painter.drawLine(
                0,
                int(yy),
                rect.width(),
                int(yy),
            )

        if len(self.values) < 2:
            return

        path = QPainterPath()

        width = rect.width()
        height = rect.height()

        step = width / max(1, len(self.values) - 1)

        for index, value in enumerate(self.values):
            x = index * step
            y = height - (value / 100.0) * height

            if index == 0:
                path.moveTo(x, y)
            else:
                path.lineTo(x, y)

        line_pen = QPen()
        line_pen.setWidth(2)

        # Let Qt use the default palette color.
        line_pen.setColor(
            self.palette().highlight().color()
        )

        painter.setPen(line_pen)
        painter.drawPath(path)


# ============================================================
# STAT CARD
# ============================================================

class StatCard(QFrame):

    def __init__(
        self,
        title: str,
        icon: str = "",
        parent=None,
    ):
        super().__init__(parent)

        self.setObjectName("StatCard")

        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            18,
            16,
            18,
            14,
        )

        layout.setSpacing(5)

        # Header
        header = QHBoxLayout()

        self.icon_label = QLabel(icon)
        self.icon_label.setObjectName("CardIcon")

        self.title_label = QLabel(title)
        self.title_label.setObjectName("CardTitle")

        header.addWidget(self.icon_label)
        header.addWidget(self.title_label)

        header.addStretch()

        layout.addLayout(header)

        # Main value
        self.value_label = QLabel("—")
        self.value_label.setObjectName("CardValue")

        layout.addWidget(self.value_label)

        # Secondary value
        self.detail_label = QLabel("Waiting for data...")
        self.detail_label.setObjectName("CardDetail")

        layout.addWidget(self.detail_label)

        # Graph
        self.graph = MiniGraph()

        layout.addWidget(self.graph)

        self.setMinimumHeight(155)

    def set_value(
        self,
        value: str,
        detail: str = "",
        graph_value: Optional[float] = None,
    ):
        self.value_label.setText(value)

        if detail:
            self.detail_label.setText(detail)

        if graph_value is not None:
            self.graph.add_value(graph_value)


# ============================================================
# DASHBOARD
# ============================================================

class DashboardPage(QWidget):

    navigation_requested = Signal(str)

    def __init__(
        self,
        parent=None,
        system_monitor=None,
        ai_analyzer=None,
        main_window=None,
    ):
        super().__init__(parent)

        self.parent_window = parent

        self.system_monitor = system_monitor
        self.ai_analyzer = ai_analyzer

        self.cpu_history = []
        self.ram_history = []
        self.gpu_history = []

        self.last_net = None
        self.last_net_time = time.monotonic()

        self.activity_items = []

        self._build_ui()
        self._apply_style()

        self._initialize_services()

        # Initial update
        self.update_dashboard()

        # Main update timer
        # Fast monitoring timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_dashboard)
        self.timer.start(1500)

        # Slow AI analysis timer
        # MainWindow settings already expect this timer to exist.
        self.ai_timer = QTimer(self)
        self.ai_timer.timeout.connect(self._run_ai_analysis)
        self.ai_timer.start(30000)
    def _run_ai_analysis(self):
        """Run AI analysis on the latest dashboard data."""
    try:
        cpu = self._get_cpu()
        ram = self._get_ram()
        gpu = self._get_gpu()
        storage = self._get_storage()

        self._update_ai(cpu, ram, gpu, storage)

    except Exception as exc:
        print(f"[Dashboard] AI timer error: {exc}")

    # ========================================================
    # UI
    # ========================================================

    def _build_ui(self):

        root = QVBoxLayout(self)

        root.setContentsMargins(
            24,
            22,
            24,
            22,
        )

        root.setSpacing(18)

        # ====================================================
        # HEADER
        # ====================================================

        header = QHBoxLayout()

        title_box = QVBoxLayout()
        title_box.setSpacing(2)

        title = QLabel("Dashboard")
        title.setObjectName("DashboardTitle")

        subtitle = QLabel(
            "PC Control Center Pro  •  System overview"
        )
        subtitle.setObjectName("DashboardSubtitle")

        title_box.addWidget(title)
        title_box.addWidget(subtitle)

        header.addLayout(title_box)

        header.addStretch()

        self.time_label = QLabel("--:--:--")
        self.time_label.setObjectName("HeaderTime")

        header.addWidget(self.time_label)

        self.refresh_button = QPushButton("⟳  Refresh")
        self.refresh_button.setObjectName("RefreshButton")
        self.refresh_button.clicked.connect(
            self.update_dashboard
        )

        header.addWidget(self.refresh_button)

        root.addLayout(header)

        # ====================================================
        # SYSTEM HEALTH + AI
        # ====================================================

        top_grid = QGridLayout()
        top_grid.setSpacing(16)

        # Health
        health_card = QFrame()
        health_card.setObjectName("HealthCard")

        health_layout = QVBoxLayout(health_card)

        health_layout.setContentsMargins(
            22,
            20,
            22,
            20,
        )

        health_header = QHBoxLayout()

        health_title = QLabel("SYSTEM HEALTH")
        health_title.setObjectName("SectionTitle")

        self.health_status = QLabel("CHECKING")
        self.health_status.setObjectName("HealthStatus")

        health_header.addWidget(health_title)
        health_header.addStretch()
        health_header.addWidget(self.health_status)

        health_layout.addLayout(health_header)

        health_main = QHBoxLayout()

        self.health_value = QLabel("—")
        self.health_value.setObjectName("HealthValue")

        health_main.addWidget(
            self.health_value,
            alignment=Qt.AlignVCenter,
        )

        health_text = QVBoxLayout()

        self.health_description = QLabel(
            "Analyzing system..."
        )
        self.health_description.setObjectName(
            "HealthDescription"
        )

        health_text.addWidget(
            self.health_description
        )

        self.health_bar = QProgressBar()
        self.health_bar.setRange(0, 100)
        self.health_bar.setValue(0)
        self.health_bar.setTextVisible(False)
        self.health_bar.setObjectName("HealthBar")

        health_text.addWidget(self.health_bar)

        health_main.addLayout(health_text)

        health_layout.addLayout(health_main)

        top_grid.addWidget(
            health_card,
            0,
            0,
            1,
            2,
        )

        # AI
        ai_card = QFrame()
        ai_card.setObjectName("AICard")

        ai_layout = QVBoxLayout(ai_card)

        ai_layout.setContentsMargins(
            22,
            20,
            22,
            20,
        )

        ai_header = QHBoxLayout()

        ai_title = QLabel("AI ANALYZER")
        ai_title.setObjectName("SectionTitle")

        ai_header.addWidget(ai_title)
        ai_header.addStretch()

        self.ai_badge = QLabel("READY")
        self.ai_badge.setObjectName("AIBadge")

        ai_header.addWidget(self.ai_badge)

        ai_layout.addLayout(ai_header)

        self.ai_status = QLabel(
            "System analysis is ready."
        )
        self.ai_status.setObjectName("AIStatus")

        self.ai_status.setWordWrap(True)

        ai_layout.addWidget(self.ai_status)

        self.ai_detail = QLabel(
            "No critical problems detected."
        )
        self.ai_detail.setObjectName("AIDetail")

        self.ai_detail.setWordWrap(True)

        ai_layout.addWidget(self.ai_detail)

        top_grid.addWidget(
            ai_card,
            0,
            2,
            1,
            2,
        )

        root.addLayout(top_grid)

        # ====================================================
        # STAT CARDS
        # ====================================================

        cards_grid = QGridLayout()
        cards_grid.setSpacing(16)

        self.cpu_card = StatCard(
            "CPU",
            "◉",
        )

        self.ram_card = StatCard(
            "MEMORY",
            "▣",
        )

        self.gpu_card = StatCard(
            "GPU",
            "◆",
        )

        self.storage_card = StatCard(
            "STORAGE",
            "▤",
        )

        cards_grid.addWidget(
            self.cpu_card,
            0,
            0,
        )

        cards_grid.addWidget(
            self.ram_card,
            0,
            1,
        )

        cards_grid.addWidget(
            self.gpu_card,
            0,
            2,
        )

        cards_grid.addWidget(
            self.storage_card,
            0,
            3,
        )

        root.addLayout(cards_grid)

        # ====================================================
        # LOWER AREA
        # ====================================================

        lower_grid = QGridLayout()
        lower_grid.setSpacing(16)

        # ----------------------------------------------------
        # NETWORK
        # ----------------------------------------------------

        network_card = QFrame()
        network_card.setObjectName("InfoCard")

        network_layout = QVBoxLayout(network_card)

        network_layout.setContentsMargins(
            20,
            18,
            20,
            18,
        )

        network_title = QLabel("NETWORK")
        network_title.setObjectName("SectionTitle")

        network_layout.addWidget(network_title)

        network_values = QHBoxLayout()

        self.download_value = QLabel(
            "↓  0 B/s"
        )
        self.download_value.setObjectName(
            "NetworkValue"
        )

        self.upload_value = QLabel(
            "↑  0 B/s"
        )
        self.upload_value.setObjectName(
            "NetworkValue"
        )

        network_values.addWidget(
            self.download_value
        )

        network_values.addStretch()

        network_values.addWidget(
            self.upload_value
        )

        network_layout.addLayout(network_values)

        self.network_status = QLabel(
            "●  Checking connection..."
        )
        self.network_status.setObjectName(
            "NetworkStatus"
        )

        network_layout.addWidget(
            self.network_status
        )

        lower_grid.addWidget(
            network_card,
            0,
            0,
        )

        # ----------------------------------------------------
        # QUICK ACTIONS
        # ----------------------------------------------------

        actions_card = QFrame()
        actions_card.setObjectName("InfoCard")

        actions_layout = QVBoxLayout(actions_card)

        actions_layout.setContentsMargins(
            20,
            18,
            20,
            18,
        )

        actions_title = QLabel("QUICK ACTIONS")
        actions_title.setObjectName("SectionTitle")

        actions_layout.addWidget(actions_title)

        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(8)

        self.optimize_button = QPushButton(
            "⚡ Optimize"
        )

        self.scan_button = QPushButton(
            "✓ Diagnose"
        )

        self.hardware_button = QPushButton(
            "▣ Hardware"
        )

        self.tools_button = QPushButton(
            "⚙ Tools"
        )

        for button in (
            self.optimize_button,
            self.scan_button,
            self.hardware_button,
            self.tools_button,
        ):
            button.setObjectName("ActionButton")
            buttons_layout.addWidget(button)

        self.optimize_button.clicked.connect(
            lambda: self._request_navigation("Optimize")
        )

        self.scan_button.clicked.connect(
            self._run_diagnostic
        )

        self.hardware_button.clicked.connect(
            lambda: self._request_navigation("Hardware")
        )

        self.tools_button.clicked.connect(
            lambda: self._request_navigation("Tools")
        )

        actions_layout.addLayout(buttons_layout)

        lower_grid.addWidget(
            actions_card,
            0,
            1,
        )

        # ----------------------------------------------------
        # ACTIVITY
        # ----------------------------------------------------

        activity_card = QFrame()
        activity_card.setObjectName("InfoCard")

        activity_layout = QVBoxLayout(activity_card)

        activity_layout.setContentsMargins(
            20,
            18,
            20,
            18,
        )

        activity_title = QLabel(
            "LIVE SYSTEM ACTIVITY"
        )
        activity_title.setObjectName(
            "SectionTitle"
        )

        activity_layout.addWidget(
            activity_title
        )

        self.activity_label = QLabel(
            "●  Dashboard initialized"
        )

        self.activity_label.setObjectName(
            "ActivityLabel"
        )

        self.activity_label.setWordWrap(True)

        activity_layout.addWidget(
            self.activity_label
        )

        activity_layout.addStretch()

        lower_grid.addWidget(
            activity_card,
            1,
            0,
            1,
            2,
        )

        root.addLayout(lower_grid)

        root.addStretch()

    # ========================================================
    # STYLE
    # ========================================================

    def _apply_style(self):

        self.setStyleSheet(
            """
            QWidget {
                font-family: "Segoe UI";
                color: #E8EDF5;
            }

            QFrame#StatCard,
            QFrame#HealthCard,
            QFrame#AICard,
            QFrame#InfoCard {
                background: #111722;
                border: 1px solid #202A3A;
                border-radius: 14px;
            }

            QFrame#StatCard:hover,
            QFrame#HealthCard:hover,
            QFrame#AICard:hover,
            QFrame#InfoCard:hover {
                border: 1px solid #35445D;
            }

            QLabel#DashboardTitle {
                font-size: 28px;
                font-weight: 700;
                color: #F4F7FB;
            }

            QLabel#DashboardSubtitle {
                font-size: 13px;
                color: #7F8CA3;
            }

            QLabel#HeaderTime {
                font-size: 13px;
                color: #8492A8;
                padding-right: 8px;
            }

            QPushButton#RefreshButton {
                background: #182131;
                border: 1px solid #2A374B;
                border-radius: 9px;
                padding: 8px 14px;
                color: #DDE5F2;
                font-weight: 600;
            }

            QPushButton#RefreshButton:hover {
                background: #202C3F;
            }

            QLabel#SectionTitle {
                font-size: 11px;
                font-weight: 700;
                letter-spacing: 1px;
                color: #7F8CA3;
            }

            QLabel#HealthStatus {
                font-size: 11px;
                font-weight: 700;
                color: #7ED6A4;
            }

            QLabel#HealthValue {
                font-size: 42px;
                font-weight: 700;
                color: #F2F6FC;
                min-width: 115px;
            }

            QLabel#HealthDescription {
                font-size: 13px;
                color: #9CA8B9;
                padding-bottom: 8px;
            }

            QProgressBar#HealthBar {
                background: #1B2432;
                border: none;
                border-radius: 4px;
                height: 8px;
            }

            QProgressBar#HealthBar::chunk {
                background: #6FD39B;
                border-radius: 4px;
            }

            QLabel#AIBadge {
                background: #17261F;
                color: #7ED6A4;
                border: 1px solid #28513A;
                border-radius: 7px;
                padding: 4px 8px;
                font-size: 10px;
                font-weight: 700;
            }

            QLabel#AIStatus {
                font-size: 16px;
                font-weight: 600;
                color: #EAF0F8;
                padding-top: 8px;
            }

            QLabel#AIDetail {
                font-size: 12px;
                color: #8491A4;
                padding-top: 3px;
            }

            QLabel#CardIcon {
                font-size: 14px;
                color: #8C9AB0;
            }

            QLabel#CardTitle {
                font-size: 11px;
                font-weight: 700;
                letter-spacing: 1px;
                color: #7F8CA3;
            }

            QLabel#CardValue {
                font-size: 27px;
                font-weight: 700;
                color: #F1F5FA;
                padding-top: 2px;
            }

            QLabel#CardDetail {
                font-size: 11px;
                color: #7D899B;
            }

            QLabel#NetworkValue {
                font-size: 16px;
                font-weight: 600;
                color: #DDE6F2;
            }

            QLabel#NetworkStatus {
                font-size: 11px;
                color: #7ED6A4;
                padding-top: 8px;
            }

            QPushButton#ActionButton {
                background: #182131;
                border: 1px solid #29364A;
                border-radius: 8px;
                padding: 9px 12px;
                color: #D9E2EF;
                font-size: 11px;
                font-weight: 600;
            }

            QPushButton#ActionButton:hover {
                background: #212D40;
                border: 1px solid #3A4B65;
            }

            QPushButton#ActionButton:pressed {
                background: #111923;
            }

            QLabel#ActivityLabel {
                font-size: 12px;
                color: #8C98AA;
                padding-top: 6px;
            }
            """
        )

    # ========================================================
    # SERVICES
    # ========================================================

    def _initialize_services(self):

        if self.system_monitor is None:
            if SystemMonitor is not None:
                try:
                    self.system_monitor = SystemMonitor(
                        history_size=60
                    )
                except Exception:
                    try:
                        self.system_monitor = SystemMonitor()
                    except Exception:
                        self.system_monitor = None

        if self.ai_analyzer is None:
            if AIAnalyzer is not None:
                try:
                    self.ai_analyzer = AIAnalyzer()
                except Exception:
                    self.ai_analyzer = None

    # ========================================================
    # MAIN UPDATE
    # ========================================================

    def update_dashboard(self):

        try:
            self.time_label.setText(
                datetime.now().strftime("%H:%M:%S")
            )
        except Exception:
            pass

        cpu = self._get_cpu()
        ram = self._get_ram()

        gpu = self._get_gpu()

        storage = self._get_storage()

        network = self._get_network()

        # ----------------------------------------------------
        # CARDS
        # ----------------------------------------------------

        self.cpu_card.set_value(
            f"{cpu:.0f}%",
            self._cpu_detail(),
            cpu,
        )

        self.ram_card.set_value(
            f"{ram['percent']:.0f}%",
            f"{ram['used']} / {ram['total']}",
            ram["percent"],
        )

        if gpu["usage"] is None:
            self.gpu_card.set_value(
                "N/A",
                gpu["name"],
                None,
            )
        else:
            self.gpu_card.set_value(
                f"{gpu['usage']:.0f}%",
                gpu["name"],
                gpu["usage"],
            )

        self.storage_card.set_value(
            f"{storage['percent']:.0f}%",
            storage["detail"],
            storage["percent"],
        )

        # ----------------------------------------------------
        # NETWORK
        # ----------------------------------------------------

        self.download_value.setText(
            f"↓  {format_speed(network['download'])}"
        )

        self.upload_value.setText(
            f"↑  {format_speed(network['upload'])}"
        )

        if network["connected"]:
            self.network_status.setText(
                "●  Connected"
            )
        else:
            self.network_status.setText(
                "●  No active connection"
            )

        # ----------------------------------------------------
        # HEALTH
        # ----------------------------------------------------

        health = self._calculate_health(
            cpu,
            ram["percent"],
            gpu["usage"],
            storage["percent"],
        )

        self._update_health(
            health,
            cpu,
            ram["percent"],
            storage["percent"],
        )

        # ----------------------------------------------------
        # AI
        # ----------------------------------------------------

        self._update_ai(
            cpu,
            ram["percent"],
            gpu["usage"],
            storage["percent"],
        )

    # ========================================================
    # CPU
    # ========================================================

    def _get_cpu(self) -> float:

        try:
            # Existing monitor first
            if self.system_monitor is not None:

                if hasattr(
                    self.system_monitor,
                    "update",
                ):
                    result = self.system_monitor.update()

                    value = self._extract(
                        result,
                        [
                            "cpu",
                            "cpu_percent",
                            "cpu_usage",
                        ],
                    )

                    if value is not None:
                        return clamp(
                            safe_float(value)
                        )

                for attr in (
                    "cpu_percent",
                    "cpu_usage",
                    "cpu",
                ):
                    if hasattr(
                        self.system_monitor,
                        attr,
                    ):
                        value = getattr(
                            self.system_monitor,
                            attr,
                        )

                        if callable(value):
                            value = value()

                        if value is not None:
                            return clamp(
                                safe_float(value)
                            )

            return clamp(
                psutil.cpu_percent(
                    interval=None
                )
            )

        except Exception:
            return 0.0

    def _cpu_detail(self) -> str:

        try:
            freq = psutil.cpu_freq()

            if freq is not None:
                return (
                    f"{freq.current:.0f} MHz"
                )

        except Exception:
            pass

        return "Processor load"

    # ========================================================
    # RAM
    # ========================================================

    def _get_ram(self):

        try:
            memory = psutil.virtual_memory()

            return {
                "percent": clamp(
                    memory.percent
                ),
                "used": format_bytes(
                    memory.used
                ),
                "total": format_bytes(
                    memory.total
                ),
            }

        except Exception:

            return {
                "percent": 0.0,
                "used": "N/A",
                "total": "N/A",
            }

    # ========================================================
    # GPU
    # ========================================================

    def _get_gpu(self):

        result = {
            "name": "GPU data unavailable",
            "usage": None,
            "temperature": None,
        }

        try:
            # Try project hardware service
            if get_hardware_info is not None:

                data = get_hardware_info()

                if isinstance(data, dict):

                    gpu = data.get(
                        "gpu",
                        data.get(
                            "GPU",
                            {},
                        ),
                    )

                    if isinstance(gpu, dict):

                        name = (
                            gpu.get("name")
                            or gpu.get("model")
                            or gpu.get("device")
                        )

                        if name:
                            result["name"] = str(
                                name
                            )

                        usage = (
                            gpu.get("usage")
                            if "usage" in gpu
                            else gpu.get(
                                "usage_percent"
                            )
                        )

                        if usage is not None:
                            result["usage"] = clamp(
                                safe_float(
                                    usage
                                )
                            )

                        temperature = gpu.get(
                            "temperature"
                        )

                        if temperature is not None:
                            result[
                                "temperature"
                            ] = safe_float(
                                temperature
                            )

            # Try common GPU service
            if result["name"] == "GPU data unavailable":

                try:
                    from app.services.gpu_info import (
                        get_gpu_info,
                    )

                    data = get_gpu_info()

                    if isinstance(data, dict):

                        name = data.get(
                            "name"
                        )

                        if name:
                            result["name"] = str(
                                name
                            )

                        usage = data.get(
                            "usage"
                        )

                        if usage is None:
                            usage = data.get(
                                "usage_percent"
                            )

                        if usage is not None:
                            result["usage"] = clamp(
                                safe_float(
                                    usage
                                )
                            )

                        temperature = data.get(
                            "temperature"
                        )

                        if temperature is not None:
                            result[
                                "temperature"
                            ] = safe_float(
                                temperature
                            )

                except Exception:
                    pass

        except Exception:
            pass

        if (
            result["name"]
            == "GPU data unavailable"
        ):
            try:
                result["name"] = (
                    "AMD Radeon / Graphics"
                )
            except Exception:
                pass

        return result

    # ========================================================
    # STORAGE
    # ========================================================

    def _get_storage(self):

        try:
            root = os.environ.get(
                "SystemDrive",
                "C:",
            )

            usage = psutil.disk_usage(
                root + "\\"
            )

            return {
                "percent": clamp(
                    usage.percent
                ),
                "detail": (
                    f"{format_bytes(usage.free)} "
                    f"free of "
                    f"{format_bytes(usage.total)}"
                ),
            }

        except Exception:

            return {
                "percent": 0.0,
                "detail": "Storage data unavailable",
            }

    # ========================================================
    # NETWORK
    # ========================================================

    def _get_network(self):

        connected = False

        try:
            stats = psutil.net_if_stats()

            for name, info in stats.items():

                if not info.isup:
                    continue

                lowered = name.lower()

                if (
                    "loopback" in lowered
                    or lowered.startswith("lo")
                ):
                    continue

                connected = True
                break

        except Exception:
            connected = False

        try:

            counters = psutil.net_io_counters()

            now = time.monotonic()

            if self.last_net is None:

                self.last_net = counters
                self.last_net_time = now

                return {
                    "download": 0.0,
                    "upload": 0.0,
                    "connected": connected,
                }

            elapsed = max(
                0.001,
                now - self.last_net_time,
            )

            download = (
                counters.bytes_recv
                - self.last_net.bytes_recv
            ) / elapsed

            upload = (
                counters.bytes_sent
                - self.last_net.bytes_sent
            ) / elapsed

            self.last_net = counters
            self.last_net_time = now

            return {
                "download": max(
                    0.0,
                    download,
                ),
                "upload": max(
                    0.0,
                    upload,
                ),
                "connected": connected,
            }

        except Exception:

            return {
                "download": 0.0,
                "upload": 0.0,
                "connected": connected,
            }

    # ========================================================
    # HEALTH
    # ========================================================

    def _calculate_health(
        self,
        cpu: float,
        ram: float,
        gpu: Optional[float],
        storage: float,
    ) -> int:

        score = 100.0

        # CPU
        if cpu >= 95:
            score -= 30
        elif cpu >= 85:
            score -= 20
        elif cpu >= 75:
            score -= 10
        elif cpu >= 65:
            score -= 5

        # RAM
        if ram >= 95:
            score -= 25
        elif ram >= 90:
            score -= 18
        elif ram >= 80:
            score -= 10
        elif ram >= 70:
            score -= 5

        # GPU
        if gpu is not None:

            if gpu >= 98:
                score -= 10
            elif gpu >= 90:
                score -= 5

        # Storage
        if storage >= 98:
            score -= 20
        elif storage >= 95:
            score -= 15
        elif storage >= 90:
            score -= 10
        elif storage >= 80:
            score -= 5

        return int(
            clamp(
                score,
                0,
                100,
            )
        )

    def _update_health(
        self,
        health: int,
        cpu: float,
        ram: float,
        storage: float,
    ):

        self.health_value.setText(
            f"{health}%"
        )

        self.health_bar.setValue(
            health
        )

        if health >= 85:

            status = "GOOD"

            description = (
                "System is operating normally."
            )

        elif health >= 65:

            status = "ATTENTION"

            description = (
                "Some system resources are under load."
            )

        elif health >= 40:

            status = "WARNING"

            description = (
                "High resource usage detected."
            )

        else:

            status = "CRITICAL"

            description = (
                "System resources are heavily constrained."
            )

        self.health_status.setText(
            status
        )

        self.health_description.setText(
            description
        )

        self._set_health_status_style(
            status
        )

    def _set_health_status_style(
        self,
        status: str,
    ):

        if status == "GOOD":
            color = "#7ED6A4"

        elif status == "ATTENTION":
            color = "#E7C66A"

        elif status == "WARNING":
            color = "#E8A96A"

        else:
            color = "#E87979"

        self.health_status.setStyleSheet(
            f"""
            color: {color};
            font-size: 11px;
            font-weight: 700;
            """
        )

    # ========================================================
    # AI
    # ========================================================

    def _update_ai(
        self,
        cpu: float,
        ram: float,
        gpu: Optional[float],
        storage: float,
    ):

        # First try existing analyzer
        analyzer_result = None

        if self.ai_analyzer is not None:

            try:

                if hasattr(
                    self.ai_analyzer,
                    "analyze",
                ):
                    analyzer_result = (
                        self.ai_analyzer.analyze()
                    )

                elif hasattr(
                    self.ai_analyzer,
                    "run",
                ):
                    analyzer_result = (
                        self.ai_analyzer.run()
                    )

                elif hasattr(
                    self.ai_analyzer,
                    "diagnose",
                ):
                    analyzer_result = (
                        self.ai_analyzer.diagnose()
                    )

            except Exception:
                analyzer_result = None

        if analyzer_result is not None:

            status = self._extract(
                analyzer_result,
                [
                    "status",
                    "state",
                    "result",
                ],
            )

            message = self._extract(
                analyzer_result,
                [
                    "message",
                    "summary",
                    "description",
                    "recommendation",
                ],
            )

            if status:
                self.ai_badge.setText(
                    str(status).upper()
                )

            if message:
                self.ai_status.setText(
                    str(message)
                )

            return

        # Local fallback analyzer
        issues = []

        if cpu >= 90:
            issues.append(
                "CPU load is high"
            )

        if ram >= 90:
            issues.append(
                "memory usage is high"
            )

        if storage >= 90:
            issues.append(
                "storage space is running low"
            )

        if gpu is not None and gpu >= 95:
            issues.append(
                "GPU load is high"
            )

        if not issues:

            self.ai_badge.setText(
                "GOOD"
            )

            self.ai_status.setText(
                "System is operating normally."
            )

            self.ai_detail.setText(
                "No critical resource problems detected."
            )

        else:

            self.ai_badge.setText(
                "ATTENTION"
            )

            self.ai_status.setText(
                "Resource attention required."
            )

            self.ai_detail.setText(
                " • ".join(issues)
            )

    # ========================================================
    # DIAGNOSTIC
    # ========================================================

    def _run_diagnostic(self):

        self.ai_badge.setText(
            "SCANNING"
        )

        self.ai_status.setText(
            "Running system diagnostics..."
        )

        self.ai_detail.setText(
            "Please wait..."
        )

        QTimer.singleShot(
            600,
            self.update_dashboard,
        )

        self._add_activity(
            "System diagnostic started"
        )

    # ========================================================
    # NAVIGATION
    # ========================================================

    def _request_navigation(
        self,
        page_name: str,
    ):

        self.navigation_requested.emit(
            page_name
        )

        # Compatibility with common MainWindow
        try:

            window = self.window()

            for method_name in (
                "show_page",
                "navigate_to",
                "switch_page",
                "open_page",
            ):

                method = getattr(
                    window,
                    method_name,
                    None,
                )

                if callable(method):

                    try:
                        method(page_name)
                        return
                    except Exception:
                        pass

        except Exception:
            pass

    # ========================================================
    # ACTIVITY
    # ========================================================

    def _add_activity(
        self,
        text: str,
    ):

        timestamp = datetime.now().strftime(
            "%H:%M:%S"
        )

        item = (
            f"●  [{timestamp}]  {text}"
        )

        self.activity_items.insert(
            0,
            item,
        )

        self.activity_items = (
            self.activity_items[:4]
        )

        self.activity_label.setText(
            "\n".join(
                self.activity_items
            )
        )

    # ========================================================
    # DATA EXTRACTION
    # ========================================================

    @staticmethod
    def _extract(
        data: Any,
        keys,
    ):

        if data is None:
            return None

        if isinstance(data, dict):

            for key in keys:

                if key in data:
                    return data[key]

            return None

        for key in keys:

            try:

                if hasattr(
                    data,
                    key,
                ):
                    value = getattr(
                        data,
                        key,
                    )

                    if callable(value):
                        value = value()

                    return value

            except Exception:
                pass

        return None

    # ========================================================
    # COMPATIBILITY METHODS
    # ========================================================

    def refresh(self):
        """Compatibility alias."""
        self.update_dashboard()

    def update_data(self):
        """Compatibility alias."""
        self.update_dashboard()

    def stop(self):
        """Stop dashboard timer."""
        try:
            self.timer.stop()
        except Exception:
            pass

    def closeEvent(self, event):

        self.stop()

        super().closeEvent(event)