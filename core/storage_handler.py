import os

VAULT_FILE = "vault.pwmanager"

def read_vault() -> bytes:
    if not os.path.exists(VAULT_FILE):
        return b""
    with open(VAULT_FILE, "rb") as f:
        return f.read()

def write_vault(data: bytes):
    temp_file = VAULT_FILE + ".tmp"
    with open(temp_file, "wb") as f:
        f.write(data)
    os.replace(temp_file, VAULT_FILE) # Atomic swap