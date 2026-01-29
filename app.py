import json
from core import encryption
from core import storage_handler
from core import storage_compression
from core import data_handler
from core import password_generator

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
                decrypted = encryption.decrypt_data(raw_blob, self.master_password) # 
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
        encrypted = encryption.encrypt_data(compressed, self.master_password) # 
        storage_handler.write_vault(encrypted)

    def menu(self):
        while True:
            print("\n1. Add | 2. Get | 3. List | 4. Modify | 5. Delete | 6. Generate Pwd | 7. Exit")
            choice = input("Choice: ")
            
            if choice == "1":
                self.add_entry_flow()
            elif choice == "2":
                self.get_entry_flow()
            elif choice == "3":
                for s in self.vault_data: print(f"- {s}")
            elif choice == "4":
                self.modify_entry_flow()
            elif choice == "5":
                self.delete_entry_flow()
            elif choice == "6":
                print(f"Generated: {password_generator.generate_secure_password()}")
            elif choice == "7":
                break

    def add_entry_flow(self):
        service = input("Service: ")
        user = input("Username: ")
        use_gen = input("Generate random password? (y/n): ").lower()
        pwd = password_generator.generate_secure_password() if use_gen == 'y' else input("Password: ")
        self.vault_data[service] = {"user": user, "pass": pwd}
        self.save()

    def get_entry_flow(self):
        service = input("Service: ")
        entry = self.vault_data.get(service)
        if entry: print(f"User: {entry['user']} | Pwd: {entry['pass']}")
        else: print("Not found.")

    def modify_entry_flow(self):
        service = input("Enter service to modify: ")
        if service not in self.vault_data:
            print("Service not found.")
            return

        new_user = None
        new_pass = None

        if input(f"Update username ({self.vault_data[service]['user']})? (y/n): ").lower() == 'y':
            new_user = input("New username: ")

        if input(f"Update password? (y/n): ").lower() == 'y':
            use_gen = input("Generate secure password? (y/n): ").lower()
            new_pass = password_generator.generate_secure_password() if use_gen == 'y' else input("New password: ")

        if data_handler.modify_entry(self.vault_data, service, new_user, new_pass):
            self.save()
            print("Account updated.")

    def delete_entry_flow(self):
        service = input("Enter service to delete: ")
        confirm = input(f"Are you sure you want to delete {service}? (yes/no): ")
        if confirm.lower() == 'yes':
            if data_handler.delete_entry(self.vault_data, service):
                self.save()
                print("Account deleted.")
            else:
                print("Service not found.")