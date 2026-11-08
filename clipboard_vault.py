from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QApplication, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QTextEdit, QVBoxLayout, QWidget,
)

from utility_widgets import BaseUtility


class ClipboardVault(BaseUtility):
    MAX_ENTRIES = 100

    def __init__(self):
        super().__init__("Clipboard Vault")
        self.resize(480, 580)

        self.entries = []
        self.capture_enabled = True
        self.suppress_text = None
        self.selected_index = None

        self.clipboard = QGuiApplication.clipboard()

        controls = QHBoxLayout()
        self.capture_button = QPushButton("Pause Capture")
        self.capture_button.clicked.connect(self.toggle_capture)
        controls.addWidget(self.capture_button)

        clear_button = QPushButton("Clear History")
        clear_button.clicked.connect(self.clear_history)
        controls.addWidget(clear_button)
        self.layout.addLayout(controls)

        self.status = QLabel("0 clips | Session only")
        self.layout.addWidget(self.status)

        self.history_page = QWidget()
        self.history_layout = QVBoxLayout(self.history_page)
        self.history_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setWidget(self.history_page)
        self.layout.addWidget(self.scroll)

        self.detail_page = QWidget()
        detail_layout = QVBoxLayout(self.detail_page)

        back_button = QPushButton("Back to History")
        back_button.clicked.connect(self.show_history)
        detail_layout.addWidget(back_button)

        self.detail_info = QLabel()
        detail_layout.addWidget(self.detail_info)

        self.detail_text = QTextEdit()
        self.detail_text.setReadOnly(True)
        self.detail_text.setLineWrapMode(
            QTextEdit.LineWrapMode.NoWrap
        )
        detail_layout.addWidget(self.detail_text)

        copy_button = QPushButton("Copy Entire Entry")
        copy_button.clicked.connect(self.copy_selected)
        detail_layout.addWidget(copy_button)

        self.layout.addWidget(self.detail_page)
        self.detail_page.hide()

        # Do not import clipboard contents that predate opening the vault.
        self.clipboard.dataChanged.connect(self.capture)
        self.refresh_history()

    def capture(self):
        if not self.capture_enabled:
            return

        mime = self.clipboard.mimeData()
        if mime is None or not mime.hasText():
            return

        text = mime.text()
        if not text:
            return

        if self.suppress_text is not None:
            suppressed = self.suppress_text
            self.suppress_text = None
            if text == suppressed:
                return

        # Existing clips move to the top instead of duplicating.
        for index, entry in enumerate(self.entries):
            if entry["text"] == text:
                self.entries.insert(0, self.entries.pop(index))
                self.refresh_history()
                return

        self.entries.insert(0, {
            "text": text,
            "time": datetime.now().strftime("%H:%M:%S"),
        })
        del self.entries[self.MAX_ENTRIES:]
        self.refresh_history()

    def copy_text(self, text):
        self.suppress_text = text
        self.clipboard.setText(text)

    def toggle_capture(self):
        self.capture_enabled = not self.capture_enabled
        self.capture_button.setText(
            "Pause Capture" if self.capture_enabled
            else "Resume Capture"
        )
        self.refresh_status()

    def clear_history(self):
        self.entries.clear()
        self.show_history()
        self.refresh_history()

    def refresh_status(self):
        state = "Capturing" if self.capture_enabled else "Paused"
        self.status.setText(
            f"{len(self.entries)} clips | {state} | Session only"
        )

    def refresh_history(self):
        while self.history_layout.count():
            item = self.history_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        for index, entry in enumerate(self.entries):
            text = entry["text"]
            lines = text.splitlines()
            preview = "  /  ".join(lines[:2]).strip()
            if len(preview) > 110:
                preview = preview[:107] + "..."

            card = QWidget()
            row = QHBoxLayout(card)

            open_button = QPushButton(
                f"#{index + 1}  {entry['time']}\n"
                f"{preview or '(blank lines)'}\n"
                f"{len(lines)} lines | {len(text)} characters"
            )
            open_button.setToolTip("Open complete clipboard entry")
            open_button.clicked.connect(
                lambda checked=False, e=entry: self.open_entry(e)
            )
            row.addWidget(open_button, 1)

            copy_button = QPushButton("Copy")
            copy_button.clicked.connect(
                lambda checked=False, value=text: self.copy_text(value)
            )
            row.addWidget(copy_button)

            self.history_layout.addWidget(card)

        self.refresh_status()

    def open_entry(self, entry):
        self.selected_index = entry
        text = entry["text"]
        self.detail_info.setText(
            f"{len(text.splitlines())} lines | "
            f"{len(text)} characters | {entry['time']}"
        )
        self.detail_text.setPlainText(text)
        self.scroll.hide()
        self.detail_page.show()

    def copy_selected(self):
        if self.selected_index is not None:
            self.copy_text(self.selected_index["text"])

    def show_history(self):
        self.selected_index = None
        self.detail_page.hide()
        self.scroll.show()


CLIPBOARD_WIDGET_CLASSES = {
    "clipboard": ClipboardVault,
}
