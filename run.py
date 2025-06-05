import os
from app import app, db
from init_db import init_db

if __name__ == '__main__':
    # Veritabanını başlat
    init_db()
    
    # Uygulama port ayarı
    port = int(os.environ.get('PORT', 5000))
    
    # Uygulamayı başlat
    app.run(host='0.0.0.0', port=port)