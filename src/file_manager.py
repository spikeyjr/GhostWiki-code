import os
from cryptography.fernet import Fernet

class FileManager:
    def __init__(self, vault_path: str):
        self.vault_path = vault_path
        self.key_path = "master.key"  # The key lives in your project root
        
        # 1. Load or Generate the Key
        if not os.path.exists(self.key_path):
            self.key = Fernet.generate_key()
            with open(self.key_path, "wb") as key_file:
                key_file.write(self.key)
        else:
            with open(self.key_path, "rb") as key_file:
                self.key = key_file.read()
        
        self.cipher = Fernet(self.key)

        # Ensure vault exists
        if not os.path.exists(vault_path):
            os.makedirs(vault_path)

    def save_note(self, title: str, content: str):
        """Encrypts and saves a note as a .ghost file."""
        # Clean title
        filename = f"{title.replace(' ', '_')}.ghost"
        file_path = os.path.join(self.vault_path, filename)
        
        # Encrypt the content
        encrypted_data = self.cipher.encrypt(content.encode())
        
        with open(file_path, "wb") as f:
            f.write(encrypted_data)
        
        return filename

    def load_note(self, filename: str):
        """Loads and decrypts a .ghost file."""
        if not filename.endswith(".ghost"):
            filename += ".ghost"
            
        file_path = os.path.join(self.vault_path, filename)
        
        if not os.path.exists(file_path):
            return None
            
        with open(file_path, "rb") as f:
            encrypted_data = f.read()
            
        try:
            # Decrypt
            decrypted_content = self.cipher.decrypt(encrypted_data).decode()
            return {
                "title": filename.replace(".ghost", "").replace("_", " "),
                "content": decrypted_content
            }
        except Exception:
            return {"title": "Error", "content": "Could not decrypt file."}
    
    def list_notes(self):
        """Returns a list of all .ghost files in the vault."""
        return sorted([f for f in os.listdir(self.vault_path) if f.endswith(".ghost")])