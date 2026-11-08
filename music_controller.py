import asyncio
import time
import queue
import sys
import threading
from datetime import timedelta
import json
from pathlib import Path

from PySide6.QtCore import Qt, QObject, Signal, QTimer
from PySide6.QtGui import QColor, QFont, QPixmap
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QProgressBar, QFrame,
    QColorDialog, QMenu
)


class MediaSignals(QObject):
    updated = Signal(object)


def to_seconds(value):
    if value is None:
        return 0.0
    if hasattr(value, "total_seconds"):
        return float(value.total_seconds())
    if isinstance(value, (int, float)):
        return float(value) / 10_000_000
    return 0.0


def clock(value):
    value = max(0, int(value))
    hours, remainder = divmod(value, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours:
        return f"{hours}:{minutes:02}:{seconds:02}"
    return f"{minutes}:{seconds:02}"


class MediaWorker:
    def __init__(self, signals):
        self.signals = signals
        self.stop_event = threading.Event()
        self.commands = queue.Queue()
        self.thread = threading.Thread(
            target=self._thread_main,
            name="WidgetWallMedia",
            daemon=True
        )

    def start(self):
        self.thread.start()

    def stop(self):
        self.stop_event.set()

    def command(self, action):
        self.commands.put(action)

    def _thread_main(self):
        try:
            asyncio.run(self._run())
        except Exception as exc:
            self.signals.updated.emit({
                "error": f"{type(exc).__name__}: {exc}"
            })

    async def _run(self):
        from winrt.windows.media.control import (
            GlobalSystemMediaTransportControlsSessionManager
        )

        manager = await (
            GlobalSystemMediaTransportControlsSessionManager.request_async()
        )

        while not self.stop_event.is_set():
            try:
                session = manager.get_current_session()

                if session is None:
                    sessions = list(manager.get_sessions())
                    session = sessions[0] if sessions else None

                if session is None:
                    self.signals.updated.emit({"empty": True})
                else:
                    while True:
                        try:
                            action = self.commands.get_nowait()
                        except queue.Empty:
                            break

                        try:
                            if action == "toggle":
                                await session.try_toggle_play_pause_async()
                            elif action == "next":
                                await session.try_skip_next_async()
                            elif action == "previous":
                                await session.try_skip_previous_async()
                        except Exception as exc:
                            self.signals.updated.emit({
                                "error": f"Media command failed: {exc}"
                            })

                    media = await session.try_get_media_properties_async()

                    art_key = (
                        session.source_app_user_model_id,
                        media.title,
                        media.artist,
                        media.album_title,
                    )

                    if art_key != getattr(self, "_last_art_key", None):
                        self._last_art_key = art_key
                        art_bytes = None

                        if media.thumbnail:
                            try:
                                from winrt.windows.storage.streams import DataReader

                                stream = await media.thumbnail.open_read_async()
                                try:
                                    size = min(int(stream.size), 5_000_000)
                                    reader = DataReader(
                                        stream.get_input_stream_at(0)
                                    )
                                    try:
                                        loaded = await reader.load_async(size)
                                        buffer = bytearray(int(loaded))
                                        reader.read_bytes(buffer)
                                        art_bytes = bytes(buffer)
                                    finally:
                                        reader.detach_stream()
                                finally:
                                    stream.close()
                            except Exception as exc:
                                print(
                                    "Artwork read unavailable:",
                                    type(exc).__name__,
                                    str(exc),
                                )

                        self.signals.updated.emit({
                            "artwork_bytes": art_bytes
                        })
                    playback = session.get_playback_info()
                    timeline = session.get_timeline_properties()
                    controls = playback.controls

                    self.signals.updated.emit({
                        "app": session.source_app_user_model_id,
                        "title": media.title or "Unknown track",
                        "artist": media.artist or "Unknown artist",
                        "album": media.album_title or "",
                        "artwork_available": bool(media.thumbnail),
                        "playing": int(playback.playback_status) == 4,
                        "position": to_seconds(timeline.position),
                        "track_key": (
                            session.source_app_user_model_id,
                            media.title,
                            media.artist,
                            media.album_title,
                        ),
                        "start": to_seconds(timeline.start_time),
                        "end": to_seconds(timeline.end_time),
                        "can_play": bool(controls.is_play_enabled),
                        "can_pause": bool(controls.is_pause_enabled),
                        "can_next": bool(controls.is_next_enabled),
                        "can_previous": bool(controls.is_previous_enabled),
                    })

            except Exception as exc:
                self.signals.updated.emit({
                    "error": f"{type(exc).__name__}: {exc}"
                })

            await asyncio.sleep(1.0)


class MusicController(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Widget Wall | Music Controller")
        self.resize(390, 310)
        self.setMinimumWidth(340)

        self.apply_palette()


        root = QVBoxLayout(self)
        root.setContentsMargins(22, 20, 22, 20)
        root.setSpacing(12)

        heading = QLabel("♫  WIDGET WALL / MEDIA")
        heading.setStyleSheet(
            "color: #69e8d1; font-size: 11px; font-weight: 700;"
        )
        root.addWidget(heading)

        self.art_label = QLabel()
        self.art_label.setFixedSize(132, 132)
        self.art_label.setAlignment(Qt.AlignCenter)
        self.art_label.setStyleSheet(
            "background: transparent; border-radius: 12px;"
        )
        self.art_label.setText("?")
        root.addWidget(self.art_label, alignment=Qt.AlignHCenter)

        self.title_label = QLabel("Waiting for media...")
        self.title_label.setObjectName("title")
        self.title_label.setWordWrap(True)
        root.addWidget(self.title_label)

        self.artist_label = QLabel("Windows Media Sessions")
        self.artist_label.setObjectName("artist")
        root.addWidget(self.artist_label)

        self.album_label = QLabel("")
        self.album_label.setObjectName("secondary")
        self.album_label.setWordWrap(True)
        root.addWidget(self.album_label)

        self.progress = QProgressBar()
        self.progress.setRange(0, 1000)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        root.addWidget(self.progress)

        times = QHBoxLayout()
        self.position_label = QLabel("0:00")
        self.duration_label = QLabel("0:00")
        for label in (self.position_label, self.duration_label):
            label.setObjectName("secondary")
        times.addWidget(self.position_label)
        times.addStretch()
        times.addWidget(self.duration_label)
        root.addLayout(times)

        buttons = QHBoxLayout()
        buttons.setSpacing(12)

        self.previous_button = QPushButton("⏮")
        self.toggle_button = QPushButton("▶")
        self.next_button = QPushButton("⏭")

        buttons.addWidget(self.previous_button)
        buttons.addWidget(self.toggle_button)
        buttons.addWidget(self.next_button)
        root.addLayout(buttons)

        self.status_label = QLabel("Connecting to Windows...")
        self.status_label.setObjectName("secondary")
        self.status_label.setWordWrap(True)

        self.palette_button = QPushButton("\U0001F3A8  Palette")
        self.palette_button.setObjectName("paletteButton")
        self.palette_button.setToolTip("Customize the music controller colors")
        self.palette_button.clicked.connect(self.open_palette_menu)
        root.addWidget(self.palette_button)
        root.addWidget(self.status_label)

        self.signals = MediaSignals()
        self.signals.updated.connect(self.apply_update)

        self.timeline_last_sample = None
        self.timeline_last_sample_at = None
        self.timeline_key = None
        self.timeline_position = 0.0
        self.timeline_start = 0.0
        self.timeline_end = 0.0
        self.timeline_playing = False
        self.timeline_valid = False
        self.timeline_anchor = time.monotonic()

        self.timeline_timer = QTimer(self)
        self.timeline_timer.setInterval(100)
        self.timeline_timer.timeout.connect(self.animate_timeline)
        self.timeline_timer.start()

        self.worker = MediaWorker(self.signals)

        self.previous_button.clicked.connect(
            lambda: self.worker.command("previous")
        )
        self.toggle_button.clicked.connect(
            lambda: self.worker.command("toggle")
        )
        self.next_button.clicked.connect(
            lambda: self.worker.command("next")
        )

        self.set_controls(False, False, False)
        self.worker.start()


    PALETTES = {
        "Midnight Mint": {
            "background": "#101722",
            "panel": "#1d2c3d",
            "accent": "#69e8d1",
            "text": "#e8f3ff",
            "muted": "#8c9eb2",
        },
        "Cyberpunk": {
            "background": "#140e24",
            "panel": "#302044",
            "accent": "#e879f9",
            "text": "#f8eaff",
            "muted": "#b8a4cb",
        },
        "Deep Ocean": {
            "background": "#071d2b",
            "panel": "#12394c",
            "accent": "#38bdf8",
            "text": "#e0f7ff",
            "muted": "#91b5c6",
        },
        "Ember": {
            "background": "#21140f",
            "panel": "#40271e",
            "accent": "#fb923c",
            "text": "#fff0e4",
            "muted": "#c6a38e",
        },
        "Monochrome": {
            "background": "#151515",
            "panel": "#303030",
            "accent": "#f1f1f1",
            "text": "#ffffff",
            "muted": "#aaaaaa",
        },
    }

    def palette_path(self):
        return Path.home() / ".widget_wall" / "music_palette.json"

    def load_palette(self):
        default = dict(self.PALETTES["Midnight Mint"])
        try:
            path = self.palette_path()
            if path.exists():
                data = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    for key in default:
                        value = data.get(key)
                        if (
                            isinstance(value, str)
                            and QColor(value).isValid()
                            and value.startswith("#")
                            and len(value) in (4, 7)
                        ):
                            default[key] = QColor(value).name()
        except (OSError, ValueError, TypeError):
            pass
        return default

    def save_palette(self):
        try:
            path = self.palette_path()
            path.parent.mkdir(parents=True, exist_ok=True)
            temporary = path.with_suffix(".tmp")
            temporary.write_text(
                json.dumps(self.theme_colors, indent=2),
                encoding="utf-8"
            )
            temporary.replace(path)
        except OSError as exc:
            self.status_label.setText(
                f"Palette could not be saved: {exc}"
            )

    def apply_palette(self):
        if not hasattr(self, "theme_colors"):
            self.theme_colors = self.load_palette()

        p = self.theme_colors
        self.setStyleSheet(f"""
            QWidget {{
                background: {p["background"]};
                color: {p["text"]};
                font-family: Segoe UI;
            }}
            QLabel {{
                background: transparent;
            }}
            QLabel#title {{
                font-size: 20px;
                font-weight: 700;
                color: {p["text"]};
            }}
            QLabel#artist {{
                font-size: 14px;
                color: {p["accent"]};
            }}
            QLabel#secondary {{
                font-size: 12px;
                color: {p["muted"]};
            }}
            QPushButton {{
                background: {p["panel"]};
                color: {p["text"]};
                border: 1px solid {p["muted"]};
                border-radius: 10px;
                padding: 10px;
                font-size: 18px;
                min-width: 45px;
            }}
            QPushButton:hover {{
                border-color: {p["accent"]};
            }}
            QPushButton:disabled {{
                color: {p["muted"]};
                opacity: 0.5;
            }}
            QPushButton#paletteButton {{
                font-size: 12px;
                padding: 7px;
                min-width: 0px;
            }}
            QProgressBar {{
                background: {p["panel"]};
                border: none;
                border-radius: 4px;
                height: 8px;
                text-align: center;
            }}
            QProgressBar::chunk {{
                background: {p["accent"]};
                border-radius: 4px;
            }}
            QMenu {{
                background: {p["panel"]};
                color: {p["text"]};
                border: 1px solid {p["muted"]};
            }}
            QMenu::item {{
                padding: 7px 20px;
            }}
            QMenu::item:selected {{
                background: {p["accent"]};
                color: {p["background"]};
            }}
        """)

    def choose_palette(self, name):
        self.theme_colors = dict(self.PALETTES[name])
        self.apply_palette()
        self.save_palette()

    def choose_color(self, key):
        labels = {
            "background": "Background",
            "panel": "Panels and buttons",
            "accent": "Accent",
            "text": "Primary text",
            "muted": "Secondary text",
        }
        color = QColorDialog.getColor(
            QColor(self.theme_colors[key]),
            self,
            f"Widget Wall | {labels[key]}"
        )
        if color.isValid():
            self.theme_colors[key] = color.name()
            self.apply_palette()
            self.save_palette()

    def open_palette_menu(self):
        menu = QMenu(self)

        for name in self.PALETTES:
            action = menu.addAction(name)
            action.triggered.connect(
                lambda checked=False, n=name: self.choose_palette(n)
            )

        menu.addSeparator()
        custom = menu.addMenu("Customize individual colors")

        labels = {
            "background": "Background",
            "panel": "Panels and buttons",
            "accent": "Accent",
            "text": "Primary text",
            "muted": "Secondary text",
        }

        for key, label in labels.items():
            action = custom.addAction(label)
            action.triggered.connect(
                lambda checked=False, k=key: self.choose_color(k)
            )

        menu.exec(
            self.palette_button.mapToGlobal(
                self.palette_button.rect().bottomLeft()
            )
        )

    def set_album_art(self, data):
        if not data:
            self.art_label.setPixmap(QPixmap())
            self.art_label.setText("?")
            return

        pixmap = QPixmap()
        if not pixmap.loadFromData(data):
            self.art_label.setPixmap(QPixmap())
            self.art_label.setText("?")
            return

        self.art_label.setText("")
        self.art_label.setPixmap(
            pixmap.scaled(
                self.art_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
        )


    def reset_timeline(self):
        self.timeline_position = 0.0
        self.timeline_start = 0.0
        self.timeline_end = 0.0
        self.timeline_playing = False
        self.timeline_valid = False
        self.timeline_anchor = time.monotonic()
        self.render_timeline()

    def render_timeline(self):
        if not self.timeline_valid:
            self.progress.setRange(0, 1000)
            self.progress.setValue(0)
            self.position_label.setText("--:--")
            self.duration_label.setText("--:--")
            return

        start = self.timeline_start
        end = self.timeline_end
        duration = end - start

        elapsed = max(
            0.0,
            min(duration, self.timeline_position - start)
        )

        self.progress.setValue(
            int(1000 * elapsed / duration)
        )

        self.position_label.setText(clock(elapsed))
        self.duration_label.setText(clock(duration))

    def animate_timeline(self):
        now = time.monotonic()

        if self.timeline_playing and self.timeline_valid:
            delta = max(0.0, now - self.timeline_anchor)
            self.timeline_position = min(
                self.timeline_end,
                self.timeline_position + delta
            )

        self.timeline_anchor = now
        self.render_timeline()

    def synchronize_timeline(self, data):
        key = tuple(data["track_key"])
        now = time.monotonic()

        if key != self.timeline_key:
            self.timeline_key = key
            self.timeline_last_sample = None
            self.timeline_last_sample_at = None
            self.reset_timeline()

        start = float(data["start"])
        end = float(data["end"])
        position = float(data["position"])

        valid = (
            end > start
            and end - start < 86400
            and start - 2 <= position <= end + 2
        )

        playing = bool(data["playing"])

        if valid:
            new_sample = (
                self.timeline_last_sample is None
                or abs(position - self.timeline_last_sample) > 0.05
            )

            self.timeline_start = start
            self.timeline_end = end

            if not self.timeline_valid:
                self.timeline_position = position
                self.timeline_valid = True

            elif new_sample:
                difference = position - self.timeline_position

                # Accept forward corrections. Reject small backward
                # jumps caused by stale browser snapshots.
                if difference >= -1.5:
                    self.timeline_position = max(
                        self.timeline_position,
                        position
                    )

                # Large backward jumps are likely a seek or restart.
                else:
                    self.timeline_position = position

            self.timeline_last_sample = position
            self.timeline_last_sample_at = now

        elif not self.timeline_valid:
            self.timeline_valid = False

        self.timeline_playing = playing
        self.timeline_anchor = now

        self.render_timeline()

    def set_controls(self, previous, toggle, next):
        self.previous_button.setEnabled(previous)
        self.toggle_button.setEnabled(toggle)
        self.next_button.setEnabled(next)

    def apply_update(self, data):
        if "artwork_bytes" in data:
            self.set_album_art(data["artwork_bytes"])
            return

        if "error" in data:
            self.status_label.setText(data["error"])
            return

        if data.get("empty"):
            self.timeline_key = None
            self.reset_timeline()
            self.set_album_art(None)
            self.title_label.setText("Nothing playing")
            self.artist_label.setText("No active media session")
            self.album_label.setText("")
            self.progress.setValue(0)
            self.position_label.setText("0:00")
            self.duration_label.setText("0:00")
            self.set_controls(False, False, False)
            self.status_label.setText("Waiting for a compatible player...")
            return

        self.title_label.setText(data["title"])
        self.artist_label.setText(data["artist"])
        self.album_label.setText(data["album"])

        self.synchronize_timeline(data)

        playing = data["playing"]
        self.toggle_button.setText("⏸" if playing else "▶")

        self.set_controls(
            data["can_previous"],
            data["can_pause"] if playing else data["can_play"],
            data["can_next"]
        )

        source = data["app"]
        if "OperaGX" in source:
            source = "Opera GX"

        artwork = "Artwork available" if data["artwork_available"] else "No artwork"
        state = "Playing" if playing else "Paused"

        self.status_label.setText(
            f"{source}  •  {state}  •  {artwork}"
        )

    def closeEvent(self, event):
        self.worker.stop()
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MusicController()
    window.show()
    sys.exit(app.exec())