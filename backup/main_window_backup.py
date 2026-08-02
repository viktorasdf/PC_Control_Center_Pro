from PySide6.QtCore import Qt, QTimer, QPointF
from PySide6.QtGui import QPainter, QPen
from PySide6.QtWidgets import (
    QGridLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QMainWindow, QProgressBar, QScrollArea, QStackedWidget,
    QVBoxLayout, QWidget, QFrame
)

from app.services.system_info import get_cpu_info, get_memory_info, get_system_info
from app.services.gpu_info import get_gpu_info
from app.services.storage_info import get_storage_info
from app.services.network_info import get_network_info
from app.services.monitoring import SystemMonitor


class GraphWidget(QWidget):
    def __init__(self, title, minimum_value=0, maximum_value=100, parent=None):
        super().__init__(parent)
        self.title = title
        self.minimum_value = minimum_value
        self.maximum_value = maximum_value
        self.values = []
        self.setMinimumHeight(190)

    def set_values(self, values):
        self.values = list(values)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        width = self.width()
        height = self.height()

        painter.fillRect(self.rect(), self.palette().base())

        painter.setPen(self.palette().text().color())
        painter.drawText(15, 25, self.title)

        left, right, top, bottom = 45, 15, 40, 30
        graph_width = width - left - right
        graph_height = height - top - bottom

        grid_pen = QPen()
        grid_pen.setStyle(Qt.DashLine)
        painter.setPen(grid_pen)

        for i in range(5):
            y = top + graph_height * i / 4
            painter.drawLine(left, int(y), width - right, int(y))

        painter.setPen(self.palette().text().color())

        for i in range(5):
            value = self.maximum_value - (
                (self.maximum_value - self.minimum_value) * i / 4
            )
            y = top + graph_height * i / 4
            painter.drawText(5, int(y + 5), f"{value:.0f}")

        if not self.values:
            painter.drawText(left + 10, top + 30, "РћР¶РёРґР°РЅРёРµ РґР°РЅРЅС‹С…...")
            return

        values = self.values[-60:]

        if len(values) == 1:
            values = [values[0], values[0]]

        points = []
        count = len(values)
        value_range = self.maximum_value - self.minimum_value
        if value_range <= 0:
            value_range = 1

        for index, value in enumerate(values):
            value = max(self.minimum_value, min(self.maximum_value, value))
            x = left + graph_width * index / (count - 1)
            normalized = (value - self.minimum_value) / value_range
            y = top + graph_height * (1 - normalized)
            points.append(QPointF(x, y))

        line_pen = QPen()
        line_pen.setWidth(2)
        painter.setPen(line_pen)

        for i in range(len(points) - 1):
            painter.drawLine(points[i], points[i + 1])

        painter.drawText(width - 85, 25, f"{values[-1]:.1f}")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("PC Control Center Pro 0.4 Alpha")
        self.resize(1400, 800)

        self.monitor = SystemMonitor(history_size=60)

        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.menu = QListWidget()
        self.menu.setFixedWidth(230)

        pages = [
            "рџЏ  Dashboard",
            "рџ“Љ Monitoring",
            "рџ–Ґ Hardware",
            "рџ’ѕ Storage",
            "рџЊђ Network",
            "вљЎ Optimize",
            "рџ”§ Tools",
            "рџ¤– AI",
            "рџ“„ Reports",
            "вљ™ Settings",
        ]

        for page in pages:
            self.menu.addItem(QListWidgetItem(page))

        main_layout.addWidget(self.menu)

        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack)

        self.dashboard = self.create_dashboard()
        self.stack.addWidget(self.dashboard)

        self.monitoring_page = self.create_monitoring_page()
        self.stack.addWidget(self.monitoring_page)

        self.hardware_page = self.create_hardware_page()
        self.stack.addWidget(self.hardware_page)

        self.storage_page = self.create_storage_page()
        self.stack.addWidget(self.storage_page)

        self.network_page = self.create_network_page()
        self.stack.addWidget(self.network_page)

        for title in ["вљЎ Optimize", "рџ”§ Tools", "рџ¤– AI", "рџ“„ Reports", "вљ™ Settings"]:
            self.stack.addWidget(self.create_placeholder_page(title))

        self.menu.currentRowChanged.connect(self.stack.setCurrentIndex)
        self.menu.setCurrentRow(0)

        # ==================================================
