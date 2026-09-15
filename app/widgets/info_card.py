from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QProgressBar,
    QVBoxLayout,
)

from app.themes.styles import (
    CARD_PADDING,
    CARD_SPACING,
    TITLE_SIZE,
    VALUE_SIZE,
)


class InfoCard(QFrame):

    def __init__(self, title: str):
        super().__init__()


        self.setFrameShape(QFrame.StyledPanel)
        self.setObjectName("InfoCard")
        self.setMinimumHeight(170)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            CARD_PADDING,
            CARD_PADDING,
            CARD_PADDING,
            CARD_PADDING,
        )
        layout.setSpacing(CARD_SPACING)
        layout.setAlignment(Qt.AlignCenter)

        self.title_label = QLabel(title)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet(
            f"font-size:{TITLE_SIZE}px;font-weight:bold;"
        )



        self.value_label = QLabel("--")
        self.value_label.setAlignment(Qt.AlignCenter)
        self.value_label.setStyleSheet(
    f"font-size:{VALUE_SIZE}px;font-weight:bold;"
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