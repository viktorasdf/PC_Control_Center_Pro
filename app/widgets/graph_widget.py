from collections import deque

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QPainter, QPen
from PySide6.QtWidgets import QWidget


class GraphWidget(QWidget):

    def __init__(
        self,
        title,
        minimum=0,
        maximum=100,
        history=60,
        parent=None,
    ):
        super().__init__(parent)

        self.title = title
        self.minimum = minimum
        self.maximum = maximum

        self.values = deque(maxlen=history)

        self.setMinimumHeight(180)

    def add_value(self, value):
        self.values.append(value)
        self.update()

    def clear(self):
        self.values.clear()
        self.update()

    def set_range(self, minimum, maximum):
        self.minimum = minimum
        self.maximum = maximum
        self.update()

    def paintEvent(self, event):

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = self.rect()

        painter.fillRect(rect, self.palette().base())

        painter.drawText(12, 22, self.title)

        left = 45
        top = 35
        right = 10
        bottom = 20

        width = rect.width() - left - right
        height = rect.height() - top - bottom

        grid_pen = QPen(Qt.gray)
        grid_pen.setStyle(Qt.DashLine)

        painter.setPen(grid_pen)

        for i in range(5):
            y = top + height * i / 4
            painter.drawLine(left, int(y), left + width, int(y))

        if len(self.values) < 2:
            return

        line_pen = QPen(Qt.green)
        line_pen.setWidth(2)

        painter.setPen(line_pen)

        value_range = max(
            1,
            self.maximum - self.minimum,
        )

        points = []

        values = list(self.values)

        for i, value in enumerate(values):

            x = left + width * i / (len(values) - 1)

            value = max(
                self.minimum,
                min(value, self.maximum),
            )

            y = (
                top
                + height
                - (
                    (value - self.minimum)
                    / value_range
                )
                * height
            )

            points.append(QPointF(x, y))

        for i in range(len(points) - 1):
            painter.drawLine(points[i], points[i + 1])