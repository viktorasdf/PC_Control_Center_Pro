from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
)


class BasePage(QWidget):

    def __init__(self, title: str, subtitle: str = ""):
        super().__init__()

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(35, 30, 35, 30)
        self.layout.setSpacing(20)

        self.title = QLabel(title)
        self.title.setAlignment(Qt.AlignLeft)
        self.title.setStyleSheet("""
            font-size:30px;
            font-weight:bold;
        """)

        self.layout.addWidget(self.title)

        if subtitle:
            self.subtitle = QLabel(subtitle)
            self.subtitle.setStyleSheet("""
                font-size:15px;
                color:gray;
            """)
            self.layout.addWidget(self.subtitle)

    def add_widget(self, widget):
        self.layout.addWidget(widget)

    def add_layout(self, layout):
        self.layout.addLayout(layout)

    def add_stretch(self):
        self.layout.addStretch()