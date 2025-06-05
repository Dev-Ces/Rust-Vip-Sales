import os
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import requests
import json
from datetime import datetime, timedelta
import uuid
import re

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'rustvipdevelopmentkey')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///rustvip.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Resim URL'lerini düzeltmek için yardımcı fonksiyon
def fix_image_url(url):
    # Eğer URL zaten tam bir URL ise değiştirme
    if url.startswith('http://') or url.startswith('https://'):
        return url
    
    # Eğer URL /static/ ile başlıyorsa, doğru yolu döndür
    if url.startswith('/static/'):
        return url
    
    # Eğer URL static/ ile başlıyorsa, başına / ekle
    if url.startswith('static/'):
        return '/' + url
    
    # Diğer durumlarda URL'yi olduğu gibi döndür
    return url

# Jinja2 filtresi olarak ekle
app.jinja_env.filters['fix_image_url'] = fix_image_url

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# RCON ayarları
RCON_HOST = os.environ.get('RCON_HOST', 'localhost')
RCON_PORT = int(os.environ.get('RCON_PORT', 28016))
RCON_PASSWORD = os.environ.get('RCON_PASSWORD', 'yourpassword')

# Veritabanı modelleri
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    orders = db.relationship('Order', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(50), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    steam_id = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, completed, cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    payment_method = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    
    def generate_order_number(self):
        self.order_number = f"RVS-{uuid.uuid4().hex[:8].upper()}"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# RCON bağlantısı için fonksiyonlar
from rcon.source import rcon

def check_rcon_connection():
    try:
        response = rcon(f"status", host=RCON_HOST, port=RCON_PORT, passwd=RCON_PASSWORD)
        return True, response
    except Exception as e:
        print(f"RCON error: {e}")
        return False, str(e)

def get_player_count():
    try:
        response = rcon(f"status", host=RCON_HOST, port=RCON_PORT, passwd=RCON_PASSWORD)
        # Gerçek bir Rust sunucusunda oyuncu sayısını çıkarmak için response'u parse etmek gerekir
        # Şimdilik örnek bir değer döndürelim
        return 150
    except Exception as e:
        print(f"RCON error: {e}")
        return 0

# VIP grup ekleme fonksiyonu
def add_vip_to_player(steam_id):
    try:
        # Kullanıcının belirttiği komut formatını kullan
        response = rcon(f"chat user add {steam_id} vip", host=RCON_HOST, port=RCON_PORT, passwd=RCON_PASSWORD)
        return True
    except Exception as e:
        print(f"RCON error: {e}")
        return False

# VIP grup kaldırma fonksiyonu
def remove_vip_from_player(steam_id):
    try:
        # Kullanıcının belirttiği komut formatını kullan
        response = rcon(f"chat user remove {steam_id} vip", host=RCON_HOST, port=RCON_PORT, passwd=RCON_PASSWORD)
        return True
    except Exception as e:
        print(f"RCON error: {e}")
        return False

# RCON komutu çalıştırma fonksiyonu
def execute_rcon_command(command):
    try:
        response = rcon(command, host=RCON_HOST, port=RCON_PORT, passwd=RCON_PASSWORD)
        return True, response
    except Exception as e:
        print(f"RCON error: {e}")
        return False, str(e)

# Ana sayfa
@app.route('/')
def index():
    player_count = get_player_count()
    return render_template('index.html', player_count=player_count)

# Kayıt sayfası
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        user_exists = User.query.filter_by(username=username).first()
        email_exists = User.query.filter_by(email=email).first()
        
        if user_exists:
            flash('Bu kullanıcı adı zaten kullanılıyor.')
            return redirect(url_for('register'))
        
        if email_exists:
            flash('Bu e-posta adresi zaten kullanılıyor.')
            return redirect(url_for('register'))
        
        new_user = User(username=username, email=email)
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Hesabınız başarıyla oluşturuldu! Şimdi giriş yapabilirsiniz.')
        return redirect(url_for('login'))
    
    return render_template('register.html')

# Giriş sayfası
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if not user or not user.check_password(password):
            flash('Geçersiz kullanıcı adı veya şifre')
            return redirect(url_for('login'))
        
        login_user(user)
        return redirect(url_for('index'))
    
    return render_template('login.html')

# Çıkış
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# VIP satın alma sayfası
@app.route('/vip', methods=['GET'])
@login_required
def vip():
    # VIP fiyatını çevre değişkeninden al (varsayılan: 5)
    vip_price = float(os.environ.get('VIP_PRICE', '5'))
    return render_template('vip.html', vip_price=vip_price)

# Sepet sayfası
@app.route('/cart', methods=['GET', 'POST'])
@login_required
def cart():
    # VIP fiyatını çevre değişkeninden al (varsayılan: 5)
    vip_price = float(os.environ.get('VIP_PRICE', '5'))
    
    if request.method == 'POST':
        steam_id = request.form.get('steam_id')
        payment_method = request.form.get('payment_method')
        
        # Basit bir doğrulama
        if not steam_id or len(steam_id) < 5:
            flash('Geçersiz Steam ID')
            return redirect(url_for('cart'))
        
        # Yeni sipariş oluştur
        new_order = Order(
            user_id=current_user.id,
            steam_id=steam_id,
            payment_method=payment_method,
            amount=vip_price  # Yapılandırılabilir fiyat
        )
        new_order.generate_order_number()
        
        db.session.add(new_order)
        db.session.commit()
        
        return redirect(url_for('order_confirmation', order_id=new_order.id))
    
    return render_template('cart.html', vip_price=vip_price)

# Sipariş onay sayfası
@app.route('/order-confirmation/<int:order_id>')
@login_required
def order_confirmation(order_id):
    order = Order.query.get_or_404(order_id)
    
    # Sadece kendi siparişlerini görebilir
    if order.user_id != current_user.id and not current_user.is_admin:
        flash('Bu sayfaya erişim izniniz yok')
        return redirect(url_for('index'))
    
    return render_template('order_confirmation.html', order=order)

# Kullanıcı siparişleri sayfası
@app.route('/my-orders')
@login_required
def my_orders():
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template('my_orders.html', orders=orders)

# Admin paneli - Giriş kontrolü
@app.route('/admin', defaults={'path': ''})
@app.route('/admin/')
@login_required
def admin(path=None):
    if not current_user.is_admin:
        flash('Bu sayfaya erişim izniniz yok')
        return redirect(url_for('index'))
    
    return render_template('admin/index.html')

# Admin paneli - Ödeme ayarları
@app.route('/admin/payment-settings', methods=['GET', 'POST'])
@login_required
def admin_payment_settings():
    if not current_user.is_admin:
        flash('Bu sayfaya erişim izniniz yok')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        # Kripto adreslerini al
        btc_address = request.form.get('btc_address', '')
        eth_address = request.form.get('eth_address', '')
        ltc_address = request.form.get('ltc_address', '')
        usdt_address = request.form.get('usdt_address', '')
        
        # Aktif ödeme yöntemlerini al
        payment_methods = request.form.getlist('payment_methods')
        
        # Veritabanı veya dosya sisteminde saklama işlemi burada yapılabilir
        # Şimdilik sadece başarılı mesajı gösterelim
        
        # Çevre değişkenlerini güncelleme (gerçek uygulamada dosyaya yazılmalı)
        os.environ['BTC_ADDRESS'] = btc_address
        os.environ['ETH_ADDRESS'] = eth_address
        os.environ['LTC_ADDRESS'] = ltc_address
        os.environ['USDT_ADDRESS'] = usdt_address
        os.environ['PAYMENT_METHODS'] = ','.join(payment_methods)
        
        flash('Ödeme ayarları başarıyla güncellendi')
        return redirect(url_for('admin_payment_settings'))
    
    # Mevcut ayarları göster
    btc_address = os.environ.get('BTC_ADDRESS', '')
    eth_address = os.environ.get('ETH_ADDRESS', '')
    ltc_address = os.environ.get('LTC_ADDRESS', '')
    usdt_address = os.environ.get('USDT_ADDRESS', '')
    payment_methods = os.environ.get('PAYMENT_METHODS', 'btc,eth,ltc,usdt').split(',')
    
    return render_template('admin/payment_settings.html', 
                           btc_address=btc_address,
                           eth_address=eth_address,
                           ltc_address=ltc_address,
                           usdt_address=usdt_address,
                           payment_methods=payment_methods)

# Admin paneli - Tüm siparişler
@app.route('/admin/orders')
@login_required
def admin_orders():
    if not current_user.is_admin:
        flash('Bu sayfaya erişim izniniz yok')
        return redirect(url_for('index'))
    
    orders = Order.query.order_by(Order.created_at.desc()).all()
    return render_template('admin/orders.html', orders=orders)

# Admin paneli - Sipariş durumu güncelleme
@app.route('/admin/orders/<int:order_id>/update', methods=['POST'])
@login_required
def update_order(order_id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'İzin reddedildi'}), 403
    
    order = Order.query.get_or_404(order_id)
    status = request.form.get('status')
    
    if status not in ['pending', 'completed', 'cancelled']:
        return jsonify({'success': False, 'message': 'Geçersiz durum'}), 400
    
    order.status = status
    
    # Eğer sipariş tamamlandıysa, VIP grubunu ekle
    if status == 'completed':
        success = add_vip_to_player(order.steam_id)
        if not success:
            return jsonify({'success': False, 'message': 'RCON hatası, VIP eklenemedi'}), 500
    
    db.session.commit()
    return jsonify({'success': True})

