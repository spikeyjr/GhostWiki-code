import getpass
from src.crypto_manager import GhostCrypto
from src.file_manager import FileManager

# 1. Setup
vault_path = "./vault"
pwd = getpass.getpass("Enter a Test Password: ")
crypto = GhostCrypto(pwd)
manager = FileManager(vault_path, crypto)

# 2. Save
print("Encrypting 'Secret Plans'...")
manager.save_note("Secret Plans", "This is the payload.", tags=["test"])

# 3. Read Raw (Show it's encrypted)
with open("./vault/secret_plans.gwk", "rb") as f:
    print(f"\nRAW FILE ON DISK (First 50 bytes):\n{f.read(50)}")

# 4. Decrypt
print("\nDecrypting...")
note = manager.load_note("secret_plans.gwk")
print(f"Decrypted Content: {note['content']}")