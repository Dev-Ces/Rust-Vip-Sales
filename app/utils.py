from rcon.source import rcon
from app import db
from app.models import ServerStats
import os
import re

def get_rcon_connection():
    """Get RCON connection settings"""
    return {
        'host': os.getenv('RCON_HOST', 'localhost'),
        'port': int(os.getenv('RCON_PORT', '28016')),
        'passwd': os.getenv('RCON_PASSWORD', '')
    }

def get_player_count():
    """Get current player count from Rust server using RCON"""
    try:
        conn = get_rcon_connection()
        response = rcon('players', **conn)
        
        # Player sayısını çıkar
        # Örnek yanıt: "1 players connected" veya "0 players"
        match = re.search(r'(\d+)\s+players?', response)
        if match:
            count = int(match.group(1))
        else:
            count = 0
            
        # Veritabanını güncelle
        stats = ServerStats()
        stats.player_count = count
        db.session.add(stats)
        db.session.commit()
        
        return count
    except Exception as e:
        print(f"RCON Error: {e}")
        # Hata durumunda son kayıtlı sayıyı döndür
        last_stats = ServerStats.get_current_stats()
        return last_stats.player_count if last_stats else 0

def grant_vip_access(steam_id):
    """Grant VIP permissions to a Steam ID using RCON"""
    try:
        conn = get_rcon_connection()
        
        # VIP grup yetkisi ver
        rcon(f'oxide.usergroup add {steam_id} vip', **conn)
        
        # Renkli isim için oxide.grant komutu (eğer gerekiyorsa)
        rcon(f'oxide.grant user {steam_id} colornick.allow', **conn)
        
        return True
    except Exception as e:
        print(f"RCON Error while granting VIP: {e}")
        return False 