# Admin paneli - Kullanıcılar
@app.route('/admin/users')
@login_required
def admin_users():
    if not current_user.is_admin:
        flash('Bu sayfaya erişim izniniz yok')
        return redirect(url_for('index'))
    
    users = User.query.all()
    return render_template('admin/users.html', users=users)

# Admin paneli - Ayarlar
@app.route('/admin/settings', methods=['GET', 'POST'])
@login_required
def admin_settings():
    if not current_user.is_admin:
        flash('Bu sayfaya erişim izniniz yok')
        return redirect(url_for('index'))
    
    # VIP fiyatını çevre değişkeninden al (varsayılan: 5)
    vip_price = os.environ.get('VIP_PRICE', '5')
    
    if request.method == 'POST':
        # RCON ayarlarını güncelle
        if 'rcon_host' in request.form:
            rcon_host = request.form.get('rcon_host')
            rcon_port = request.form.get('rcon_port')
            rcon_password = request.form.get('rcon_password')
            
            # Çevre değişkenlerini güncelleme (gerçek uygulamada dosyaya yazılmalı)
            os.environ['RCON_HOST'] = rcon_host
            os.environ['RCON_PORT'] = rcon_port
            os.environ['RCON_PASSWORD'] = rcon_password
            
            # Global değişkenleri güncelle
            global RCON_HOST, RCON_PORT, RCON_PASSWORD
            RCON_HOST = rcon_host
            RCON_PORT = int(rcon_port)
            RCON_PASSWORD = rcon_password
            
            flash('RCON ayarları başarıyla güncellendi')
        
        # VIP ayarlarını güncelle
        elif 'vip_price' in request.form:
            new_vip_price = request.form.get('vip_price')
            
            # Çevre değişkenini güncelle
            os.environ['VIP_PRICE'] = new_vip_price
            vip_price = new_vip_price
            
            flash('VIP ayarları başarıyla güncellendi')
        
        # Site ayarlarını güncelle
        elif 'site_name' in request.form:
            # Site ayarlarını kaydetme işlemleri burada yapılabilir
            flash('Site ayarları başarıyla güncellendi')
        
        return redirect(url_for('admin_settings'))
    
    return render_template('admin/settings.html', 
                          RCON_HOST=RCON_HOST,
                          RCON_PORT=RCON_PORT,
                          RCON_PASSWORD=RCON_PASSWORD,
                          vip_price=vip_price)

