from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel


class StatusBadge(QLabel):

    COLORS = {
        "excellent": "#42D392",
        "good": "#F5C542",
        "warning": "#FF6B6B",
    }

    ICONS = {
        "excellent": "🟢",
        "good": "🟡",
        "warning": "🔴",
    }

    def __init__(self, status="excellent", text="Healthy"):
        super().__init__()

        self.setAlignment(Qt.AlignCenter)
        self.setMinimumHeight(34)

        self.set_status(status, text)

    def set_status(self, status, text):

        color = self.COLORS.get(status, "#42D392")
        icon = self.ICONS.get(status, "🟢")

        self.setText(f"{icon}  {text}")

        self.setStyleSheet(f"""
            QLabel {{
                background-color: {color};
                color: white;
                border-radius: 10px;
                padding: 6px 14px;
                font-weight: bold;
            }}
        """)