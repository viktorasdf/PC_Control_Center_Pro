from PySide6.QtWidgets import QWidget,QVBoxLayout,QLabel,QFrame

class PlaceholderPage(QWidget):
    def __init__(self,title,subtitle,parent=None):
        super().__init__(parent); self.setObjectName('PlaceholderPage'); self.setStyleSheet("QWidget#PlaceholderPage{background:#050b18;} QLabel{color:#f4f7ff;}")
        lay=QVBoxLayout(self); lay.setContentsMargins(40,40,40,40); lay.setSpacing(10)
        t=QLabel(title); t.setStyleSheet("font-size:30px;font-weight:800;background:transparent;border:none;")
        s=QLabel(subtitle); s.setStyleSheet("font-size:13px;color:#8ea3bd;background:transparent;border:none;")
        card=QFrame(); card.setStyleSheet("QFrame{background:#091528;border:1px solid #1d3152;border-radius:14px;}")
        cl=QVBoxLayout(card); cl.setContentsMargins(24,24,24,24); cl.addWidget(QLabel("Раздел подготовлен для следующего этапа.")); lay.addWidget(t); lay.addWidget(s); lay.addWidget(card); lay.addStretch()
