import os
from dotenv import load_dotenv

# .env dosyasını yükle
load_dotenv()

class Config:
    # Flask yapılandırması
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'change_this_to_a_random_string'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///rust_vip_sales.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # RCON yapılandırması
    RCON_HOST = os.environ.get('RCON_HOST') or '127.0.0.1'
    RCON_PORT = int(os.environ.get('RCON_PORT') or 28016)
    RCON_PASSWORD = os.environ.get('RCON_PASSWORD') or 'your_rcon_password'
    
    # Admin yapılandırması
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME') or 'admin'
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD') or 'changeme'
    
    # Kripto para adresleri
    BTC_ADDRESS = os.environ.get('BTC_ADDRESS') or '1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa'
    ETH_ADDRESS = os.environ.get('ETH_ADDRESS') or '0x0000000000000000000000000000000000000000'
    LTC_ADDRESS = os.environ.get('LTC_ADDRESS') or 'LTc1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa'
    
    # VIP paket fiyatları (TL)
    STANDARD_VIP_PRICE = 50
    PREMIUM_VIP_PRICE = 100
    ELITE_VIP_PRICE = 200
    
    # VIP paket süreleri (gün)
    STANDARD_VIP_DURATION = 30
    PREMIUM_VIP_DURATION = 60
    ELITE_VIP_DURATION = 90

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///dev_rust_vip_sales.db'

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///test_rust_vip_sales.db'

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False

# Yapılandırma sözlüğü
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}