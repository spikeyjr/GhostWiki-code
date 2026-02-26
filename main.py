"""
GhostWiki — local-first encrypted wiki
Features: dark mode, pinned pages, weekly+daily todo
Install:  pip install PyQt6 gitpython keyring
Run:      python main.py
"""

import sys, os, json
from datetime import date, timedelta

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QSplitter,
    QVBoxLayout, QHBoxLayout, QToolBar, QTabWidget,
    QTextEdit, QTreeWidget, QTreeWidgetItem,
    QInputDialog, QLabel, QStatusBar, QLineEdit,
    QMessageBox, QSizePolicy, QMenu, QProgressDialog,
    QFrame, QScrollArea, QCheckBox, QPushButton,
    QToolButton,
)
from PyQt6.QtGui import (
    QAction, QFont, QKeySequence, QColor, QPalette,
    QTextCharFormat, QTextCursor, QTextListFormat,
)
from PyQt6.QtCore import Qt, QTimer, QSize, QThread, pyqtSignal

from src.file_manager import FileManager
from src.sync_manager import SyncManager
from src.sync_setup_dialog import SyncSetupDialog

# ─────────────────────────────────────────────
#  Prefs  (dark mode, pinned pages)
# ─────────────────────────────────────────────

PREFS_PATH = os.path.expanduser("~/.ghostwiki_prefs.json")
TODO_PATH  = os.path.expanduser("~/.ghostwiki_todo.json")

def load_prefs() -> dict:
    try:
        with open(PREFS_PATH) as f:
            return json.load(f)
    except Exception:
        return {"dark": False, "pinned": []}

def save_prefs(p: dict):
    try:
        with open(PREFS_PATH, "w") as f:
            json.dump(p, f, indent=2)
    except Exception:
        pass

def load_todo() -> dict:
    try:
        with open(TODO_PATH) as f:
            return json.load(f)
    except Exception:
        return {"weekly": [], "daily": {}}

def save_todo(t: dict):
    try:
        with open(TODO_PATH, "w") as f:
            json.dump(t, f, indent=2)
    except Exception:
        pass


# ─────────────────────────────────────────────
#  Path helpers
# ─────────────────────────────────────────────

SEP = "__"

def path_to_filename(path: str) -> str:
    return path.replace("/", SEP).replace(" ", "_") + ".ghost"

def filename_to_parts(filename: str) -> list[str]:
    stem = filename.replace(".ghost", "")
    return [p.replace("_", " ") for p in stem.split(SEP)]

def filename_to_display(filename: str) -> str:
    return filename_to_parts(filename)[-1]


# ─────────────────────────────────────────────
#  Palettes & stylesheets
# ─────────────────────────────────────────────

def build_palette(dark: bool) -> QPalette:
    p = QPalette()
    if dark:
        p.setColor(QPalette.ColorRole.Window,          QColor("#1e1e2e"))
        p.setColor(QPalette.ColorRole.WindowText,      QColor("#cdd6f4"))
        p.setColor(QPalette.ColorRole.Base,            QColor("#181825"))
        p.setColor(QPalette.ColorRole.AlternateBase,   QColor("#1e1e2e"))
        p.setColor(QPalette.ColorRole.Text,            QColor("#cdd6f4"))
        p.setColor(QPalette.ColorRole.Button,          QColor("#313244"))
        p.setColor(QPalette.ColorRole.ButtonText,      QColor("#cdd6f4"))
        p.setColor(QPalette.ColorRole.BrightText,      QColor("#cdd6f4"))
        p.setColor(QPalette.ColorRole.Highlight,       QColor("#a6e3a1"))
        p.setColor(QPalette.ColorRole.HighlightedText, QColor("#1e1e2e"))
        p.setColor(QPalette.ColorRole.ToolTipBase,     QColor("#313244"))
        p.setColor(QPalette.ColorRole.ToolTipText,     QColor("#cdd6f4"))
        p.setColor(QPalette.ColorRole.PlaceholderText, QColor("#6c7086"))
    else:
        p.setColor(QPalette.ColorRole.Window,          QColor("#f5f5f5"))
        p.setColor(QPalette.ColorRole.WindowText,      QColor("#2c2c2c"))
        p.setColor(QPalette.ColorRole.Base,            QColor("#ffffff"))
        p.setColor(QPalette.ColorRole.AlternateBase,   QColor("#f5f5f5"))
        p.setColor(QPalette.ColorRole.Text,            QColor("#2c2c2c"))
        p.setColor(QPalette.ColorRole.Button,          QColor("#e0e0e0"))
        p.setColor(QPalette.ColorRole.ButtonText,      QColor("#2c2c2c"))
        p.setColor(QPalette.ColorRole.BrightText,      QColor("#2c2c2c"))
        p.setColor(QPalette.ColorRole.Highlight,       QColor("#4caf50"))
        p.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
        p.setColor(QPalette.ColorRole.ToolTipBase,     QColor("#ffffff"))
        p.setColor(QPalette.ColorRole.ToolTipText,     QColor("#2c2c2c"))
        p.setColor(QPalette.ColorRole.PlaceholderText, QColor("#aaaaaa"))
    return p


