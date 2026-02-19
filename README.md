# GhostWiki
# 👻 GhostWiki

> **Local-First. Cloud-Backed. Zero-Trust Storage.**

GhostWiki is a terminal-based personal knowledge base (PKB) designed for developers who live in the CLI. It combines the organizational power of **VimWiki**, the ubiquity of **GitHub** for storage, and the security of **Fernet symmetric encryption** to keep your thoughts private, even in a public repo.

![Status](https://img.shields.io/badge/Status-In_Development-yellow)
![Python](https://img.shields.io/badge/Python-3.11%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)

---

## 🚀 The Concept

I wanted a notepad that felt like **VimWiki**—fast, keyboard-driven, and structured—but I needed to access it anywhere without exposing my raw notes to the cloud provider.

**GhostWiki** solves this by decoupling the **Interface** from the **Storage**:
1.  **Interface:** A rich TUI (Terminal User Interface) that runs locally.
2.  **Storage:** A Git repository (GitHub/GitLab) that acts as a "dumb drive."
3.  **Security:** Files are encrypted *before* they touch the disk. The cloud only ever sees binary noise.

## 🛠 Tech Stack

* **Core:** Python 3.11+
* **UI Framework:** [Textual](https://textual.textualize.io/) (Modern TUI with mouse support & smooth animations)
* **Cryptography:** `cryptography` library (Fernet/AES-128)
* **Sync Engine:** `GitPython` for automated commit/push/pull operations.

## 🔐 The `.gwk` File Format

Unlike standard Markdown wikis, GhostWiki saves data in a custom `.gwk` format.

* **Structure:** A serialized JSON object containing metadata (tags, creation time) and the content body.
* **Encryption:** The entire JSON blob is encrypted using a user-derived key (PBKDF2HMAC).
* **Obfuscation:** Opening a `.gwk` file in a standard text editor yields a meaningless string of characters.

## ✨ Features (Planned)

### Phase 1: The Core & The Crypt
- [ ] **Custom CryptoManager:** Handles on-the-fly encryption/decryption of notes.
- [ ] **File System:** Virtualized file handling that reads `.gwk` but displays Markdown.
- [ ] **Secure Config:** Local password hashing to unlock the vault.

### Phase 2: The Interface (Vim Mode)
- [ ] **TUI Dashboard:** Split-pane view (File Tree vs. Editor).
- [ ] **Vim Keybindings:** `j/k` navigation, `i` for insert, `:w` to save.
- [ ] **WikiLinking:** Support for `[[WikiLinks]]` to instantly jump between or create new files.

### Phase 3: The Cloud Brain
- [ ] **Auto-Sync:** Pull changes on startup, push changes on exit.
- [ ] **Conflict Resolution:** Basic timestamp checking to prevent overwrites.

## 📦 Installation & Usage

*Coming soon.*

## 🤝 Contributing

This is currently a solo project. If you're interested in secure, terminal-based productivity tools, feel free to watch the repo.

---
*Built with 💀 by [YourUsername]*