"""
GhostWiki - PyQt6 GUI with Tree Subpages + GitHub Sync
Install: pip install PyQt6 gitpython keyring
Run:     python main.py
"""

import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QSplitter,
    QVBoxLayout, QToolBar, QTabWidget,
    QPlainTextEdit, QTreeWidget, QTreeWidgetItem,
    QInputDialog, QLabel, QStatusBar,
    QMessageBox, QSizePolicy, QMenu, QProgressDialog
)
from PyQt6.QtGui import (
    QAction, QFont, QKeySequence, QColor, QPalette,
    QSyntaxHighlighter, QTextCharFormat, QTextCursor
)
from PyQt6.QtCore import Qt, QTimer, QRegularExpression, QSize, QThread, pyqtSignal

from src.file_manager import FileManager
from src.sync_manager import SyncManager
from src.sync_setup_dialog import SyncSetupDialog

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
#  Background sync worker (keeps UI responsive)
# ─────────────────────────────────────────────

class SyncWorker(QThread):
    done = pyqtSignal(bool, str)   # success, message

    def __init__(self, sm: SyncManager, operation: str):
        super().__init__()
        self.sm        = sm
        self.operation = operation   # "pull" or "push"

    def run(self):
        if self.operation == "pull":
            ok, msg = self.sm.pull()
        else:
            ok, msg = self.sm.push()
        self.done.emit(ok, msg)


# ─────────────────────────────────────────────
#  Light palette
# ─────────────────────────────────────────────

def build_light_palette():
    p = QPalette()
    white      = QColor("#ffffff")
    light_grey = QColor("#f5f5f5")
    mid_grey   = QColor("#e0e0e0")
    dark_text  = QColor("#2c2c2c")
    green      = QColor("#4caf50")
    p.setColor(QPalette.ColorRole.Window,          light_grey)
    p.setColor(QPalette.ColorRole.WindowText,      dark_text)
    p.setColor(QPalette.ColorRole.Base,            white)
    p.setColor(QPalette.ColorRole.AlternateBase,   light_grey)
    p.setColor(QPalette.ColorRole.Text,            dark_text)
    p.setColor(QPalette.ColorRole.Button,          mid_grey)
    p.setColor(QPalette.ColorRole.ButtonText,      dark_text)
    p.setColor(QPalette.ColorRole.BrightText,      dark_text)
    p.setColor(QPalette.ColorRole.Highlight,       green)
    p.setColor(QPalette.ColorRole.HighlightedText, white)
    p.setColor(QPalette.ColorRole.ToolTipBase,     white)
    p.setColor(QPalette.ColorRole.ToolTipText,     dark_text)
    p.setColor(QPalette.ColorRole.PlaceholderText, QColor("#aaaaaa"))
    return p


# ─────────────────────────────────────────────
#  Global stylesheet
# ─────────────────────────────────────────────

