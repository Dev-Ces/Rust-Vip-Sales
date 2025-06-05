import os
import sys
from werkzeug.security import generate_password_hash
from app import app, db, User
from config import Config

def init_db():
    """Veritabanını başlat ve admin kullanıcısını oluştur"""
    with app.app_context():
        # Veritabanını oluştur
        db.create_all()
        
        # Admin kullanıcısı var mı kontrol et
        admin = User.query.filter_by(username=Config.ADMIN_USERNAME).first()
        
        if admin is None:
            # Admin kullanıcısını oluştur
            admin = User(
                username=Config.ADMIN_USERNAME,
                email=f"{Config.ADMIN_USERNAME}@example.com",
                password_hash=generate_password_hash(Config.ADMIN_PASSWORD),
                is_admin=True
            )
            db.session.add(admin)
            db.session.commit()
            print(f"Admin kullanıcısı oluşturuldu: {Config.ADMIN_USERNAME}")
        else:
            print(f"Admin kullanıcısı zaten mevcut: {Config.ADMIN_USERNAME}")

if __name__ == "__main__":
    init_db()
    print("Veritabanı başlatıldı.")