LIGHT_STYLE = """
QMainWindow,QWidget{background:#f5f5f5;color:#2c2c2c}
QMenuBar{background:#f0f0f0;color:#2c2c2c;border-bottom:1px solid #d0d0d0;font-size:13px;padding:2px 4px}
QMenuBar::item{background:transparent;padding:4px 10px;border-radius:3px}
QMenuBar::item:selected{background:#d0e8d0;color:#1a1a1a}
QMenu{background:#fff;color:#2c2c2c;border:1px solid #ccc}
QMenu::item{padding:5px 24px}
QMenu::item:selected{background:#d0e8d0;color:#1a1a1a}
QToolBar{background:#f8f8f8;border-bottom:1px solid #ddd;spacing:4px;padding:4px 8px}
QToolBar QToolButton{background:#fff;color:#2c2c2c;border:1px solid #c0c0c0;border-radius:4px;padding:4px 12px;font-size:12px;font-weight:bold;min-width:24px}
QToolBar QToolButton:hover{background:#d0e8d0;border-color:#4caf50}
QToolBar QToolButton:pressed{background:#b2dfb2}
QSplitter::handle{background:#ddd}
QTreeWidget{background:#eef4ee;color:#2c2c2c;border:none;font-size:13px;outline:0}
QTreeWidget::item{padding:4px 6px;border-radius:3px}
QTreeWidget::item:selected{background:#4caf50;color:#fff}
QTreeWidget::item:hover:!selected{background:#d0e8d0}
QTreeWidget::branch{background:#eef4ee}
QTabWidget::pane{border-top:1px solid #ddd;background:#fff}
QTabBar::tab{background:#e8e8e8;color:#2c2c2c;border:1px solid #ccc;border-bottom:none;padding:6px 18px;font-size:12px;margin-right:2px;border-radius:4px 4px 0 0}
QTabBar::tab:selected{background:#fff;font-weight:bold;color:#2e7d32}
QTabBar::tab:hover:!selected{background:#d0e8d0}
QStatusBar{background:#f0f0f0;color:#555;border-top:1px solid #ddd;font-size:11px}
QLineEdit{background:#fff;color:#2c2c2c;border:1px solid #ccc;border-radius:3px;padding:3px 6px}
QScrollArea,QScrollArea>QWidget>QWidget{background:#fff}
QCheckBox{spacing:6px;font-size:12px}
QCheckBox::indicator{width:14px;height:14px;border:1px solid #aaa;border-radius:3px;background:#fff}
QCheckBox::indicator:checked{background:#4caf50;border-color:#4caf50}
QPushButton{background:#fff;color:#2c2c2c;border:1px solid #ccc;border-radius:4px;padding:4px 12px}
QPushButton:hover{background:#d0e8d0;border-color:#4caf50}
QInputDialog QLineEdit,QDialog QLineEdit{background:#fff;color:#2c2c2c;border:1px solid #ccc;border-radius:3px;padding:4px}
QDialogButtonBox QPushButton,QDialog QPushButton{background:#fff;color:#2c2c2c;border:1px solid #ccc;border-radius:4px;padding:5px 16px}
"""

DARK_STYLE = """
QMainWindow,QWidget{background:#1e1e2e;color:#cdd6f4}
QMenuBar{background:#181825;color:#cdd6f4;border-bottom:1px solid #313244;font-size:13px;padding:2px 4px}
QMenuBar::item{background:transparent;padding:4px 10px;border-radius:3px}
QMenuBar::item:selected{background:#313244;color:#a6e3a1}
QMenu{background:#181825;color:#cdd6f4;border:1px solid #313244}
QMenu::item{padding:5px 24px}
QMenu::item:selected{background:#313244;color:#a6e3a1}
QToolBar{background:#181825;border-bottom:1px solid #313244;spacing:4px;padding:4px 8px}
QToolBar QToolButton{background:#313244;color:#cdd6f4;border:1px solid #45475a;border-radius:4px;padding:4px 12px;font-size:12px;font-weight:bold;min-width:24px}
QToolBar QToolButton:hover{background:#45475a;border-color:#a6e3a1}
QToolBar QToolButton:pressed{background:#585b70}
QSplitter::handle{background:#313244}
QTreeWidget{background:#181825;color:#cdd6f4;border:none;font-size:13px;outline:0}
QTreeWidget::item{padding:4px 6px;border-radius:3px}
QTreeWidget::item:selected{background:#a6e3a1;color:#1e1e2e}
QTreeWidget::item:hover:!selected{background:#313244}
QTreeWidget::branch{background:#181825}
QTabWidget::pane{border-top:1px solid #313244;background:#181825}
QTabBar::tab{background:#1e1e2e;color:#cdd6f4;border:1px solid #313244;border-bottom:none;padding:6px 18px;font-size:12px;margin-right:2px;border-radius:4px 4px 0 0}
QTabBar::tab:selected{background:#181825;font-weight:bold;color:#a6e3a1}
QTabBar::tab:hover:!selected{background:#313244}
QStatusBar{background:#181825;color:#6c7086;border-top:1px solid #313244;font-size:11px}
QLineEdit{background:#313244;color:#cdd6f4;border:1px solid #45475a;border-radius:3px;padding:3px 6px}
QScrollArea,QScrollArea>QWidget>QWidget{background:#181825}
QCheckBox{spacing:6px;font-size:12px;color:#cdd6f4}
QCheckBox::indicator{width:14px;height:14px;border:1px solid #585b70;border-radius:3px;background:#313244}
QCheckBox::indicator:checked{background:#a6e3a1;border-color:#a6e3a1}
QPushButton{background:#313244;color:#cdd6f4;border:1px solid #45475a;border-radius:4px;padding:4px 12px}
QPushButton:hover{background:#45475a;border-color:#a6e3a1}
QInputDialog QLineEdit,QDialog QLineEdit{background:#313244;color:#cdd6f4;border:1px solid #45475a;border-radius:3px;padding:4px}
QDialogButtonBox QPushButton,QDialog QPushButton{background:#313244;color:#cdd6f4;border:1px solid #45475a;border-radius:4px;padding:5px 16px}
"""


