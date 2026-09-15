from collections import deque

import pyqtgraph as pg

from PySide6.QtWidgets import QFrame, QVBoxLayout


class HistoryGraph(QFrame):

    def __init__(self, title="History", max_points=60):
        super().__init__()

        self.data = deque(
            [0] * max_points,
            maxlen=max_points
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.graph = pg.PlotWidget(
            title=title
        )

        self.graph.setMinimumHeight(120)
        self.graph.setMaximumHeight(150)

        self.graph.setBackground(
            "#242730"
        )

        self.graph.showGrid(
            x=False,
            y=True,
            alpha=0.15
        )

        self.graph.setYRange(
            0,
            100,
            padding=0
        )

        self.graph.hideButtons()

        self.graph.setMouseEnabled(
            False,
            False
        )

        self.graph.setMenuEnabled(False)

        self.graph.getPlotItem().hideAxis(
            "bottom"
        )

        self.curve = self.graph.plot(
            pen=pg.mkPen(
                "#4DA3FF",
                width=2
            ),
            antialias=False
        )

        layout.addWidget(
            self.graph
        )

        self.last_value = None


    def add_value(self, value):

        try:
            value = float(value)
        except (ValueError, TypeError):
            return

        value = max(
            0,
            min(100, value)
        )

        self.data.append(value)

        if self.last_value == value:
            return

        self.last_value = value

        self.curve.setData(
            self.data,
            _callSync="off"
        )