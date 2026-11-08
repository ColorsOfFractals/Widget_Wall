"""Native analog clock for Widget Wall."""
from datetime import datetime
from math import sin, cos, pi
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QPen, QFont
from PySide6.QtWidgets import QWidget

class AnalogClock(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Widget Wall | Analog Clock')
        self.resize(280, 300)
        self.setMinimumSize(160, 160)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(1000)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor('#17151f'))
        side = min(self.width(), self.height())
        p.translate(self.width()/2, self.height()/2)
        p.scale(side/240, side/240)
        p.setPen(QPen(QColor('#a77ed5'), 3))
        p.setBrush(QColor('#201a2a'))
        p.drawEllipse(-104, -104, 208, 208)
        for n in range(60):
            angle = n*pi/30
            r = 82 if n % 5 == 0 else 91
            p.setPen(QPen(QColor('#e4c4ff' if n%5==0 else '#6c597c'), 3 if n%5==0 else 1))
            p.drawLine(int(sin(angle)*r), int(-cos(angle)*r), int(sin(angle)*96), int(-cos(angle)*96))
        now = datetime.now()
        def hand(angle, length, width, color):
            p.setPen(QPen(QColor(color), width, Qt.SolidLine, Qt.RoundCap))
            p.drawLine(0, 0, int(sin(angle)*length), int(-cos(angle)*length))
        hand((now.hour%12 + now.minute/60)*pi/6, 49, 7, '#f5caa5')
        hand((now.minute + now.second/60)*pi/30, 74, 5, '#e9d8ff')
        hand(now.second*pi/30, 82, 2, '#d78dff')
        p.setPen(Qt.NoPen)
        p.setBrush(QColor('#e9d8ff'))
        p.drawEllipse(-5, -5, 10, 10)
        p.end()