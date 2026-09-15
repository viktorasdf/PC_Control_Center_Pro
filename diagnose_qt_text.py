from PySide6.QtWidgets import QApplication, QLabel, QPushButton
from app.core.main_window import MainWindow
import sys

app = QApplication(sys.argv)
w = MainWindow()

print("=== ALL CYRILLIC QT TEXT ===")

for widget in [w] + w.findChildren(QLabel) + w.findChildren(QPushButton):
    try:
        text = widget.text().strip()
        if text and any('\u0400' <= ch <= '\u04ff' for ch in text):
            print(type(widget).__name__, "=>", repr(text))
    except Exception:
        pass

print("=== END ===")
