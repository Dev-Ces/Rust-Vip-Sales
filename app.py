from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from datetime import datetime, timedelta
import os
import secrets
import string
import json

# Import our models and utilities
from models import db, User, VipPackage, Order, Settings, ActivityLog, SystemLog, init_database
from utils import (
    RconClient, VipManager, TaskScheduler, PaymentValidator, SecurityUtils, 
    StatsCalculator, get_rcon_client, format_currency, format_datetime, 
    format_date, time_ago
)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'rust-vip-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///rust_vip_sales.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Initialize task scheduler
scheduler = TaskScheduler(app)

# Template filters
app.jinja_env.filters['currency'] = format_currency
app.jinja_env.filters['datetime'] = format_datetime
app.jinja_env.filters['date'] = format_date
app.jinja_env.filters['time_ago'] = time_ago

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    packages = VipPackage.query.filter_by(active=True).all()
    stats = StatsCalculator.get_dashboard_stats()
    return render_template('index.html', packages=packages, stats=stats)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Validation
        if not SecurityUtils.validate_username(username):
            flash('Geçersiz kullanıcı adı', 'error')
            return render_template('register.html')
        
        if not SecurityUtils.validate_email(email):
            flash('Geçersiz e-posta adresi', 'error')
            return render_template('register.html')
        
        if not SecurityUtils.validate_password(password):
            flash('Şifre en az 8 karakter olmalı', 'error')
            return render_template('register.html')
        
        # Check if user exists
        if User.query.filter_by(username=username).first():
            flash('Bu kullanıcı adı zaten kullanılıyor', 'error')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Bu e-posta adresi zaten kullanılıyor', 'error')
            return render_template('register.html')
        
        # Create user
        user = User(username=username, email=email)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        ActivityLog.log_activity(user.id, 'user_registered', f'Kullanıcı kaydı: {username}')
        
        flash('Hesabınız başarıyla oluşturuldu!', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            ActivityLog.log_activity(user.id, 'user_login', 'Kullanıcı girişi')
            
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('Geçersiz kullanıcı adı veya şifre', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    ActivityLog.log_activity(current_user.id, 'user_logout', 'Kullanıcı çıkışı')
    logout_user()
    return redirect(url_for('index'))

@app.route('/packages')
def packages():
    packages = VipPackage.query.filter_by(active=True).all()
    return render_template('packages.html', packages=packages)

@app.route('/buy/<int:package_id>', methods=['GET', 'POST'])
@login_required
def buy_package(package_id):
    package = VipPackage.query.get_or_404(package_id)
    
    if not package.active:
        flash('Bu paket artık mevcut değil', 'error')
        return redirect(url_for('packages'))
    
    if request.method == 'POST':
        steam_id = request.form.get('steam_id')
        payment_method = request.form.get('payment_method')
        
        # Validation
        if not SecurityUtils.validate_steam_id(steam_id):
            flash('Geçersiz Steam ID', 'error')
            return render_template('buy_package.html', package=package)
        
        if payment_method not in ['btc', 'eth', 'ltc', 'usdt']:
            flash('Geçersiz ödeme yöntemi', 'error')
            return render_template('buy_package.html', package=package)
        
        # Create order
        order = Order(
            user_id=current_user.id,
            vip_package_id=package.id,
            steam_id=steam_id,
            amount=package.price,
            payment_method=payment_method
        )
        
        # Set VIP expiration date
        order.vip_expires_at = datetime.utcnow() + timedelta(days=package.duration)
        
        db.session.add(order)
        db.session.commit()
        
        ActivityLog.log_activity(current_user.id, 'order_created', f'Sipariş oluşturuldu: {order.order_number}')
        
        return redirect(url_for('order_detail', order_id=order.id))
    
    return render_template('buy_package.html', package=package)

@app.route('/orders')
@login_required
def my_orders():
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template('my_orders.html', orders=orders)

@app.route('/order/<int:order_id>')
@login_required
def order_detail(order_id):
    order = Order.query.get_or_404(order_id)
    
    if order.user_id != current_user.id and not current_user.is_admin:
        flash('Bu sayfaya erişim yetkiniz yok', 'error')
        return redirect(url_for('my_orders'))
    
    # Get payment address
    payment_address = None
    if order.payment_method in ['btc', 'eth', 'ltc', 'usdt']:
        payment_address = Settings.get_setting(f'{order.payment_method}_address')
    
    return render_template('order_detail.html', order=order, payment_address=payment_address)

# Admin routes
@app.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash('Bu sayfaya erişim yetkiniz yok', 'error')
        return redirect(url_for('index'))
    
    stats = StatsCalculator.get_admin_stats()
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(10).all()
    recent_logs = ActivityLog.query.order_by(ActivityLog.created_at.desc()).limit(10).all()
    
    return render_template('admin/dashboard.html', 
                         stats=stats, 
                         recent_orders=recent_orders,
                         recent_logs=recent_logs)

@app.route('/admin/orders')
@login_required
def admin_orders():
    if not current_user.is_admin:
        flash('Bu sayfaya erişim yetkiniz yok', 'error')
        return redirect(url_for('index'))
    
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', 'all')
    
    query = Order.query
    if status != 'all':
        query = query.filter_by(status=status)
    
    orders = query.order_by(Order.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False)
    
    return render_template('admin/orders.html', orders=orders, current_status=status)

@app.route('/admin/orders/<int:order_id>/approve', methods=['POST'])
@login_required
def admin_approve_order(order_id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Yetkisiz erişim'}), 403
    
    order = Order.query.get_or_404(order_id)
    
    if order.status != 'pending':
        return jsonify({'success': False, 'message': 'Sipariş zaten işlenmiş'}), 400
    
    try:
        # Add VIP to player
        vip_manager = VipManager()
        success = vip_manager.add_vip(order.steam_id, order.vip_package.name, order.vip_expires_at)
        
        if success:
            order.status = 'completed'
            order.completed_at = datetime.utcnow()
            db.session.commit()
            
            ActivityLog.log_activity(current_user.id, 'order_approved', f'Sipariş onaylandı: {order.order_number}')
            
            return jsonify({'success': True, 'message': 'Sipariş başarıyla onaylandı'})
        else:
            return jsonify({'success': False, 'message': 'VIP eklenirken hata oluştu'}), 500
    
    except Exception as e:
        SystemLog.log_error('order_approval_error', str(e))
        return jsonify({'success': False, 'message': 'Sistem hatası'}), 500

@app.route('/admin/orders/<int:order_id>/reject', methods=['POST'])
@login_required
def admin_reject_order(order_id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Yetkisiz erişim'}), 403
    
    order = Order.query.get_or_404(order_id)
    
    if order.status != 'pending':
        return jsonify({'success': False, 'message': 'Sipariş zaten işlenmiş'}), 400
    
    order.status = 'cancelled'
    db.session.commit()
    
    ActivityLog.log_activity(current_user.id, 'order_rejected', f'Sipariş reddedildi: {order.order_number}')
    
    return jsonify({'success': True, 'message': 'Sipariş reddedildi'})

@app.route('/admin/packages')
@login_required
def admin_packages():
    if not current_user.is_admin:
        flash('Bu sayfaya erişim yetkiniz yok', 'error')
        return redirect(url_for('index'))
    
    packages = VipPackage.query.order_by(VipPackage.created_at.desc()).all()
    return render_template('admin/packages.html', packages=packages)

@app.route('/admin/packages/new', methods=['GET', 'POST'])
@app.route('/admin/packages/<int:package_id>/edit', methods=['GET', 'POST'])
@login_required
def admin_package_form(package_id=None):
    if not current_user.is_admin:
        flash('Bu sayfaya erişim yetkiniz yok', 'error')
        return redirect(url_for('index'))
    
    package = VipPackage.query.get(package_id) if package_id else None
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        price = float(request.form.get('price'))
        duration = int(request.form.get('duration'))
        features = request.form.getlist('features')
        active = bool(request.form.get('active'))
        
        if package:
            package.name = name
            package.description = description
            package.price = price
            package.duration = duration
            package.features = features
            package.active = active
            action = 'updated'
        else:
            package = VipPackage(
                name=name,
                description=description,
                price=price,
                duration=duration,
                features=features,
                active=active
            )
            db.session.add(package)
            action = 'created'
        
        db.session.commit()
        
        ActivityLog.log_activity(current_user.id, f'package_{action}', f'Paket {action}: {package.name}')
        
        flash(f'Paket başarıyla {"güncellendi" if action == "updated" else "oluşturuldu"}', 'success')
        return redirect(url_for('admin_packages'))
    
    return render_template('admin/package_form.html', package=package)

@app.route('/admin/packages/<int:package_id>/delete', methods=['POST'])
@login_required
def admin_delete_package(package_id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Yetkisiz erişim'}), 403
    
    package = VipPackage.query.get_or_404(package_id)
    
    # Check if package has orders
    if package.orders:
        return jsonify({'success': False, 'message': 'Bu pakete ait siparişler var, silinemez'}), 400
    
    db.session.delete(package)
    db.session.commit()
    
    ActivityLog.log_activity(current_user.id, 'package_deleted', f'Paket silindi: {package.name}')
    
    return jsonify({'success': True, 'message': 'Paket silindi'})

@app.route('/admin/settings', methods=['GET', 'POST'])
@login_required
def admin_settings():
    if not current_user.is_admin:
        flash('Bu sayfaya erişim yetkiniz yok', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        # Update settings
        settings_data = {
            'rcon_host': request.form.get('rcon_host'),
            'rcon_port': request.form.get('rcon_port'),
            'rcon_password': request.form.get('rcon_password'),
            'btc_address': request.form.get('btc_address'),
            'eth_address': request.form.get('eth_address'),
            'ltc_address': request.form.get('ltc_address'),
            'usdt_address': request.form.get('usdt_address'),
            'site_title': request.form.get('site_title'),
            'site_description': request.form.get('site_description'),
        }
        
        for key, value in settings_data.items():
            if value is not None:
                Settings.set_setting(key, value)
        
        ActivityLog.log_activity(current_user.id, 'settings_updated', 'Sistem ayarları güncellendi')
        
        flash('Ayarlar başarıyla güncellendi', 'success')
        return redirect(url_for('admin_settings'))
    
    # Get current settings
    settings = {
        'rcon_host': Settings.get_setting('rcon_host', '127.0.0.1'),
        'rcon_port': Settings.get_setting('rcon_port', '28016'),
        'rcon_password': Settings.get_setting('rcon_password', ''),
        'btc_address': Settings.get_setting('btc_address', ''),
        'eth_address': Settings.get_setting('eth_address', ''),
        'ltc_address': Settings.get_setting('ltc_address', ''),
        'usdt_address': Settings.get_setting('usdt_address', ''),
        'site_title': Settings.get_setting('site_title', 'Rust VIP Sales'),
        'site_description': Settings.get_setting('site_description', 'Rust sunucusu için VIP paket satışı'),
    }
    
    return render_template('admin/settings.html', settings=settings)

@app.route('/admin/users')
@login_required
def admin_users():
    if not current_user.is_admin:
        flash('Bu sayfaya erişim yetkiniz yok', 'error')
        return redirect(url_for('index'))
    
    page = request.args.get('page', 1, type=int)
    users = User.query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False)
    
    return render_template('admin/users.html', users=users)

@app.route('/admin/logs')
@login_required
def admin_logs():
    if not current_user.is_admin:
        flash('Bu sayfaya erişim yetkiniz yok', 'error')
        return redirect(url_for('index'))
    
    page = request.args.get('page', 1, type=int)
    log_type = request.args.get('type', 'activity')
    
    if log_type == 'system':
        logs = SystemLog.query.order_by(SystemLog.created_at.desc()).paginate(
            page=page, per_page=50, error_out=False)
    else:
        logs = ActivityLog.query.order_by(ActivityLog.created_at.desc()).paginate(
            page=page, per_page=50, error_out=False)
    
    return render_template('admin/logs.html', logs=logs, current_type=log_type)

# API routes
@app.route('/api/rcon/test', methods=['POST'])
@login_required
def api_test_rcon():
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Yetkisiz erişim'}), 403
    
    try:
        rcon_client = get_rcon_client()
        result = rcon_client.test_connection()
        
        if result['success']:
            return jsonify({'success': True, 'message': 'RCON bağlantısı başarılı', 'data': result['data']})
        else:
            return jsonify({'success': False, 'message': f'RCON bağlantısı başarısız: {result["error"]}'})
    
    except Exception as e:
        SystemLog.log_error('rcon_test_error', str(e))
        return jsonify({'success': False, 'message': 'Sistem hatası'}), 500

@app.route('/api/payment/validate', methods=['POST'])
@login_required
def api_validate_payment():
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Yetkisiz erişim'}), 403
    
    order_id = request.json.get('order_id')
    transaction_hash = request.json.get('transaction_hash')
    
    if not order_id or not transaction_hash:
        return jsonify({'success': False, 'message': 'Eksik parametreler'}), 400
    
    order = Order.query.get_or_404(order_id)
    
    try:
        validator = PaymentValidator()
        result = validator.validate_transaction(order.payment_method, transaction_hash, order.amount)
        
        if result['valid']:
            order.transaction_hash = transaction_hash
            order.status = 'completed'
            order.completed_at = datetime.utcnow()
            
            # Add VIP to player
            vip_manager = VipManager()
            vip_manager.add_vip(order.steam_id, order.vip_package.name, order.vip_expires_at)
            
            db.session.commit()
            
            ActivityLog.log_activity(current_user.id, 'payment_validated', f'Ödeme doğrulandı: {order.order_number}')
            
            return jsonify({'success': True, 'message': 'Ödeme doğrulandı ve VIP eklendi'})
        else:
            return jsonify({'success': False, 'message': f'Ödeme doğrulanamadı: {result["error"]}'})
    
    except Exception as e:
        SystemLog.log_error('payment_validation_error', str(e))
        return jsonify({'success': False, 'message': 'Sistem hatası'}), 500

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    SystemLog.log_error('internal_server_error', str(error))
    return render_template('errors/500.html'), 500

if __name__ == '__main__':
    with app.app_context():
        init_database()
        
        # Start background tasks
        scheduler.start()
    
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)