GLOBAL_STYLE = """
QMainWindow, QWidget          { background:#f5f5f5; color:#2c2c2c; }

QMenuBar                      { background:#f0f0f0; color:#2c2c2c;
                                border-bottom:1px solid #d0d0d0;
                                font-size:13px; padding:2px 4px; }
QMenuBar::item                { background:transparent; color:#2c2c2c;
                                padding:4px 10px; border-radius:3px; }
QMenuBar::item:selected       { background:#d0e8d0; color:#1a1a1a; }
QMenu                         { background:#ffffff; color:#2c2c2c;
                                border:1px solid #ccc; }
QMenu::item                   { padding:5px 24px; color:#2c2c2c; }
QMenu::item:selected          { background:#d0e8d0; color:#1a1a1a; }

QToolBar                      { background:#f8f8f8; color:#2c2c2c;
                                border-bottom:1px solid #ddd;
                                spacing:4px; padding:4px 8px; }
QToolBar QToolButton          { background:#ffffff; color:#2c2c2c;
                                border:1px solid #c0c0c0; border-radius:4px;
                                padding:4px 12px; font-size:12px;
                                font-weight:bold; min-width:24px; }
QToolBar QToolButton:hover    { background:#d0e8d0; border-color:#4caf50; color:#1a1a1a; }
QToolBar QToolButton:pressed  { background:#b2dfb2; color:#111; }

QSplitter::handle             { background:#ddd; }

QTreeWidget                   { background:#eef4ee; color:#2c2c2c;
                                border:none; font-size:13px; outline:0; }
QTreeWidget::item             { padding:4px 6px; border-radius:3px; color:#2c2c2c; }
QTreeWidget::item:selected    { background:#4caf50; color:#ffffff; }
QTreeWidget::item:hover:!selected { background:#d0e8d0; color:#1a1a1a; }
QTreeWidget::branch           { background:#eef4ee; }

QTabWidget::pane              { border-top:1px solid #ddd; background:#ffffff; }
QTabBar::tab                  { background:#e8e8e8; color:#2c2c2c;
                                border:1px solid #ccc; border-bottom:none;
                                padding:6px 18px; font-size:12px;
                                margin-right:2px; border-radius:4px 4px 0 0; }
QTabBar::tab:selected         { background:#ffffff; font-weight:bold; color:#2e7d32; }
QTabBar::tab:hover:!selected  { background:#d0e8d0; color:#1a1a1a; }

QStatusBar                    { background:#f0f0f0; color:#555;
                                border-top:1px solid #ddd; font-size:11px; }

QInputDialog QLineEdit, QDialog QLineEdit {
    background:#ffffff; color:#2c2c2c;
    border:1px solid #ccc; border-radius:3px; padding:4px; }
QDialogButtonBox QPushButton, QDialog QPushButton {
    background:#ffffff; color:#2c2c2c;
    border:1px solid #ccc; border-radius:4px; padding:5px 16px; }
QDialogButtonBox QPushButton:hover { background:#d0e8d0; }
"""


# ─────────────────────────────────────────────
#  Markdown highlighter
# ─────────────────────────────────────────────

class MarkdownHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.rules = []

        def rule(pattern, color, bold=False, italic=False):
            fmt = QTextCharFormat()
            fmt.setForeground(QColor(color))
            if bold:   fmt.setFontWeight(700)
            if italic: fmt.setFontItalic(True)
            self.rules.append((QRegularExpression(pattern), fmt))

        rule(r"^#\s.+",        "#1a6e2a", bold=True)
        rule(r"^##\s.+",       "#2a7a3a", bold=True)
        rule(r"^###\s.+",      "#3a8a4a", bold=True)
        rule(r"\*\*[^*]+\*\*", "#222222", bold=True)
        rule(r"_[^_]+_",       "#444444", italic=True)
        rule(r"`[^`]+`",       "#c0392b")
        rule(r"^\s*[-*+]\s",   "#8e44ad")
        rule(r"\[.+?\]\(.+?\)","#2980b9")
        rule(r"^>.*",          "#7f8c8d", italic=True)

    def highlightBlock(self, text):
        for pattern, fmt in self.rules:
            it = pattern.globalMatch(text)
            while it.hasNext():
                m = it.next()
                self.setFormat(m.capturedStart(), m.capturedLength(), fmt)


# ─────────────────────────────────────────────
#  Editor widget
# ─────────────────────────────────────────────

class GhostEditor(QPlainTextEdit):
    def __init__(self):
        super().__init__()
        font = QFont("Monospace", 11)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.setFont(font)
        self.setStyleSheet("""
            QPlainTextEdit {
                background-color: #ffffff; color: #2c2c2c;
                border: none; padding: 16px 24px;
                selection-background-color: #c8e6c9;
                selection-color: #1a1a1a;
            }
        """)
        self.highlighter = MarkdownHighlighter(self.document())


# ─────────────────────────────────────────────
#  Main window
# ─────────────────────────────────────────────

class GhostWikiWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.fm            = FileManager("./vault")
        self.sm            = SyncManager("./vault")
        self.autosave_timers = {}
        self._sync_worker  = None   # keep reference so it isn't GC'd

        self.setWindowTitle("GhostWiki")
        self.resize(1200, 750)
        self._build_ui()
        self._build_menu()
        self._build_toolbar()
        self.refresh_tree()

        # First-run: prompt for credentials if not set
        if not self.sm.has_credentials():
            QTimer.singleShot(300, self._prompt_setup)
        else:
            # Pull on startup in background
            QTimer.singleShot(500, self._pull_on_startup)

    # ── Sync helpers ──────────────────────────

    def _prompt_setup(self):
        dlg = SyncSetupDialog(self.sm, self)
        if dlg.exec():
            self.status.showMessage("GitHub credentials saved. Pulling…")
            self._run_sync("pull", on_done=self._after_startup_pull)
        else:
            self.status.showMessage(
                "GitHub sync skipped. You can set it up via File → GitHub Sync Setup."
            )

    def _pull_on_startup(self):
        self.status.showMessage("Pulling latest from GitHub…")
        self._run_sync("pull", on_done=self._after_startup_pull)

    def _after_startup_pull(self, ok: bool, msg: str):
        if ok:
            self.refresh_tree()
            self.status.showMessage(f"✓ {msg}", 4000)
        else:
            self.status.showMessage(f"⚠ {msg}", 6000)

    def _push_on_quit(self):
        """Blocking push — called from closeEvent after saves are done."""
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
                                f"Could not push to GitHub:\n{msg}\n\n"
                                "Your notes are saved locally.")

    def _run_sync(self, operation: str, on_done=None):
        """Run pull or push in a background thread."""
        worker = SyncWorker(self.sm, operation)
        self._sync_worker = worker   # prevent GC
        if on_done:
            worker.done.connect(on_done)
        worker.done.connect(lambda ok, msg: self.status.showMessage(
            f"{'✓' if ok else '⚠'} {msg}", 5000
        ))
        worker.start()

    def _manual_push(self):
        if not self.sm.has_credentials():
            self._prompt_setup()
            return
        self.save_current(silent=True)
        self.status.showMessage("Pushing to GitHub…")
        self._run_sync("push")

    def _manual_pull(self):
        if not self.sm.has_credentials():
            self._prompt_setup()
            return
        self.status.showMessage("Pulling from GitHub…")
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
        sidebar.setMinimumWidth(160)
        sidebar.setMaximumWidth(300)
        sb_lay = QVBoxLayout(sidebar)
        sb_lay.setContentsMargins(0, 0, 0, 0)
        sb_lay.setSpacing(0)

        idx_label = QLabel("  INDEX")
        idx_label.setFixedHeight(32)
        idx_label.setStyleSheet(
            "background:#4caf50; color:#ffffff; font-weight:bold;"
            "font-size:12px; letter-spacing:1px;"
        )
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
        splitter.setSizes([220, 980])
        lay.addWidget(splitter)

        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage("Ready  —  GhostWiki v0.5")

    # ── Menu ──────────────────────────────────

    def _build_menu(self):
        mb = self.menuBar()

        fm = mb.addMenu("File")
        self._act(fm, "New Page", "Ctrl+N", self.new_page)
        self._act(fm, "Save",     "Ctrl+S", self.save_current)
        fm.addSeparator()
        self._act(fm, "Quit",     "Ctrl+Q", self.close)

        em = mb.addMenu("Edit")
        self._act(em, "Undo",   "Ctrl+Z", lambda: self.current_editor() and self.current_editor().undo())
        self._act(em, "Redo",   "Ctrl+Y", lambda: self.current_editor() and self.current_editor().redo())
        em.addSeparator()
        self._act(em, "Bold",   "Ctrl+B", self.insert_bold)
        self._act(em, "Italic", "Ctrl+I", self.insert_italic)

        # Sync menu
        sm_menu = mb.addMenu("Sync")
        self._act(sm_menu, "Push to GitHub",      None, self._manual_push)
        self._act(sm_menu, "Pull from GitHub",    None, self._manual_pull)
        sm_menu.addSeparator()
        self._act(sm_menu, "GitHub Sync Setup…",  None, lambda: SyncSetupDialog(self.sm, self).exec())
        self._act(sm_menu, "Clear Saved Credentials", None, self._clear_creds)

        hm = mb.addMenu("Help")
        self._act(hm, "About", None, lambda: QMessageBox.information(
            self, "GhostWiki",
            "GhostWiki v0.5\nLocal-first encrypted wiki with GitHub sync.\n\n"
            "Ctrl+N  New page\nCtrl+S  Save\nCtrl+Q  Quit (auto-pushes)\n"
            "Ctrl+B  Bold\nCtrl+I  Italic\n\n"
            "Right-click sidebar to add subpages.\n"
            "Use Sync menu to push/pull manually."
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
        reply = QMessageBox.question(
            self, "Clear Credentials",
            "Remove saved GitHub credentials from keychain?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
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

        btn("B",       "Bold (Ctrl+B)",        self.insert_bold)
        btn("I",       "Italic (Ctrl+I)",      self.insert_italic)
        btn("Code",    "Inline code",          self.insert_code)
        btn("H1",      "Heading 1",            self.insert_h1)
        btn("H2",      "Heading 2",            self.insert_h2)
        btn("• List",  "Bullet list",          self.insert_bullet)
        tb.addSeparator()
        btn("+ New",   "New page (Ctrl+N)",    self.new_page)
        btn("Save",    "Save (Ctrl+S)",        self.save_current)
        tb.addSeparator()
        btn("⬆ Push",  "Push to GitHub",       self._manual_push)
        btn("⬇ Pull",  "Pull from GitHub",     self._manual_pull)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        tb.addWidget(spacer)

        self.sync_label = QLabel("☁ Not synced   ")
        self.sync_label.setStyleSheet("color:#aaa; font-size:11px;")
        tb.addWidget(self.sync_label)

    def _set_sync_label(self, ok: bool, msg: str):
        if ok:
            self.sync_label.setText("☁ Synced   ")
            self.sync_label.setStyleSheet("color:#4caf50; font-size:11px;")
        else:
            self.sync_label.setText("⚠ Sync error   ")
            self.sync_label.setStyleSheet("color:#e53935; font-size:11px;")

    # ── Tree sidebar ──────────────────────────

    def refresh_tree(self):
        expanded = self._get_expanded_paths()
        self.tree.clear()

        files  = self.fm.list_notes()
        root: dict = {}
        for f in sorted(files):
            parts = filename_to_parts(f)
            node  = root
            for part in parts:
                node = node.setdefault(part, {})
            node["__file__"] = f

        def populate(parent_widget, subtree: dict, path_parts: list):
            for key, val in sorted(subtree.items()):
                if key == "__file__":
                    continue
                item = QTreeWidgetItem([key])
                item.setData(0, Qt.ItemDataRole.UserRole, val.get("__file__", ""))
                if not path_parts:
                    font = item.font(0)
                    font.setBold(True)
                    item.setFont(0, font)
                if any(k != "__file__" for k in val):
                    item.setChildIndicatorPolicy(
                        QTreeWidgetItem.ChildIndicatorPolicy.ShowIndicator
                    )
                if isinstance(parent_widget, QTreeWidget):
                    parent_widget.addTopLevelItem(item)
                else:
                    parent_widget.addChild(item)
                populate(item, val, path_parts + [key])

        populate(self.tree, root, [])
        self._restore_expanded(expanded)

    def _get_expanded_paths(self) -> set[str]:
        expanded = set()
        def walk(item):
            if item.isExpanded():
                expanded.add(self._item_path(item))
            for i in range(item.childCount()):
                walk(item.child(i))
        for i in range(self.tree.topLevelItemCount()):
            walk(self.tree.topLevelItem(i))
        return expanded

    def _restore_expanded(self, expanded: set[str]):
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
            parts.append(item.text(0))
            item = item.parent()
        return "/".join(reversed(parts))

    # ── Context menu ──────────────────────────

    def _tree_context_menu(self, pos):
        item   = self.tree.itemAt(pos)
        menu   = QMenu(self)

        if item:
            open_act   = menu.addAction("Open")
            sub_act    = menu.addAction("Add Subpage")
            rename_act = menu.addAction("Rename")
            menu.addSeparator()
            del_act    = menu.addAction("Delete")
        else:
            new_act = menu.addAction("New Top-Level Page")

        action = menu.exec(self.tree.mapToGlobal(pos))
        if not action:
            return

        if item:
            if action == open_act:   self._open_item(item)
            elif action == sub_act:  self._add_subpage(item)
            elif action == rename_act: self._rename_page(item)
            elif action == del_act:  self._delete_item(item)
        else:
            if action == new_act:
                self.new_page()

    def _on_tree_click(self, item: QTreeWidgetItem, _col: int):
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
        note = self.fm.load_note(filename)
        if not note:
            self.status.showMessage(f"Could not load {filename}")
            return
        editor = GhostEditor()
        editor.setPlainText(note.get("content", ""))
        editor.textChanged.connect(lambda: self._schedule_autosave(editor))
        display = filename_to_display(filename)
        idx = self.tabs.addTab(editor, display[:22])
        self.tabs.setTabToolTip(idx, filename)
        self.tabs.setCurrentIndex(idx)
        self.status.showMessage(f"Opened: {self._item_path(item)}")

    def new_page(self):
        name, ok = QInputDialog.getText(self, "New Page", "Page name:")
        if not ok or not name.strip():
            return
        name     = name.strip()
        filename = path_to_filename(name)
        content  = f"# {name}\n\n"
        self.fm.save_note(filename.replace(".ghost", ""), content)
        self.refresh_tree()
        self._open_by_filename(filename, content)

    def _add_subpage(self, parent_item: QTreeWidgetItem):
        name, ok = QInputDialog.getText(
            self, "New Subpage",
            f"Subpage name under '{self._item_path(parent_item)}':"
        )
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
        self._open_by_filename(filename, content)
        self.status.showMessage(f"Created subpage: {full_path}")

    def _rename_page(self, item: QTreeWidgetItem):
        old_name = item.text(0)
        new_name, ok = QInputDialog.getText(
            self, "Rename Page", "New name:", text=old_name
        )
        if not ok or not new_name.strip() or new_name.strip() == old_name:
            return
        new_name    = new_name.strip()
        old_path    = self._item_path(item)
        parent_path = "/".join(old_path.split("/")[:-1])
        new_path    = f"{parent_path}/{new_name}" if parent_path else new_name

        old_stem = path_to_filename(old_path).replace(".ghost", "")
        new_stem = path_to_filename(new_path).replace(".ghost", "")

        for f in self.fm.list_notes():
            fstem = f.replace(".ghost", "")
            if fstem == old_stem or fstem.startswith(old_stem + SEP):
                new_fstem = fstem.replace(old_stem, new_stem, 1)
                src = os.path.join(self.fm.vault_path, f)
                dst = os.path.join(self.fm.vault_path, new_fstem + ".ghost")
                os.rename(src, dst)
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
        msg      = (f"Delete '{path}' and ALL its subpages?\nThis cannot be undone."
                    if item.childCount() > 0 else
                    f"Delete '{path}'?\nThis cannot be undone.")
        reply = QMessageBox.question(
            self, "Delete", msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
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

    def _open_by_filename(self, filename: str, content: str):
        editor = GhostEditor()
        editor.setPlainText(content)
        editor.textChanged.connect(lambda: self._schedule_autosave(editor))
        display = filename_to_display(filename)
        idx = self.tabs.addTab(editor, display[:22])
        self.tabs.setTabToolTip(idx, filename)
        self.tabs.setCurrentIndex(idx)

    def _expand_to_path(self, slash_path: str):
        parts = slash_path.split("/")
        item  = None
        for part in parts:
            found = None
            if item is None:
                for i in range(self.tree.topLevelItemCount()):
                    if self.tree.topLevelItem(i).text(0) == part:
                        found = self.tree.topLevelItem(i)
                        break
            else:
                for i in range(item.childCount()):
                    if item.child(i).text(0) == part:
                        found = item.child(i)
                        break
            if found:
                found.setExpanded(True)
                item = found

    # ── Tabs ──────────────────────────────────

    def close_tab(self, index):
        editor   = self.tabs.widget(index)
        filename = self.tabs.tabToolTip(index)
        if filename and editor:
            self.fm.save_note(filename.replace(".ghost", ""), editor.toPlainText())
        self.tabs.removeTab(index)

    def _on_tab_changed(self, index):
        if index >= 0:
            filename = self.tabs.tabToolTip(index)
            if filename:
                self.status.showMessage(
                    f"Editing: {' / '.join(filename_to_parts(filename))}"
                )

    def current_editor(self):
        w = self.tabs.currentWidget()
        return w if isinstance(w, GhostEditor) else None

    # ── Save ──────────────────────────────────

    def save_current(self, silent=False):
        editor   = self.current_editor()
        idx      = self.tabs.currentIndex()
        if not editor or idx < 0:
            return
        filename = self.tabs.tabToolTip(idx)
        if not filename:
            return
        self.fm.save_note(filename.replace(".ghost", ""), editor.toPlainText())
        if not silent:
            self.status.showMessage(
                f"Saved: {' / '.join(filename_to_parts(filename))}"
            )

    # ── Autosave ──────────────────────────────

    def _schedule_autosave(self, editor: GhostEditor):
        eid = id(editor)
        if eid in self.autosave_timers:
            self.autosave_timers[eid].stop()
        t = QTimer(self)
        t.setSingleShot(True)
        t.timeout.connect(lambda: self._do_autosave(editor))
        t.start(2000)
        self.autosave_timers[eid] = t

    def _do_autosave(self, editor: GhostEditor):
        for i in range(self.tabs.count()):
            if self.tabs.widget(i) is editor:
                filename = self.tabs.tabToolTip(i)
                if filename:
                    self.fm.save_note(filename.replace(".ghost", ""), editor.toPlainText())
                    self.status.showMessage(
                        f"Autosaved: {' / '.join(filename_to_parts(filename))}", 2000
                    )
                return

    # ── Formatting ────────────────────────────

    def _wrap_selection(self, before, after, placeholder):
        editor = self.current_editor()
        if not editor:
            return
        cur = editor.textCursor()
        sel = cur.selectedText()
        if sel:
            cur.insertText(f"{before}{sel}{after}")
        else:
            start = cur.position()
            cur.insertText(f"{before}{placeholder}{after}")
            cur.setPosition(start + len(before))
            cur.setPosition(start + len(before) + len(placeholder),
                            QTextCursor.MoveMode.KeepAnchor)
            editor.setTextCursor(cur)

    def _prefix_line(self, prefix):
        editor = self.current_editor()
        if not editor:
            return
        cur = editor.textCursor()
        cur.movePosition(QTextCursor.MoveOperation.StartOfLine)
        cur.insertText(prefix)
        editor.setTextCursor(cur)

    def insert_bold(self):   self._wrap_selection("**", "**", "bold")
    def insert_italic(self): self._wrap_selection("_",  "_",  "italic")
    def insert_code(self):   self._wrap_selection("`",  "`",  "code")
    def insert_h1(self):     self._prefix_line("# ")
    def insert_h2(self):     self._prefix_line("## ")
    def insert_bullet(self): self._prefix_line("- ")

    # ── Quit (save all + push) ────────────────

    def closeEvent(self, event):
        # 1. Save all open tabs
        for i in range(self.tabs.count()):
            editor   = self.tabs.widget(i)
            filename = self.tabs.tabToolTip(i)
            if editor and filename:
                self.fm.save_note(filename.replace(".ghost", ""), editor.toPlainText())

        # 2. Push to GitHub
        self._push_on_quit()
        event.accept()


# ─────────────────────────────────────────────
#  Entry point
# ─────────────────────────────────────────────

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("GhostWiki")
    app.setStyle("Fusion")
    app.setPalette(build_light_palette())
    app.setStyleSheet(GLOBAL_STYLE)
    window = GhostWikiWindow()
    window.show()
    sys.exit(app.exec())