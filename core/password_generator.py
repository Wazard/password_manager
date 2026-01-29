import secrets

def generate_secure_password() -> str:
    """
    Generates a high-entropy password in the format [hex]-[hex]-[hex].
    Each hex segment represents 2 bytes (4 characters).
    """
    part1 = secrets.token_hex(2)
    part2 = secrets.token_hex(2)
    part3 = secrets.token_hex(2)
    return f"{part1}-{part2}-{part3}"