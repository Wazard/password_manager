def delete_entry(vault_data: dict, service: str) -> bool:
    """
    Removes a service and its associated data entirely.
    Prevents orphaned data by deleting the full key-value pair.
    """
    if service in vault_data:
        del vault_data[service]
        return True
    return False

def modify_entry(vault_data: dict, service: str, new_user: str = None, new_pass: str = None) -> bool:
    """
    Updates the username, password, or both for a specific service.
    Validates service existence before performing partial updates.
    """
    if service not in vault_data:
        return False
    
    if new_user:
        vault_data[service]['user'] = new_user
    
    if new_pass:
        vault_data[service]['pass'] = new_pass
        
    return True