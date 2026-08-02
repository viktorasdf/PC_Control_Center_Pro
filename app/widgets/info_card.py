from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QProgressBar,
    QVBoxLayout,
)


class InfoCard(QFrame):

    def __init__(self, title: str):
        super().__init__()

        self.setFrameShape(QFrame.StyledPanel)
        self.setObjectName("InfoCard")

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        self.title_label = QLabel(title)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet(
            "font-size:18px;font-weight:bold;"
        )

        self.value_label = QLabel("--")
        self.value_label.setAlignment(Qt.AlignCenter)
        self.value_label.setStyleSheet(
            "font-size:30px;font-weight:bold;"
        )

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)

        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)
        layout.addWidget(self.progress)

    def set_value(self, value):
        self.value_label.setText(str(value))

    def set_progress(self, value):
        self.progress.setValue(int(value))

    def set_title(self, title):
        self.title_label.setText(title)