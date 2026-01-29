import secrets

def generate_secure_password() -> str:
    """
    Generates a high-entropy password in the format [hex]-[hex]-[hex].
    Each hex segment represents 3 bytes (6 characters).
    """
    part1 = secrets.token_hex(3)
    part2 = secrets.token_hex(3)
    part3 = secrets.token_hex(3)
    return f"{part1}-{part2}-{part3}"