"""Stock watchlist; Yahoo chart API is an unofficial best-effort data source."""
import json
from pathlib import Path
from urllib.request import Request, urlopen
from PySide6.QtCore import Qt, QTimer, QObject, Signal, QThread, QStandardPaths
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QPlainTextEdit

CONFIG = Path(QStandardPaths.writableLocation(QStandardPaths.AppConfigLocation)) / 'Widget_Wall' / 'stock_ticker.json'

class FetchWorker(QThread):
    finished_data = Signal(list)
    def __init__(self, symbols):
        super().__init__()
        self.symbols = symbols
    def run(self):
        results = []
        for symbol in self.symbols[:12]:
            try:
                url = 'https://query1.finance.yahoo.com/v8/finance/chart/' + symbol + '?range=1d&interval=1d'
                req = Request(url, headers={'User-Agent': 'Mozilla/5.0 WidgetWall/0.3'})
                with urlopen(req, timeout=6) as response:
                    data = json.load(response)['chart']['result'][0]
                meta = data['meta']
                price = meta.get('regularMarketPrice')
                currency = meta.get('currency', '')
                stamp = meta.get('regularMarketTime', 0)
                if price is None: raise ValueError('price unavailable')
                from datetime import datetime, timezone
                age = datetime.fromtimestamp(stamp, timezone.utc).strftime('%Y-%m-%d %H:%M UTC') if stamp else 'timestamp unknown'
                results.append(f'{symbol:<9} {price:,.2f} {currency}  | as of {age}')
            except Exception:
                results.append(f'{symbol:<9} quote unavailable (network/provider)')
        self.finished_data.emit(results)

class StockTicker(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Widget Wall | Stock Ticker')
        self.resize(550, 340)
        self.setStyleSheet('QWidget { background:#17151f; color:#e9d8ff; font-size:13px; } QPushButton,QLineEdit,QPlainTextEdit { background:#30263c; border:1px solid #75538d; border-radius:5px; padding:7px; }')
        self.worker = None
        lay = QVBoxLayout(self)
        lay.addWidget(QLabel('STOCK TICKER  /  WATCHLIST'))
        row = QHBoxLayout()
        self.entry = QLineEdit()
        self.entry.setPlaceholderText('Symbols separated by commas: MSFT, AAPL, NVDA')
        row.addWidget(self.entry)
        self.button = QPushButton('Refresh')
        self.button.clicked.connect(self.refresh)
        row.addWidget(self.button)
        lay.addLayout(row)
        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        lay.addWidget(self.output)
        lay.addWidget(QLabel('Unofficial provider; quotes may be delayed. Not real-time trading data.'))
        try: self.entry.setText(', '.join(json.loads(CONFIG.read_text(encoding='utf-8')).get('symbols', [])))
        except (OSError, ValueError): self.entry.setText('MSFT, AAPL, NVDA')
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(300000)
        QTimer.singleShot(300, self.refresh)

    def refresh(self):
        if self.worker is not None and self.worker.isRunning(): return
        symbols = list(dict.fromkeys(s.strip().upper() for s in self.entry.text().split(',') if s.strip()))[:12]
        symbols = [s for s in symbols if len(s) <= 12 and all(c.isalnum() or c in '.-^' for c in s)]
        if not symbols:
            self.output.setPlainText('Enter at least one valid ticker symbol.')
            return
        CONFIG.parent.mkdir(parents=True, exist_ok=True)
        CONFIG.write_text(json.dumps({'symbols': symbols}, indent=2), encoding='utf-8')
        self.output.setPlainText('Fetching quotes...')
        self.button.setEnabled(False)
        self.worker = FetchWorker(symbols)
        self.worker.finished_data.connect(self.show_data)
        self.worker.finished.connect(lambda: self.button.setEnabled(True))
        self.worker.start()

    def show_data(self, rows):
        self.output.setPlainText('\n'.join(rows))