"""Pocket Weather: draggable transparent weather sprite for Widget_Wall."""
import json
import math
import queue
import random
import threading
import time
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from PySide6.QtCore import Qt, QTimer, QPointF
from PySide6.QtGui import QColor, QPainter, QPen, QBrush, QFont
from PySide6.QtWidgets import QWidget, QMenu, QInputDialog


def _fetch_json(url):
    req = Request(url, headers={"User-Agent": "WidgetWall-PocketWeather/0.8"})
    with urlopen(req, timeout=9) as response:
        return json.load(response)


def _weather_for_windows():
    import asyncio
    from winrt.windows.devices.geolocation import Geolocator, GeolocationAccessStatus

    async def locate():
        access = await Geolocator.request_access_async()
        if access != GeolocationAccessStatus.ALLOWED:
            raise PermissionError("Windows location access denied")
        locator = Geolocator()
        locator.desired_accuracy_in_meters = 1000
        pos = await locator.get_geoposition_async()
        coords = pos.coordinate.point.position
        return coords.latitude, coords.longitude

    # Run in a worker thread, never block Qt's GUI thread.
    latitude, longitude = asyncio.run(asyncio.wait_for(locate(), timeout=20))
    label = "WINDOWS LOCATION"

    try:
        # Resolve the Windows-provided coordinates into a readable place.
        # Coordinates are shared with OpenStreetMap's Nominatim service.
        query = urlencode({
            "lat": round(latitude, 5),
            "lon": round(longitude, 5),
            "format": "json",
            "addressdetails": 1,
            "zoom": 10
        })

        place = _fetch_json(
            "https://nominatim.openstreetmap.org/reverse?" + query
        )

        address = place.get("address") or {}
        city = (
            address.get("city")
            or address.get("town")
            or address.get("village")
            or address.get("municipality")
            or address.get("county")
        )
        state = address.get("state_code") or address.get("state")
        if state and state.lower() == "washington":
            state = "WA"

        if city:
            label = city.upper()
            if state:
                label += ", " + state.upper()

    except Exception:
        # Geocoding must never prevent weather updates.
        pass

    return _weather_for_coordinates(latitude, longitude, label)


def _weather_for_coordinates(latitude, longitude, label):
    query = urlencode({"latitude": round(latitude, 3), "longitude": round(longitude, 3),
                       "current": "temperature_2m,weather_code,is_day", "temperature_unit": "fahrenheit",
                       "timezone": "auto"})
    data = _fetch_json("https://api.open-meteo.com/v1/forecast?" + query)
    current = data["current"]
    code = int(current["weather_code"])
    day = bool(current.get("is_day", 1))
    if code in (0, 1):
        condition = "sun" if day else "night"
    elif code in (2, 3, 45, 48):
        condition = "cloud"
    elif code in (51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82):
        condition = "rain"
    elif code in (71, 73, 75, 77, 85, 86):
        condition = "snow"
    elif code in (95, 96, 99):
        condition = "storm"
    else:
        condition = "cloud"
    return condition, f"{label}  {round(current['temperature_2m'])} \u00b0F"


def _weather_for_city(city):
    geocode = _fetch_json("https://geocoding-api.open-meteo.com/v1/search?" + urlencode({"name": city, "count": 1, "language": "en", "format": "json"}))
    results = geocode.get("results") or []
    if not results:
        raise ValueError("City not found")
    place = results[0]
    return _weather_for_coordinates(place["latitude"], place["longitude"], place["name"] )


