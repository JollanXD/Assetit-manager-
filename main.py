from __future__ import annotations

import json
import os
import sys
import hashlib
from pathlib import Path
from datetime import datetime

from PySide6.QtCore import Qt, QSize, QThread, Signal
from PySide6.QtGui import QAction, QPixmap, QIcon
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QLineEdit, QListWidget, QListWidgetItem, QFileDialog,
    QSplitter, QFrame, QScrollArea, QDialog, QFormLayout, QCheckBox, QComboBox,
    QMessageBox, QToolButton, QMenu, QStatusBar, QSizePolicy, QSlider, QSpinBox
)

APP_NAME = "AssetIt"
APP_VERSION = "0.1.0"
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff", ".exr", ".hdr"}
HDRI_EXTS = {".exr", ".hdr", ".tx"}
MODEL_EXTS = {".fbx", ".obj", ".abc", ".usd", ".usda", ".usdc", ".glb", ".gltf", ".stl", ".ply", ".vdb"}
PROJECT_EXTS = {".ma", ".mb", ".blend", ".c4d", ".hip", ".hiplc", ".max", ".3ds", ".ztl"}
ASSET_EXTS = IMAGE_EXTS | MODEL_EXTS | PROJECT_EXTS
APPDATA = Path(os.environ.get("LOCALAPPDATA", str(Path.home() / ".local" / "share"))) / "AssetIt"
SETTINGS_FILE = APPDATA / "settings.json"
PLUGIN_DIR = Path(sys.executable).resolve().parent / "Plugins" if getattr(sys, "frozen", False) else Path(__file__).resolve().parent / "Plugins"


def load_settings():
    try:
        return json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"libraries": [], "thumbnail_size": 150, "show_hidden": False, "favorites": [], "ui_scale": 1.0}


def save_settings(settings):
    APPDATA.mkdir(parents=True, exist_ok=True)
    SETTINGS_FILE.write_text(json.dumps(settings, indent=2, ensure_ascii=False), encoding="utf-8")


def cache_file_for(root: Path) -> Path:
    key = hashlib.sha1(str(root).encode("utf-8", errors="ignore")).hexdigest()[:16]
    return APPDATA / "cache" / f"library_{key}.json"


def read_library_cache(root: Path):
    try:
        data = json.loads(cache_file_for(root).read_text(encoding="utf-8"))
        return [Path(item) for item in data if Path(item).is_file()]
    except (OSError, json.JSONDecodeError, TypeError):
        return []