# ─────────────────────────────────────────────
#  Sync worker
# ─────────────────────────────────────────────

class SyncWorker(QThread):
    done = pyqtSignal(bool, str)
    def __init__(self, sm, operation):
        super().__init__()
        self.sm = sm
        self.operation = operation
    def run(self):
        ok, msg = (self.sm.pull() if self.operation == "pull" else self.sm.push())
        self.done.emit(ok, msg)


# ─────────────────────────────────────────────
#  Note widget
# ─────────────────────────────────────────────

class NoteWidget(QTextEdit):
    """Full-area rich text editor. Loads/saves via Qt's built-in markdown."""
    def __init__(self, content: str = "", dark: bool = False, parent=None):
        super().__init__(parent)
        self.setFont(QFont("Georgia", 11))
        self.setFrameShape(QFrame.Shape.NoFrame)
        self._apply_style(dark)
        try:
            self.setMarkdown(content)
        except Exception:
            self.setPlainText(content)

    def _apply_style(self, dark: bool):
        ed_bg  = "#181825" if dark else "#ffffff"
        ed_fg  = "#cdd6f4" if dark else "#2c2c2c"
        sel_bg = "#313244" if dark else "#c8e6c9"
        self.setStyleSheet(
            f"QTextEdit{{background:{ed_bg};color:{ed_fg};border:none;"
            f"padding:24px 48px;selection-background-color:{sel_bg};}}"
        )

    def set_dark(self, dark: bool):
        self._apply_style(dark)

    def get_content(self) -> str:
        try:
            return self.toMarkdown().rstrip()
        except Exception:
            return self.toPlainText()


# ─────────────────────────────────────────────
#  Todo tab
# ─────────────────────────────────────────────

