from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QPen, QFont
from PySide6.QtWidgets import QWidget


class GraphWidget(QWidget):

    def __init__(
        self,
        title="Graph",
        minimum_value=0,
        maximum_value=100,
        parent=None,
    ):
        super().__init__(parent)

        self.title = title
        self.minimum_value = minimum_value
        self.maximum_value = maximum_value

        # Старый режим: один график
        self.values = []

        # Новый режим: несколько графиков
        self.series = {}

        self.setMinimumHeight(260)

        self.setStyleSheet("""
            QWidget {
                background: #111827;
            }
        """)

    # ==========================================================
    # ONE SERIES
    # ==========================================================

    def set_values(self, values):

        self.values = list(values)[-60:]

        self.series = {
            "GPU": self.values
        }

        self.update()

    # ==========================================================
    # MULTIPLE SERIES
    # ==========================================================

    def set_series(self, series):

        cleaned = {}

        if not isinstance(series, dict):
            self.series = {}
            self.update()
            return

        for name, values in series.items():

            if values is None:
                continue

            try:
                clean_values = []

                for value in list(values)[-60:]:

                    try:
                        if value is None:
                            continue

                        value = float(value)

                        if value != value:
                            continue

                        if value < self.minimum_value:
                            value = self.minimum_value

                        if value > self.maximum_value:
                            value = self.maximum_value

                        clean_values.append(value)

                    except (ValueError, TypeError):
                        continue

                if clean_values:
                    cleaned[str(name)] = clean_values

            except Exception:
                continue

        self.series = cleaned

        # Совместимость со старым кодом
        if "GPU" in cleaned:
            self.values = cleaned["GPU"]

        self.update()

    # ==========================================================
    # PAINT
    # ==========================================================

    def paintEvent(self, event):

        painter = QPainter(self)

        painter.setRenderHint(
            QPainter.Antialiasing
        )

        width = self.width()
        height = self.height()

        left = 65
        right = 25
        top = 45
        bottom = 35

        graph_width = max(
            1,
            width - left - right
        )

        graph_height = max(
            1,
            height - top - bottom
        )

        # ======================================================
        # TITLE
        # ======================================================

        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)

        painter.setFont(title_font)
        painter.setPen(
            QPen(Qt.GlobalColor.white)
        )

        painter.drawText(
            left,
            25,
            self.title
        )

        # ======================================================
        # GRID
        # ======================================================

        grid_pen = QPen(
            Qt.GlobalColor.darkGray
        )

        grid_pen.setStyle(
            Qt.PenStyle.DashLine
        )

        painter.setPen(grid_pen)

        for i in range(6):

            y = top + (
                graph_height * i / 5
            )

            painter.drawLine(
                left,
                int(y),
                width - right,
                int(y)
            )

        # ======================================================
        # AXIS
        # ======================================================

        axis_font = QFont()
        axis_font.setPointSize(10)
        axis_font.setBold(True)

        painter.setFont(axis_font)

        painter.setPen(
            QPen(Qt.GlobalColor.white)
        )

        for i in range(6):

            value = (
                self.maximum_value
                - (
                    self.maximum_value
                    - self.minimum_value
                ) * i / 5
            )

            y = top + (
                graph_height * i / 5
            )

            painter.drawText(
                5,
                int(y + 4),
                f"{value:.0f}%"
            )

        # ======================================================
        # DATA
        # ======================================================

        if not self.series:

            empty_font = QFont()
            empty_font.setPointSize(12)
            empty_font.setBold(True)

            painter.setFont(empty_font)

            painter.setPen(
                QPen(Qt.GlobalColor.lightGray)
            )

            painter.drawText(
                left,
                top + graph_height // 2,
                "GPU data unavailable"
            )

            painter.end()
            return

        # ======================================================
        # GRAPH COLORS
        # ======================================================

        colors = [
            Qt.GlobalColor.cyan,
            Qt.GlobalColor.green,
            Qt.GlobalColor.yellow,
            Qt.GlobalColor.magenta,
        ]

        # ======================================================
        # DRAW SERIES
        # ======================================================

        legend_x = left
        legend_y = height - 10

        for series_index, (name, values) in enumerate(
            self.series.items()
        ):

            if not values:
                continue

            color = colors[
                series_index % len(colors)
            ]

            pen = QPen(color)
            pen.setWidth(2)

            painter.setPen(pen)

            points = []

            count = len(values)

            for index, value in enumerate(values):

                try:
                    value = float(value)
                except (ValueError, TypeError):
                    continue

                value = max(
                    self.minimum_value,
                    min(
                        self.maximum_value,
                        value
                    )
                )

                if count <= 1:
                    x = left
                else:
                    x = left + (
                        graph_width
                        * index
                        / (count - 1)
                    )

                value_range = (
                    self.maximum_value
                    - self.minimum_value
                )

                if value_range <= 0:
                    normalized = 0
                else:
                    normalized = (
                        value
                        - self.minimum_value
                    ) / value_range

                y = (
                    top
                    + graph_height
                    * (1 - normalized)
                )

                points.append(
                    (int(x), int(y))
                )

            for i in range(1, len(points)):

                painter.drawLine(
                    points[i - 1][0],
                    points[i - 1][1],
                    points[i][0],
                    points[i][1],
                )

            # ==================================================
            # CURRENT VALUE
            # ==================================================

            if points:

                current = values[-1]

                try:
                    current = float(current)
                except (ValueError, TypeError):
                    current = 0.0

                current_font = QFont()
                current_font.setPointSize(11)
                current_font.setBold(True)

                painter.setFont(current_font)

                painter.setPen(
                    QPen(color)
                )

                painter.drawText(
                    width - 105,
                    25 + series_index * 18,
                    f"{name}: {current:.1f}%"
                )

            # ==================================================
            # LEGEND
            # ==================================================

            painter.setPen(
                QPen(color)
            )

            painter.drawText(
                legend_x,
                legend_y,
                str(name)
            )

            legend_x += 100

        painter.end()