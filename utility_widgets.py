import ast
import json
import operator
import pathlib
import sys
import webbrowser
import xml.etree.ElementTree as ET
from datetime import datetime
from urllib.parse import quote, quote_plus

import psutil
import requests

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QTextEdit,
    QListWidget, QCheckBox, QComboBox, QProgressBar,
    QFormLayout, QMessageBox, QInputDialog
)


DATA_DIR = pathlib.Path.home() / ".widget_wall"
HTTP_TIMEOUT = 8


def http_get(url):
    response = requests.get(
        url,
        timeout=HTTP_TIMEOUT,
        headers={"User-Agent": "WidgetWall/0.8"}
    )
    response.raise_for_status()
    return response



ROYGBV_THEMES = {
    "Red": "#ef5350",
    "Orange": "#ff963f",
    "Yellow": "#f5ce48",
    "Green": "#51d88a",
    "Blue": "#5ca8ff",
    "Indigo": "#9b83f5",
    "Violet": "#ce79f2",
}

THEME_FILE = DATA_DIR / "themes.json"


def load_theme_preferences():
    try:
        data = json.loads(THEME_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError, TypeError):
        return {}


def save_theme_preference(widget_id, theme_name):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    preferences = load_theme_preferences()
    preferences[widget_id] = theme_name

    temporary = THEME_FILE.with_suffix(".tmp")
    temporary.write_text(
        json.dumps(preferences, indent=2),
        encoding="utf-8"
    )
    temporary.replace(THEME_FILE)


class BaseUtility(QWidget):
    def __init__(self, title):
        super().__init__()
        self.setWindowTitle(f"Widget Wall | {title}")
        self.resize(380, 350)
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(10)

        heading = QLabel(title.upper())
        heading.setStyleSheet(
            "font-weight: 700; font-size: 16px; color: #6ee7cf;"
        )
        self.layout.addWidget(heading)

        self.setStyleSheet("""
            QWidget {
                background: #141b26;
                color: #e5efff;
                font-family: Segoe UI;
            }
            QLineEdit, QTextEdit, QListWidget, QComboBox {
                background: #202c3d;
                border: 1px solid #42546b;
                border-radius: 5px;
                padding: 6px;
            }
            QPushButton {
                background: #29445b;
                border: 1px solid #4a6d83;
                border-radius: 6px;
                padding: 8px;
            }
            QPushButton:hover {
                background: #365d77;
            }
        """)

        self.theme_id = title
        self.theme_selector = QComboBox()
        self.theme_selector.addItems(ROYGBV_THEMES)

        preferences = load_theme_preferences()
        saved = preferences.get(self.theme_id, "Blue")

        if saved not in ROYGBV_THEMES:
            saved = "Blue"

        self.theme_selector.setCurrentText(saved)
        self.theme_selector.currentTextChanged.connect(
            self.apply_theme
        )

        self.layout.addWidget(self.theme_selector)
        self.apply_theme(saved)

    def apply_theme(self, theme_name):
        accent = ROYGBV_THEMES.get(
            theme_name, ROYGBV_THEMES["Blue"]
        )

        self.setStyleSheet(f"""
            QWidget {{
                background: #141b26;
                color: #e5efff;
                font-family: Segoe UI;
            }}
            QLabel {{
                background: transparent;
            }}
            QLineEdit, QTextEdit, QListWidget, QComboBox {{
                background: #202c3d;
                border: 1px solid {accent};
                border-radius: 5px;
                padding: 6px;
            }}
            QPushButton {{
                background: #29445b;
                border: 1px solid {accent};
                border-radius: 6px;
                padding: 8px;
            }}
            QPushButton:hover {{
                background: {accent};
                color: #101820;
            }}
            QProgressBar {{
                background: #202c3d;
                border: 1px solid #42546b;
                border-radius: 4px;
                text-align: right;
            }}
            QProgressBar::chunk {{
                background: {accent};
                border-radius: 3px;
            }}
        """)

        for label in self.findChildren(QLabel):
            if label.text().strip() == self.theme_id.upper():
                label.setStyleSheet(
                    f"font-weight: 700; font-size: 16px; "
                    f"color: {accent};"
                )

        save_theme_preference(self.theme_id, theme_name)


    def add_label(self, text=""):
        label = QLabel(text)
        label.setWordWrap(True)
        self.layout.addWidget(label)
        return label

    def add_button(self, label, callback):
        button = QPushButton(label)
        button.clicked.connect(callback)
        self.layout.addWidget(button)
        return button


class CpuRamMonitor(BaseUtility):
    def __init__(self):
        super().__init__("CPU / RAM Monitor")
        self.cpu = self.add_label()
        self.cpu_bar = QProgressBar()
        self.layout.addWidget(self.cpu_bar)
        self.ram = self.add_label()
        self.ram_bar = QProgressBar()
        self.layout.addWidget(self.ram_bar)
        self.details = self.add_label()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(1000)
        self.refresh()

    def refresh(self):
        cpu = psutil.cpu_percent(interval=None)
        memory = psutil.virtual_memory()
        self.cpu.setText(f"CPU utilization: {cpu:.1f}%")
        self.cpu_bar.setValue(round(cpu))
        self.ram.setText(f"RAM utilization: {memory.percent:.1f}%")
        self.ram_bar.setValue(round(memory.percent))
        self.details.setText(
            f"RAM used: {memory.used / 2**30:.2f} GiB\n"
            f"RAM available: {memory.available / 2**30:.2f} GiB\n"
            f"Logical CPUs: {psutil.cpu_count()}"
        )