# TIMERS
# ==================================================

        # ==================================================
        # TIMERS
        # ==================================================

        # Быстрый мониторинг
        self.monitor_timer = QTimer(self)
        self.monitor_timer.timeout.connect(
            self.update_monitoring
        )
        self.monitor_timer.start(1000)

        # Dashboard
        self.dashboard_timer = QTimer(self)
        self.dashboard_timer.timeout.connect(
            self.update_dashboard
        )
        self.dashboard_timer.start(2000)

        # Network
        self.network_timer = QTimer(self)
        self.network_timer.timeout.connect(
            self.update_network_page
        )
        self.network_timer.start(3000)

        # Storage
        self.storage_timer = QTimer(self)
        self.storage_timer.timeout.connect(
            self.update_storage_page
        )
        self.storage_timer.start(5000)

        # Hardware
        self.hardware_timer = QTimer(self)
        self.hardware_timer.timeout.connect(
            self.update_hardware
        )
        self.hardware_timer.start(10000)

        # ==================================================
        # INITIAL UPDATE
        # ==================================================

        self.update_hardware()




   

    def create_placeholder_page(self, title):
        page = QWidget()
        layout = QVBoxLayout(page)

        label = QLabel(title)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-size: 30px; font-weight: bold;")

        layout.addStretch()
        layout.addWidget(label)
        layout.addStretch()

        return page

    def create_dashboard(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(35, 30, 35, 30)
        layout.setSpacing(20)

        title = QLabel("PC Control Center Pro")
        title.setStyleSheet("font-size: 32px; font-weight: bold;")

        subtitle = QLabel("System Dashboard")

        layout.addWidget(title)
        layout.addWidget(subtitle)

        cards = QGridLayout()
        cards.setSpacing(20)

        cpu_card, self.cpu_value, self.cpu_bar = self.create_card("CPU")
        ram_card, self.ram_value, self.ram_bar = self.create_card("RAM")
        gpu_card, self.gpu_value, self.gpu_bar = self.create_card("GPU")

        cards.addWidget(cpu_card, 0, 0)
        cards.addWidget(ram_card, 0, 1)
        cards.addWidget(gpu_card, 0, 2)

        layout.addLayout(cards)

        gpu_frame = QFrame()
        gpu_frame.setFrameShape(QFrame.StyledPanel)
        gpu_layout = QVBoxLayout(gpu_frame)

        gpu_title = QLabel("Graphics")
        gpu_title.setStyleSheet("font-size: 20px; font-weight: bold;")

        self.gpu_details = QLabel()
        self.gpu_details.setStyleSheet("font-size: 15px;")

        gpu_layout.addWidget(gpu_title)
        gpu_layout.addWidget(self.gpu_details)
        layout.addWidget(gpu_frame)

        system_frame = QFrame()
        system_frame.setFrameShape(QFrame.StyledPanel)
        system_layout = QVBoxLayout(system_frame)

        system_title = QLabel("System")
        system_title.setStyleSheet("font-size: 20px; font-weight: bold;")

        self.system_label = QLabel()
        self.system_label.setStyleSheet("font-size: 15px;")

        system_layout.addWidget(system_title)
        system_layout.addWidget(self.system_label)
        layout.addWidget(system_frame)

        layout.addStretch()
        return page

    def create_card(self, title):
        frame = QFrame()
        frame.setFrameShape(QFrame.StyledPanel)

        layout = QVBoxLayout(frame)

        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")

        value_label = QLabel("0%")
        value_label.setStyleSheet("font-size: 30px; font-weight: bold;")

        progress = QProgressBar()
        progress.setRange(0, 100)
        progress.setValue(0)

        layout.addWidget(title_label)
        layout.addWidget(value_label)
        layout.addWidget(progress)

        return frame, value_label, progress

    def create_monitoring_page(self):
        page = QWidget()
        main_layout = QVBoxLayout(page)
        main_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(35, 30, 35, 30)
        layout.setSpacing(15)

        title = QLabel("рџ“Љ Monitoring")
        title.setStyleSheet("font-size: 32px; font-weight: bold;")
        layout.addWidget(title)

        layout.addWidget(QLabel("Real-time system performance"))

        values_frame = QFrame()
        values_frame.setFrameShape(QFrame.StyledPanel)
        values_layout = QHBoxLayout(values_frame)

        self.monitor_cpu_label = QLabel("CPU: 0%")
        self.monitor_ram_label = QLabel("RAM: 0%")
        self.monitor_download_label = QLabel("в†“ Download: 0 Mbps")
        self.monitor_upload_label = QLabel("в†‘ Upload: 0 Mbps")

        for label in [
            self.monitor_cpu_label,
            self.monitor_ram_label,
            self.monitor_download_label,
            self.monitor_upload_label,
        ]:
            label.setStyleSheet("font-size: 16px; font-weight: bold;")
            values_layout.addWidget(label)

        layout.addWidget(values_frame)

        self.cpu_graph = GraphWidget("CPU Usage (%)", 0, 100)
        self.ram_graph = GraphWidget("RAM Usage (%)", 0, 100)
        self.download_graph = GraphWidget("Download (Mbps)", 0, 100)
        self.upload_graph = GraphWidget("Upload (Mbps)", 0, 100)

        layout.addWidget(self.cpu_graph)
        layout.addWidget(self.ram_graph)
        layout.addWidget(self.download_graph)
        layout.addWidget(self.upload_graph)
        layout.addStretch()

        scroll.setWidget(content)
        main_layout.addWidget(scroll)

        return page

    def update_monitoring(self):
        data = self.monitor.update()

        cpu = data["cpu"]
        ram = data["ram"]
        download = self.monitor.bytes_to_mbps(data["download"])
        upload = self.monitor.bytes_to_mbps(data["upload"])

        self.monitor_cpu_label.setText(f"CPU: {cpu:.1f}%")
        self.monitor_ram_label.setText(f"RAM: {ram:.1f}%")
        self.monitor_download_label.setText(f"в†“ Download: {download:.3f} Mbps")
        self.monitor_upload_label.setText(f"в†‘ Upload: {upload:.3f} Mbps")

        self.cpu_graph.set_values(self.monitor.cpu_history)
        self.ram_graph.set_values(self.monitor.ram_history)

        download_history = [
            self.monitor.bytes_to_mbps(value)
            for value in self.monitor.download_history
        ]
        upload_history = [
            self.monitor.bytes_to_mbps(value)
            for value in self.monitor.upload_history
        ]

        self.download_graph.set_values(download_history)
        self.upload_graph.set_values(upload_history)

        self.update_graph_scale(self.download_graph, download_history)
        self.update_graph_scale(self.upload_graph, upload_history)

    @staticmethod
    def update_graph_scale(graph, values):
        if not values:
            return

        maximum = max(values)

        if maximum <= 1:
            maximum = 1
        elif maximum <= 10:
            maximum = 10
        elif maximum <= 50:
            maximum = 50
        elif maximum <= 100:
            maximum = 100
        else:
            maximum = (int(maximum / 100) + 1) * 100

        graph.maximum_value = maximum
        graph.update()

    def create_hardware_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(35, 30, 35, 30)
        layout.setSpacing(20)

        title = QLabel("рџ–Ґ Hardware")
        title.setStyleSheet("font-size: 32px; font-weight: bold;")
        layout.addWidget(title)

        layout.addWidget(QLabel("Detailed hardware information"))

        self.hardware_cpu = self.add_hardware_frame(layout, "рџ§  Processor")
        self.hardware_ram = self.add_hardware_frame(layout, "рџ§  Memory")
        self.hardware_system = self.add_hardware_frame(layout, "рџ’» System")
        self.hardware_gpu = self.add_hardware_frame(layout, "рџЋ® Graphics")

        layout.addStretch()
        return page

    @staticmethod
    def add_hardware_frame(layout, title):
        frame = QFrame()
        frame.setFrameShape(QFrame.StyledPanel)
        frame_layout = QVBoxLayout(frame)

        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 20px; font-weight: bold;")

        value = QLabel("Р—Р°РіСЂСѓР·РєР°...")
        value.setStyleSheet("font-size: 15px;")

        frame_layout.addWidget(title_label)
        frame_layout.addWidget(value)
        layout.addWidget(frame)

        return value

    def update_hardware(self):
        from app.services.hardware_info import get_hardware_info

        hardware = get_hardware_info()

        cpu = hardware["cpu"]
        ram = hardware["ram"]
        system = hardware["system"]

        self.hardware_cpu.setText(
            f"РќР°Р·РІР°РЅРёРµ: {cpu['name']}\n"
            f"РЇРґРµСЂ: {cpu['cores']}\n"
            f"РџРѕС‚РѕРєРѕРІ: {cpu['threads']}\n"
            f"РўРµРєСѓС‰Р°СЏ С‡Р°СЃС‚РѕС‚Р°: {cpu['frequency_current'] / 1000:.2f} GHz\n"
            f"РњР°РєСЃРёРјР°Р»СЊРЅР°СЏ С‡Р°СЃС‚РѕС‚Р°: {cpu['frequency_max'] / 1000:.2f} GHz"
        )

        self.hardware_ram.setText(
            f"РћР±С‰РёР№ РѕР±СЉС‘Рј: {ram['total_gb']:.2f} GB"
        )

        self.hardware_system.setText(
            f"РљРѕРјРїСЊСЋС‚РµСЂ: {system['computer']}\n"
            f"РћРЎ: {system['name']} {system['release']}\n"
            f"Р’РµСЂСЃРёСЏ: {system['version']}\n"
            f"РђСЂС…РёС‚РµРєС‚СѓСЂР°: {system['architecture']}"
        )

        gpu = get_gpu_info()

        self.hardware_gpu.setText(
            f"GPU: {gpu['name']}\n"
            f"РџСЂРѕРёР·РІРѕРґРёС‚РµР»СЊ: {gpu['vendor']}\n"
            f"VRAM: {gpu['memory_total']:.1f} GB\n"
            f"Р”СЂР°Р№РІРµСЂ: {gpu.get('driver', 'РќРµ РѕРїСЂРµРґРµР»С‘РЅ')}"
        )

    def create_storage_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(35, 30, 35, 30)
        layout.setSpacing(20)

        title = QLabel("рџ’ѕ Storage")
        title.setStyleSheet("font-size: 32px; font-weight: bold;")
        layout.addWidget(title)

        layout.addWidget(QLabel("Disk usage and available space"))

        self.storage_layout = QVBoxLayout()
        self.storage_layout.setSpacing(15)
        layout.addLayout(self.storage_layout)
        layout.addStretch()

        return page

    def update_storage_page(self):
        while self.storage_layout.count():
            item = self.storage_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        drives = get_storage_info()

        if not drives:
            self.storage_layout.addWidget(QLabel("Р”РёСЃРєРё РЅРµ РѕР±РЅР°СЂСѓР¶РµРЅС‹"))
            return

        for drive in drives:
            frame = QFrame()
            frame.setFrameShape(QFrame.StyledPanel)
            drive_layout = QVBoxLayout(frame)

            name = QLabel(
                f"{drive['device']} вЂ” {drive['filesystem']}"
            )
            name.setStyleSheet("font-size: 20px; font-weight: bold;")

            details = QLabel(
                f"Р—Р°РЅСЏС‚Рѕ: {drive['used_gb']:.1f} GB   |   "
                f"РЎРІРѕР±РѕРґРЅРѕ: {drive['free_gb']:.1f} GB   |   "
                f"Р’СЃРµРіРѕ: {drive['total_gb']:.1f} GB"
            )

            progress = QProgressBar()
            progress.setRange(0, 100)
            progress.setValue(int(drive["percent"]))

            drive_layout.addWidget(name)
            drive_layout.addWidget(details)
            drive_layout.addWidget(progress)

            self.storage_layout.addWidget(frame)

    def create_network_page(self):
        page = QWidget()
        main_layout = QVBoxLayout(page)
        main_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(35, 30, 35, 30)
        layout.setSpacing(20)

        title = QLabel("рџЊђ Network")
        title.setStyleSheet("font-size: 32px; font-weight: bold;")
        layout.addWidget(title)

        layout.addWidget(
            QLabel("Network interfaces and connection information")
        )

        self.network_layout = QVBoxLayout()
        self.network_layout.setSpacing(15)
        layout.addLayout(self.network_layout)
        layout.addStretch()

        scroll.setWidget(content)
        main_layout.addWidget(scroll)

        return page

    def update_network_page(self):
        while self.network_layout.count():
            item = self.network_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        networks = get_network_info()

        if not networks:
            self.network_layout.addWidget(
                QLabel("РЎРµС‚РµРІС‹Рµ РёРЅС‚РµСЂС„РµР№СЃС‹ РЅРµ РѕР±РЅР°СЂСѓР¶РµРЅС‹")
            )
            return

        networks = sorted(networks, key=lambda x: not x["is_up"])

        for network in networks:
            frame = QFrame()
            frame.setFrameShape(QFrame.StyledPanel)
            network_layout = QVBoxLayout(frame)

            name = QLabel(network["name"])
            name.setStyleSheet("font-size: 20px; font-weight: bold;")

            status = QLabel(
                "в—Џ РџРѕРґРєР»СЋС‡РµРЅРѕ" if network["is_up"] else "в—Џ РћС‚РєР»СЋС‡РµРЅРѕ"
            )

            details = QLabel(
                f"IPv4: {network['ipv4']}\n"
                f"IPv6: {network['ipv6']}\n"
                f"MAC: {network['mac']}\n"
                f"РЎРєРѕСЂРѕСЃС‚СЊ РёРЅС‚РµСЂС„РµР№СЃР°: {network['speed_mbps']} Mbps\n"
                f"РћС‚РїСЂР°РІР»РµРЅРѕ: {self.format_bytes(network['bytes_sent'])}\n"
                f"РџРѕР»СѓС‡РµРЅРѕ: {self.format_bytes(network['bytes_recv'])}"
            )
            details.setStyleSheet("font-size: 15px;")

            network_layout.addWidget(name)
            network_layout.addWidget(status)
            network_layout.addWidget(details)

            self.network_layout.addWidget(frame)

    @staticmethod
    def format_bytes(value):
        if value < 1024:
            return f"{value:.0f} B"
        if value < 1024 ** 2:
            return f"{value / 1024:.1f} KB"
        if value < 1024 ** 3:
            return f"{value / (1024 ** 2):.1f} MB"
        return f"{value / (1024 ** 3):.2f} GB"

    def update_dashboard(self):
        cpu = get_cpu_info()
        cpu_usage = int(cpu["usage"])

        self.cpu_value.setText(f"{cpu_usage}%")
        self.cpu_bar.setValue(cpu_usage)

        memory = get_memory_info()
        ram_usage = int(memory["percent"])

        used_gb = memory["used"] / (1024 ** 3)
        total_gb = memory["total"] / (1024 ** 3)

        self.ram_value.setText(f"{used_gb:.1f} / {total_gb:.1f} GB")
        self.ram_bar.setValue(ram_usage)

        gpu = get_gpu_info()

        gpu_name = gpu["name"]
        gpu_memory = gpu["memory_total"]
        gpu_usage = gpu["usage"]

        if gpu_usage is not None:
            self.gpu_value.setText(f"{int(gpu_usage)}%")
            self.gpu_bar.setValue(int(gpu_usage))
        else:
            self.gpu_value.setText(gpu_name)
            self.gpu_bar.setValue(0)

        gpu_details = (
            f"GPU: {gpu_name}\n"
            f"Vendor: {gpu['vendor']}\n"
            f"VRAM: {gpu_memory:.1f} GB"
        )

        if gpu["temperature"] is not None:
            gpu_details += f"\nTemperature: {gpu['temperature']:.0f} В°C"

        if "driver" in gpu:
            gpu_details += f"\nDriver: {gpu['driver']}"

        self.gpu_details.setText(gpu_details)

        system = get_system_info()

        self.system_label.setText(
            f"Computer: {system['computer']}\n"
            f"System: {system['system']} {system['release']}\n"
            f"Architecture: {system['machine']}\n"
            f"CPU: {cpu['name']}\n"
            f"Cores: {cpu['cores']}\n"
            f"Threads: {cpu['threads']}"
        )



