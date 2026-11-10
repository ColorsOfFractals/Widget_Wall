from pathlib import Path

# The spec lives in installer/, one level below the repository root.
PROJECT_ROOT = Path(SPECPATH).resolve().parent
# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules

hiddenimports = []
hiddenimports += collect_submodules('winrt')
hiddenimports += collect_submodules('winrt.windows')
hiddenimports += collect_submodules('winrt.windows.devices.geolocation')
hiddenimports += collect_submodules('winrt.windows.media.control')
hiddenimports += collect_submodules('winrt.windows.storage.streams')


a = Analysis(
    [str(PROJECT_ROOT / 'widget_wall.py')],
    pathex=[],
    binaries=[],
    datas=[(str(PROJECT_ROOT / 'dist'), 'dist'), (str(PROJECT_ROOT / 'assets'), 'assets'), (str(PROJECT_ROOT / 'sonic_workshop'), 'sonic_workshop'), (str(PROJECT_ROOT / 'powershell_discovery.ps1'), '.'), (str(PROJECT_ROOT / 'powershell_descriptions.json'), '.'), (str(PROJECT_ROOT / 'src' / 'fractal_lexicon.json'), 'src'), (str(PROJECT_ROOT / 'src' / 'tokenbridges_lexicon.json'), 'src')],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
# Widget Wall lean distribution filters.
# Keep core Qt/WebEngine binaries and resources intact.
# Remove only categories validated in isolated candidate testing.

def widget_wall_exclude(entry):
    name = str(entry[0]).replace("\\", "/").lower()
    parts = name.split("/")
    base = parts[-1]

    if "pyside6" not in parts:
        return False

    qt_index = parts.index("pyside6")
    relative = parts[qt_index + 1:]

    if relative and relative[0] == "qml":
        return True

    if "resources" in relative and (
        base.endswith(".debug.pak") or
        base == "v8_context_snapshot.debug.bin"
    ):
        return True

    if len(relative) == 1 and base.endswith(".dll"):
        return base.startswith((
            "qt63d",
            "qt6quick3d",
            "qt6charts",
            "qt6graphs",
            "qt6virtualkeyboard",
            "qt6labs",
        ))

    return False


def widget_wall_filter(toc):
    kept = []
    removed = []

    for entry in toc:
        if widget_wall_exclude(entry):
            removed.append(entry[0])
        else:
            kept.append(entry)

    return kept, removed

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Widget_Wall',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=[str(PROJECT_ROOT / 'assets' / 'Widget_Wall.ico')],
    contents_directory='.',
)
# Apply filters after Analysis and before COLLECT.
# TOC objects are replaced with filtered equivalents.
a.binaries, lean_removed_binaries = widget_wall_filter(a.binaries)
a.datas, lean_removed_datas = widget_wall_filter(a.datas)

print(
    "WIDGET WALL LEAN | removed entries:",
    len(lean_removed_binaries) + len(lean_removed_datas)
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Widget_Wall_Lean_Rebuild',
)
