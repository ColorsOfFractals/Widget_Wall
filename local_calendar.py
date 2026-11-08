"""Local, offline appointment calendar for Widget Wall."""
import json
from datetime import date
from pathlib import Path
from PySide6.QtCore import QStandardPaths
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCalendarWidget, QListWidget, QPushButton, QInputDialog, QMessageBox

CONFIG = Path(QStandardPaths.writableLocation(QStandardPaths.AppConfigLocation)) / 'Widget_Wall' / 'calendar.json'

class LocalCalendar(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Widget Wall | Calendar')
        self.resize(480, 520)
        self.setStyleSheet('QWidget { background:#17151f; color:#e9d8ff; font-size:13px; } QPushButton,QListWidget { background:#30263c; border:1px solid #75538d; border-radius:5px; padding:7px; }')
        try:
            value = json.loads(CONFIG.read_text(encoding='utf-8'))
            self.events = value if isinstance(value, dict) else {}
        except (OSError, ValueError): self.events = {}
        lay = QVBoxLayout(self)
        lay.addWidget(QLabel('CALENDAR  /  LOCAL APPOINTMENTS'))
        self.calendar = QCalendarWidget()
        self.calendar.selectionChanged.connect(self.refresh)
        lay.addWidget(self.calendar)
        self.heading = QLabel()
        lay.addWidget(self.heading)
        self.items = QListWidget()
        lay.addWidget(self.items)
        row = QHBoxLayout()
        add = QPushButton('Add appointment')
        add.clicked.connect(self.add)
        remove = QPushButton('Remove selected')
        remove.clicked.connect(self.remove)
        row.addWidget(add)
        row.addWidget(remove)
        lay.addLayout(row)
        lay.addWidget(QLabel('Saved locally. No cloud account or calendar sync.'))
        self.refresh()

    def key(self):
        return self.calendar.selectedDate().toString('yyyy-MM-dd')

    def refresh(self):
        day = self.key()
        self.heading.setText('APPOINTMENTS  /  ' + day)
        self.items.clear()
        self.items.addItems(self.events.get(day, []))

    def save(self):
        CONFIG.parent.mkdir(parents=True, exist_ok=True)
        CONFIG.write_text(json.dumps(self.events, indent=2, ensure_ascii=False), encoding='utf-8')

    def add(self):
        value, ok = QInputDialog.getText(self, 'Add appointment', 'Appointment / reminder:')
        if ok and value.strip():
            self.events.setdefault(self.key(), []).append(value.strip())
            self.save()
            self.refresh()

    def remove(self):
        index = self.items.currentRow()
        if index < 0: return
        day = self.key()
        if day in self.events and index < len(self.events[day]):
            self.events[day].pop(index)
            if not self.events[day]: del self.events[day]
            self.save()
            self.refresh()