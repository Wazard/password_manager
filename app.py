import json
from core import encryption
from core import storage_handler
from core import storage_compression

class PasswordManagerApp:
    def __init__(self):
        self.master_password = ""
        self.vault_data = {}

    def start(self):
        print("--- Secure Vault CLI ---")
        self.master_password = input("Enter Master Password: ")
        
        raw_blob = storage_handler.read_vault()
        if raw_blob:
            try:
                decrypted = encryption.decrypt_data(raw_blob, self.master_password)
                decompressed = storage_compression.decompress_data(decrypted)
                self.vault_data = json.loads(decompressed)
            except Exception:
                print("Error: Invalid password or corrupted vault.")
                return
        else:
            print("No vault found. Creating new vault.")
            self.vault_data = {}

        self.menu()

    def save(self):
        json_data = json.dumps(self.vault_data)
        compressed = storage_compression.compress_data(json_data)
        encrypted = encryption.encrypt_data(compressed, self.master_password)
        storage_handler.write_vault(encrypted)

    def menu(self):
        while True:
            choice = input("\n1. Add 2. Get 3. List 4. Exit: ")
            if choice == "1":
                service = input("Service: ")
                user = input("Username: ")
                pwd = input("Password: ")
                self.vault_data[service] = {"user": user, "pass": pwd}
                self.save()
            elif choice == "2":
                service = input("Service: ")
                entry = self.vault_data.get(service)
                if entry: print(f"User: {entry['user']} | Pwd: {entry['pass']}")
                else: print("Not found.")
            elif choice == "3":
                for s in self.vault_data: print(f"- {s}")
            elif choice == "4":
                break