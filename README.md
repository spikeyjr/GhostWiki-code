# 👻 GhostWiki

> **Local-first. GitHub-backed. Zero-trust encrypted notes.**

GhostWiki is a desktop note-taking app built in Python with a clean GUI, designed for people who want their notes private, organised, and synced across devices — without trusting any cloud provider with readable data.

![Status](https://img.shields.io/badge/Status-Active-brightgreen)
![Python](https://img.shields.io/badge/Python-3.11%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![GUI](https://img.shields.io/badge/GUI-PyQt6-informational)

---

## 🔐 How the security works

Every note is encrypted **before it touches the disk** using [Fernet](https://cryptography.io/en/latest/fernet/) (AES-128-CBC + HMAC). The encryption key lives in `master.key` on your machine only — it is never uploaded anywhere. Your GitHub vault repo only ever stores binary noise.

This means:
- You can use a **public GitHub repo** for the vault and your notes are still private
- Even if someone clones your vault repo, they cannot read anything without `master.key`
- `master.key` should be transferred between devices manually (USB stick etc), never via Git or cloud storage

---

## ✨ Features

- **PyQt6 GUI** — clean light-themed desktop app, not a terminal
- **Encrypted notes** — `.ghost` files encrypted with Fernet symmetric encryption
- **Tree sidebar** — unlimited depth page/subpage hierarchy (like CherryTree)
- **Tabs** — multiple notes open at once
- **Markdown editor** — syntax highlighting for headings, bold, italic, code, links
- **Formatting toolbar** — B, I, Code, H1, H2, bullet list buttons
- **Autosave** — saves automatically 2 seconds after you stop typing
- **GitHub sync** — pulls on startup, pushes on quit; credentials stored in system keychain (KWallet/Keychain), never in plaintext
- **Right-click context menu** — add subpage, rename, delete (cascades to children)

---

## 🗂️ Project structure

```
GhostWiki/
├── main.py                  # PyQt6 GUI app entry point
├── src/
│   ├── file_manager.py      # Encrypt/decrypt .ghost files
│   ├── crypto_manager.py    # Fernet key derivation (PBKDF2)
│   ├── sync_manager.py      # Git pull/push + keychain credential storage
│   └── sync_setup_dialog.py # First-run GitHub setup dialog
├── vault/                   # Your encrypted notes (separate git repo)
├── master.key               # 🔑 Encryption key — NEVER commit this
├── requirements.txt
├── .gitignore
└── README.md
```

---

## 📦 Installation

### Prerequisites
- Python 3.11+
- `git` installed and on PATH
- A GitHub account

### 1. Clone the code repo
```bash
git clone https://github.com/spikeyjr/GhostWiki.git
cd GhostWiki
```

### 2. Create and activate a virtual environment
```bash
python -m venv venv
source venv/bin/activate        # Linux/Mac
# venv\Scripts\activate         # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Add your master.key
Copy your `master.key` file into the project root. On a fresh device, transfer it via USB stick or another secure offline method — **do not send it over the internet**.

If this is your very first install and you have no key yet, one will be generated automatically on first run.

### 5. Run
```bash
python main.py
```

On first launch a setup dialog will appear asking for your GitHub username, Personal Access Token, and vault repo URL. The PAT is stored in your system keychain and never written to disk in plaintext.

---

## ☁️ GitHub sync setup

### Vault repo (your encrypted notes)
1. Create a new repo on GitHub (public or private, doesn't matter)
2. On first launch, enter its URL in the sync setup dialog
3. GhostWiki will push your encrypted `.ghost` files there automatically on quit

### PAT permissions
Create a PAT at: **GitHub → Settings → Developer Settings → Personal Access Tokens → Tokens (classic)**

Required scope: `repo`

---

## 💻 Setting up on a new device

```bash
# 1. Clone the code
git clone https://github.com/spikeyjr/GhostWiki.git
cd GhostWiki

# 2. Set up venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Copy master.key onto this device (USB stick etc)
cp /path/to/master.key ./master.key

# 4. Run — enter your PAT and vault repo URL in the setup dialog
python main.py
```

GhostWiki will pull your encrypted notes from GitHub and decrypt them locally using `master.key`.

---

## 📝 Note format

Notes are stored as `.ghost` files — Fernet-encrypted JSON blobs. The subpage hierarchy is encoded in the filename using `__` as a separator:

| Page path | Filename |
|-----------|----------|
| `HackTheBox` | `HackTheBox.ghost` |
| `HackTheBox / Easy` | `HackTheBox__Easy.ghost` |
| `HackTheBox / Easy / Machine1` | `HackTheBox__Easy__Machine1.ghost` |

---

## 🛠️ Tech stack

| Component | Library |
|-----------|---------|
| GUI | PyQt6 |
| Encryption | `cryptography` (Fernet/AES-128) |
| Git sync | `gitpython` |
| Keychain | `keyring` (KWallet on KDE, Keychain on Mac) |

---

*Built by [@spikeyjr](https://github.com/spikeyjr)*