"""
src/sync_manager.py

Handles GitHub sync for GhostWiki.
- Auto-initialises the vault as a git repo if it isn't one already
- Stores PAT securely in the system keychain (via keyring)
- git pull on startup, git add/commit/push on quit
- Install deps: pip install gitpython keyring
"""

import os
import keyring
import git
from datetime import datetime

KEYRING_SERVICE = "GhostWiki"
KEYRING_USER    = "github_pat"


class SyncManager:
    def __init__(self, vault_path: str):
        self.vault_path = os.path.abspath(vault_path)
        self._pat       = None

        # Ensure vault folder exists
        os.makedirs(self.vault_path, exist_ok=True)

        # Auto-init git repo if the folder isn't one yet
        try:
            self.repo = git.Repo(self.vault_path)
        except git.InvalidGitRepositoryError:
            self.repo = git.Repo.init(self.vault_path)

    # ── Credential management ─────────────────

    def has_credentials(self) -> bool:
        return bool(keyring.get_password(KEYRING_SERVICE, KEYRING_USER))

    def save_credentials(self, pat: str, github_user: str):
        keyring.set_password(KEYRING_SERVICE, KEYRING_USER,  pat)
        keyring.set_password(KEYRING_SERVICE, "github_user", github_user)

    def get_pat(self) -> str:
        if not self._pat:
            self._pat = keyring.get_password(KEYRING_SERVICE, KEYRING_USER) or ""
        return self._pat

    def get_github_user(self) -> str:
        return keyring.get_password(KEYRING_SERVICE, "github_user") or ""

    def clear_credentials(self):
        try:
            keyring.delete_password(KEYRING_SERVICE, KEYRING_USER)
        except Exception:
            pass
        try:
            keyring.delete_password(KEYRING_SERVICE, "github_user")
        except Exception:
            pass
        self._pat = None

    def has_remote(self) -> bool:
        return "origin" in [r.name for r in self.repo.remotes]

    def set_remote(self, url: str):
        """Set or update the origin remote URL (plain https, no PAT embedded)."""
        try:
            if self.has_remote():
                self.repo.remotes.origin.set_url(url)
            else:
                self.repo.create_remote("origin", url)
        except Exception as e:
            raise RuntimeError(f"Could not set remote: {e}")

    # ── Auth URL ──────────────────────────────

    def _auth_url(self) -> str:
        """Inject PAT into remote URL for authentication."""
        pat    = self.get_pat()
        user   = self.get_github_user()
        remote = self.repo.remotes.origin.url

        # Strip any existing embedded credentials
        if "@" in remote:
            remote = "https://" + remote.split("@", 1)[-1]

        return remote.replace("https://", f"https://{user}:{pat}@")

    # ── Git operations ────────────────────────

    def pull(self) -> tuple[bool, str]:
        if not self.has_remote():
            return False, "No remote configured. Add your repo URL in Sync Setup."
        try:
            origin = self.repo.remotes.origin
            origin.set_url(self._auth_url())
            origin.pull()
            return True, "Pulled latest changes from GitHub."
        except git.GitCommandError as e:
            return False, f"Pull failed: {e}"
        except Exception as e:
            return False, f"Pull error: {e}"

    def push(self, commit_message: str = None) -> tuple[bool, str]:
        if not self.has_remote():
            return False, "No remote configured. Add your repo URL in Sync Setup."
        try:
            repo = self.repo

            if not repo.is_dirty(untracked_files=True):
                return True, "Nothing to commit — vault is already up to date."

            repo.git.add(A=True)

            if not commit_message:
                ts = datetime.now().strftime("%Y-%m-%d %H:%M")
                commit_message = f"GhostWiki sync — {ts}"

            # Set git identity if not already configured (avoids commit errors)
            with repo.config_writer() as cfg:
                if not cfg.has_option("user", "email"):
                    cfg.set_value("user", "email", "ghostwiki@local")
                if not cfg.has_option("user", "name"):
                    cfg.set_value("user", "name", "GhostWiki")

            repo.index.commit(commit_message)

            origin = repo.remotes.origin
            origin.set_url(self._auth_url())
            origin.push()

            return True, f"Pushed to GitHub: '{commit_message}'"

        except git.GitCommandError as e:
            return False, f"Push failed: {e}"
        except Exception as e:
            return False, f"Push error: {e}"