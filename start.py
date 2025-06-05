import os
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash
from app import app, db, User

def create_admin_user():
    with app.app_context():
        # Veritabanını oluştur
        db.create_all()
        
        # Admin kullanıcısını kontrol et ve oluştur
        admin_username = os.environ.get('ADMIN_USERNAME', 'admin')
        admin_password = os.environ.get('ADMIN_PASSWORD', 'adminpassword')
        
        admin = User.query.filter_by(username=admin_username).first()
        if not admin:
            print(f"Creating admin user: {admin_username}")
            admin = User(username=admin_username, email=f"{admin_username}@rustvip.com", is_admin=True)
            admin.set_password(admin_password)
            db.session.add(admin)
            db.session.commit()
            print("Admin user created successfully!")
        else:
            print("Admin user already exists.")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    print(f"Starting server on port {port}...")
    
    # Admin kullanıcısını oluştur
    create_admin_user()
    
    # Sunucuyu başlat
    app.run(host='0.0.0.0', port=port, debug=False)