from __future__ import annotations

import json
import os
import sys
import hashlib
import shutil
from pathlib import Path
from datetime import datetime

from PySide6.QtCore import Qt, QSize, QThread, Signal, QTimer
from PySide6.QtGui import QAction, QPixmap, QIcon, QPainter, QPixmapCache, QImageReader
from PySide6.QtCore import QByteArray
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QLineEdit, QListWidget, QListWidgetItem, QFileDialog,
    QSplitter, QFrame, QScrollArea, QDialog, QFormLayout, QCheckBox, QComboBox,
    QMessageBox, QToolButton, QMenu, QStatusBar, QSizePolicy, QSlider, QSpinBox, QProgressBar
)

APP_NAME = "AssetIt"
APP_VERSION = "0.3.1"
DEFAULT_TAGS = ["PBR", "Grid", "Sci-Fi", "Seamless", "NormalMap", "4K", "HardSurface", "Arasaka", "Metal", "Blueprint", "HDRI", "8K", "Outdoor"]
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff", ".exr", ".hdr"}
HDRI_EXTS = {".exr", ".hdr", ".tx"}
IMAGE_EXTS.add(".tx")
MODEL_EXTS = {".fbx", ".obj", ".abc", ".usd", ".usda", ".usdc", ".glb", ".gltf", ".stl", ".ply", ".vdb"}
PROJECT_EXTS = {".ma", ".mb", ".blend", ".c4d", ".hip", ".hiplc", ".max", ".3ds", ".ztl"}
ASSET_EXTS = IMAGE_EXTS | MODEL_EXTS | PROJECT_EXTS
APPDATA = Path(os.environ.get("LOCALAPPDATA", str(Path.home() / ".local" / "share"))) / "AssetIt"
SETTINGS_FILE = APPDATA / "settings.json"
PLUGIN_DIR = Path(sys.executable).resolve().parent / "Plugins" if getattr(sys, "frozen", False) else Path(__file__).resolve().parent / "Plugins"


def thumbnail_cache_path(path: Path, size: int) -> Path:
    """Persistent thumbnail cache invalidated when source path, timestamp, size or thumb size changes."""
    try:
        stat = path.stat()
        identity = f"{path.resolve()}|{stat.st_mtime_ns}|{stat.st_size}|{size}"
    except OSError:
        identity = f"{path}|missing|{size}"
    key = hashlib.sha1(identity.encode("utf-8", errors="replace")).hexdigest()
    return APPDATA / "cache" / "thumbnails" / f"{key}.png"


def cached_preview(path: Path, size: int) -> QPixmap:
    """Load an already-generated preview without decoding the original asset on the UI thread."""
    cache_path = thumbnail_cache_path(path, size)
    key = f"assetit:{cache_path}"
    cached = QPixmapCache.find(key)
    if cached is not None:
        return cached
    if cache_path.is_file():
        pix = QPixmap(str(cache_path))
        if not pix.isNull():
            QPixmapCache.insert(key, pix)
            return pix
    return QPixmap()


class ThumbnailBatchWorker(QThread):
    thumbnail_ready = Signal(str, object)

    def __init__(self, paths, size, parent=None):
        super().__init__(parent)
        self.paths = list(paths)
        self.size = max(32, int(size))

    def run(self):
        for path in self.paths:
            try:
                cache_path = thumbnail_cache_path(path, self.size)
                image = QImageReader(str(cache_path)).read() if cache_path.is_file() else None
                if image is None or image.isNull():
                    reader = QImageReader(str(path))
                    reader.setAutoTransform(True)
                    original = reader.size()
                    if original.isValid():
                        reader.setScaledSize(original.scaled(QSize(self.size, self.size), Qt.AspectRatioMode.KeepAspectRatio))
                    image = reader.read()
                    if image.isNull():
                        continue
                    try:
                        cache_path.parent.mkdir(parents=True, exist_ok=True)
                        image.save(str(cache_path), "PNG")
                    except OSError:
                        pass
                self.thumbnail_ready.emit(str(path), image)
            except Exception:
                continue


