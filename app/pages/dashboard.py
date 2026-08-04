from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QGridLayout,
    QFrame,
    QProgressBar
)

from app.services.system_info import (
    get_cpu_info,
    get_memory_info,
    get_system_info
)

from app.services.gpu_info import get_gpu_info
from app.widgets.info_card import InfoCard


class DashboardPage(QWidget):

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(35, 30, 35, 30)
        layout.setSpacing(20)

# ===== HEADER =====

header = QHBoxLayout()

# Левая часть
left_layout = QVBoxLayout()

title = QLabel("PC Control Center Pro")
title.setStyleSheet("""
font-size:32px;
font-weight:bold;
""")

subtitle = QLabel("System Dashboard")
subtitle.setStyleSheet("""
font-size:16px;
color:#909090;
""")

left_layout.addWidget(title)
left_layout.addWidget(subtitle)

# Правая часть
right_layout = QVBoxLayout()

self.status_label = QLabel("🟢 System OK")
self.status_label.setStyleSheet("""
font-size:16px;
font-weight:bold;
color:#44cc44;
""")

self.time_label = QLabel("--:--:--")
self.time_label.setStyleSheet("""
font-size:14px;
color:#909090;
""")

right_layout.addWidget(self.status_label)
right_layout.addWidget(self.time_label)

header.addLayout(left_layout)
header.addStretch()
header.addLayout(right_layout)

layout.addLayout(header)

        cards = QGridLayout()
        cards.setSpacing(20)

        self.cpu_card = InfoCard("CPU")
        self.ram_card = InfoCard("RAM")
        self.gpu_card = InfoCard("GPU")

        cards.addWidget(self.cpu_card, 0, 0)
        cards.addWidget(self.ram_card, 0, 1)
        cards.addWidget(self.gpu_card, 0, 2)

        layout.addLayout(cards)

        gpu_frame = QFrame()
        gpu_layout = QVBoxLayout(gpu_frame)

        gpu_title = QLabel("Graphics")
        gpu_title.setStyleSheet("font-size:20px;font-weight:bold;")

        self.gpu_details = QLabel()

        gpu_layout.addWidget(gpu_title)
        gpu_layout.addWidget(self.gpu_details)

        layout.addWidget(gpu_frame)

        system_frame = QFrame()
        system_layout = QVBoxLayout(system_frame)

        system_title = QLabel("System")
        system_title.setStyleSheet("font-size:20px;font-weight:bold;")

        self.system_label = QLabel()

        system_layout.addWidget(system_title)
        system_layout.addWidget(self.system_label)

        layout.addWidget(system_frame)

        layout.addStretch()



    def update_dashboard(self):

        cpu = get_cpu_info()
        cpu_usage = int(cpu["usage"])

        self.cpu_card.set_value(f"{cpu_usage}%")
        self.cpu_card.set_progress(cpu_usage)

        memory = get_memory_info()
        ram_usage = int(memory["percent"])

        used_gb = memory["used"] / (1024 ** 3)
        total_gb = memory["total"] / (1024 ** 3)

self.ram_card.set_value(
    f"{used_gb:.1f} / {total_gb:.1f} GB"
)
self.ram_card.set_progress(ram_usage)

        gpu = get_gpu_info()

        gpu_name = gpu["name"]
        gpu_memory = gpu["memory_total"]
        gpu_usage = gpu["usage"]

        if gpu_usage is not None:
    self.gpu_card.set_value(f"{int(gpu_usage)}%")
    self.gpu_card.set_progress(int(gpu_usage))
else:
    self.gpu_card.set_value(gpu_name)
    self.gpu_card.set_progress(0)

        gpu_details = (
            f"GPU: {gpu_name}\n"
            f"Vendor: {gpu['vendor']}\n"
            f"VRAM: {gpu_memory:.1f} GB"
        )

        if gpu["temperature"] is not None:
            gpu_details += (
                f"\nTemperature: {gpu['temperature']:.0f} °C"
            )

        if "driver" in gpu:
            gpu_details += (
                f"\nDriver: {gpu['driver']}"
            )

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