class BatteryMonitor(BaseUtility):
    def __init__(self):
        super().__init__("Battery Monitor")
        self.state = self.add_label()
        self.bar = QProgressBar()
        self.layout.addWidget(self.bar)
        self.details = self.add_label()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(5000)
        self.refresh()

    def refresh(self):
        battery = psutil.sensors_battery()
        if battery is None:
            self.state.setText("No battery reported by Windows.")
            self.details.setText("This is normal on desktop PCs.")
            self.bar.setValue(0)
            return

        self.bar.setValue(round(battery.percent))
        self.state.setText(f"Battery: {battery.percent:.0f}%")
        self.details.setText(
            "Power: " + (
                "Plugged in" if battery.power_plugged else "On battery"
            )
        )


class RssNewsReader(BaseUtility):
    FEEDS = {
        "BBC World": "https://feeds.bbci.co.uk/news/world/rss.xml",
        "NPR News": "https://feeds.npr.org/1001/rss.xml",
        "Ars Technica": "https://feeds.arstechnica.com/arstechnica/index",
    }

    def __init__(self):
        super().__init__("RSS News Reader")
        self.feed = QComboBox()
        self.feed.addItems(self.FEEDS)
        self.layout.addWidget(self.feed)
        self.items = QListWidget()
        self.layout.addWidget(self.items)
        self.status = self.add_label("Choose a feed and refresh.")
        self.add_button("Refresh headlines", self.refresh)
        self.links = []
        self.items.itemDoubleClicked.connect(self.open_item)

    def refresh(self):
        self.items.clear()
        self.links = []
        self.status.setText("Loading...")
        QApplication.processEvents()

        try:
            response = http_get(self.FEEDS[self.feed.currentText()])
            root = ET.fromstring(response.content)
            entries = root.findall(".//item")

            if not entries:
                entries = root.findall(
                    ".//{http://www.w3.org/2005/Atom}entry"
                )

            for entry in entries[:30]:
                title = entry.findtext("title")
                if title is None:
                    title = entry.findtext(
                        "{http://www.w3.org/2005/Atom}title"
                    )

                link = entry.findtext("link")
                if link is None:
                    element = entry.find(
                        "{http://www.w3.org/2005/Atom}link"
                    )
                    link = element.get("href", "") if element is not None else ""

                self.items.addItem(title or "(Untitled)")
                self.links.append(link)

            self.status.setText(f"{len(self.links)} headlines loaded.")

        except Exception as exc:
            self.status.setText(
                f"Feed unavailable: {type(exc).__name__}: {exc}"
            )

    def open_item(self, item):
        index = self.items.row(item)
        if 0 <= index < len(self.links) and self.links[index]:
            webbrowser.open(self.links[index])


OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def safe_calculate(expression):
    def evaluate(node):
        if isinstance(node, ast.Expression):
            return evaluate(node.body)

        if isinstance(node, ast.Constant):
            if type(node.value) in (int, float):
                return node.value
            raise ValueError("Numbers only.")

        if isinstance(node, ast.BinOp) and type(node.op) in OPS:
            left = evaluate(node.left)
            right = evaluate(node.right)

            if isinstance(node.op, ast.Pow) and abs(right) > 12:
                raise ValueError("Exponent too large.")

            result = OPS[type(node.op)](left, right)

            if abs(result) > 1e15:
                raise ValueError("Result too large.")

            return result

        if isinstance(node, ast.UnaryOp) and type(node.op) in OPS:
            return OPS[type(node.op)](evaluate(node.operand))

        raise ValueError("Unsupported expression.")

    if len(expression) > 100:
        raise ValueError("Expression too long.")

    return evaluate(ast.parse(expression, mode="eval"))


class Calculator(BaseUtility):
    def __init__(self):
        super().__init__("Calculator")
        self.input = QLineEdit()
        self.input.setPlaceholderText("Example: (12 + 8) * 3")
        self.input.returnPressed.connect(self.calculate)
        self.layout.addWidget(self.input)
        self.result = self.add_label("Result: ")
        self.add_button("Calculate", self.calculate)

    def calculate(self):
        try:
            result = safe_calculate(self.input.text())
            self.result.setText(f"Result: {result}")
        except Exception as exc:
            self.result.setText(f"Invalid expression: {exc}")