def load_settings():
    try:
        return json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"libraries": [], "thumbnail_size": 150, "show_hidden": False, "favorites": [], "ui_scale": 1.0, "show_disk_usage": False, "asset_tags": {}}


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
    favorite_toggled = Signal(str)

    def __init__(self, path: Path, thumb_size: int, is_favorite=False, parent=None):
        super().__init__(parent)
        self.path = path
        self.setObjectName("assetCard")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumWidth(150)
        self.setMaximumWidth(260)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(7, 7, 7, 7)
        layout.setSpacing(5)

        thumb = QWidget()
        thumb.setObjectName("thumbContainer")
        thumb.setFixedHeight(thumb_size)
        thumb_layout = QGridLayout(thumb)
        thumb_layout.setContentsMargins(0, 0, 0, 0)
        thumb_layout.setSpacing(0)
        preview = QLabel()
        preview.setObjectName("preview")
        preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview.setMinimumWidth(120)
        preview.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.preview_label = preview
        if path.suffix.lower() in IMAGE_EXTS:
            pix = cached_preview(path, thumb_size)
            if not pix.isNull():
                preview.setPixmap(pix)
            else:
                preview.setText("Loading thumbnail…")
        else:
            preview.setText(self._type_label(path))
        thumb_layout.addWidget(preview, 0, 0)

        badge = QLabel(path.suffix.upper().lstrip(".") or "FILE")
        badge.setObjectName("formatBadge")
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setFixedWidth(48)
        thumb_layout.addWidget(badge, 0, 0, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        star = QToolButton()
        star.setObjectName("cardFavorite")
        star.setText("")
        star.setIcon(AssetCard._icon("star", "#ffbf3f" if is_favorite else "#8c9aaa", 16))
        star.setToolTip("Remove from favorites" if is_favorite else "Add to favorites")
        star.clicked.connect(lambda: self.favorite_toggled.emit(str(self.path)))
        thumb_layout.addWidget(star, 0, 0, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)

        try:
            if path.suffix.lower() in IMAGE_EXTS:
                reader = QImageReader(str(path))
                image_size = reader.size()
                detail = QLabel(f"{image_size.width()} × {image_size.height()}" if image_size.isValid() else "")
            else:
                detail = QLabel("")
        except OSError:
            detail = QLabel("")
        detail.setObjectName("resolutionBadge")
        thumb_layout.addWidget(detail, 0, 0, Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight)

        name = QLabel(path.name)
        name.setObjectName("assetName")
        name.setWordWrap(True)
        name.setAlignment(Qt.AlignmentFlag.AlignLeft)
        name.setToolTip(str(path))
        layout.addWidget(thumb)
        layout.addWidget(name)
        self.setToolTip(str(path))
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(lambda pos: self.context_requested.emit(str(self.path), self.mapToGlobal(pos)))

    @staticmethod
    def _icon(name, color, size):
        paths = {
            "star": '<path d="m12 2 3 6.5 7 .8-5.2 4.8 1.5 6.9-6.3-3.5-6.3 3.5 1.5-6.9L2 9.3l7-.8z"/>'
        }
        svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24"><g fill="{color}" stroke="{color}" stroke-width="1.2">{paths[name]}</g></svg>'
        renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()
        return QIcon(pixmap)

    @staticmethod
    def _type_label(path):
        return path.suffix.lower().lstrip(".").upper() or "FILE"

    def set_favorite(self, is_favorite):
        star = self.findChild(QToolButton, "cardFavorite")
        if star:
            star.setIcon(self._icon("star", "#ffbf3f" if is_favorite else "#8c9aaa", 16))
            star.setToolTip("Remove from favorites" if is_favorite else "Add to favorites")

    def set_preview(self, image):
        pix = QPixmap.fromImage(image) if image is not None else QPixmap()
        if not pix.isNull():
            self.preview_label.setPixmap(pix)
            self.preview_label.setText("")

    def mousePressEvent(self, event):
        self.selected.emit(str(self.path))
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
        self.disk_usage = QCheckBox("Show disk usage in sidebar")
        self.disk_usage.setChecked(settings.get("show_disk_usage", False))
        self.hidden.toggled.connect(self._hidden_changed)
        self.disk_usage.toggled.connect(self._disk_usage_changed)
        self.scale = QSpinBox()
        self.scale.setRange(50, 300)
        self.scale.setSingleStep(10)
        self.scale.setSuffix("%")
        self.scale.setValue(round(float(settings.get("ui_scale", 1.0)) * 100))
        self.scale.valueChanged.connect(self._apply_scale_live)
        form.addRow("Interface scale", self.scale)
        form.addRow("", self.hidden)
        form.addRow("", self.disk_usage)
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

    def _hidden_changed(self, checked):
        self.settings["show_hidden"] = checked
        save_settings(self.settings)
        if self.parent():
            self.parent()._settings_changed("show_hidden")

    def _disk_usage_changed(self, checked):
        self.settings["show_disk_usage"] = checked
        save_settings(self.settings)
        if self.parent():
            self.parent()._settings_changed("show_disk_usage")

    def _apply_scale_live(self, value):
        scale = value / 100.0
        app = QApplication.instance()
        if app:
            font = app.font()
            font.setPointSizeF(10 * scale)
            app.setFont(font)
        if self.parent():
            self.parent()._apply_ui_scale(scale)

    def accept(self):
        self.settings["ui_scale"] = self.scale.value() / 100.0
        self.settings["show_hidden"] = self.hidden.isChecked()
        self.settings["show_disk_usage"] = self.disk_usage.isChecked()
        save_settings(self.settings)
        super().accept()


class AssetItWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = load_settings()
        self.current_library = None
        self.current_asset = None
        self.cards = []
        self._scan_thread = None
        self._thumbnail_workers = []
        self._selected_paths = set()
        self._render_generation = 0
        self._render_queue = []
        self._render_cols = 1
        self._render_thumb = 150
        self._render_favorites = set()
        self._card_widgets = {}
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
        logo = QLabel()
        logo.setObjectName("logo")
        self.logo = logo
        logo.setFixedSize(30, 30)
        logo.setPixmap(self._make_icon().pixmap(30, 30))
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
        self.settings_button.setIcon(self._svg_icon("settings", "#b8c7d5", 18))
        self.settings_button.setText("")
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
        library_heading = QHBoxLayout()
        library_heading.addWidget(self._section_label("LIBRARIES"))
        library_heading.addStretch()
        self.library_path_badge = QLabel("")
        self.library_path_badge.setObjectName("pathBadge")
        library_heading.addWidget(self.library_path_badge)
        side.addLayout(library_heading)
        self.library_list = QListWidget()
        self.library_list.setObjectName("libraryList")
        self.library_list.currentRowChanged.connect(self._library_changed)
        self.library_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.library_list.customContextMenuRequested.connect(self._library_context_menu)
        self.library_list.setMaximumHeight(105)
        side.addWidget(self.library_list)
        side.addWidget(self._section_label("CATEGORIES"))
        self.category_list = QListWidget()
        self.category_list.setObjectName("categoryList")
        for label, icon_name in [("All Assets", "grid"), ("3D Models", "cube"), ("Textures & Normals", "image"), ("HDRI Maps", "sun"), ("Scenes & Presets", "folder")]:
            item = QListWidgetItem(self._svg_icon(icon_name, "#19c5f5", 17), label)
            item.setData(Qt.ItemDataRole.UserRole, label)
            self.category_list.addItem(item)
        self.category_list.setCurrentRow(0)
        self.category_list.currentRowChanged.connect(self._category_changed)
        self.category_list.setMaximumHeight(178)
        side.addWidget(self.category_list)
        self.favorites_button = QToolButton()
        self.favorites_button.setIcon(self._svg_icon("star", "#ffbd32", 17))
        self.favorites_button.setText("Favorites Only: OFF")
        self.favorites_button.setCheckable(True)
        self.favorites_button.toggled.connect(self._favorites_filter_changed)
        side.addWidget(self.favorites_button)
        side.addWidget(self._section_label("TAGS"))
        self.tag_presets = QWidget()
        self.tag_presets_layout = QGridLayout(self.tag_presets)
        self.tag_presets_layout.setContentsMargins(0, 0, 0, 0)
        self.tag_presets_layout.setSpacing(4)
        self._build_tag_presets()
        side.addWidget(self.tag_presets)
        self.tags_list = QListWidget()
        self.tags_list.setObjectName("tagsList")
        self.tags_list.setMaximumHeight(150)
        self.tags_list.itemClicked.connect(self._tag_clicked)
        self.tags_list.hide()
        side.addStretch(1)
        self.disk_usage_label = QLabel("")
        self.disk_usage_label.setObjectName("muted")
        side.addWidget(self.disk_usage_label)
        self.disk_usage_bar = QProgressBar()
        self.disk_usage_bar.setRange(0, 100)
        self.disk_usage_bar.setTextVisible(False)
        self.disk_usage_bar.setFixedHeight(5)
        self.disk_usage_bar.setObjectName("diskUsageBar")
        side.addWidget(self.disk_usage_bar)
        self._refresh_sidebar_metadata()
        splitter.addWidget(sidebar)

        browser = QWidget()
        browser_layout = QVBoxLayout(browser)
        browser_layout.setContentsMargins(8, 0, 8, 0)
        browser_layout.setSpacing(8)
        toolbar = QHBoxLayout()
        self.breadcrumb = QLabel("Choose a library")
        self.breadcrumb.setObjectName("muted")
        self.breadcrumb.setMinimumWidth(80)
        toolbar.addWidget(self.breadcrumb)
        self.filter_group = QWidget()
        filter_layout = QHBoxLayout(self.filter_group)
        filter_layout.setContentsMargins(0, 0, 0, 0)
        filter_layout.setSpacing(3)
        self.filter_buttons = []
        for index, (key, tip, icon_name) in enumerate([("All", "All assets", "grid"), ("Models", "3D models: FBX, OBJ, USD, GLTF…", "cube"), ("Textures", "Images and textures", "image"), ("HDRI", "HDRI / environment maps: EXR, HDR", "sun"), ("Projects", "3D application project files", "folder")]):
            button = QToolButton()
            button.setIcon(self._svg_icon(icon_name, "#19c5f5", 17))
            button.setText("")
            button.setToolTip(tip)
            button.setCheckable(True)
            button.setAutoExclusive(True)
            button.setObjectName("filterButton")
            button.clicked.connect(lambda checked=False, i=index: self._set_filter(i))
            filter_layout.addWidget(button)
            self.filter_buttons.append(button)
        self.filter_buttons[0].setChecked(True)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search assets, formats, tags… (Ctrl+F)")
        self.search.setClearButtonEnabled(True)
        self.search.setMinimumWidth(150)
        self.search.setMaximumWidth(380)
        toolbar.addWidget(self.search, 1)
        self.filter_group.hide()
        self.thumb_size = QSlider(Qt.Orientation.Horizontal)
        self.thumb_size.setRange(90, 240)
        self.thumb_size.setSingleStep(10)
        self.thumb_size.setFixedWidth(100)
        self.thumb_size.setToolTip("Thumbnail size")
        self.thumb_size.setValue(int(self.settings.get("thumbnail_size", 150)))
        self.thumb_size.valueChanged.connect(self._thumbnail_size_changed)
        toolbar.addWidget(self.thumb_size)
        self.search.textChanged.connect(self._render_cards)
        refresh = QToolButton()
        refresh.setIcon(self._svg_icon("refresh", "#aab8c5", 17))
        refresh.setText("")
        refresh.setToolTip("Refresh (F5)")
        refresh.clicked.connect(self._scan_current)
        toolbar.addWidget(refresh)
        browser_layout.addLayout(toolbar)
        status_row = QHBoxLayout()
        self.count_label = QLabel("0 Assets Found")
        self.count_label.setObjectName("countLabel")
        status_row.addWidget(self.count_label)
        separator = QLabel("|")
        separator.setObjectName("muted")
        status_row.addWidget(separator)
        filter_caption = QLabel("Filter:")
        filter_caption.setObjectName("muted")
        status_row.addWidget(filter_caption)
        self.active_filter_badge = QLabel("All")
        self.active_filter_badge.setObjectName("filterBadge")
        status_row.addWidget(self.active_filter_badge)
        status_row.addStretch()
        sort_label = QLabel("Sort:")
        sort_label.setObjectName("muted")
        status_row.addWidget(sort_label)
        self.sort_select = QComboBox()
        self.sort_select.addItems(["Name (A-Z)", "Date Added", "File Size", "Resolution"])
        self.sort_select.currentIndexChanged.connect(self._render_cards)
        self.sort_select.setFixedWidth(130)
        status_row.addWidget(self.sort_select)
        browser_layout.addLayout(status_row)
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
        self.info_preview.setMinimumHeight(130)
        self.info_preview.setMaximumHeight(180)
        self.info_preview.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        info_layout.addWidget(self.info_preview)
        self.info_name = QLabel("—")
        self.info_name.setObjectName("infoName")
        self.info_name.setWordWrap(True)
        info_layout.addWidget(self.info_name)
        self.info_type = QLabel("TYPE   —")
        self.info_path = QLabel("PATH   —")
        self.info_path.hide()
        self.info_size = QLabel("SIZE   —")
        self.info_resolution = QLabel("RESOLUTION   —")
        self.info_color_space = QLabel("COLOR SPACE   —")
        self.info_modified = QLabel("DATE MODIFIED   —")
        self.info_format = QLabel("FORMAT   —")
        for label in (self.info_type, self.info_size, self.info_resolution, self.info_color_space, self.info_format, self.info_modified):
            label.setObjectName("infoText")
            label.setWordWrap(True)
            info_layout.addWidget(label)
        path_heading = QLabel("FILE PATH")
        path_heading.setObjectName("sectionLabel")
        info_layout.addWidget(path_heading)
        path_row = QHBoxLayout()
        self.info_path_edit = QLineEdit()
        self.info_path_edit.setReadOnly(True)
        self.info_path_edit.setPlaceholderText("Select an asset")
        copy_path = QToolButton()
        copy_path.setText("Copy")
        copy_path.setToolTip("Copy full path")
        copy_path.clicked.connect(lambda: QApplication.clipboard().setText(self.info_path_edit.text()))
        path_row.addWidget(self.info_path_edit, 1)
        path_row.addWidget(copy_path)
        info_layout.addLayout(path_row)
        tags_heading = QLabel("ASSIGNED TAGS")
        tags_heading.setObjectName("sectionLabel")
        info_layout.addWidget(tags_heading)
        self.info_tags_container = QWidget()
        self.info_tags_layout = QGridLayout(self.info_tags_container)
        self.info_tags_layout.setContentsMargins(0, 0, 0, 0)
        self.info_tags_layout.setSpacing(4)
        info_layout.addWidget(self.info_tags_container)
        tag_row = QHBoxLayout()
        self.tag_input = QLineEdit()
        self.tag_input.setPlaceholderText("Add or create tag…")
        self.tag_input.returnPressed.connect(self._add_tag)
        add_tag = QPushButton("Add")
        add_tag.clicked.connect(self._add_tag)
        tag_row.addWidget(self.tag_input, 1)
        tag_row.addWidget(add_tag)
        info_layout.addLayout(tag_row)
        info_layout.addStretch()
        self.import_button = QPushButton("Import To…")
        self.import_button.setIcon(self._svg_icon("cube", "#ffffff", 17))
        self.import_button.setObjectName("primary")
        self.import_button.clicked.connect(self._import_to)
        info_layout.addWidget(self.import_button)
        self.open_file_button = QPushButton("Explorer")
        self.open_file_button.setEnabled(False)
        self.open_file_button.clicked.connect(self.open_in_explorer)
        info_layout.addWidget(self.open_file_button)
        self.export_button = QPushButton("Export As…")
        self.export_button.clicked.connect(self.export_selected)
        info_layout.addWidget(self.export_button)
        splitter.addWidget(info)
        splitter.setSizes([220, 850, 270])
        self.sidebar_widget = sidebar
        self.info_widget = info
        self.toggle_left = QToolButton()
        self.toggle_left.setIcon(self._svg_icon("grid", "#aab8c5", 17))
        self.toggle_left.setText("")
        self.toggle_left.setToolTip("Show/hide libraries panel")
        self.toggle_left.clicked.connect(lambda: self._toggle_panel(self.sidebar_widget))
        self.toggle_right = QToolButton()
        self.toggle_right.setIcon(self._svg_icon("image", "#aab8c5", 17))
        self.toggle_right.setText("")
        self.toggle_right.setToolTip("Show/hide asset information panel")
        self.toggle_right.clicked.connect(lambda: self._toggle_panel(self.info_widget))
        toolbar.insertWidget(1, self.toggle_left)
        toolbar.insertWidget(2, self.toggle_right)

        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage("Ready")
        self._refresh_sidebar_metadata()
        self._update_disk_usage()

    def _settings_changed(self, key):
        save_settings(self.settings)
        if key == "show_hidden":
            self._scan_current()
        elif key == "show_disk_usage":
            self._update_disk_usage()

    def _apply_ui_scale(self, scale):
        self.settings["ui_scale"] = float(scale)
        save_settings(self.settings)
        import re
        scaled_style = re.sub(r"font-size:\s*([0-9.]+)pt", lambda match: f"font-size: {float(match.group(1)) * scale:.1f}pt", STYLE)
        app = QApplication.instance()
        if app:
            app.setStyleSheet(scaled_style)
        icon_size = max(10, round(18 * scale))
        for widget in self.findChildren(QToolButton):
            widget.setIconSize(QSize(icon_size, icon_size))
        for widget in self.findChildren(QPushButton):
            widget.setIconSize(QSize(icon_size, icon_size))
        if hasattr(self, "logo"):
            self.logo.setPixmap(self._make_icon().pixmap(max(16, round(30 * scale)), max(16, round(30 * scale))))
        # Do not rebuild cards: thumbnails remain cached while the interface scales.

    def _toggle_panel(self, panel):
        panel.setVisible(not panel.isVisible())

    def _category_changed(self, row):
        self._render_cards()

    def _tag_clicked(self, item):
        tag = item.data(Qt.ItemDataRole.UserRole)
        if tag:
            self.search.setText(tag)

    def _refresh_sidebar_metadata(self):
        if not hasattr(self, "tags_list"):
            return
        self.tags_list.clear()
        tag_counts = {}
        for path_tags in self.settings.get("asset_tags", {}).values():
            for tag in path_tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        if hasattr(self, "category_list"):
            counts = [
                len(self.cards),
                sum(p.suffix.lower() in MODEL_EXTS for p in self.cards),
                sum(p.suffix.lower() in IMAGE_EXTS and p.suffix.lower() not in HDRI_EXTS for p in self.cards),
                sum(p.suffix.lower() in HDRI_EXTS for p in self.cards),
                sum(p.suffix.lower() in PROJECT_EXTS for p in self.cards),
            ]
            category_labels = ["All Assets", "3D Models", "Textures & Normals", "HDRI Maps", "Scenes & Presets"]
            for index, (label, count) in enumerate(zip(category_labels, counts)):
                item = self.category_list.item(index)
                if item:
                    item.setText(f"{label}   {count}")
            favorite_count = len(self.settings.get("favorites", []))
            self.favorites_button.setText(("Favorites Only: ON" if self.favorites_button.isChecked() else "Favorites Only: OFF") + f"   ({favorite_count})")
        for tag, count in sorted(tag_counts.items(), key=lambda item: item[0].casefold()):
            item = QListWidgetItem(self._svg_icon("star", "#19c5f5", 12), f"#{tag}   {count}")
            item.setData(Qt.ItemDataRole.UserRole, tag)
            self.tags_list.addItem(item)
        self._update_disk_usage()

    def _update_disk_usage(self):
        if not hasattr(self, "disk_usage_label"):
            return
        enabled = bool(self.settings.get("show_disk_usage", False))
        self.disk_usage_label.setVisible(enabled)
        if hasattr(self, "disk_usage_bar"):
            self.disk_usage_bar.setVisible(enabled)
        if not enabled or not self.current_library:
            return
        try:
            usage = shutil.disk_usage(self.current_library)
            used_pct = int((usage.total - usage.free) * 100 / max(1, usage.total))
            self.disk_usage_label.setText(f"Local Vault   {usage.free / 1024**3:.1f} GB free / {usage.total / 1024**3:.0f} GB")
            if hasattr(self, "disk_usage_bar"):
                self.disk_usage_bar.setValue(used_pct)
                self.disk_usage_bar.setToolTip(f"{used_pct}% used")
        except OSError:
            self.disk_usage_label.setText("Disk usage unavailable")

    def _render_inspector_tags(self, path):
        while self.info_tags_layout.count():
            item = self.info_tags_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        tags = self.settings.get("asset_tags", {}).get(str(path), [])
        for index, tag in enumerate(tags):
            chip = QToolButton()
            chip.setObjectName("assignedTagChip")
            chip.setText("#" + tag + "  ×")
            chip.setToolTip("Click to remove this tag")
            chip.clicked.connect(lambda checked=False, value=tag: self._remove_tag(value))
            self.info_tags_layout.addWidget(chip, index // 2, index % 2)

    def _remove_tag(self, tag):
        if not self.current_asset:
            return
        key = str(self.current_asset)
        tags = self.settings.setdefault("asset_tags", {}).get(key, [])
        self.settings["asset_tags"][key] = [value for value in tags if value.casefold() != tag.casefold()]
        save_settings(self.settings)
        self.select_asset(key)
        self._refresh_sidebar_metadata()

    def _bridge_placeholder(self):
        if not self.current_asset:
            self.status.showMessage("Select an asset first")
            return
        self.status.showMessage("Bridge system is planned; Blender / Cinema 4D plugins are not installed yet.")

    def export_selected(self):
        if not self.current_asset or not self.current_asset.exists():
            return
        destination, _ = QFileDialog.getSaveFileName(self, "Export / Copy Asset As", self.current_asset.name, "All files (*.*)")
        if not destination:
            return
        try:
            shutil.copy2(self.current_asset, destination)
            self.status.showMessage(f"Exported asset to {destination}")
        except OSError as exc:
            QMessageBox.warning(self, "Export failed", str(exc))

    def _add_tag(self):
        if not self.current_asset or not self.tag_input.text().strip():
            return
        tag = self.tag_input.text().strip().lstrip("#")
        tags = self.settings.setdefault("asset_tags", {})
        key = str(self.current_asset)
        existing = tags.setdefault(key, [])
        if tag.casefold() not in [value.casefold() for value in existing]:
            existing.append(tag)
        save_settings(self.settings)
        self.tag_input.clear()
        self.select_asset(key)
        self._refresh_sidebar_metadata()

    def _toggle_selected_favorite(self, checked):
        if not self.current_asset:
            return
        favorites = set(self.settings.get("favorites", []))
        key = str(self.current_asset)
        if checked:
            favorites.add(key)
        else:
            favorites.discard(key)
        self.settings["favorites"] = sorted(favorites)
        save_settings(self.settings)
        self.favorite_asset_button.setText("In Favorites" if checked else "Add to Favorites")
        self.favorite_asset_button.setIcon(self._svg_icon("star", "#ffbf3f" if checked else "#8c9aaa", 16))
        self._render_cards()
        self._refresh_sidebar_metadata()

    def _thumbnail_size_changed(self, value):
        self.settings["thumbnail_size"] = int(value)
        self._render_cards()

    def _set_filter(self, index):
        if 0 <= index < len(self.filter_buttons):
            self.filter_buttons[index].setChecked(True)
            self._render_cards()

    def _build_tag_presets(self):
        while self.tag_presets_layout.count():
            item = self.tag_presets_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for index, tag in enumerate(DEFAULT_TAGS):
            button = QToolButton()
            button.setText("#" + tag)
            button.setObjectName("tagChip")
            button.setToolTip("Apply tag to selected asset")
            button.clicked.connect(lambda checked=False, value=tag: self._apply_tag(value))
            self.tag_presets_layout.addWidget(button, index // 3, index % 3)

    def _apply_tag(self, tag):
        if not self.current_asset:
            self.status.showMessage("Select an asset first to apply a tag")
            return
        tags = self.settings.setdefault("asset_tags", {})
        key = str(self.current_asset)
        existing = tags.setdefault(key, [])
        if tag.casefold() not in [value.casefold() for value in existing]:
            existing.append(tag)
        save_settings(self.settings)
        self.select_asset(key)
        self._refresh_sidebar_metadata()
        self.status.showMessage(f"Applied #{tag}")

    @staticmethod
    def _svg_icon(name, color="#19c5f5", size=18):
        paths = {
            "cube": '<path d="M12 2 21 7v10l-9 5-9-5V7z M3 7l9 5 9-5 M12 12v10"/>',
            "settings": '<circle cx="12" cy="12" r="3"/><path d="M19 13a7 7 0 0 0 0-2l2-1.5-2-3.5-2.3 1a7 7 0 0 0-1.7-1L14.5 3h-5L9 6a7 7 0 0 0-1.7 1L5 6 3 9.5 5 11a7 7 0 0 0 0 2l-2 1.5L5 18l2.3-1a7 7 0 0 0 1.7 1l.5 3h5l.5-3a7 7 0 0 0 1.7-1l2.3 1 2-3.5z"/>',
            "grid": '<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>',
            "image": '<rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><path d="m21 15-5-5L5 21"/>',
            "sun": '<circle cx="12" cy="12" r="4"/><path d="M12 2v2m0 16v2M4.9 4.9l1.4 1.4m11.4 11.4 1.4 1.4M2 12h2m16 0h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
            "folder": '<path d="M3 6h7l2 2h9v11H3z"/><path d="M3 6V4h7l2 2"/>',
            "star": '<path d="m12 2 3 6.5 7 .8-5.2 4.8 1.5 6.9-6.3-3.5-6.3 3.5 1.5-6.9L2 9.3l7-.8z"/>',
            "refresh": '<path d="M20 7v5h-5M4 17v-5h5"/><path d="M5.5 9A7 7 0 0 1 18 6l2 6M4 12l2 6a7 7 0 0 0 12.5-3"/>'
        }
        svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24"><g fill="none" stroke="{color}" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">{paths.get(name, paths["cube"])}</g></svg>'
        renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()
        return QIcon(pixmap)

    @staticmethod
    def _section_label(text):
        label = QLabel(text)
        label.setObjectName("sectionLabel")
        return label

    def _library_context_menu(self, pos):
        item = self.library_list.itemAt(pos)
        if not item:
            return
        path = item.data(Qt.ItemDataRole.UserRole)
        menu = QMenu(self)
        rename_action = menu.addAction("Rename display name…")
        icon_menu = menu.addMenu("Set library icon")
        icon_choices = [("folder", "Default"), ("cube", "Materials"), ("image", "Textures"), ("cube", "Models"), ("sun", "HDRI"), ("star", "Favorites"), ("folder", "Projects")]
        icon_actions = {icon_menu.addAction(self._svg_icon(glyph, "#19c5f5", 16), label): glyph for glyph, label in icon_choices}
        remove_action = menu.addAction("Remove library")
        chosen = menu.exec(self.library_list.mapToGlobal(pos))
        if chosen in icon_actions:
            self.settings.setdefault("library_icons", {})[path] = icon_actions[chosen]
            save_settings(self.settings)
            self.refresh_libraries()
        elif chosen == remove_action:
            self.settings["libraries"] = [p for p in self.settings.get("libraries", []) if p != path]
            save_settings(self.settings)
            self.refresh_libraries()
        elif chosen == rename_action:
            from PySide6.QtWidgets import QInputDialog
            name, ok = QInputDialog.getText(self, "Library display name", "Name:", text=self.settings.get("library_names", {}).get(path, Path(path).name))
            if ok and name.strip():
                self.settings.setdefault("library_names", {})[path] = name.strip()
                save_settings(self.settings)
                self.refresh_libraries()

    def refresh_libraries(self):
        self.library_list.blockSignals(True)
        self.library_list.clear()
        for path in self.settings.get("libraries", []):
            display_name = self.settings.get("library_names", {}).get(path, Path(path).name)
            icon = self.settings.get("library_icons", {}).get(path, "folder")
            item = QListWidgetItem(self._svg_icon(icon, "#19c5f5", 17), display_name)
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
        if hasattr(self, "library_path_badge"):
            self.library_path_badge.setText(self.current_library.name)
            self.library_path_badge.setToolTip(str(self.current_library))
        self._update_disk_usage()
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
        self._refresh_sidebar_metadata()
        self._render_cards()
        if warning:
            self.status.showMessage(f"Scan completed with warning: {warning}")
        else:
            self.status.showMessage(f"Scanned {len(self.cards)} supported files")

    def _render_cards(self, *_):
        # Invalidate any queued card batches so filtering never leaves stale cards behind.
        self._render_generation += 1
        generation = self._render_generation
        while self.grid.count():
            item = self.grid.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        query = self.search.text().casefold().strip()
        mode = next((i for i, button in enumerate(self.filter_buttons) if button.isChecked()), 0)
        category_row = self.category_list.currentRow() if hasattr(self, "category_list") else 0
        category = {1: "models", 2: "textures", 3: "hdri", 4: "projects"}.get(category_row, "all")
        visible = []
        favorites = set(self.settings.get("favorites", []))
        normalized_query = query.lstrip("#")
        tag_map = self.settings.get("asset_tags", {})
        for path in self.cards:
            ext = path.suffix.lower()
            if self.favorites_button.isChecked() and str(path) not in favorites:
                continue
            path_tags = tag_map.get(str(path), [])
            searchable_tags = " ".join(path_tags).casefold()
            if query and query not in path.name.casefold() and query not in str(path.parent).casefold() and normalized_query not in searchable_tags:
                continue
            if category == "models" and ext not in MODEL_EXTS:
                continue
            if category == "textures" and (ext not in IMAGE_EXTS or ext in HDRI_EXTS):
                continue
            if category == "hdri" and ext not in HDRI_EXTS:
                continue
            if category == "projects" and ext not in PROJECT_EXTS:
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

        sort_mode = self.sort_select.currentIndex() if hasattr(self, "sort_select") else 0
        if sort_mode == 1:
            visible.sort(key=lambda p: p.stat().st_mtime if p.exists() else 0, reverse=True)
        elif sort_mode == 2:
            visible.sort(key=lambda p: p.stat().st_size if p.exists() else 0, reverse=True)
        elif sort_mode == 3:
            visible.sort(key=self._resolution_sort_key, reverse=True)
        else:
            visible.sort(key=lambda p: p.name.casefold())

        self.count_label.setText(f"{len(visible)} Assets Found")
        if hasattr(self, "active_filter_badge"):
            selected_filter = query or (self.category_list.currentItem().text() if self.category_list.currentItem() else "All")
            self.active_filter_badge.setText(selected_filter[:24])
        if not visible:
            self._show_empty("No matching assets found" if self.cards else "This library contains no supported assets")
            return

        self._render_queue = visible
        self._card_widgets = {}
        self._render_index = 0
        self._render_cols = max(1, self.scroll.viewport().width() // (self.settings.get("thumbnail_size", 150) + 28))
        self._render_thumb = self.settings.get("thumbnail_size", 150)
        self._render_favorites = favorites
        self.status.showMessage(f"Preparing {len(visible)} assets…")
        image_paths = [p for p in visible if p.suffix.lower() in IMAGE_EXTS]
        if image_paths:
            worker = ThumbnailBatchWorker(image_paths, self._render_thumb, self)
            worker.thumbnail_ready.connect(lambda path, image, g=generation: self._thumbnail_ready(path, image, g))
            worker.finished.connect(lambda w=worker: self._thumbnail_worker_finished(w))
            self._thumbnail_workers.append(worker)
            worker.start()
        QTimer.singleShot(0, lambda: self._render_next_batch(generation))

    def _render_next_batch(self, generation):
        if generation != self._render_generation:
            return
        # Small batches keep the window responsive even for libraries with thousands of files.
        batch_size = 18
        end = min(self._render_index + batch_size, len(self._render_queue))
        for index in range(self._render_index, end):
            path = self._render_queue[index]
            card = AssetCard(path, self._render_thumb, str(path) in self._render_favorites)
            card.selected.connect(self.select_asset)
            card.activated.connect(self._open_path)
            card.favorite_toggled.connect(self._toggle_favorite_path)
            card.context_requested.connect(self._asset_context_menu)
            self.grid.addWidget(card, index // self._render_cols, index % self._render_cols)
            self._card_widgets[str(path)] = card
        self._render_index = end
        if end < len(self._render_queue):
            self.status.showMessage(f"Loading thumbnails… {end} / {len(self._render_queue)}")
            QTimer.singleShot(0, lambda: self._render_next_batch(generation))
        else:
            self.status.showMessage(f"Ready — {len(self._render_queue)} assets")

    def _thumbnail_ready(self, path_string, image, generation):
        if generation != self._render_generation:
            return
        card = self._card_widgets.get(path_string)
        if card:
            card.set_preview(image)
            cache_path = thumbnail_cache_path(Path(path_string), self._render_thumb)
            pix = QPixmap.fromImage(image)
            if not pix.isNull():
                QPixmapCache.insert(f"assetit:{cache_path}", pix)

    def _thumbnail_worker_finished(self, worker):
        if worker in self._thumbnail_workers:
            self._thumbnail_workers.remove(worker)
        worker.deleteLater()

    def _favorites_filter_changed(self, checked):
        self.favorites_button.setText("Favorites Only: ON" if checked else "Favorites Only: OFF")
        self._render_cards()

    def _toggle_favorite_path(self, path_string):
        favorites = set(self.settings.get("favorites", []))
        if path_string in favorites:
            favorites.remove(path_string)
        else:
            favorites.add(path_string)
        self.settings["favorites"] = sorted(favorites)
        save_settings(self.settings)
        card = self._card_widgets.get(path_string)
        if card:
            card.set_favorite(path_string in favorites)
        if self.favorites_button.isChecked():
            self._render_cards()
        self._refresh_sidebar_metadata()

    @staticmethod
    def _resolution_sort_key(path):
        if path.suffix.lower() not in IMAGE_EXTS:
            return 0
        try:
            from PySide6.QtGui import QImageReader
            size = QImageReader(str(path)).size()
            return size.width() * size.height() if size.isValid() else 0
        except Exception:
            return 0

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
        if hasattr(self, "info_path_edit"):
            self.info_path_edit.setText(str(path))
        try:
            size = path.stat().st_size
            self.info_size.setText(f"FILE SIZE   {size / 1024:.1f} KB" if size < 1024**2 else f"FILE SIZE   {size / 1024**2:.2f} MB")
        except OSError:
            self.info_size.setText("SIZE   unavailable")
        try:
            self.info_modified.setText("DATE MODIFIED   " + datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d"))
        except OSError:
            self.info_modified.setText("DATE MODIFIED   —")
        self.info_format.setText("FORMAT   " + (path.suffix.upper().lstrip(".") or "Unknown") + " File")
        self.info_resolution.setText("RESOLUTION   —")
        self.info_color_space.setText("COLOR SPACE   —")
        self._render_inspector_tags(path)
        self.info_preview.clear()
        if path.suffix.lower() in IMAGE_EXTS:
            reader = QImageReader(str(path))
            image_size = reader.size()
            if image_size.isValid():
                self.info_resolution.setText(f"RESOLUTION   {image_size.width()} × {image_size.height()} px")
            try:
                from PIL import Image
                with Image.open(path) as image_meta:
                    profile = image_meta.info.get("icc_profile")
                    self.info_color_space.setText("COLOR SPACE   Embedded ICC profile" if profile else "COLOR SPACE   Not specified")
            except Exception:
                self.info_color_space.setText("COLOR SPACE   Unknown")
            pix = cached_preview(path, 240)
            if not pix.isNull():
                self.info_preview.setPixmap(pix)
            else:
                self.info_preview.setText("Preview unavailable")
        else:
            self.info_preview.setText(path.suffix.upper() + "\n\nPreview not available yet")
        self.open_file_button.setEnabled(True)

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

    def open_in_explorer(self):
        if not self.current_asset or not self.current_asset.exists():
            return
        if os.name == "nt":
            import subprocess
            subprocess.Popen(["explorer.exe", "/select,", str(self.current_asset)])
        else:
            self.open_containing_folder()

    def _import_to(self):
        if not self.current_asset or not self.current_asset.exists():
            self.status.showMessage("Select an asset first")
            return
        dialog = QDialog(self)
        dialog.setWindowTitle("Import asset to")
        dialog.setMinimumWidth(360)
        layout = QVBoxLayout(dialog)
        prompt = QLabel("Choose a target application for:\n" + self.current_asset.name)
        prompt.setWordWrap(True)
        layout.addWidget(prompt)
        app_choice = QComboBox()
        app_choice.addItems(["Active bridge (if available)", "Blender", "Autodesk Maya", "Cinema 4D"])
        layout.addWidget(app_choice)
        note = QLabel("Bridge plugins are not installed yet. This selection prepares the import workflow.")
        note.setObjectName("muted")
        note.setWordWrap(True)
        layout.addWidget(note)
        buttons = QHBoxLayout()
        buttons.addStretch()
        cancel = QPushButton("Cancel")
        go = QPushButton("Continue")
        go.setObjectName("primary")
        cancel.clicked.connect(dialog.reject)
        go.clicked.connect(dialog.accept)
        buttons.addWidget(cancel)
        buttons.addWidget(go)
        layout.addLayout(buttons)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.status.showMessage("Import target selected: " + app_choice.currentText() + " — bridge integration is not installed yet")

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
QMainWindow, QDialog, QWidget { background: #121316; color: #d8dbe4; font-family: "Segoe UI"; font-size: 9pt; }
QMenuBar { background: #1a1b22; color: #a7adbc; border-bottom: 1px solid #2c2f3b; }
QMenuBar::item { padding: 5px 10px; background: transparent; }
QMenuBar::item:selected, QMenu::item:selected { background: #2a2d39; color: #00d2ff; }
QMenu { background: #1a1b22; border: 1px solid #2c2f3b; }
QMenu::item { padding: 6px 24px; }
QLineEdit, QComboBox { background: #121316; border: 1px solid #2c2f3b; border-radius: 5px; padding: 6px 8px; selection-background-color: #0082d9; }
QLineEdit:focus, QComboBox:focus { border: 1px solid #00a3ff; }
QComboBox QAbstractItemView { background: #1a1b22; selection-background-color: #323645; }
QPushButton, QToolButton { background: #20222b; border: 1px solid #2c2f3b; border-radius: 5px; padding: 6px 9px; }
QPushButton:hover, QToolButton:hover { background: #2a2d39; border-color: #00a3ff; color: #eafaff; }
QToolButton#filterButton { min-width: 27px; min-height: 25px; padding: 4px 7px; font-size: 11pt; }
QToolButton#filterButton:checked { background: #323645; border: 1px solid #00a3ff; color: #00d2ff; }
QPushButton#primary { background: #0082d9; border: 1px solid #0082d9; color: #ffffff; font-weight: 600; }
QPushButton#primary:hover { background: #00a3ff; }
QFrame#sidebar, QFrame#infoPanel { background: #1a1b22; border: none; border-radius: 0; }
QListWidget { background: transparent; border: none; outline: none; }
QListWidget::item { padding: 7px 7px; border-radius: 5px; color: #c4c9d5; }
QListWidget::item:selected { background: #323645; color: #00d2ff; }
QListWidget#categoryList::item { padding: 7px 5px; }
QListWidget#tagsList::item { padding: 4px 5px; color: #00c3ff; }
QLabel#brand { color: #00d2ff; font-size: 16pt; font-weight: 700; }
QLabel#logo { color: #00d2ff; font-size: 20pt; font-weight: bold; }
QLabel#muted, QLabel#sectionLabel { color: #788195; }
QLabel#countLabel { color: #e1e5ed; font-weight: 600; }
QLabel#filterBadge { color: #d5d9e3; background: #2c2f3b; border-radius: 4px; padding: 3px 8px; font-family: Consolas, monospace; }
QProgressBar#diskUsageBar { background: #2c2f3b; border: 0; border-radius: 2px; }
QProgressBar#diskUsageBar::chunk { background: #00a3ff; border-radius: 2px; }
QLabel#pathBadge { color: #00c3ff; background: #101b28; border: 1px solid #16425b; border-radius: 4px; padding: 3px 6px; font-family: Consolas, monospace; font-size: 8pt; }
QLabel#sectionLabel { font-size: 8pt; font-weight: 600; letter-spacing: 1px; padding: 5px 0; }
QLabel#preview { background: #1a1b22; border: 1px solid #2c2f3b; border-radius: 3px; color: #00d2ff; font-size: 11pt; }
QLabel#formatBadge { background: rgba(26,27,34,230); color: #00d2ff; border: 1px solid #2c2f3b; border-radius: 4px; padding: 2px 5px; font-size: 7pt; font-weight: bold; margin: 5px; }
QLabel#resolutionBadge { background: rgba(26,27,34,220); color: #c1c8d6; border-radius: 3px; padding: 2px 4px; font-size: 7pt; margin: 5px; }
QWidget#thumbContainer { background: #1a1b22; border: 1px solid #2c2f3b; border-radius: 3px; }
QToolButton#cardFavorite { background: rgba(26,27,34,220); border: 1px solid #2c2f3b; border-radius: 9px; padding: 3px; margin: 4px; }
QToolButton#tagChip { background: #121316; color: #00c3ff; border: 1px solid #2c2f3b; border-radius: 10px; padding: 3px 6px; font-size: 8pt; }
QToolButton#tagChip:hover { background: #20222b; border-color: #00a3ff; }
QToolButton#assignedTagChip { background: #121316; color: #00c3ff; border: 1px solid #2c2f3b; border-radius: 4px; padding: 4px 6px; font-size: 8pt; }
QToolButton#assignedTagChip:hover { color: #ff7d90; border-color: #b44b63; }
QFrame#assetCard { background: #20222b; border: 1px solid #2c2f3b; border-radius: 7px; }
QFrame#assetCard:hover { background: #2a2d39; border: 1px solid #00a3ff; }
QLabel#assetName { color: #e1e5ed; font-size: 9pt; }
QLabel#infoPreview { background: #1a1b22; border: 1px solid #2c2f3b; border-radius: 6px; color: #8e9aa5; }
QLabel#infoName { color: #f0f3f8; font-weight: 600; padding-top: 7px; }
QLabel#infoText { color: #8993a7; font-size: 9pt; padding: 3px 0; }
QPushButton:checked { background: #323645; border-color: #00a3ff; color: #00d2ff; }
QLabel#emptyState { color: #788195; font-size: 12pt; padding: 40px; }
QCheckBox { spacing: 8px; }
QCheckBox::indicator { width: 14px; height: 14px; }
QCheckBox::indicator:checked { background: #00a3ff; border: 1px solid #00d2ff; }
QStatusBar { background: #121316; color: #788195; border-top: 1px solid #2c2f3b; }
QScrollArea { background: #121316; border: none; }
QSplitter::handle { background: #121316; width: 1px; }
QToolTip { background: #20222b; color: #e8edf2; border: 1px solid #00a3ff; padding: 4px; }
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