class PocketWeather(QWidget):
    CONDITIONS = ("rain", "sun", "cloud", "storm", "snow", "night")

    def __init__(self, number=0):
        super().__init__()
        self.condition = "rain"
        self.city = ""
        self.source = "windows"
        self.caption = "LOCATING WEATHER..."
        self.live = False
        self.frame = 0
        self.drag_delta = None
        self.results = queue.Queue()
        self.fetching = False
        self.particles = [(random.uniform(25, 155), random.uniform(92, 160), random.uniform(.7, 1.7)) for _ in range(24)]
        self.setWindowTitle("Widget_Wall | Pocket Weather")
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setMouseTracking(True)
        self.resize(180, 180)
        self.move(160 + number * 17, 170 + number * 17)
        self.setToolTip("Drag to move Â· Right-click for weather menu Â· Mouse wheel to resize")
        self.animation = QTimer(self)
        self.animation.timeout.connect(self._tick)
        self.animation.start(45)
        self.poller = QTimer(self)
        self.poller.timeout.connect(self._poll)
        self.poller.start(250)
        self.refresh = QTimer(self)
        self.refresh.timeout.connect(self._request_weather)
        self.refresh.start(15 * 60 * 1000)
        QTimer.singleShot(100, self._request_weather)

    def _tick(self):
        self.frame += 1
        self.update()

    def _request_weather(self):
        if self.source == "demo" or self.fetching:
            return
        self.fetching = True
        source, city = self.source, self.city
        key = (source, city)
        def worker():
            try:
                result = _weather_for_windows() if source == "windows" else _weather_for_city(city)
                self.results.put((key, result, None))
            except Exception as exc:
                self.results.put((key, None, str(exc)))
        threading.Thread(target=worker, daemon=True).start()

    def _poll(self):
        try:
            while True:
                key, result, error = self.results.get_nowait()
                if key != (self.source, self.city):
                    continue
                self.fetching = False
                if error:
                    self.caption = "WEATHER UNAVAILABLE"
                    self.live = False
                else:
                    self.condition, self.caption = result
                    self.live = True
                self.update()
        except queue.Empty:
            pass

    def _set_city(self):
        city, ok = QInputDialog.getText(None, "Pocket Weather", "City or town:", text=self.city)
        if ok and city.strip():
            self.city = city.strip()
            self.source = "city"
            self.fetching = False
            self.caption = "FETCHING WEATHER..."
            self._request_weather()

    def _set_manual(self, condition):
        self.city = ""
        self.source = "demo"
        self.fetching = False
        self.condition = condition
        self.live = False
        self.caption = condition.upper() + "  Â·  DEMO"
        self.update()

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.setStyleSheet("QMenu{background:#17151c;color:#ffe4cb;border:1px solid #ff922f;padding:6px}QMenu::item:selected{background:#713c22}")
        windows_action = menu.addAction("Use Windows location (live)")
        city_action = menu.addAction("Set city / live weather...")
        refresh_action = menu.addAction("Refresh weather")
        menu.addSeparator()
        actions = {menu.addAction("Preview: " + name.title()): name for name in self.CONDITIONS}
        menu.addSeparator()
        close_action = menu.addAction("Close pocket weather")
        selected = menu.exec(event.globalPos())
        if selected == windows_action:
            self.source = "windows"
            self.fetching = False
            self.city = ""
            self.caption = "LOCATING WEATHER..."
            self._request_weather()
        elif selected == city_action:
            self._set_city()
        elif selected == refresh_action:
            self._request_weather()
        elif selected == close_action:
            self.close()
        elif selected in actions:
            self._set_manual(actions[selected])

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_delta = event.globalPosition().toPoint() - self.pos()
            event.accept()

    def mouseMoveEvent(self, event):
        if self.drag_delta is not None and event.buttons() & Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_delta)
            event.accept()

    def mouseReleaseEvent(self, event):
        self.drag_delta = None

    def wheelEvent(self, event):
        side = max(110, min(340, self.width() + (20 if event.angleDelta().y() > 0 else -20)))
        self.resize(side, side)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        scale = min(self.width(), self.height()) / 180.0
        p.scale(scale, scale)
        bob = math.sin(self.frame * .055) * 3
        kind = self.condition
        if kind in ("sun", "night"):
            if kind == "sun":
                p.setPen(QPen(QColor("#ffc55e"), 5, Qt.SolidLine, Qt.RoundCap))
                for i in range(12):
                    angle = (i * math.pi / 6) + self.frame * .006
                    x, y = math.cos(angle), math.sin(angle)
                    p.drawLine(QPointF(90 + x * 43, 75 + y * 43), QPointF(90 + x * 56, 75 + y * 56))
                p.setPen(Qt.NoPen)
                p.setBrush(QColor("#ffcd62"))
                p.drawEllipse(QPointF(90, 75), 34, 34)
                p.setBrush(QColor("#ffe6a1"))
                p.drawEllipse(QPointF(80, 66), 10, 9)
            else:
                p.setPen(Qt.NoPen)
                p.setBrush(QColor("#e8e6ff"))
                p.drawEllipse(QPointF(90, 75), 38, 38)
                p.setBrush(QColor(0, 0, 0, 0))
                p.setCompositionMode(QPainter.CompositionMode_Clear)
                p.drawEllipse(QPointF(109, 59), 34, 34)
                p.setCompositionMode(QPainter.CompositionMode_SourceOver)
                p.setPen(QPen(QColor("#fff2ae"), 3))
                for i in range(6):
                    x = 38 + i * 21
                    y = 31 + (i % 3) * 9
                    p.drawPoint(QPointF(x, y))
        else:
            p.setPen(Qt.NoPen)
            base = "#8c9aac" if kind == "storm" else "#d6e3ec"
            p.setBrush(QColor(base))
            for x, y, radius in ((59, 83, 26), (90, 68, 34), (121, 84, 27)):
                p.drawEllipse(QPointF(x, y + bob), radius, radius)
            p.drawRoundedRect(39, 79 + bob, 103, 34, 16, 16)
            p.setBrush(QColor("#f5f9ff" if kind != "storm" else "#a5b1c4"))
            p.drawEllipse(QPointF(80, 64 + bob), 20, 15)
            if kind in ("rain", "snow", "storm"):
                for i, (x, y, speed) in enumerate(self.particles):
                    yy = 112 + ((y - 112 + self.frame * speed * (2.3 if kind != "snow" else .7)) % 47)
                    xx = x + (math.sin(self.frame * .035 + i) * 5 if kind == "snow" else 0)
                    if kind == "snow":
                        p.setPen(QPen(QColor("#f4fcff"), 2))
                        p.drawLine(QPointF(xx - 3, yy), QPointF(xx + 3, yy))
                        p.drawLine(QPointF(xx, yy - 3), QPointF(xx, yy + 3))
                    else:
                        p.setPen(QPen(QColor("#65caff"), 2.5, Qt.SolidLine, Qt.RoundCap))
                        p.drawLine(QPointF(xx, yy), QPointF(xx - 4, yy + 9))
            if kind == "storm" and self.frame % 70 < 11:
                p.setPen(Qt.NoPen)
                p.setBrush(QColor("#ffe65b"))
                from PySide6.QtGui import QPolygonF
                p.drawPolygon(QPolygonF([QPointF(91, 110), QPointF(78, 137), QPointF(91, 137), QPointF(83, 160), QPointF(112, 128), QPointF(98, 128), QPointF(107, 110)]))
        p.setPen(QColor("#55EAFF"))
        font = QFont("Consolas", 8, QFont.Bold)
        p.setFont(font)
        text = self.caption
        font = p.font()
        while font.pointSize() > 6:
            if p.fontMetrics().horizontalAdvance(text) <= 168:
                break
            font.setPointSize(font.pointSize() - 1)
            p.setFont(font)
        p.drawText(4, 164, 172, 13, Qt.AlignCenter, text)

        p.end()