class TodoList(BaseUtility):
    def __init__(self):
        super().__init__("To-Do List")
        self.tasks = QListWidget()
        self.layout.addWidget(self.tasks)

        self.input = QLineEdit()
        self.input.setPlaceholderText("New task...")
        self.input.returnPressed.connect(self.add_task)
        self.layout.addWidget(self.input)

        self.add_button("Add task", self.add_task)
        self.add_button("Remove selected", self.remove_task)
        self.load()

    @property
    def path(self):
        return DATA_DIR / "todo.json"

    def load(self):
        try:
            if self.path.exists():
                items = json.loads(
                    self.path.read_text(encoding="utf-8")
                )
                for item in items:
                    self.tasks.addItem(str(item))
        except (OSError, ValueError) as exc:
            self.add_label(f"Unable to load tasks: {exc}")

    def save(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps([
                self.tasks.item(i).text()
                for i in range(self.tasks.count())
            ], indent=2),
            encoding="utf-8"
        )

    def add_task(self):
        text = self.input.text().strip()
        if text:
            self.tasks.addItem(text)
            self.input.clear()
            self.save()

    def remove_task(self):
        row = self.tasks.currentRow()
        if row >= 0:
            self.tasks.takeItem(row)
            self.save()


class CurrencyConverter(BaseUtility):
    CURRENCIES = ["USD", "EUR", "GBP", "JPY", "CAD", "AUD", "CHF"]

    def __init__(self):
        super().__init__("Currency Converter")
        self.amount = QLineEdit("100")
        self.layout.addWidget(self.amount)

        self.source = QComboBox()
        self.target = QComboBox()

        self.source.addItems(self.CURRENCIES)
        self.target.addItems(self.CURRENCIES)
        self.target.setCurrentText("EUR")

        self.layout.addWidget(self.source)
        self.layout.addWidget(self.target)

        self.result = self.add_label("Ready.")
        self.add_button("Convert", self.convert)
        self.cache = {}

    def convert(self):
        try:
            amount = float(self.amount.text())
            source = self.source.currentText()
            target = self.target.currentText()

            if source == target:
                self.result.setText(f"{amount:.2f} {target}")
                return

            key = source
            cached = self.cache.get(key)

            if cached and (
                datetime.now() - cached[0]
            ).total_seconds() < 3600:
                rates = cached[1]
            else:
                url = (
                    "https://open.er-api.com/v6/latest/"
                    + quote(source)
                )
                rates = http_get(url).json()["rates"]
                self.cache[key] = (datetime.now(), rates)

            converted = amount * rates[target]

            self.result.setText(
                f"{amount:,.2f} {source} = "
                f"{converted:,.2f} {target}\n"
                "Rates are indicative, not transaction quotes."
            )

        except Exception as exc:
            self.result.setText(
                f"Conversion unavailable: {type(exc).__name__}: {exc}"
            )


class WebSearch(BaseUtility):
    def __init__(self):
        super().__init__("Web Search")
        self.query = QLineEdit()
        self.query.setPlaceholderText("Search the web...")
        self.query.returnPressed.connect(self.search)
        self.layout.addWidget(self.query)

        self.engine = QComboBox()
        self.engine.addItems(["DuckDuckGo", "Google", "Bing"])
        self.layout.addWidget(self.engine)

        self.add_button("Search in browser", self.search)

    def search(self):
        query = self.query.text().strip()
        if not query:
            return

        encoded = quote_plus(query)

        urls = {
            "DuckDuckGo": "https://duckduckgo.com/?q=",
            "Google": "https://www.google.com/search?q=",
            "Bing": "https://www.bing.com/search?q=",
        }

        webbrowser.open(urls[self.engine.currentText()] + encoded)


class Dictionary(BaseUtility):
    def __init__(self):
        super().__init__("Dictionary")
        self.word = QLineEdit()
        self.word.setPlaceholderText("Enter a word...")
        self.word.returnPressed.connect(self.lookup)
        self.layout.addWidget(self.word)

        self.result = QTextEdit()
        self.result.setReadOnly(True)
        self.layout.addWidget(self.result)

        self.add_button("Look up definition", self.lookup)
        self.cache = {}

    def lookup(self):
        word = self.word.text().strip()
        if not word:
            return

        key = word.lower()

        if key in self.cache:
            self.result.setPlainText(self.cache[key])
            return

        try:
            url = (
                "https://api.dictionaryapi.dev/api/v2/entries/en/"
                + quote(word)
            )
            data = http_get(url).json()

            lines = []
            for entry in data[:2]:
                for meaning in entry.get("meanings", [])[:4]:
                    lines.append(
                        meaning.get("partOfSpeech", "").upper()
                    )
                    for definition in meaning.get(
                        "definitions", []
                    )[:4]:
                        lines.append(
                            "- " + definition.get("definition", "")
                        )
                    lines.append("")

            text = "\n".join(lines).strip()
            self.cache[key] = text
            self.result.setPlainText(text or "No definitions found.")

        except Exception as exc:
            self.result.setPlainText(
                f"Lookup unavailable: {type(exc).__name__}: {exc}"
            )


WIDGET_CLASSES = {
    "cpu-ram": CpuRamMonitor,
    "battery": BatteryMonitor,
    "rss": RssNewsReader,
    "calculator": Calculator,
    "todo": TodoList,
    "currency": CurrencyConverter,
    "web-search": WebSearch,
    "dictionary": Dictionary,
}


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CpuRamMonitor()
    window.show()
    sys.exit(app.exec())