# RCON API endpoint'leri
@app.route('/api/rcon/status', methods=['GET'])
@login_required
def rcon_status():
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'İzin reddedildi'}), 403
    
    success, response = check_rcon_connection()
    player_count = get_player_count()
    
    return jsonify({
        'success': success,
        'online': success,
        'message': 'Bağlantı başarılı' if success else response,
        'player_count': player_count,
        'server': RCON_HOST,
        'port': RCON_PORT,
        'last_check': datetime.now().strftime('%H:%M:%S')
    })

@app.route('/api/rcon/test', methods=['POST'])
@login_required
def rcon_test():
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'İzin reddedildi'}), 403
    
    command = request.form.get('command', 'status')
    success, response = execute_rcon_command(command)
    
    # HTML içeriği olabilecek karakterleri temizle
    if isinstance(response, str):
        response = response.replace('<', '&lt;').replace('>', '&gt;')
    
    return jsonify({
        'success': success,
        'response': response
    })

# Son siparişleri getiren API endpoint'i
@app.route('/api/orders/recent', methods=['GET'])
@login_required
def recent_orders():
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'İzin reddedildi'}), 403
    
    # Son 5 siparişi getir
    orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()
    
    orders_list = []
    for order in orders:
        orders_list.append({
            'orderNumber': f'RVS-{order.id}',
            'date': order.created_at.strftime('%d.%m.%Y %H:%M'),
            'user': order.user.username,
            'steamId': order.steam_id,
            'amount': f'{order.amount} {order.currency}',
            'status': order.status
        })
    
    return jsonify({
        'success': True,
        'orders': orders_list
    })

# Veritabanını oluştur
with app.app_context():
    db.create_all()
    
    # Admin kullanıcısı oluştur (ilk çalıştırmada)
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
        print(f"Admin user already exists: {admin_username}")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)