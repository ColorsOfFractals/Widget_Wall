# Widget_Wall

A Windows desktop widget playground built with Python, Qt, React, and Vite.

Widget_Wall combines a native PySide6 desktop shell with an embedded React interface, draggable widget windows, weather functionality, and experimental Sonic Workshop instruments.

## Current status

Development version: 0.3.0

The project currently runs from source. A packaged Windows installer and GitHub Releases updater are planned.

## Requirements

- Windows
- Python 3.13
- Node.js and npm

## Run from source

Install Python dependencies:

    python -m pip install -r requirements.txt

Install frontend dependencies and build:

    npm ci
    npm run build

Launch Widget_Wall:

    python widget_wall.py

## Development notes

- Python and PySide6 provide the native desktop application.
- React and Vite provide the embedded frontend.
- The frontend build is generated in dist/.
- Sonic Workshop features currently depend on local experimental assets that are not included in the repository.
- Windows geolocation is used for location-aware weather functionality.

## License

MIT. See LICENSE.
