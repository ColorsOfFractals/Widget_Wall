import ctypes
import os
import subprocess
import time
from ctypes import wintypes

import psutil

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QApplication, QComboBox, QHBoxLayout,
    QLabel, QLineEdit, QMessageBox,
    QProgressBar, QPushButton, QWidget
)

from utility_widgets import BaseUtility


class NetworkMonitor(BaseUtility):
    def __init__(self):
        super().__init__("Network Monitor")

        self.interface = QComboBox()
        self.interface.addItem("All interfaces")
        self.interface.addItems(sorted(psutil.net_if_addrs()))
        self.layout.addWidget(self.interface)

        self.upload = self.add_label("Upload: measuring...")
        self.download = self.add_label("Download: measuring...")
        self.total = self.add_label()
        self.status = self.add_label()

        self.previous = None
        self.previous_time = None

        self.interface.currentTextChanged.connect(self.reset_sample)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(1000)
        self.refresh()

    def reset_sample(self, *_):
        self.previous = None
        self.previous_time = None
        self.refresh()

    @staticmethod
    def format_bytes(value):
        for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
            if abs(value) < 1024:
                return f"{value:.2f} {unit}"
            value /= 1024
        return f"{value:.2f} PiB"

    def refresh(self):
        selected = self.interface.currentText()

        if selected == "All interfaces":
            counters = psutil.net_io_counters()
        else:
            counters = psutil.net_io_counters(pernic=True).get(selected)

        if counters is None:
            self.status.setText("Interface unavailable.")
            return

        now = time.monotonic()

        if self.previous is not None:
            elapsed = max(now - self.previous_time, 0.001)

            sent = max(
                0, counters.bytes_sent - self.previous.bytes_sent
            ) / elapsed
            received = max(
                0, counters.bytes_recv - self.previous.bytes_recv
            ) / elapsed

            self.upload.setText(
                "Upload: " + self.format_bytes(sent) + "/s"
            )
            self.download.setText(
                "Download: " + self.format_bytes(received) + "/s"
            )

        self.total.setText(
            "Total sent: "
            + self.format_bytes(counters.bytes_sent)
            + "\nTotal received: "
            + self.format_bytes(counters.bytes_recv)
        )

        self.status.setText(f"Monitoring: {selected}")

        self.previous = counters
        self.previous_time = now


class CountdownTimer(BaseUtility):
    def __init__(self):
        super().__init__("Countdown Timer")

        self.hours = QLineEdit("0")
        self.minutes = QLineEdit("5")
        self.seconds = QLineEdit("0")

        row = QHBoxLayout()
        for label, field in (
            ("Hours", self.hours),
            ("Minutes", self.minutes),
            ("Seconds", self.seconds),
        ):
            column = QHBoxLayout()
            column.addWidget(QLabel(label))
            column.addWidget(field)
            row.addLayout(column)

        self.layout.addLayout(row)

        self.display = self.add_label("00:05:00")
        self.display.setStyleSheet(
            "font-size: 28px; font-weight: bold;"
        )

        self.start_button = self.add_button("Start", self.start)
        self.pause_button = self.add_button("Pause", self.pause)
        self.add_button("Reset", self.reset)

        self.remaining = 300.0
        self.deadline = None
        self.running = False

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(100)

    def configured_seconds(self):
        values = [
            int(self.hours.text()),
            int(self.minutes.text()),
            int(self.seconds.text())
        ]

        if any(value < 0 for value in values):
            raise ValueError("Negative values are not allowed.")

        return values[0] * 3600 + values[1] * 60 + values[2]

    def start(self):
        if self.running:
            return

        if self.remaining <= 0 or self.pause_button.text() != "Resume":
            try:
                self.remaining = self.configured_seconds()
            except ValueError:
                QMessageBox.warning(
                    self, "Invalid time", "Enter valid whole numbers."
                )
                return

        if self.remaining <= 0:
            return

        self.deadline = time.monotonic() + self.remaining
        self.running = True
        self.pause_button.setText("Pause")
        self.tick()

    def pause(self):
        if self.running:
            self.remaining = max(
                0, self.deadline - time.monotonic()
            )
            self.running = False
            self.deadline = None
            self.pause_button.setText("Resume")
            self.tick()
        elif self.pause_button.text() == "Resume":
            self.start()

    def reset(self):
        self.running = False
        self.deadline = None
        self.pause_button.setText("Pause")

        try:
            self.remaining = self.configured_seconds()
        except ValueError:
            self.remaining = 0

        self.tick()

    def tick(self):
        if self.running:
            self.remaining = max(
                0, self.deadline - time.monotonic()
            )

            if self.remaining <= 0:
                self.running = False
                self.deadline = None
                self.pause_button.setText("Pause")
                self.update_display()
                QApplication.beep()
                QMessageBox.information(
                    self, "Countdown Complete", "Time is up!"
                )
                return

        self.update_display()

    def update_display(self):
        import math
        total = math.ceil(self.remaining)

        hours, remainder = divmod(total, 3600)
        minutes, seconds = divmod(remainder, 60)

        self.display.setText(
            f"{hours:02}:{minutes:02}:{seconds:02}"
        )


class SHQUERYRBINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("i64Size", ctypes.c_longlong),
        ("i64NumItems", ctypes.c_longlong),
    ]


class RecycleBin(BaseUtility):
    def __init__(self):
        super().__init__("Recycle Bin")

        self.count = self.add_label("Reading Recycle Bin...")
        self.size = self.add_label()

        self.add_button("Refresh", self.refresh)
        self.add_button("Open Recycle Bin", self.open_bin)
        self.add_button("Empty Recycle Bin", self.empty_bin)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(10000)

        self.refresh()

    def refresh(self):
        info = SHQUERYRBINFO()
        info.cbSize = ctypes.sizeof(info)

        shell32 = ctypes.windll.shell32
        result = shell32.SHQueryRecycleBinW(None, ctypes.byref(info))

        if result != 0:
            self.count.setText(
                f"Recycle Bin query failed: 0x{result & 0xffffffff:08X}"
            )
            return

        self.count.setText(
            f"Items in Recycle Bin: {info.i64NumItems:,}"
        )
        self.size.setText(
            f"Total size: {info.i64Size / 2**20:,.2f} MiB"
        )

    def open_bin(self):
        subprocess.Popen([
            "explorer.exe",
            "shell:RecycleBinFolder"
        ])

    def empty_bin(self):
        choice = QMessageBox.question(
            self,
            "Empty Recycle Bin",
            "Permanently delete all items in the Recycle Bin?",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if choice != QMessageBox.StandardButton.Yes:
            return

        shell32 = ctypes.windll.shell32
        result = shell32.SHEmptyRecycleBinW(
            int(self.winId()),
            None,
            0
        )

        if result != 0:
            QMessageBox.warning(
                self,
                "Recycle Bin",
                f"Windows returned 0x{result & 0xffffffff:08X}"
            )

        self.refresh()


SYSTEM_WIDGET_CLASSES = {
    "network": NetworkMonitor,
    "countdown": CountdownTimer,
    "recycle": RecycleBin,
}