import os
from rcon.source import rcon

def get_rcon_connection():
    """Get a RCON connection to the Rust server"""
    host = os.getenv('RCON_HOST')
    port = int(os.getenv('RCON_PORT', 28016))
    password = os.getenv('RCON_PASSWORD')
    
    if not all([host, port, password]):
        raise ValueError("RCON connection details not properly configured")
    
    return lambda cmd: rcon(cmd, host=host, port=port, passwd=password)

def get_player_count():
    """Get the current player count from the server"""
    try:
        conn = get_rcon_connection()
        response = conn("players")
        # Response format: "Connected players:\nplayername[1234]\nplayername2[5678]"
        lines = response.split('\n')
        # Subtract 1 to exclude the "Connected players:" line
        return max(0, len(lines) - 1)
    except Exception as e:
        print(f"Error getting player count: {e}")
        return 0

def add_vip(steam_id):
    """Add VIP permissions for a player"""
    try:
        conn = get_rcon_connection()
        # Add to oxide/rust VIP group
        conn(f"oxide.usergroup add {steam_id} vip")
        # Set name color (if supported by your server configuration)
        conn(f"oxide.grant user {steam_id} colornick")
        return True
    except Exception as e:
        print(f"Error adding VIP permissions: {e}")
        return False

def remove_vip(steam_id):
    """Remove VIP permissions from a player"""
    try:
        conn = get_rcon_connection()
        # Remove from oxide/rust VIP group
        conn(f"oxide.usergroup remove {steam_id} vip")
        # Remove name color permission
        conn(f"oxide.revoke user {steam_id} colornick")
        return True
    except Exception as e:
        print(f"Error removing VIP permissions: {e}")
        return False

def grant_vip_access(steam_id):
    """Grant VIP permissions to a Steam ID using RCON"""
    try:
        conn = get_rcon_connection()
        
        # VIP grup yetkisi ver
        conn(f'oxide.usergroup add {steam_id} vip')
        
        # Renkli isim için oxide.grant komutu (eğer gerekiyorsa)
        conn(f'oxide.grant user {steam_id} colornick.allow')
        
        return True
    except Exception as e:
        print(f"RCON Error while granting VIP: {e}")
        return False 