class TodoTab(QWidget):
    def __init__(self, dark: bool, parent=None):
        super().__init__(parent)
        self._dark = dark
        self._data = load_todo()
        self._today_key = str(date.today())

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

        self._inner = QWidget()
        self._lay = QVBoxLayout(self._inner)
        self._lay.setContentsMargins(32, 24, 32, 24)
        self._lay.setSpacing(16)
        scroll.setWidget(self._inner)

        self._build()

    def _build(self):
        while self._lay.count():
            w = self._lay.takeAt(0).widget()
            if w:
                w.deleteLater()

        accent = "#a6e3a1" if self._dark else "#4caf50"

        # ── Today ─────────────────────────────
        today_label = QLabel(f"📅  Today — {date.today().strftime('%A, %B %d')}")
        today_label.setStyleSheet(f"font-size:16px;font-weight:bold;color:{accent};")
        self._lay.addWidget(today_label)

        today_items = self._data["daily"].get(self._today_key, [])
        self._daily_checks: list[QCheckBox] = []
        for item in today_items:
            cb = self._make_cb(item["text"], item["done"])
            self._daily_checks.append(cb)
            self._lay.addWidget(cb)

        daily_row = QWidget()
        dl = QHBoxLayout(daily_row)
        dl.setContentsMargins(0, 0, 0, 0)
        dl.setSpacing(6)
        self._daily_input = QLineEdit()
        self._daily_input.setPlaceholderText("Add a task for today…")
        self._daily_input.setFixedHeight(28)
        self._daily_input.returnPressed.connect(self._add_daily)
        dl.addWidget(self._daily_input)
        clear_btn = QPushButton("Clear done")
        clear_btn.setFixedHeight(28)
        clear_btn.clicked.connect(self._clear_daily_done)
        dl.addWidget(clear_btn)
        self._lay.addWidget(daily_row)

        # Divider
        div = QFrame()
        div.setFrameShape(QFrame.Shape.HLine)
        div.setStyleSheet(f"color:{'#313244' if self._dark else '#ddd'};")
        self._lay.addWidget(div)

        # ── Weekly ────────────────────────────
        week_start = date.today() - timedelta(days=date.today().weekday())
        week_end   = week_start + timedelta(days=6)
        week_label = QLabel(
            f"📋  Week of {week_start.strftime('%b %d')} – {week_end.strftime('%b %d')}")
        week_label.setStyleSheet(f"font-size:16px;font-weight:bold;color:{accent};")
        self._lay.addWidget(week_label)

        self._weekly_checks: list[QCheckBox] = []
        for item in self._data["weekly"]:
            cb = self._make_cb(item["text"], item["done"])
            self._weekly_checks.append(cb)
            self._lay.addWidget(cb)

        weekly_row = QWidget()
        wl = QHBoxLayout(weekly_row)
        wl.setContentsMargins(0, 0, 0, 0)
        wl.setSpacing(6)
        self._weekly_input = QLineEdit()
        self._weekly_input.setPlaceholderText("Add a weekly goal…")
        self._weekly_input.setFixedHeight(28)
        self._weekly_input.returnPressed.connect(self._add_weekly)
        wl.addWidget(self._weekly_input)
        reset_btn = QPushButton("Reset week")
        reset_btn.setFixedHeight(28)
        reset_btn.clicked.connect(self._reset_weekly)
        wl.addWidget(reset_btn)
        self._lay.addWidget(weekly_row)

        self._lay.addStretch(1)

    def _make_cb(self, text: str, done: bool) -> QCheckBox:
        cb = QCheckBox(text)
        cb.setChecked(done)
        self._style_cb(cb, done)
        cb.stateChanged.connect(lambda _, c=cb: self._on_check(c))
        return cb

    def _style_cb(self, cb: QCheckBox, done: bool):
        if done:
            cb.setStyleSheet("QCheckBox{color:#888;text-decoration:line-through;}")
        else:
            fg = "#cdd6f4" if self._dark else "#2c2c2c"
            cb.setStyleSheet(f"QCheckBox{{color:{fg};}}")

    def _on_check(self, cb: QCheckBox):
        self._style_cb(cb, cb.isChecked())
        self._save()

    def _add_daily(self):
        text = self._daily_input.text().strip()
        if not text:
            return
        self._daily_input.clear()
        self._data["daily"].setdefault(self._today_key, []).append(
            {"text": text, "done": False})
        self._save()
        self._rebuild()

    def _add_weekly(self):
        text = self._weekly_input.text().strip()
        if not text:
            return
        self._weekly_input.clear()
        self._data["weekly"].append({"text": text, "done": False})
        self._save()
        self._rebuild()

    def _clear_daily_done(self):
        today = self._data["daily"].get(self._today_key, [])
        self._data["daily"][self._today_key] = [i for i in today if not i["done"]]
        self._save()
        self._rebuild()

    def _reset_weekly(self):
        reply = QMessageBox.question(self, "Reset Week", "Clear all weekly tasks?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self._data["weekly"] = []
            self._save()
            self._rebuild()

    def _sync_to_data(self):
        today = self._data["daily"].get(self._today_key, [])
        for i, cb in enumerate(self._daily_checks):
            if i < len(today):
                today[i]["done"] = cb.isChecked()
        for i, cb in enumerate(self._weekly_checks):
            if i < len(self._data["weekly"]):
                self._data["weekly"][i]["done"] = cb.isChecked()

    def _save(self):
        self._sync_to_data()
        save_todo(self._data)

    def _rebuild(self):
        self._data = load_todo()
        self._build()

    def set_dark(self, dark: bool):
        self._dark = dark
        self._rebuild()


# ─────────────────────────────────────────────
#  Main window
# ─────────────────────────────────────────────

class GhostWikiWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._prefs          = load_prefs()
        self.fm              = FileManager("./vault")
        self.sm              = SyncManager("./vault")
        self.autosave_timers = {}
        self._sync_worker    = None

        self.setWindowTitle("GhostWiki")
        self.resize(1280, 800)
        self._build_ui()
        self._build_menu()
        self._build_toolbar()
        self._apply_theme()
        self.refresh_tree()
        self._open_todo_tab()

        if not self.sm.has_credentials():
            QTimer.singleShot(300, self._prompt_setup)
        else:
            QTimer.singleShot(500, self._pull_on_startup)

    # ── Theme ─────────────────────────────────

    @property
    def _dark(self) -> bool:
        return self._prefs.get("dark", False)

    def _apply_theme(self):
        app = QApplication.instance()
        app.setPalette(build_palette(self._dark))
        app.setStyleSheet(DARK_STYLE if self._dark else LIGHT_STYLE)
        for i in range(self.tabs.count()):
            w = self.tabs.widget(i)
            if isinstance(w, NoteWidget):
                w.set_dark(self._dark)
            elif isinstance(w, TodoTab):
                w.set_dark(self._dark)
        if hasattr(self, "_theme_btn"):
            self._theme_btn.setText("☀️" if self._dark else "🌙")

    def _toggle_dark(self):
        self._prefs["dark"] = not self._dark
        save_prefs(self._prefs)
        self._apply_theme()

    # ── Sync helpers ──────────────────────────

    def _prompt_setup(self):
        dlg = SyncSetupDialog(self.sm, self)
        if dlg.exec():
            self.status.showMessage("GitHub credentials saved. Pulling…")
            self._run_sync("pull", on_done=self._after_startup_pull)
        else:
            self.status.showMessage("GitHub sync skipped — use Sync menu to set up.")

    def _pull_on_startup(self):
        self.status.showMessage("Pulling latest from GitHub…")
        self._run_sync("pull", on_done=self._after_startup_pull)

    def _after_startup_pull(self, ok, msg):
        if ok:
            self.refresh_tree()
            self.status.showMessage(f"✓ {msg}", 4000)
        else:
            self.status.showMessage(f"⚠ {msg}", 6000)

    def _push_on_quit(self):
        if not self.sm.has_credentials():
            return
        dlg = QProgressDialog("Pushing to GitHub…", None, 0, 0, self)
        dlg.setWindowModality(Qt.WindowModality.WindowModal)
        dlg.setMinimumDuration(0)
        dlg.setValue(0)
        dlg.show()
        QApplication.processEvents()
        ok, msg = self.sm.push()
        dlg.close()
        if not ok:
            QMessageBox.warning(self, "Sync Warning",
                f"Could not push to GitHub:\n{msg}\n\nNotes saved locally.")

    def _run_sync(self, operation, on_done=None):
        worker = SyncWorker(self.sm, operation)
        self._sync_worker = worker
        if on_done:
            worker.done.connect(on_done)
        worker.done.connect(lambda ok, msg: self.status.showMessage(
            f"{'✓' if ok else '⚠'} {msg}", 5000))
        worker.start()

    def _manual_push(self):
        if not self.sm.has_credentials():
            self._prompt_setup(); return
        self.save_current(silent=True)
        self._run_sync("push")

    def _manual_pull(self):
        if not self.sm.has_credentials():
            self._prompt_setup(); return
        self._run_sync("pull", on_done=lambda ok, _: ok and self.refresh_tree())

    # ── Layout ────────────────────────────────

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        lay = QVBoxLayout(central)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)

        sidebar = QWidget()
        sidebar.setMinimumWidth(180)
        sidebar.setMaximumWidth(320)
        sb_lay = QVBoxLayout(sidebar)
        sb_lay.setContentsMargins(0, 0, 0, 0)
        sb_lay.setSpacing(0)

        idx_label = QLabel("  INDEX")
        idx_label.setFixedHeight(32)
        idx_label.setStyleSheet(
            "background:#4caf50;color:#fff;font-weight:bold;font-size:12px;letter-spacing:1px;")
        sb_lay.addWidget(idx_label)

        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._tree_context_menu)
        self.tree.itemClicked.connect(self._on_tree_click)
        self.tree.setExpandsOnDoubleClick(True)
        self.tree.setAnimated(True)
        sb_lay.addWidget(self.tree)

        splitter.addWidget(sidebar)

        editor_area = QWidget()
        ea_lay = QVBoxLayout(editor_area)
        ea_lay.setContentsMargins(0, 0, 0, 0)
        ea_lay.setSpacing(0)

        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self._on_tab_changed)
        ea_lay.addWidget(self.tabs)

        splitter.addWidget(editor_area)
        splitter.setSizes([240, 1040])
        lay.addWidget(splitter)

        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage("Ready  —  GhostWiki")

    # ── Todo tab (permanent) ──────────────────

    def _open_todo_tab(self):
        for i in range(self.tabs.count()):
            if self.tabs.tabToolTip(i) == "__todo__":
                self.tabs.setCurrentIndex(i)
                return
        todo = TodoTab(self._dark)
        idx = self.tabs.addTab(todo, "✅ Tasks")
        self.tabs.setTabToolTip(idx, "__todo__")
        self.tabs.tabBar().moveTab(idx, 0)

    # ── Menu ──────────────────────────────────

    def _build_menu(self):
        mb = self.menuBar()

        fm = mb.addMenu("File")
        self._act(fm, "New Page", "Ctrl+N", self.new_page)
        self._act(fm, "Save",     "Ctrl+S", self.save_current)
        fm.addSeparator()
        self._act(fm, "Quit",     "Ctrl+Q", self.close)

        em = mb.addMenu("Edit")
        self._act(em, "Undo",   "Ctrl+Z",
                  lambda: self._editor() and self._editor().undo())
        self._act(em, "Redo",   "Ctrl+Y",
                  lambda: self._editor() and self._editor().redo())
        em.addSeparator()
        self._act(em, "Bold",   "Ctrl+B", self.insert_bold)
        self._act(em, "Italic", "Ctrl+I", self.insert_italic)

        sm_menu = mb.addMenu("Sync")
        self._act(sm_menu, "Push to GitHub",          None, self._manual_push)
        self._act(sm_menu, "Pull from GitHub",        None, self._manual_pull)
        sm_menu.addSeparator()
        self._act(sm_menu, "GitHub Sync Setup…",      None,
                  lambda: SyncSetupDialog(self.sm, self).exec())
        self._act(sm_menu, "Clear Saved Credentials", None, self._clear_creds)

        vm = mb.addMenu("View")
        self._act(vm, "Toggle Dark Mode", "Ctrl+D", self._toggle_dark)

        hm = mb.addMenu("Help")
        self._act(hm, "About", None, lambda: QMessageBox.information(
            self, "GhostWiki",
            "GhostWiki\nLocal-first encrypted wiki.\n\n"
            "Ctrl+N  New page\nCtrl+S  Save\nCtrl+D  Toggle dark mode\n"
            "Ctrl+B  Bold\nCtrl+I  Italic\n\n"
            "Right-click sidebar to pin, add subpages, rename, or delete.\n"
            "Tasks tab: daily quick-todos + persistent weekly goals."
        ))

    def _act(self, menu, label, shortcut, callback):
        a = QAction(label, self)
        if shortcut:
            a.setShortcut(QKeySequence(shortcut))
        a.triggered.connect(callback)
        menu.addAction(a)
        self.addAction(a)
        return a

    def _clear_creds(self):
        reply = QMessageBox.question(self, "Clear Credentials",
            "Remove saved GitHub credentials?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.sm.clear_credentials()
            self.status.showMessage("Credentials cleared.", 3000)

    # ── Toolbar ───────────────────────────────

    def _build_toolbar(self):
        tb = QToolBar("Formatting")
        tb.setMovable(False)
        tb.setIconSize(QSize(16, 16))
        self.addToolBar(tb)

        def btn(label, tip, fn):
            a = QAction(label, self)
            a.setToolTip(tip)
            a.triggered.connect(fn)
            tb.addAction(a)

        btn("B",      "Bold (Ctrl+B)",     self.insert_bold)
        btn("I",      "Italic (Ctrl+I)",   self.insert_italic)
        btn("H1",     "Heading 1",         self.insert_h1)
        btn("H2",     "Heading 2",         self.insert_h2)
        btn("• List", "Bullet list",       self.insert_bullet)
        tb.addSeparator()
        btn("+ New",  "New page (Ctrl+N)", self.new_page)
        btn("Save",   "Save (Ctrl+S)",     self.save_current)
        btn("Tasks",  "Open tasks tab",    self._open_todo_tab)
        tb.addSeparator()
        btn("⬆ Push", "Push to GitHub",    self._manual_push)
        btn("⬇ Pull", "Pull from GitHub",  self._manual_pull)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        tb.addWidget(spacer)

        self._theme_btn = QToolButton()
        self._theme_btn.setText("☀️" if self._dark else "🌙")
        self._theme_btn.setToolTip("Toggle dark mode (Ctrl+D)")
        self._theme_btn.clicked.connect(self._toggle_dark)
        self._theme_btn.setStyleSheet(
            "QToolButton{font-size:16px;border:none;background:transparent;padding:2px 6px;}")
        tb.addWidget(self._theme_btn)

    # ── Tree sidebar ──────────────────────────

    def refresh_tree(self):
        expanded = self._get_expanded_paths()
        self.tree.clear()
        pinned = set(self._prefs.get("pinned", []))

        files = self.fm.list_notes()
        root: dict = {}
        for f in sorted(files):
            parts = filename_to_parts(f)
            node  = root
            for part in parts:
                node = node.setdefault(part, {})
            node["__file__"] = f

        def populate(parent_widget, subtree: dict, path_parts: list):
            items = sorted(subtree.items())
            if not path_parts:
                items = sorted(items, key=lambda kv: (
                    0 if kv[1].get("__file__", "") in pinned else 1, kv[0]))
            for key, val in items:
                if key == "__file__":
                    continue
                fname    = val.get("__file__", "")
                is_pinned = fname in pinned
                label    = f"📌 {key}" if is_pinned else key
                item     = QTreeWidgetItem([label])
                item.setData(0, Qt.ItemDataRole.UserRole, fname)
                if not path_parts:
                    f2 = item.font(0)
                    f2.setBold(True)
                    item.setFont(0, f2)
                if any(k != "__file__" for k in val):
                    item.setChildIndicatorPolicy(
                        QTreeWidgetItem.ChildIndicatorPolicy.ShowIndicator)
                if isinstance(parent_widget, QTreeWidget):
                    parent_widget.addTopLevelItem(item)
                else:
                    parent_widget.addChild(item)
                populate(item, val, path_parts + [key])

        populate(self.tree, root, [])
        self._restore_expanded(expanded)

    def _get_expanded_paths(self) -> set:
        exp = set()
        def walk(item):
            if item.isExpanded():
                exp.add(self._item_path(item))
            for i in range(item.childCount()):
                walk(item.child(i))
        for i in range(self.tree.topLevelItemCount()):
            walk(self.tree.topLevelItem(i))
        return exp

    def _restore_expanded(self, expanded: set):
        def walk(item):
            if self._item_path(item) in expanded:
                item.setExpanded(True)
            for i in range(item.childCount()):
                walk(item.child(i))
        for i in range(self.tree.topLevelItemCount()):
            walk(self.tree.topLevelItem(i))

    def _item_path(self, item: QTreeWidgetItem) -> str:
        parts = []
        while item:
            parts.append(item.text(0).lstrip("📌 "))
            item = item.parent()
        return "/".join(reversed(parts))

    # ── Context menu ──────────────────────────

    def _tree_context_menu(self, pos):
        item   = self.tree.itemAt(pos)
        menu   = QMenu(self)
        pinned = set(self._prefs.get("pinned", []))

        if item:
            fname      = item.data(0, Qt.ItemDataRole.UserRole)
            open_act   = menu.addAction("Open")
            sub_act    = menu.addAction("Add Subpage")
            pin_act    = menu.addAction("Unpin" if fname in pinned else "📌 Pin to top")
            rename_act = menu.addAction("Rename")
            menu.addSeparator()
            del_act    = menu.addAction("Delete")
        else:
            new_act = menu.addAction("New Top-Level Page")

        action = menu.exec(self.tree.mapToGlobal(pos))
        if not action:
            return

        if item:
            if action == open_act:     self._open_item(item)
            elif action == sub_act:    self._add_subpage(item)
            elif action == pin_act:    self._toggle_pin(item)
            elif action == rename_act: self._rename_page(item)
            elif action == del_act:    self._delete_item(item)
        else:
            if action == new_act:
                self.new_page()

    def _toggle_pin(self, item: QTreeWidgetItem):
        fname  = item.data(0, Qt.ItemDataRole.UserRole)
        pinned = self._prefs.setdefault("pinned", [])
        if fname in pinned:
            pinned.remove(fname)
        else:
            pinned.append(fname)
        save_prefs(self._prefs)
        self.refresh_tree()

    def _on_tree_click(self, item: QTreeWidgetItem, _col):
        if item.data(0, Qt.ItemDataRole.UserRole):
            self._open_item(item)

    # ── Page operations ───────────────────────

    def _open_item(self, item: QTreeWidgetItem):
        filename = item.data(0, Qt.ItemDataRole.UserRole)
        if not filename:
            return
        for i in range(self.tabs.count()):
            if self.tabs.tabToolTip(i) == filename:
                self.tabs.setCurrentIndex(i)
                return
        self.save_current(silent=True)
        try:
            note = self.fm.load_note(filename)
            if not note:
                self.status.showMessage(f"Could not load {filename}")
                return
            nw = NoteWidget(note.get("content", ""), self._dark)
            nw.textChanged.connect(lambda: self._schedule_autosave(nw))
            display = filename_to_display(filename)
            idx = self.tabs.addTab(nw, display[:22])
            self.tabs.setTabToolTip(idx, filename)
            self.tabs.setCurrentIndex(idx)
            self.status.showMessage(f"Opened: {self._item_path(item)}")
        except Exception as e:
            self.status.showMessage(f"Error opening {filename}: {e}")

    def new_page(self):
        name, ok = QInputDialog.getText(self, "New Page", "Page name:")
        if not ok or not name.strip():
            return
        name     = name.strip()
        filename = path_to_filename(name)
        content  = f"# {name}\n\n"
        self.fm.save_note(filename.replace(".ghost", ""), content)
        self.refresh_tree()
        self._open_new(filename, content)

    def _add_subpage(self, parent_item: QTreeWidgetItem):
        name, ok = QInputDialog.getText(
            self, "New Subpage", f"Subpage under '{self._item_path(parent_item)}':")
        if not ok or not name.strip():
            return
        name        = name.strip()
        parent_path = self._item_path(parent_item)
        full_path   = f"{parent_path}/{name}"
        filename    = path_to_filename(full_path)
        content     = f"# {name}\n\n"
        self.fm.save_note(filename.replace(".ghost", ""), content)
        self.refresh_tree()
        self._expand_to_path(parent_path)
        self._open_new(filename, content)
        self.status.showMessage(f"Created: {full_path}")

    def _open_new(self, filename: str, content: str):
        nw = NoteWidget(content, self._dark)
        nw.textChanged.connect(lambda: self._schedule_autosave(nw))
        display = filename_to_display(filename)
        idx = self.tabs.addTab(nw, display[:22])
        self.tabs.setTabToolTip(idx, filename)
        self.tabs.setCurrentIndex(idx)

    def _rename_page(self, item: QTreeWidgetItem):
        old_name = item.text(0).lstrip("📌 ")
        new_name, ok = QInputDialog.getText(self, "Rename", "New name:", text=old_name)
        if not ok or not new_name.strip() or new_name.strip() == old_name:
            return
        new_name    = new_name.strip()
        old_path    = self._item_path(item)
        parent_path = "/".join(old_path.split("/")[:-1])
        new_path    = f"{parent_path}/{new_name}" if parent_path else new_name
        old_stem    = path_to_filename(old_path).replace(".ghost", "")
        new_stem    = path_to_filename(new_path).replace(".ghost", "")

        for f in self.fm.list_notes():
            fstem = f.replace(".ghost", "")
            if fstem == old_stem or fstem.startswith(old_stem + SEP):
                new_fstem = fstem.replace(old_stem, new_stem, 1)
                os.rename(os.path.join(self.fm.vault_path, f),
                          os.path.join(self.fm.vault_path, new_fstem + ".ghost"))
                for i in range(self.tabs.count()):
                    if self.tabs.tabToolTip(i) == f:
                        self.tabs.setTabToolTip(i, new_fstem + ".ghost")
                        if f == old_stem + ".ghost":
                            self.tabs.setTabText(i, new_name[:22])
        self.refresh_tree()
        self.status.showMessage(f"Renamed '{old_name}' → '{new_name}'")

    def _delete_item(self, item: QTreeWidgetItem):
        path     = self._item_path(item)
        filename = item.data(0, Qt.ItemDataRole.UserRole)
        msg = (f"Delete '{path}' and ALL subpages?\nThis cannot be undone."
               if item.childCount() > 0 else f"Delete '{path}'?\nThis cannot be undone.")
        reply = QMessageBox.question(self, "Delete", msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes:
            return
        stem = (filename or path_to_filename(path)).replace(".ghost", "")
        for f in self.fm.list_notes():
            fstem = f.replace(".ghost", "")
            if fstem == stem or fstem.startswith(stem + SEP):
                fpath = os.path.join(self.fm.vault_path, f)
                if os.path.exists(fpath):
                    os.remove(fpath)
                for i in range(self.tabs.count()):
                    if self.tabs.tabToolTip(i) == f:
                        self.tabs.removeTab(i)
                        break
        self.refresh_tree()
        self.status.showMessage(f"Deleted: {path}")

    def _expand_to_path(self, slash_path: str):
        parts = slash_path.split("/")
        item  = None
        for part in parts:
            found = None
            if item is None:
                for i in range(self.tree.topLevelItemCount()):
                    if self.tree.topLevelItem(i).text(0).lstrip("📌 ") == part:
                        found = self.tree.topLevelItem(i); break
            else:
                for i in range(item.childCount()):
                    if item.child(i).text(0).lstrip("📌 ") == part:
                        found = item.child(i); break
            if found:
                found.setExpanded(True)
                item = found

    # ── Tabs ──────────────────────────────────

    def close_tab(self, index):
        if self.tabs.tabToolTip(index) == "__todo__":
            return  # todo tab can't be closed
        widget   = self.tabs.widget(index)
        filename = self.tabs.tabToolTip(index)
        if filename and isinstance(widget, NoteWidget):
            self.fm.save_note(filename.replace(".ghost", ""), widget.get_content())
        self.tabs.removeTab(index)

    def _on_tab_changed(self, index):
        if index < 0:
            return
        try:
            filename = self.tabs.tabToolTip(index)
            if filename and filename.endswith(".ghost"):
                self.status.showMessage(
                    f"Editing: {' / '.join(filename_to_parts(filename))}")
            elif filename == "__todo__":
                self.status.showMessage("Tasks")
        except Exception:
            pass

    def _editor(self) -> "NoteWidget | None":
        w = self.tabs.currentWidget()
        return w if isinstance(w, NoteWidget) else None

    # ── Save ──────────────────────────────────

    def save_current(self, silent=False):
        nw  = self._editor()
        idx = self.tabs.currentIndex()
        if not nw or idx < 0:
            return
        filename = self.tabs.tabToolTip(idx)
        if not filename or not filename.endswith(".ghost"):
            return
        self.fm.save_note(filename.replace(".ghost", ""), nw.get_content())
        if not silent:
            self.status.showMessage(
                f"Saved: {' / '.join(filename_to_parts(filename))}")

    def _schedule_autosave(self, nw: "NoteWidget"):
        eid = id(nw)
        if eid in self.autosave_timers:
            self.autosave_timers[eid].stop()
        t = QTimer(self)
        t.setSingleShot(True)
        t.timeout.connect(lambda: self._do_autosave(nw))
        t.start(2000)
        self.autosave_timers[eid] = t

    def _do_autosave(self, nw: "NoteWidget"):
        for i in range(self.tabs.count()):
            if self.tabs.widget(i) is nw:
                filename = self.tabs.tabToolTip(i)
                if filename and filename.endswith(".ghost"):
                    self.fm.save_note(filename.replace(".ghost", ""), nw.get_content())
                    self.status.showMessage(
                        f"Autosaved: {' / '.join(filename_to_parts(filename))}", 2000)
                return

    # ── Formatting ────────────────────────────

    def insert_bold(self):
        ed = self._editor()
        if not ed: return
        cur = ed.textCursor()
        fmt = QTextCharFormat()
        fmt.setFontWeight(QFont.Weight.Normal if cur.charFormat().fontWeight() >= 700
                          else QFont.Weight.Bold)
        if cur.hasSelection(): cur.mergeCharFormat(fmt)
        else: ed.mergeCurrentCharFormat(fmt)

    def insert_italic(self):
        ed = self._editor()
        if not ed: return
        cur = ed.textCursor()
        fmt = QTextCharFormat()
        fmt.setFontItalic(not cur.charFormat().fontItalic())
        if cur.hasSelection(): cur.mergeCharFormat(fmt)
        else: ed.mergeCurrentCharFormat(fmt)

    def insert_h1(self):
        ed = self._editor()
        if not ed: return
        cur = ed.textCursor()
        cur.select(QTextCursor.SelectionType.BlockUnderCursor)
        text = cur.selectedText().strip()
        cur.removeSelectedText()
        fmt = QTextCharFormat()
        fmt.setFontPointSize(20)
        fmt.setFontWeight(QFont.Weight.Bold)
        fmt.setForeground(QColor("#a6e3a1" if self._dark else "#1a6e2a"))
        if text: cur.insertText(text, fmt)
        ed.mergeCurrentCharFormat(fmt)
        ed.setTextCursor(cur)

    def insert_h2(self):
        ed = self._editor()
        if not ed: return
        cur = ed.textCursor()
        cur.select(QTextCursor.SelectionType.BlockUnderCursor)
        text = cur.selectedText().strip()
        cur.removeSelectedText()
        fmt = QTextCharFormat()
        fmt.setFontPointSize(16)
        fmt.setFontWeight(QFont.Weight.Bold)
        fmt.setForeground(QColor("#94e2d5" if self._dark else "#2a7a3a"))
        if text: cur.insertText(text, fmt)
        ed.mergeCurrentCharFormat(fmt)
        ed.setTextCursor(cur)

    def insert_bullet(self):
        ed = self._editor()
        if not ed: return
        cur = ed.textCursor()
        lf  = QTextListFormat()
        lf.setStyle(QTextListFormat.Style.ListDisc)
        lf.setIndent(1)
        cur.insertList(lf)
        ed.setTextCursor(cur)

    # ── Quit ──────────────────────────────────

    def closeEvent(self, event):
        for i in range(self.tabs.count()):
            w  = self.tabs.widget(i)
            fn = self.tabs.tabToolTip(i)
            if fn and fn.endswith(".ghost") and isinstance(w, NoteWidget):
                self.fm.save_note(fn.replace(".ghost", ""), w.get_content())
            elif isinstance(w, TodoTab):
                w._save()
        self._push_on_quit()
        event.accept()


# ─────────────────────────────────────────────
#  Entry point
# ─────────────────────────────────────────────

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("GhostWiki")
    app.setStyle("Fusion")
    prefs = load_prefs()
    app.setPalette(build_palette(prefs.get("dark", False)))
    app.setStyleSheet(DARK_STYLE if prefs.get("dark", False) else LIGHT_STYLE)
    window = GhostWikiWindow()
    window.show()
    sys.exit(app.exec())