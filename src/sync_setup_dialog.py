"""
src/sync_setup_dialog.py

First-run dialog that collects GitHub username + PAT
and optionally the remote repo URL.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QFormLayout, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class SyncSetupDialog(QDialog):
    def __init__(self, sync_manager, parent=None):
        super().__init__(parent)
        self.sm = sync_manager
        self.setWindowTitle("GitHub Sync Setup")
        self.setMinimumWidth(480)
        self.setModal(True)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Title
        title = QLabel("Connect GhostWiki to GitHub")
        font = QFont()
        font.setBold(True)
        font.setPointSize(13)
        title.setFont(font)
        title.setStyleSheet("color: #2e7d32;")
        layout.addWidget(title)

        info = QLabel(
            "Your notes are already encrypted — GitHub will only\n"
            "ever see unreadable binary data. Even a public repo is fine.\n\n"
            "Create a PAT at: GitHub → Settings → Developer Settings\n"
            "→ Personal Access Tokens → Tokens (classic)\n"
            "Required scope: repo"
        )
        info.setStyleSheet("color: #555; font-size: 12px;")
        info.setWordWrap(True)
        layout.addWidget(info)

        # Form
        form = QFormLayout()
        form.setSpacing(8)

        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("e.g. spike3y")
        form.addRow("GitHub Username:", self.user_input)

        self.pat_input = QLineEdit()
        self.pat_input.setPlaceholderText("ghp_xxxxxxxxxxxx")
        self.pat_input.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("Personal Access Token:", self.pat_input)

        self.remote_input = QLineEdit()
        self.remote_input.setPlaceholderText("https://github.com/youruser/ghostwiki-vault.git")
        form.addRow("Remote Repo URL\n(skip if already set):", self.remote_input)

        layout.addLayout(form)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        skip_btn = QPushButton("Skip for now")
        skip_btn.setStyleSheet("color: #888; border: none; background: transparent;")
        skip_btn.clicked.connect(self.reject)
        btn_row.addWidget(skip_btn)

        save_btn = QPushButton("Save & Connect")
        save_btn.setDefault(True)
        save_btn.setStyleSheet("""
            QPushButton {
                background: #4caf50; color: white;
                border-radius: 4px; padding: 6px 18px;
                font-weight: bold;
            }
            QPushButton:hover { background: #388e3c; }
        """)
        save_btn.clicked.connect(self._save)
        btn_row.addWidget(save_btn)

        layout.addLayout(btn_row)

    def _save(self):
        user = self.user_input.text().strip()
        pat  = self.pat_input.text().strip()
        url  = self.remote_input.text().strip()

        if not user or not pat:
            QMessageBox.warning(self, "Missing Fields",
                                "Please enter both your GitHub username and PAT.")
            return

        # Save to keychain
        self.sm.save_credentials(pat, user)

        # Optionally set remote
        if url:
            try:
                self.sm.set_remote(url)
            except RuntimeError as e:
                QMessageBox.critical(self, "Remote Error", str(e))
                return

        self.accept()