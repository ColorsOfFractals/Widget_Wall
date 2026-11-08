from weather_pocket import PocketWeather
import sys
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QProcess, Signal, Qt, QUrl, QObject, Slot
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QPushButton, QTextEdit
)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtGui import QIcon

ROOT = Path(__file__).resolve().parent

COLORS = {
    "scratchpad": "#ff922f",
    "counter": "#8ced53",
    "clock": "#df6580"
}

PALETTE = [
    ("Ember",   "#ff922f", "#25160d"),
    ("Toxic",   "#8ced53", "#122010"),
    ("Rose",    "#df6580", "#261019"),
    ("Cyan",    "#53dfff", "#0b2027"),
    ("Violet",  "#b18aff", "#1b142a"),
    ("Gold",    "#ffd166", "#27200d"),
    ("Ice",     "#a3d9ff", "#11212b"),
    ("Crimson", "#ff465e", "#270e14")
]


class MiniWidget(QWidget):
    def __init__(self, kind, number):
        super().__init__()

        self.kind = kind
        self.count = 0
        self.drag_offset = None
        self.accent = COLORS[kind]
        self.color_index = next(
            i for i, item in enumerate(PALETTE)
            if item[1] == self.accent
        )

        self.setWindowFlags(
            Qt.Window |
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setWindowTitle(f"Widget_Wall | {kind}")

        self.setStyleSheet(f"""
            QWidget {{
                background: #110d10;
                color: #fff0e7;
                font-family: Segoe UI;
            }}
            QLabel#heading {{
                color: {self.accent};
                font-size: 12px;
                font-weight: bold;
            }}
            QPushButton {{
                background: #261b1c;
                color: {self.accent};
                border: 1px solid {self.accent};
                border-radius: 6px;
                padding: 7px;
            }}
            QPushButton:hover {{
                background: #49302b;
            }}
            QTextEdit {{
                background: #1b1519;
                color: #f8e9dc;
                border: 1px solid #684039;
                border-radius: 7px;
                padding: 8px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 12)

        self.header_widget = QWidget()
        self.header_widget.setFixedHeight(38)
        self.header_widget.setCursor(Qt.OpenHandCursor)

        header = QHBoxLayout(self.header_widget)
        header.setContentsMargins(0, 0, 0, 0)

        title = QLabel(kind.upper())
        title.setObjectName("heading")
        title.setAttribute(Qt.WA_TransparentForMouseEvents)
        header.addWidget(title)
        header.addStretch()

        close = QPushButton("×")
        close.setFixedSize(29, 29)
        close.clicked.connect(self.close)
        header.addWidget(close)

        layout.addWidget(self.header_widget)

        self.header_widget.mousePressEvent = self.drag_start
        self.header_widget.mouseMoveEvent = self.drag_move
        self.header_widget.mouseReleaseEvent = self.drag_end

        if kind == "scratchpad":
            self.resize(310, 260)

            self.editor = QTextEdit()
            self.editor.setPlaceholderText("Tiny thoughts go here...")
            layout.addWidget(self.editor)

            buttons = QHBoxLayout()
            copy = QPushButton("COPY")
            clear = QPushButton("CLEAR")

            copy.clicked.connect(
                lambda: QApplication.clipboard().setText(
                    self.editor.toPlainText()
                )
            )
            clear.clicked.connect(self.editor.clear)

            buttons.addWidget(copy)
            buttons.addWidget(clear)
            layout.addLayout(buttons)

        elif kind == "counter":
            self.resize(230, 160)

            self.value = QLabel("0")
            self.value.setAlignment(Qt.AlignCenter)
            self.value.setStyleSheet(
                f"font-size:42px;font-weight:bold;color:{self.accent};"
            )
            layout.addWidget(self.value)

            buttons = QHBoxLayout()

            for label, delta in [("−", -1), ("+", 1)]:
                button = QPushButton(label)
                button.clicked.connect(
                    lambda checked=False, d=delta: self.change(d)
                )
                buttons.addWidget(button)

            reset = QPushButton("RESET")
            reset.clicked.connect(self.reset)
            buttons.addWidget(reset)
            layout.addLayout(buttons)

        elif kind == "clock":
            from PySide6.QtCore import QTimer

            self.resize(280, 125)
            self.display = QLabel()
            self.display.setAlignment(Qt.AlignCenter)
            self.display.setStyleSheet(
                f"font: bold 30px Consolas;color:{self.accent};"
            )
            layout.addWidget(self.display)

            self.timer = QTimer(self)
            self.timer.timeout.connect(self.update_clock)
            self.timer.start(1000)
            self.update_clock()

        self.color_button = QPushButton("COLOR!")
        self.color_button.setObjectName("colorButton")
        self.color_button.setCursor(Qt.PointingHandCursor)
        self.color_button.clicked.connect(self.cycle_color)
        layout.addWidget(self.color_button)

        self.apply_color()

        self.move(140 + (number % 8) * 35,
                  140 + (number % 8) * 35)

    def cycle_color(self):
        self.color_index = (self.color_index + 1) % len(PALETTE)
        self.apply_color()

    def apply_color(self):
        name, accent, background = PALETTE[self.color_index]
        self.accent = accent

        self.setStyleSheet(f"""
            QWidget {{
                background: {background};
                color: #fff0e7;
                font-family: Segoe UI;
            }}
            QLabel#heading {{
                color: {accent};
                font-size: 12px;
                font-weight: bold;
            }}
            QPushButton {{
                background: #20171b;
                color: {accent};
                border: 1px solid {accent};
                border-radius: 6px;
                padding: 7px;
            }}
            QPushButton:hover {{
                background: {background};
            }}
            QTextEdit {{
                background: #120f13;
                color: #f8e9dc;
                border: 1px solid {accent};
                border-radius: 7px;
                padding: 8px;
            }}
        """)

        if hasattr(self, "value"):
            self.value.setStyleSheet(
                f"font-size:42px;font-weight:bold;color:{accent};"
            )

        if hasattr(self, "display"):
            self.display.setStyleSheet(
                f"font:bold 30px Consolas;color:{accent};"
            )

        self.color_button.setToolTip(f"Current color: {name}")
    def change(self, delta):
        self.count += delta
        self.value.setText(str(self.count))

    def reset(self):
        self.count = 0
        self.value.setText("0")

    def update_clock(self):
        self.display.setText(
            datetime.now().strftime("%I:%M:%S %p")
        )

    def drag_start(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_offset = (
                event.globalPosition().toPoint()
                - self.frameGeometry().topLeft()
            )
            self.header_widget.setCursor(Qt.ClosedHandCursor)
            event.accept()

    def drag_move(self, event):
        if self.drag_offset is not None:
            if event.buttons() & Qt.LeftButton:
                self.move(
                    event.globalPosition().toPoint()
                    - self.drag_offset
                )
                event.accept()

    def drag_end(self, event):
        self.drag_offset = None
        self.header_widget.setCursor(Qt.OpenHandCursor)
        event.accept()


class SonicTitleBar(QWidget):
    """Chromatic native title bar for the detached music laboratory."""
    def __init__(self, host):
        super().__init__()
        self.host = host
        self.drag_offset = None
        self.setFixedHeight(46)
        self.setAttribute(Qt.WA_StyledBackground, False)
        from PySide6.QtGui import QPixmap
        row = QHBoxLayout(self)
        row.setContentsMargins(12, 0, 8, 0)
        icon = QLabel()
        icon.setPixmap(QPixmap(str(ROOT / 'sonic_workshop' / 'assets' / 'Neon Music Book Icon.png')).scaled(28, 28, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        icon.setFixedSize(28, 28)
        row.addWidget(icon)
        label = QLabel('SONIC WORKSHOP  |  LIVING MUSIC BOOK')
        label.setStyleSheet('color:#ffd5ab;font:bold 12px Segoe UI;border:none;background:transparent;letter-spacing:1px;')
        row.addWidget(label)
        row.addStretch()
        for symbol, callback in [('\u2212', host.showMinimized), ('\u25a1', self.toggle_maximize), ('\u00d7', host.close)]:
            button = QPushButton(symbol)
            button.setFixedSize(42, 31)
            button.setStyleSheet('QPushButton{background:transparent;color:#ffe8f4;border:none;font-size:18px;} QPushButton:hover{background:#7a2858;border-radius:5px;}')
            button.clicked.connect(callback)
            row.addWidget(button)

    def paintEvent(self, event):
        from PySide6.QtGui import QColor, QPainter, QLinearGradient, QPen
        painter = QPainter(self)
        gradient = QLinearGradient(0, 0, self.width(), 0)
        gradient.setColorAt(0.0, QColor('#522318'))
        gradient.setColorAt(0.33, QColor('#33204a'))
        gradient.setColorAt(0.67, QColor('#102d3d'))
        gradient.setColorAt(1.0, QColor('#4b163b'))
        painter.fillRect(self.rect(), gradient)
        painter.setPen(QPen(QColor('#b65fa0'), 1))
        painter.drawLine(0, self.height()-1, self.width(), self.height()-1)
        painter.end()

    def toggle_maximize(self):
        self.host.showNormal() if self.host.isMaximized() else self.host.showMaximized()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_offset = event.globalPosition().toPoint() - self.host.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self.drag_offset is not None and event.buttons() & Qt.LeftButton:
            if not self.host.isMaximized():
                self.host.move(event.globalPosition().toPoint() - self.drag_offset)
            event.accept()

    def mouseReleaseEvent(self, event):
        self.drag_offset = None

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.toggle_maximize()

class SonicWindow(QMainWindow):
    """Independent WebEngine window for local Sonic Workshop instruments."""
    def __init__(self, path):
        super().__init__()
        from PySide6.QtGui import QIcon
        self.setWindowTitle('Widget_Wall | Sonic Workshop')
        self.setWindowIcon(QIcon(str(ROOT / 'sonic_workshop' / 'assets' / 'Sonic_Music_Book.ico')))
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.resize(1100, 850)
        self.setMinimumSize(640, 480)
        shell = QWidget(self)
        shell.setStyleSheet('background:#090d16;')
        layout = QVBoxLayout(shell)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.sonic_titlebar = SonicTitleBar(self)
        layout.addWidget(self.sonic_titlebar)
        self.web = QWebEngineView(self)
        layout.addWidget(self.web, 1)
        self.setCentralWidget(shell)
        self.web.load(QUrl.fromLocalFile(str(path)))

class Bridge(QObject):
    def __init__(self, host):
        super().__init__()
        self.host = host

    @Slot(str)
    def spawn(self, kind):
        if kind not in COLORS and kind not in ("weather", "sonic-workshop", "polyrhythm-reactor"):
            return
        self.host.spawn_widget(kind)



    powerShellDiscovered = Signal(str)

    @Slot()
    def discoverPowerShell(self):
        if getattr(self, "_ps_process", None) is not None:
            if self._ps_process.state() != QProcess.NotRunning:
                return
        executable = r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"
        script = ROOT / "powershell_discovery.ps1"
        if not script.is_file():
            self.powerShellDiscovered.emit('{"ok":false,"error":"Discovery script missing"}')
            return
        process = QProcess(self)
        self._ps_process = process
        process.setProgram(executable)
        process.setArguments(["-NoLogo", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File", str(script)])
        process.setProcessChannelMode(QProcess.SeparateChannels)
        def finished(exit_code, status):
            stdout = bytes(process.readAllStandardOutput()).decode("utf-8-sig", errors="replace").strip()
            stderr = bytes(process.readAllStandardError()).decode("utf-8-sig", errors="replace").strip()
            if exit_code == 0 and stdout:
                self.powerShellDiscovered.emit(stdout)
            else:
                import json
                self.powerShellDiscovered.emit(json.dumps({"ok": False, "error": (stderr or "Discovery failed")[:400]}))
            process.deleteLater()
            self._ps_process = None
        process.finished.connect(finished)
        process.start()

class TitleBar(QWidget):
    def __init__(self, host):
        super().__init__()
        self.host = host
        self.drag_offset = None
        self.setFixedHeight(42)
        self.setObjectName("InfernalTitleBar")
        self.setAttribute(Qt.WA_StyledBackground, False)

        row = QHBoxLayout(self)
        row.setContentsMargins(14, 0, 7, 0)

        label = QLabel("◆  WIDGET_WALL  |  RING 0.8")
        label.setStyleSheet(
            "color:#ffab65;font:bold 12px Segoe UI;border:none;"
        )
        row.addWidget(label)
        row.addStretch()

        for symbol, callback in [
            ("−", host.showMinimized),
            ("□", self.toggle_maximize),
            ("×", host.close)
        ]:
            button = QPushButton(symbol)
            button.setFixedSize(42, 30)
            button.setStyleSheet("""
                QPushButton {
                    background:transparent;
                    color:#ffe5d1;
                    border:none;
                    font-size:17px;
                }
                QPushButton:hover {
                    background:#76351e;
                }
            """)
            button.clicked.connect(callback)
            row.addWidget(button)

    def paintEvent(self, event):
        from PySide6.QtGui import QColor, QPainter, QLinearGradient, QPen

        painter = QPainter(self)

        gradient = QLinearGradient(0, 0, self.width(), 0)
        gradient.setColorAt(0.0, QColor("#542714"))
        gradient.setColorAt(0.48, QColor("#19251b"))
        gradient.setColorAt(1.0, QColor("#49182c"))

        painter.fillRect(self.rect(), gradient)

        painter.setPen(QPen(QColor("#9b4b29"), 1))
        painter.drawLine(
            0, self.height() - 1,
            self.width(), self.height() - 1
        )

        painter.end()
    def toggle_maximize(self):
        if self.host.isMaximized():
            self.host.showNormal()
        else:
            self.host.showMaximized()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_offset = (
                event.globalPosition().toPoint()
                - self.host.frameGeometry().topLeft()
            )

    def mouseMoveEvent(self, event):
        if self.drag_offset is not None:
            if event.buttons() & Qt.LeftButton:
                if not self.host.isMaximized():
                    self.host.move(
                        event.globalPosition().toPoint()
                        - self.drag_offset
                    )

    def mouseReleaseEvent(self, event):
        self.drag_offset = None

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.toggle_maximize()


class WidgetWall(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon(str(Path(__file__).resolve().parent / 'assets' / 'Widget_Wall.ico')))

        self.widgets = []
        self.setWindowTitle("Widget_Wall | Ring 0.8")
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.resize(1100, 820)
        self.setMinimumSize(700, 520)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(1, 1, 1, 1)
        layout.setSpacing(0)

        self.titlebar = TitleBar(self)
        layout.addWidget(self.titlebar)

        self.web = QWebEngineView()
        layout.addWidget(self.web, 1)
        self.setCentralWidget(container)

        self.bridge = Bridge(self)
        self.channel = QWebChannel(self.web.page())
        self.channel.registerObject("widgetBridge", self.bridge)
        self.web.page().setWebChannel(self.channel)

        page = ROOT / "dist" / "index.html"
        if not page.exists():
            raise FileNotFoundError("Run npm run build first.")

        self.web.load(QUrl.fromLocalFile(str(page)))

    def spawn_widget(self, kind):
        if kind in ("sonic-workshop", "polyrhythm-reactor"):
            filename = "index.html" if kind == "sonic-workshop" else "Polyrhythm_Reactor.html"
            path = ROOT / "sonic_workshop" / filename
            if not path.is_file():
                print(f"Sonic instrument missing: {path}")
                return
            widget = SonicWindow(path)
            self.widgets.append(widget)
            widget.destroyed.connect(lambda obj=None, w=widget: self.remove_widget(w))
            widget.show()
            widget.raise_()
            return
        widget = PocketWeather(len(self.widgets)) if kind == "weather" else MiniWidget(kind, len(self.widgets))
        self.widgets.append(widget)
        widget.destroyed.connect(
            lambda obj=None, w=widget: self.remove_widget(w)
        )
        widget.show()
        widget.raise_()

    def remove_widget(self, widget):
        if widget in self.widgets:
            self.widgets.remove(widget)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WidgetWall()
    window.show()
    sys.exit(app.exec())