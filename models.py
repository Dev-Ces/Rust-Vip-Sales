from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
import string

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    orders = db.relationship('Order', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash"""
        return check_password_hash(self.password_hash, password)
    
    def get_total_spent(self):
        """Get total amount spent by user"""
        total = db.session.query(db.func.sum(Order.amount)).filter(
            Order.user_id == self.id,
            Order.status == 'completed'
        ).scalar()
        return total or 0
    
    def get_active_vips(self):
        """Get active VIP orders"""
        return Order.query.filter(
            Order.user_id == self.id,
            Order.status == 'completed',
            Order.vip_expires_at > datetime.utcnow()
        ).all()
    
    def __repr__(self):
        return f'<User {self.username}>'

class VipPackage(db.Model):
    __tablename__ = 'vip_packages'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    duration = db.Column(db.Integer, nullable=False)  # days
    features = db.Column(db.JSON)  # List of features
    active = db.Column(db.Boolean, default=True)
    featured = db.Column(db.Boolean, default=False)
    order = db.Column(db.Integer, default=0)  # Display order
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    orders = db.relationship('Order', backref='vip_package', lazy=True)
    
    def get_sales_count(self):
        """Get total sales count"""
        return Order.query.filter(
            Order.vip_package_id == self.id,
            Order.status == 'completed'
        ).count()
    
    def get_total_revenue(self):
        """Get total revenue from this package"""
        total = db.session.query(db.func.sum(Order.amount)).filter(
            Order.vip_package_id == self.id,
            Order.status == 'completed'
        ).scalar()
        return total or 0
    
    def __repr__(self):
        return f'<VipPackage {self.name}>'

class Order(db.Model):
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(20), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    vip_package_id = db.Column(db.Integer, db.ForeignKey('vip_packages.id'), nullable=False)
    steam_id = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(20), nullable=False)  # bitcoin, ethereum, litecoin, usdt
    payment_address = db.Column(db.String(255))  # Crypto address for payment
    transaction_hash = db.Column(db.String(255))  # Transaction hash when paid
    status = db.Column(db.String(20), default='pending')  # pending, completed, cancelled, expired
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)  # Payment expiration
    completed_at = db.Column(db.DateTime)  # When payment was completed
    vip_expires_at = db.Column(db.DateTime)  # When VIP expires
    rcon_executed = db.Column(db.Boolean, default=False)  # Whether RCON command was executed
    notes = db.Column(db.Text)  # Admin notes
    
    def __init__(self, **kwargs):
        super(Order, self).__init__(**kwargs)
        if not self.order_number:
            self.order_number = self.generate_order_number()
        if not self.expires_at:
            # Default 24 hours to pay
            self.expires_at = datetime.utcnow() + timedelta(hours=24)
    
    @staticmethod
    def generate_order_number():
        """Generate unique order number"""
        while True:
            # Generate format: RVS-YYYYMMDD-XXXX
            date_part = datetime.utcnow().strftime('%Y%m%d')
            random_part = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(4))
            order_number = f'RVS-{date_part}-{random_part}'
            
            # Check if already exists
            if not Order.query.filter_by(order_number=order_number).first():
                return order_number
    
    def is_expired(self):
        """Check if order is expired"""
        return self.expires_at and datetime.utcnow() > self.expires_at
    
    def get_payment_address(self):
        """Get payment address based on payment method"""
        settings = Settings.get_settings()
        
        if self.payment_method == 'bitcoin':
            return settings.get('btc_address')
        elif self.payment_method == 'ethereum':
            return settings.get('eth_address')
        elif self.payment_method == 'litecoin':
            return settings.get('ltc_address')
        elif self.payment_method == 'usdt':
            return settings.get('usdt_address')
        
        return None
    
    def complete_order(self, transaction_hash=None):
        """Complete the order"""
        self.status = 'completed'
        self.completed_at = datetime.utcnow()
        self.vip_expires_at = datetime.utcnow() + timedelta(days=self.vip_package.duration)
        
        if transaction_hash:
            self.transaction_hash = transaction_hash
        
        db.session.commit()
    
    def cancel_order(self, reason=None):
        """Cancel the order"""
        self.status = 'cancelled'
        if reason:
            self.notes = reason
        db.session.commit()
    
    def expire_order(self):
        """Expire the order"""
        self.status = 'expired'
        db.session.commit()
    
    def __repr__(self):
        return f'<Order {self.order_number}>'

class Settings(db.Model):
    __tablename__ = 'settings'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @staticmethod
    def get_setting(key, default=None):
        """Get a setting value"""
        setting = Settings.query.filter_by(key=key).first()
        return setting.value if setting else default
    
    @staticmethod
    def set_setting(key, value):
        """Set a setting value"""
        setting = Settings.query.filter_by(key=key).first()
        if setting:
            setting.value = str(value)
            setting.updated_at = datetime.utcnow()
        else:
            setting = Settings(key=key, value=str(value))
            db.session.add(setting)
        
        db.session.commit()
        return setting
    
    @staticmethod
    def get_settings():
        """Get all settings as a dictionary"""
        settings = Settings.query.all()
        return {setting.key: setting.value for setting in settings}
    
    @staticmethod
    def initialize_default_settings():
        """Initialize default settings"""
        defaults = {
            'site_title': 'Rust VIP Sales',
            'site_description': 'Premium VIP packages for Rust servers',
            'contact_email': 'admin@example.com',
            'discord_url': '',
            'maintenance_mode': 'false',
            'registration_enabled': 'true',
            'rcon_host': 'localhost',
            'rcon_port': '28016',
            'rcon_password': '',
            'auto_vip_management': 'true',
            'btc_address': '',
            'eth_address': '',
            'ltc_address': '',
            'usdt_address': '',
            'payment_timeout': '24',
            'min_order_amount': '1.00',
            'two_factor_enabled': 'false',
            'ip_restriction_enabled': 'false',
            'allowed_ips': '',
        }
        
        for key, value in defaults.items():
            if not Settings.query.filter_by(key=key).first():
                Settings.set_setting(key, value)
    
    def __repr__(self):
        return f'<Settings {self.key}={self.value}>'

class ActivityLog(db.Model):
    __tablename__ = 'activity_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    action = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='activity_logs')
    
    @staticmethod
    def log_activity(action, description=None, user_id=None, ip_address=None, user_agent=None):
        """Log an activity"""
        log = ActivityLog(
            action=action,
            description=description,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.session.add(log)
        db.session.commit()
        return log
    
    def __repr__(self):
        return f'<ActivityLog {self.action}>'

class RconCommand(db.Model):
    __tablename__ = 'rcon_commands'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=True)
    command = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text)
    success = db.Column(db.Boolean, default=False)
    executed_at = db.Column(db.DateTime, default=datetime.utcnow)
    error_message = db.Column(db.Text)
    
    # Relationships
    order = db.relationship('Order', backref='rcon_commands')
    
    @staticmethod
    def log_command(command, response=None, success=False, order_id=None, error_message=None):
        """Log an RCON command"""
        cmd = RconCommand(
            command=command,
            response=response,
            success=success,
            order_id=order_id,
            error_message=error_message
        )
        db.session.add(cmd)
        db.session.commit()
        return cmd
    
    def __repr__(self):
        return f'<RconCommand {self.command[:50]}>'

class SystemLog(db.Model):
    __tablename__ = 'system_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    level = db.Column(db.String(20), nullable=False)  # info, warning, error, success
    message = db.Column(db.Text, nullable=False)
    module = db.Column(db.String(50))  # Which module/component
    details = db.Column(db.JSON)  # Additional details
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @staticmethod
    def log(level, message, module=None, details=None):
        """Log a system message"""
        log = SystemLog(
            level=level,
            message=message,
            module=module,
            details=details
        )
        db.session.add(log)
        db.session.commit()
        return log
    
    @staticmethod
    def info(message, module=None, details=None):
        """Log info message"""
        return SystemLog.log('info', message, module, details)
    
    @staticmethod
    def warning(message, module=None, details=None):
        """Log warning message"""
        return SystemLog.log('warning', message, module, details)
    
    @staticmethod
    def error(message, module=None, details=None):
        """Log error message"""
        return SystemLog.log('error', message, module, details)
    
    @staticmethod
    def success(message, module=None, details=None):
        """Log success message"""
        return SystemLog.log('success', message, module, details)
    
    def __repr__(self):
        return f'<SystemLog {self.level}: {self.message[:50]}>'

# Helper functions
def create_admin_user(username='admin', email='admin@example.com', password='admin123'):
    """Create default admin user"""
    admin = User.query.filter_by(username=username).first()
    if not admin:
        admin = User(
            username=username,
            email=email,
            is_admin=True
        )
        admin.set_password(password)
        db.session.add(admin)
        db.session.commit()
        
        ActivityLog.log_activity(
            action='admin_created',
            description=f'Admin user {username} created',
            user_id=admin.id
        )
        
        SystemLog.info(f'Admin user {username} created', 'system')
    
    return admin

def create_sample_vip_packages():
    """Create sample VIP packages"""
    packages = [
        {
            'name': 'VIP Bronze',
            'description': 'Temel VIP ayrıcalıkları ile oyun deneyiminizi geliştirin.',
            'price': 9.99,
            'duration': 30,
            'features': [
                'Özel VIP kanalına erişim',
                'Günlük bonus kaynaklar',
                'Hızlı respawn',
                'VIP kit erişimi',
                'Öncelikli sunucu girişi'
            ],
            'active': True,
            'featured': False,
            'order': 1
        },
        {
            'name': 'VIP Silver',
            'description': 'Gelişmiş VIP özellikleri ile daha fazla avantaj elde edin.',
            'price': 19.99,
            'duration': 30,
            'features': [
                'Tüm Bronze özellikleri',
                'Ek bonus kaynaklar',
                'Özel VIP alanları',
                'Gelişmiş kit erişimi',
                'Teleport komutları',
                'Özel VIP etkinlikleri'
            ],
            'active': True,
            'featured': True,
            'order': 2
        },
        {
            'name': 'VIP Gold',
            'description': 'Premium VIP deneyimi ile maksimum ayrıcalıkları yaşayın.',
            'price': 39.99,
            'duration': 30,
            'features': [
                'Tüm Silver özellikleri',
                'Maksimum bonus kaynaklar',
                'Özel Gold alanları',
                'Sınırsız kit erişimi',
                'Gelişmiş teleport',
                'Özel Gold etkinlikleri',
                'Admin desteği önceliği'
            ],
            'active': True,
            'featured': False,
            'order': 3
        }
    ]
    
    for package_data in packages:
        existing = VipPackage.query.filter_by(name=package_data['name']).first()
        if not existing:
            package = VipPackage(**package_data)
            db.session.add(package)
    
    db.session.commit()
    SystemLog.info('Sample VIP packages created', 'system')

def init_database():
    """Initialize database with default data"""
    db.create_all()
    
    # Initialize settings
    Settings.initialize_default_settings()
    
    # Create admin user
    create_admin_user()
    
    # Create sample VIP packages
    create_sample_vip_packages()
    
    SystemLog.info('Database initialized successfully', 'system')