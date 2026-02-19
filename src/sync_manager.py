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

        os.makedirs(self.vault_path, exist_ok=True)

        try:
            self.repo = git.Repo(self.vault_path)
        except git.InvalidGitRepositoryError:
            self.repo = git.Repo.init(self.vault_path)

    # ── Credentials ───────────────────────────

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
        for key in (KEYRING_USER, "github_user"):
            try:
                keyring.delete_password(KEYRING_SERVICE, key)
            except Exception:
                pass
        self._pat = None

    def has_remote(self) -> bool:
        return "origin" in [r.name for r in self.repo.remotes]

    def set_remote(self, url: str):
        try:
            if self.has_remote():
                self.repo.remotes.origin.set_url(url)
            else:
                self.repo.create_remote("origin", url)
        except Exception as e:
            raise RuntimeError(f"Could not set remote: {e}")

    # ── Auth URL ──────────────────────────────

    def _auth_url(self) -> str:
        pat    = self.get_pat()
        user   = self.get_github_user()
        remote = self.repo.remotes.origin.url
        if "@" in remote:
            remote = "https://" + remote.split("@", 1)[-1]
        return remote.replace("https://", f"https://{user}:{pat}@")

    # ── Ensure branch is 'main' ───────────────

    def _ensure_main_branch(self):
        """Rename local branch to 'main' if it's called 'master'."""
        try:
            if self.repo.active_branch.name == "master":
                self.repo.git.branch("-m", "master", "main")
        except Exception:
            pass

    def _has_upstream(self) -> bool:
        try:
            return self.repo.active_branch.tracking_branch() is not None
        except Exception:
            return False

    # ── Git operations ────────────────────────

    def pull(self) -> tuple[bool, str]:
        if not self.has_remote():
            return False, "No remote configured. Add your repo URL in Sync Setup."
        try:
            origin = self.repo.remotes.origin
            origin.set_url(self._auth_url())
            # Allow unrelated histories on first pull (remote has init commit)
            self.repo.git.pull("--allow-unrelated-histories", "origin", "main")
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
            self._ensure_main_branch()

            # Stage everything
            repo.git.add(A=True)

            # Nothing staged? nothing to do
            if not repo.is_dirty(index=True, untracked_files=False):
                # Check untracked too
                if not repo.untracked_files:
                    return True, "Nothing to commit — vault is already up to date."

            if not commit_message:
                ts = datetime.now().strftime("%Y-%m-%d %H:%M")
                commit_message = f"GhostWiki sync — {ts}"

            # Set git identity if missing
            with repo.config_writer() as cfg:
                if not cfg.has_option("user", "email"):
                    cfg.set_value("user", "email", "ghostwiki@local")
                if not cfg.has_option("user", "name"):
                    cfg.set_value("user", "name", "GhostWiki")

            repo.index.commit(commit_message)

            origin = repo.remotes.origin
            origin.set_url(self._auth_url())
            branch = repo.active_branch.name

            if self._has_upstream():
                # Normal push
                origin.push(refspec=f"{branch}:{branch}")
            else:
                # First push — force to overwrite GitHub's empty init commit
                repo.git.push("--force", "--set-upstream", "origin", branch)

            return True, f"Pushed to GitHub: '{commit_message}'"

        except git.GitCommandError as e:
            return False, f"Push failed: {e}"
        except Exception as e:
            return False, f"Push error: {e}"