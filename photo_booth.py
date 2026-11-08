"""Photo Booth: local image slideshow for Widget Wall."""
import json
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, QStandardPaths
from PySide6.QtGui import QColor, QPainter, QPixmap, QImageReader, QPainterPath
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFileDialog,
    QListWidget, QSpinBox, QComboBox, QCheckBox, QMessageBox
)

EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp', '.tif', '.tiff'}


def settings_file():
    base = QStandardPaths.writableLocation(QStandardPaths.AppConfigLocation)
    path = Path(base) / 'Widget_Wall'
    path.mkdir(parents=True, exist_ok=True)
    return path / 'photo_booth.json'


class Slideshow(QWidget):
    def __init__(self, photos, seconds, transition, shuffle, loop, fit, on_exit=None):
        super().__init__()
        self.photos = list(photos)
        if shuffle:
            import random
            random.shuffle(self.photos)
        self.seconds = seconds
        self.transition = transition
        self.loop = loop
        self.fit = fit
        self.on_exit = on_exit
        self.index = 0
        self.paused = False
        self.previous = None
        self.progress = 1.0
        self.setWindowTitle('Photo Booth | Slideshow')
        self.setStyleSheet('background: black;')
        self.setFocusPolicy(Qt.StrongFocus)
        self.slide_timer = QTimer(self)
        self.slide_timer.timeout.connect(self.next_slide)
        self.fade_timer = QTimer(self)
        self.fade_timer.setInterval(25)
        self.fade_timer.timeout.connect(self.fade_step)
        self.current = self.load_image(self.photos[0])

    def load_image(self, path):
        reader = QImageReader(str(path))
        reader.setAutoTransform(True)
        return QPixmap.fromImageReader(reader)

    def start(self):
        self.showFullScreen()
        self.slide_timer.start(self.seconds * 1000)

    def fade_step(self):
        self.progress = min(1.0, self.progress + 0.05)
        if self.progress >= 1:
            self.fade_timer.stop()
            self.previous = None
        self.update()

    def advance(self, step):
        target = self.index + step
        if target >= len(self.photos):
            if not self.loop:
                self.close()
                return
            target = 0
        if target < 0:
            target = len(self.photos) - 1 if self.loop else 0
        if target == self.index:
            return
        next_image = self.load_image(self.photos[target])
        if next_image.isNull():
            self.index = target
            self.advance(step)
            return
        self.previous = self.current if self.transition in ('Dissolve', 'Fractal Zoom') else None
        self.current = next_image
        self.index = target
        self.progress = 0.0 if self.previous is not None else 1.0
        if self.previous is not None:
            self.fade_timer.start()
        self.update()
        if not self.paused:
            self.slide_timer.start(self.seconds * 1000)

    def next_slide(self):
        self.advance(1)

    def paint_fractal_portal(self, painter):
        """Recursive photo tunnel and expanding circular destination portal."""
        from math import sin, pi, hypot

        p = max(0.0, min(1.0, self.progress))
        ease = p * p * (3.0 - 2.0 * p)
        bounds = self.rect()
        width, height = bounds.width(), bounds.height()
        if width < 2 or height < 2:
            return
        cx, cy = width / 2.0, height / 2.0

        def render(pixmap, x, y, w, h, opacity=1.0):
            if pixmap is None or pixmap.isNull() or w < 1 or h < 1:
                return
            painter.save()
            painter.setOpacity(max(0.0, min(1.0, opacity)))
            mode = Qt.KeepAspectRatioByExpanding if self.fit == 'Fill' else Qt.KeepAspectRatio
            scaled = pixmap.scaled(int(max(1, w)), int(max(1, h)), mode, Qt.SmoothTransformation)
            painter.setClipRect(int(x), int(y), int(w), int(h))
            painter.drawPixmap(int(x + (w - scaled.width()) / 2),
                               int(y + (h - scaled.height()) / 2), scaled)
            painter.restore()

        # Accelerating camera dive into the outgoing image.
        zoom = 1.0 + 2.2 * ease
        render(self.previous, cx - width * zoom / 2, cy - height * zoom / 2,
               width * zoom, height * zoom)

        # Recursively nested image windows; each ring shifts depth as we zoom.
        for depth in range(5, 0, -1):
            scale = 0.58 ** depth
            phase = (ease * 1.65 + depth * 0.17) % 1.0
            scale *= 1.0 + 1.8 * phase
            w, h = width * scale, height * scale
            painter.save()
            painter.setPen(QColor(185, 125, 255, int(155 * (1.0 - ease))))
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(int(cx - w / 2), int(cy - h / 2), int(w), int(h))
            painter.restore()
            render(self.previous, cx - w / 2, cy - h / 2, w, h,
                   opacity=0.65 * (1.0 - ease))

        # The destination photo opens as a circular wormhole from the center.
        radius = hypot(width, height) * 0.55 * ease
        painter.save()
        portal = QPainterPath()
        portal.addEllipse(cx - radius, cy - radius, radius * 2, radius * 2)
        painter.setClipPath(portal)
        incoming_zoom = 1.35 - 0.35 * ease
        render(self.current, cx - width * incoming_zoom / 2,
               cy - height * incoming_zoom / 2,
               width * incoming_zoom, height * incoming_zoom)
        painter.restore()
        if p < 0.99 and radius > 1:
            painter.save()
            glow = QColor(185, 125, 255, int(190 * sin(pi * ease)))
            painter.setPen(glow)
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(int(cx - radius), int(cy - radius),
                                int(radius * 2), int(radius * 2))
            painter.restore()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor('black'))
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        def draw(pixmap, opacity):
            if pixmap is None or pixmap.isNull():
                return
            bounds = self.rect()
            scaled = pixmap.scaled(bounds.size(),
                Qt.KeepAspectRatioByExpanding if self.fit == 'Fill' else Qt.KeepAspectRatio,
                Qt.SmoothTransformation)
            painter.save()
            painter.setOpacity(opacity)
            if self.fit == 'Fill':
                painter.setClipRect(bounds)
            painter.drawPixmap((bounds.width() - scaled.width()) // 2,
                               (bounds.height() - scaled.height()) // 2, scaled)
            painter.restore()
        if self.previous is not None and self.transition == 'Fractal Zoom':
            self.paint_fractal_portal(painter)
        elif self.previous is not None:
            draw(self.previous, 1.0)
            draw(self.current, self.progress)
        else:
            draw(self.current, 1.0)
        painter.end()

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_Escape:
            self.close()
        elif key == Qt.Key_Space:
            self.paused = not self.paused
            if self.paused:
                self.slide_timer.stop()
            else:
                self.slide_timer.start(self.seconds * 1000)
        elif key in (Qt.Key_Right, Qt.Key_Down):
            self.advance(1)
        elif key in (Qt.Key_Left, Qt.Key_Up):
            self.advance(-1)
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event):
        self.slide_timer.stop()
        self.fade_timer.stop()
        super().closeEvent(event)
        if self.on_exit:
            self.on_exit()