def write_library_cache(root: Path, paths):
    try:
        target = cache_file_for(root)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps([str(path) for path in paths], ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass


class LibraryScanThread(QThread):
    finished_scan = Signal(list, str)

    def __init__(self, root: Path, show_hidden: bool, parent=None):
        super().__init__(parent)
        self.root = root
        self.show_hidden = show_hidden

    def run(self):
        found = []
        warning = ""
        try:
            for path in self.root.rglob("*"):
                try:
                    if not path.is_file() or path.suffix.lower() not in ASSET_EXTS:
                        continue
                    if not self.show_hidden and any(part.startswith(".") for part in path.relative_to(self.root).parts):
                        continue
                    found.append(path)
                except OSError:
                    continue
        except (OSError, PermissionError) as exc:
            warning = str(exc)
        self.finished_scan.emit(found, warning)


class AssetCard(QFrame):
    activated = Signal(str)
    selected = Signal(str)
    context_requested = Signal(str, object)

    def __init__(self, path: Path, thumb_size: int, parent=None):
        super().__init__(parent)
        self.path = path
        self.setObjectName("assetCard")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumWidth(150)
        self.setMaximumWidth(260)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(7)
        preview = QLabel()
        preview.setObjectName("preview")
        preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview.setFixedHeight(thumb_size)
        preview.setMinimumWidth(120)
        if path.suffix.lower() in IMAGE_EXTS:
            pix = QPixmap(str(path))
            if not pix.isNull():
                preview.setPixmap(pix.scaled(QSize(thumb_size, thumb_size), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            else:
                preview.setText("IMAGE")
        else:
            preview.setText(self._type_label(path))
        name = QLabel(path.name)
        name.setObjectName("assetName")
        name.setWordWrap(True)
        name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name.setToolTip(str(path))
        layout.addWidget(preview)
        layout.addWidget(name)
        self.setToolTip(str(path))
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(lambda pos: self.context_requested.emit(str(self.path), self.mapToGlobal(pos)))

    @staticmethod
    def _type_label(path):
        ext = path.suffix.lower().lstrip(".").upper() or "FILE"
        return "◇\n\n" + ext

    def mousePressEvent(self, event):
        self.selected.emit(str(self.path))
        if event.button() == Qt.MouseButton.LeftButton and event.type() == event.Type.MouseButtonDblClick:
            self.activated.emit(str(self.path))
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        self.activated.emit(str(self.path))
        super().mouseDoubleClickEvent(event)


class SettingsDialog(QDialog):
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AssetIt Settings")
        self.setMinimumWidth(430)
        self.settings = settings
        root = QVBoxLayout(self)
        form = QFormLayout()
        self.hidden = QCheckBox("Show hidden files")
        self.hidden.setChecked(settings.get("show_hidden", False))
        self.scale = QSpinBox()
        self.scale.setRange(50, 300)
        self.scale.setSingleStep(10)
        self.scale.setSuffix("%")
        self.scale.setValue(round(float(settings.get("ui_scale", 1.0)) * 100))
        form.addRow("Interface scale", self.scale)
        form.addRow("", self.hidden)
        root.addLayout(form)
        plugin_note = QLabel(f"Plugin directory:\n{PLUGIN_DIR}\n\nPlugins are discovered from subfolders containing plugin.json.")
        plugin_note.setWordWrap(True)
        plugin_note.setObjectName("muted")
        root.addWidget(plugin_note)
        buttons = QHBoxLayout()
        buttons.addStretch()
        cancel = QPushButton("Cancel")
        save = QPushButton("Save")
        save.setObjectName("primary")
        cancel.clicked.connect(self.reject)
        save.clicked.connect(self.accept)
        buttons.addWidget(cancel)
        buttons.addWidget(save)
        root.addLayout(buttons)

    def accept(self):
        self.settings["ui_scale"] = self.scale.value() / 100.0
        self.settings["show_hidden"] = self.hidden.isChecked()
        super().accept()


class AssetItWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = load_settings()
        self.current_library = None
        self.current_asset = None
        self.cards = []
        self._scan_thread = None
        self._selected_paths = set()
        self.setWindowTitle(f"AssetIt {APP_VERSION}")
        self.resize(1380, 850)
        self.setMinimumSize(980, 620)
        self.setWindowIcon(self._make_icon())
        self._build_ui()
        self._build_menu()
        self.refresh_libraries()
        self._scan_current()

    def _make_icon(self):
        pix = QPixmap(64, 64)
        pix.fill(Qt.GlobalColor.transparent)
        from PySide6.QtGui import QPainter, QColor, QPolygon
        painter = QPainter(pix)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#14bce9"))
        painter.drawPolygon(QPolygon([__import__("PySide6").QtCore.QPoint(6, 54), __import__("PySide6").QtCore.QPoint(27, 10), __import__("PySide6").QtCore.QPoint(42, 10), __import__("PySide6").QtCore.QPoint(22, 54)]))
        painter.setBrush(QColor("#0879ec"))
        painter.drawPolygon(QPolygon([__import__("PySide6").QtCore.QPoint(29, 10), __import__("PySide6").QtCore.QPoint(43, 10), __import__("PySide6").QtCore.QPoint(60, 43), __import__("PySide6").QtCore.QPoint(46, 54)]))
        painter.end()
        return QIcon(pix)

    def _build_menu(self):
        file_menu = self.menuBar().addMenu("File")
        add_action = QAction("Add Library…", self)
        add_action.triggered.connect(self.add_library)
        file_menu.addAction(add_action)
        refresh_action = QAction("Refresh Library", self)
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self._scan_current)
        file_menu.addAction(refresh_action)
        file_menu.addSeparator()
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        tools_menu = self.menuBar().addMenu("Tools")
        settings_action = QAction("Settings…", self)
        settings_action.triggered.connect(self.open_settings)
        tools_menu.addAction(settings_action)
        plugins_action = QAction("Open Plugins Folder", self)
        plugins_action.triggered.connect(self.open_plugins_folder)
        tools_menu.addAction(plugins_action)

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(10, 10, 10, 8)
        root.setSpacing(8)

        header = QHBoxLayout()
        logo = QLabel("▲")
        logo.setObjectName("logo")
        logo.setFixedWidth(28)
        title = QLabel("AssetIt")
        title.setObjectName("brand")
        version = QLabel(APP_VERSION)
        version.setObjectName("muted")
        header.addWidget(logo)
        header.addWidget(title)
        header.addWidget(version)
        header.addStretch()
        self.library_button = QPushButton("+ Add Library")
        self.library_button.setObjectName("primary")
        self.library_button.clicked.connect(self.add_library)
        header.addWidget(self.library_button)
        self.settings_button = QToolButton()
        self.settings_button.setText("⚙")
        self.settings_button.setToolTip("Settings")
        self.settings_button.clicked.connect(self.open_settings)
        header.addWidget(self.settings_button)
        root.addLayout(header)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        root.addWidget(splitter, 1)

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setMinimumWidth(190)
        sidebar.setMaximumWidth(280)
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(8, 10, 8, 8)
        side.addWidget(self._section_label("LIBRARIES"))
        self.library_list = QListWidget()
        self.library_list.setObjectName("libraryList")
        self.library_list.currentRowChanged.connect(self._library_changed)
        side.addWidget(self.library_list, 1)
        self.favorites = QCheckBox("Show favorites only")
        self.favorites.setChecked(False)
        self.favorites.toggled.connect(self._render_cards)
        side.addWidget(self.favorites)
        splitter.addWidget(sidebar)

        browser = QWidget()
        browser_layout = QVBoxLayout(browser)
        browser_layout.setContentsMargins(8, 0, 8, 0)
        browser_layout.setSpacing(8)
        toolbar = QHBoxLayout()
        self.breadcrumb = QLabel("Choose a library")
        self.breadcrumb.setObjectName("muted")
        toolbar.addWidget(self.breadcrumb)
        self.filter_group = QWidget()
        filter_layout = QHBoxLayout(self.filter_group)
        filter_layout.setContentsMargins(0, 0, 0, 0)
        filter_layout.setSpacing(3)
        self.filter_buttons = []
        for index, (key, tip, glyph) in enumerate([("All", "All assets", "▦"), ("Models", "3D models: FBX, OBJ, USD, GLTF…", "⬡"), ("Textures", "Images and textures", "▧"), ("HDRI", "HDRI / environment maps: EXR, HDR", "◉"), ("Projects", "3D application project files", "▣")]):
            button = QToolButton()
            button.setText(glyph)
            button.setToolTip(tip)
            button.setCheckable(True)
            button.setAutoExclusive(True)
            button.setObjectName("filterButton")
            button.clicked.connect(lambda checked=False, i=index: self._set_filter(i))
            filter_layout.addWidget(button)
            self.filter_buttons.append(button)
        self.filter_buttons[0].setChecked(True)
        toolbar.addWidget(self.filter_group)
        self.thumb_size = QSlider(Qt.Orientation.Horizontal)
        self.thumb_size.setRange(90, 240)
        self.thumb_size.setSingleStep(10)
        self.thumb_size.setFixedWidth(100)
        self.thumb_size.setToolTip("Thumbnail size")
        self.thumb_size.setValue(int(self.settings.get("thumbnail_size", 150)))
        self.thumb_size.valueChanged.connect(self._thumbnail_size_changed)
        toolbar.addWidget(self.thumb_size)
        toolbar.addStretch()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search assets…")
        self.search.setClearButtonEnabled(True)
        self.search.setMaximumWidth(320)
        self.search.textChanged.connect(self._render_cards)
        toolbar.addWidget(self.search)
        refresh = QToolButton()
        refresh.setText("↻")
        refresh.setToolTip("Refresh (F5)")
        refresh.clicked.connect(self._scan_current)
        toolbar.addWidget(refresh)
        browser_layout.addLayout(toolbar)
        self.count_label = QLabel("0 assets")
        self.count_label.setObjectName("muted")
        browser_layout.addWidget(self.count_label)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.grid_host = QWidget()
        self.grid = QGridLayout(self.grid_host)
        self.grid.setContentsMargins(2, 2, 2, 2)
        self.grid.setSpacing(9)
        self.scroll.setWidget(self.grid_host)
        browser_layout.addWidget(self.scroll, 1)
        splitter.addWidget(browser)

        info = QFrame()
        info.setObjectName("infoPanel")
        info.setMinimumWidth(230)
        info.setMaximumWidth(310)
        info_layout = QVBoxLayout(info)
        info_layout.setContentsMargins(12, 12, 12, 12)
        info_layout.addWidget(self._section_label("ASSET INFO"))
        self.info_preview = QLabel("Select an asset")
        self.info_preview.setObjectName("infoPreview")
        self.info_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.info_preview.setMinimumHeight(170)
        self.info_preview.setMaximumHeight(250)
        info_layout.addWidget(self.info_preview)
        self.info_name = QLabel("—")
        self.info_name.setObjectName("infoName")
        self.info_name.setWordWrap(True)
        info_layout.addWidget(self.info_name)
        self.info_type = QLabel("TYPE   —")
        self.info_path = QLabel("PATH   —")
        self.info_size = QLabel("SIZE   —")
        for label in (self.info_type, self.info_path, self.info_size):
            label.setObjectName("infoText")
            label.setWordWrap(True)
            info_layout.addWidget(label)
        info_layout.addStretch()
        self.open_file_button = QPushButton("Open File")
        self.open_file_button.setEnabled(False)
        self.open_file_button.clicked.connect(self.open_selected)
        info_layout.addWidget(self.open_file_button)
        self.open_folder_button = QPushButton("Open Containing Folder")
        self.open_folder_button.setEnabled(False)
        self.open_folder_button.clicked.connect(self.open_containing_folder)
        info_layout.addWidget(self.open_folder_button)
        splitter.addWidget(info)
        splitter.setSizes([220, 850, 270])
        self.sidebar_widget = sidebar
        self.info_widget = info
        self.toggle_left = QToolButton()
        self.toggle_left.setText("◧")
        self.toggle_left.setToolTip("Show/hide libraries panel")
        self.toggle_left.clicked.connect(lambda: self._toggle_panel(self.sidebar_widget))
        self.toggle_right = QToolButton()
        self.toggle_right.setText("◨")
        self.toggle_right.setToolTip("Show/hide asset information panel")
        self.toggle_right.clicked.connect(lambda: self._toggle_panel(self.info_widget))
        toolbar.insertWidget(1, self.toggle_left)
        toolbar.insertWidget(2, self.toggle_right)

        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage("Ready")

    def _toggle_panel(self, panel):
        panel.setVisible(not panel.isVisible())

    def _thumbnail_size_changed(self, value):
        self.settings["thumbnail_size"] = int(value)
        self._render_cards()

    def _set_filter(self, index):
        if 0 <= index < len(self.filter_buttons):
            self.filter_buttons[index].setChecked(True)
            self._render_cards()

    @staticmethod
    def _section_label(text):
        label = QLabel(text)
        label.setObjectName("sectionLabel")
        return label

    def refresh_libraries(self):
        self.library_list.blockSignals(True)
        self.library_list.clear()
        for path in self.settings.get("libraries", []):
            item = QListWidgetItem("▣  " + Path(path).name)
            item.setToolTip(path)
            item.setData(Qt.ItemDataRole.UserRole, path)
            self.library_list.addItem(item)
        self.library_list.blockSignals(False)
        if self.library_list.count():
            self.library_list.setCurrentRow(0)
        else:
            self._show_empty("Add a library folder to begin")

    def add_library(self):
        folder = QFileDialog.getExistingDirectory(self, "Add Asset Library")
        if not folder:
            return
        folder = str(Path(folder).resolve())
        if folder not in self.settings["libraries"]:
            self.settings["libraries"].append(folder)
            save_settings(self.settings)
        self.refresh_libraries()
        for i in range(self.library_list.count()):
            if self.library_list.item(i).data(Qt.ItemDataRole.UserRole) == folder:
                self.library_list.setCurrentRow(i)
                break

    def _library_changed(self, row):
        if row < 0 or row >= self.library_list.count():
            self.current_library = None
            self._show_empty("Add a library folder to begin")
            return
        self.current_library = Path(self.library_list.item(row).data(Qt.ItemDataRole.UserRole))
        self.breadcrumb.setText(str(self.current_library))
        self._scan_current()

    def _scan_current(self):
        if self._scan_thread and self._scan_thread.isRunning():
            self.status.showMessage("A library scan is already running…")
            return
        if not self.current_library or not self.current_library.exists():
            self.cards = []
            self._render_cards()
            self.status.showMessage("Library folder is unavailable")
            return
        library = self.current_library
        show_hidden = self.settings.get("show_hidden", False)
        self.status.showMessage("Scanning library in background…")
        cached = read_library_cache(library)
        if cached:
            self.cards = cached
            self._render_cards()
            self.status.showMessage(f"Loaded {len(cached)} cached assets; checking for changes…")
        self._scan_thread = LibraryScanThread(library, show_hidden, self)
        self._scan_thread.finished_scan.connect(self._scan_finished)
        self._scan_thread.start()

    def _scan_finished(self, paths, warning):
        self.cards = paths
        self.cards.sort(key=lambda p: (p.suffix.lower() not in IMAGE_EXTS, p.name.casefold()))
        if self.current_library:
            write_library_cache(self.current_library, self.cards)
        self._render_cards()
        if warning:
            self.status.showMessage(f"Scan completed with warning: {warning}")
        else:
            self.status.showMessage(f"Scanned {len(self.cards)} supported files")

    def _render_cards(self, *_):
        while self.grid.count():
            item = self.grid.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        query = self.search.text().casefold().strip()
        mode = next((i for i, button in enumerate(self.filter_buttons) if button.isChecked()), 0)
        visible = []
        favorites = set(self.settings.get("favorites", []))
        for path in self.cards:
            ext = path.suffix.lower()
            if self.favorites.isChecked() and str(path) not in favorites:
                continue
            if query and query not in path.name.casefold() and query not in str(path.parent).casefold():
                continue
            if mode == 1 and ext not in MODEL_EXTS:
                continue
            if mode == 2 and (ext not in IMAGE_EXTS or ext in HDRI_EXTS):
                continue
            if mode == 3 and ext not in HDRI_EXTS:
                continue
            if mode == 4 and ext not in PROJECT_EXTS:
                continue
            visible.append(path)
        cols = max(1, self.scroll.viewport().width() // (self.settings.get("thumbnail_size", 150) + 28))
        thumb = self.settings.get("thumbnail_size", 150)
        for index, path in enumerate(visible):
            card = AssetCard(path, thumb)
            card.selected.connect(self.select_asset)
            card.activated.connect(self._open_path)
            card.context_requested.connect(self._asset_context_menu)
            self.grid.addWidget(card, index // cols, index % cols)
        self.count_label.setText(f"{len(visible)} assets")
        if not visible:
            self._show_empty("No matching assets found" if self.cards else "This library contains no supported assets")

    def _asset_context_menu(self, path_string, global_pos):
        path = Path(path_string)
        favorites = set(self.settings.get("favorites", []))
        menu = QMenu(self)
        favorite_action = menu.addAction("Remove from favorites" if path_string in favorites else "Add to favorites")
        menu.addSeparator()
        open_action = menu.addAction("Open file")
        folder_action = menu.addAction("Open containing folder")
        chosen = menu.exec(global_pos)
        if chosen == favorite_action:
            if path_string in favorites:
                favorites.remove(path_string)
            else:
                favorites.add(path_string)
            self.settings["favorites"] = sorted(favorites)
            save_settings(self.settings)
            self._render_cards()
        elif chosen == open_action:
            self._open_path(path_string)
        elif chosen == folder_action:
            self.current_asset = path
            self.open_containing_folder()

    def _show_empty(self, message):
        while self.grid.count():
            item = self.grid.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        label = QLabel(message)
        label.setObjectName("emptyState")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.grid.addWidget(label, 0, 0)
        self.count_label.setText("0 assets")

    def select_asset(self, path_string):
        path = Path(path_string)
        self.current_asset = path
        self.info_name.setText(path.name)
        self.info_type.setText("TYPE   " + (path.suffix[1:].upper() if path.suffix else "FILE"))
        self.info_path.setText("PATH   " + str(path))
        try:
            size = path.stat().st_size
            self.info_size.setText(f"SIZE   {size / 1024:.1f} KB" if size < 1024**2 else f"SIZE   {size / 1024**2:.2f} MB")
        except OSError:
            self.info_size.setText("SIZE   unavailable")
        self.info_preview.clear()
        if path.suffix.lower() in IMAGE_EXTS:
            pix = QPixmap(str(path))
            if not pix.isNull():
                self.info_preview.setPixmap(pix.scaled(self.info_preview.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            else:
                self.info_preview.setText("Preview unavailable")
        else:
            self.info_preview.setText(path.suffix.upper() + "\n\nPreview not available yet")
        self.open_file_button.setEnabled(True)
        self.open_folder_button.setEnabled(True)

    def _open_path(self, path):
        self.select_asset(path)
        if Path(path).suffix.lower() in IMAGE_EXTS:
            dlg = QDialog(self)
            dlg.setWindowTitle(Path(path).name)
            dlg.resize(900, 700)
            layout = QVBoxLayout(dlg)
            image = QLabel()
            image.setAlignment(Qt.AlignmentFlag.AlignCenter)
            pix = QPixmap(path)
            image.setPixmap(pix.scaled(860, 630, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            layout.addWidget(image)
            details = QLabel(f"{pix.width()} × {pix.height()} px   •   {Path(path).suffix.upper()}")
            details.setObjectName("muted")
            layout.addWidget(details)
            dlg.exec()
        else:
            self.open_selected()

    def open_selected(self):
        if self.current_asset and self.current_asset.exists():
            os.startfile(str(self.current_asset)) if os.name == "nt" else __import__("subprocess").Popen(["xdg-open", str(self.current_asset)])

    def open_containing_folder(self):
        if self.current_asset and self.current_asset.exists():
            if os.name == "nt":
                os.startfile(str(self.current_asset.parent))
            else:
                __import__("subprocess").Popen(["xdg-open", str(self.current_asset.parent)])

    def open_settings(self):
        dialog = SettingsDialog(self.settings, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            save_settings(self.settings)
            scale = float(self.settings.get("ui_scale", 1.0))
            font = QApplication.font()
            font.setPointSizeF(10 * scale)
            QApplication.setFont(font)
            self._render_cards()

    def open_plugins_folder(self):
        PLUGIN_DIR.mkdir(parents=True, exist_ok=True)
        if os.name == "nt":
            os.startfile(str(PLUGIN_DIR))
        else:
            __import__("subprocess").Popen(["xdg-open", str(PLUGIN_DIR)])


STYLE = """
QMainWindow, QDialog, QWidget { background: #202124; color: #d7dbe0; font-family: "Segoe UI"; font-size: 10pt; }
QMenuBar { background: #25272a; color: #d7dbe0; border-bottom: 1px solid #34373b; }
QMenuBar::item { padding: 5px 10px; background: transparent; }
QMenuBar::item:selected, QMenu::item:selected { background: #173d50; color: #54cfff; }
QMenu { background: #292c30; border: 1px solid #41454a; }
QMenu::item { padding: 6px 24px; }
QLineEdit, QComboBox { background: #181a1c; border: 1px solid #3b3f43; border-radius: 4px; padding: 7px; selection-background-color: #087db0; }
QLineEdit:focus, QComboBox:focus { border: 1px solid #1db8ed; }
QComboBox QAbstractItemView { background: #25272a; selection-background-color: #17445a; }
QPushButton, QToolButton { background: #2b2e32; border: 1px solid #41454a; border-radius: 4px; padding: 7px 10px; }
QPushButton:hover, QToolButton:hover { border-color: #16b9f0; color: #59d1ff; }
QToolButton#filterButton { min-width: 28px; padding: 6px 9px; font-size: 13pt; }
QToolButton#filterButton:checked { background: #123b4d; border: 1px solid #087fb1; color: #65d5ff; }
QPushButton#primary { background: #123b4d; border: 1px solid #087fb1; color: #65d5ff; font-weight: 600; }
QPushButton#primary:hover { background: #174c62; }
QFrame#sidebar, QFrame#infoPanel { background: #242629; border: 1px solid #34373b; border-radius: 5px; }
QListWidget { background: transparent; border: none; outline: none; }
QListWidget::item { padding: 10px 7px; border-radius: 4px; }
QListWidget::item:selected { background: #143b4c; color: #62d5ff; }
QLabel#brand { color: #e7f6ff; font-size: 18pt; font-weight: 600; }
QLabel#logo { color: #1fc5f5; font-size: 22pt; font-weight: bold; }
QLabel#muted, QLabel#sectionLabel { color: #89939d; }
QLabel#sectionLabel { font-size: 8pt; font-weight: bold; letter-spacing: 1px; padding: 5px 0; }
QLabel#preview { background: #191b1d; border: 1px solid #2c2f32; border-radius: 3px; color: #35c5f4; font-size: 15pt; }
QFrame#assetCard { background: #25272a; border: 1px solid #34373b; border-radius: 5px; }
QFrame#assetCard:hover { background: #2a2e32; border: 1px solid #0d9fce; }
QLabel#assetName { color: #cbd1d7; font-size: 9pt; }
QLabel#infoPreview { background: #191b1d; border: 1px solid #34373b; border-radius: 4px; color: #8e9aa5; }
QLabel#infoName { color: #59d0ff; font-weight: bold; padding-top: 7px; }
QLabel#infoText { color: #a9b1b8; font-size: 9pt; padding: 3px 0; }
QLabel#emptyState { color: #78848d; font-size: 12pt; padding: 40px; }
QCheckBox { spacing: 8px; }
QCheckBox::indicator { width: 14px; height: 14px; }
QCheckBox::indicator:checked { background: #0b9dce; border: 1px solid #35c7f5; }
QStatusBar { background: #1a1c1e; color: #8d969e; border-top: 1px solid #34373b; }
QScrollArea { background: transparent; }
QSplitter::handle { background: #202124; width: 5px; }
QToolTip { background: #30343a; color: #e8edf2; border: 1px solid #0e94c4; padding: 4px; }
"""


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setStyle("Fusion")
    scale = float(load_settings().get("ui_scale", 1.0))
    import re
    scaled_style = re.sub(r"font-size:\s*([0-9.]+)pt", lambda match: f"font-size: {float(match.group(1)) * scale:.1f}pt", STYLE)
    app.setStyleSheet(scaled_style)
    window = AssetItWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