class PhotoBoothTitleBar(QWidget):
    """Compact draggable title bar for the Photo Booth settings window."""
    def __init__(self, host):
        super().__init__(host)
        self.host = host
        self.setObjectName('photoTitleBar')
        self.setFixedHeight(38)
        row = QHBoxLayout(self)
        row.setContentsMargins(12, 2, 5, 2)
        row.setSpacing(3)
        label = QLabel('PHOTO BOOTH')
        label.setObjectName('photoTitleLabel')
        row.addWidget(label)
        row.addStretch(1)
        for text, action, name in (
            ('-', host.showMinimized, 'photoMinimize'),
            ('[]', host.toggle_maximize, 'photoMaximize'),
            ('X', host.close, 'photoClose'),
        ):
            button = QPushButton(text)
            button.setObjectName(name)
            button.setFixedSize(34, 29)
            button.setFocusPolicy(Qt.NoFocus)
            button.clicked.connect(action)
            row.addWidget(button)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.host.windowHandle().startSystemMove()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.host.toggle_maximize()
            event.accept()
        else:
            super().mouseDoubleClickEvent(event)

class PhotoBooth(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Widget Wall | Photo Booth')
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.resize(570, 520)
        self.setStyleSheet('''
            QWidget { background: #17171f; color: #eeeaf6; font-size: 13px; }
            QPushButton, QComboBox, QSpinBox { background: #30263c; border: 1px solid #75538d;
                border-radius: 6px; padding: 8px; }
            QPushButton:hover { background: #513765; }
            QListWidget { background: #111018; border: 1px solid #51405e; border-radius: 6px; }
            QWidget#photoTitleBar { background: #201a2a; border-bottom: 1px solid #59416c; }
            QLabel#photoTitleLabel { color: #c9a6ee; font-weight: bold; letter-spacing: 1px; }
            QPushButton#photoMinimize, QPushButton#photoMaximize, QPushButton#photoClose {
                background: transparent; border: none; border-radius: 4px; padding: 0px;
                color: #e8d6ff; font-size: 12px;
            }
            QPushButton#photoMinimize:hover, QPushButton#photoMaximize:hover { background: #513765; }
            QPushButton#photoClose:hover { background: #a52a48; color: white; }
        ''')
        self.slideshow = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 0, 10, 10)
        layout.setSpacing(8)
        layout.addWidget(PhotoBoothTitleBar(self))
        layout.addWidget(QLabel('PHOTO BOOTH  /  LOCAL SLIDESHOW'))
        self.list = QListWidget()
        layout.addWidget(self.list, 1)
        row = QHBoxLayout()
        add = QPushButton('Add Photos')
        add.clicked.connect(self.add_photos)
        remove = QPushButton('Remove Selected')
        remove.clicked.connect(self.remove_selected)
        clear = QPushButton('Clear')
        clear.clicked.connect(self.list.clear)
        for button in (add, remove, clear):
            row.addWidget(button)
        layout.addLayout(row)
        settings = QHBoxLayout()
        settings.addWidget(QLabel('Seconds'))
        self.seconds = QSpinBox()
        self.seconds.setRange(1, 120)
        self.seconds.setValue(5)
        settings.addWidget(self.seconds)
        self.transition = QComboBox()
        self.transition.addItems(['Dissolve', 'Cut', 'Fractal Zoom'])
        settings.addWidget(self.transition)
        self.fit = QComboBox()
        self.fit.addItems(['Fit', 'Fill'])
        settings.addWidget(self.fit)
        layout.addLayout(settings)
        flags = QHBoxLayout()
        self.shuffle = QCheckBox('Shuffle')
        self.loop = QCheckBox('Loop')
        self.loop.setChecked(True)
        flags.addWidget(self.shuffle)
        flags.addWidget(self.loop)
        layout.addLayout(flags)
        start = QPushButton('START FULLSCREEN SLIDESHOW')
        start.clicked.connect(self.start_slideshow)
        layout.addWidget(start)
        layout.addWidget(QLabel('Space: Pause   |   â† / â†’: Navigate   |   Esc: Return'))
        self.load_settings()
        self.list.model().rowsInserted.connect(self.save_settings)
        self.list.model().rowsRemoved.connect(self.save_settings)
        for control in (self.seconds, self.transition, self.fit, self.shuffle, self.loop):
            signal = (control.valueChanged if isinstance(control, QSpinBox) else
                      control.currentIndexChanged if isinstance(control, QComboBox) else
                      control.toggled)
            signal.connect(self.save_settings)

    def toggle_maximize(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()
    def photos(self):
        return [self.list.item(i).text() for i in range(self.list.count())]

    def add_photos(self):
        files, _ = QFileDialog.getOpenFileNames(self, 'Choose photos', '',
            'Images (*.jpg *.jpeg *.png *.bmp *.gif *.webp *.tif *.tiff)')
        existing = set(self.photos())
        for path in files:
            if path not in existing and Path(path).suffix.lower() in EXTENSIONS:
                self.list.addItem(path)
                existing.add(path)
        self.save_settings()

    def remove_selected(self):
        for item in self.list.selectedItems():
            self.list.takeItem(self.list.row(item))
        self.save_settings()

    def load_settings(self):
        try:
            data = json.loads(settings_file().read_text(encoding='utf-8'))
        except (OSError, ValueError):
            return
        for path in data.get('photos', []):
            if isinstance(path, str) and Path(path).is_file():
                self.list.addItem(path)
        self.seconds.setValue(int(data.get('seconds', 5)))
        for control, key in ((self.transition, 'transition'), (self.fit, 'fit')):
            value = data.get(key)
            if value in [control.itemText(i) for i in range(control.count())]:
                control.setCurrentText(value)
        self.shuffle.setChecked(bool(data.get('shuffle', False)))
        self.loop.setChecked(bool(data.get('loop', True)))

    def save_settings(self, *args):
        data = dict(photos=self.photos(), seconds=self.seconds.value(),
                    transition=self.transition.currentText(), fit=self.fit.currentText(),
                    shuffle=self.shuffle.isChecked(), loop=self.loop.isChecked())
        settings_file().write_text(json.dumps(data, indent=2), encoding='utf-8')

    def start_slideshow(self):
        valid = []
        for path in self.photos():
            if Path(path).is_file() and not QImageReader(str(path)).read().isNull():
                valid.append(path)
        if not valid:
            QMessageBox.information(self, 'Photo Booth', 'Select at least one readable image.')
            return
        self.save_settings()
        self.hide()
        self.slideshow = Slideshow(valid, self.seconds.value(),
            self.transition.currentText(), self.shuffle.isChecked(),
            self.loop.isChecked(), self.fit.currentText(), on_exit=self.show)
        self.slideshow.start()

    def closeEvent(self, event):
        if self.slideshow is not None:
            self.slideshow.on_exit = None
            self.slideshow.close()
        self.save_settings()
        super().closeEvent(event)