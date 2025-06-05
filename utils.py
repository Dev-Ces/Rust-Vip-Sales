import socket
import struct
import time
from datetime import datetime, timedelta
from models import db, Settings, Order, RconCommand, SystemLog, ActivityLog
from threading import Thread
import schedule
import logging

class RconClient:
    """RCON client for Rust server communication"""
    
    def __init__(self, host=None, port=None, password=None):
        self.host = host or Settings.get_setting('rcon_host', 'localhost')
        self.port = int(port or Settings.get_setting('rcon_port', '28016'))
        self.password = password or Settings.get_setting('rcon_password', '')
        self.socket = None
        self.request_id = 1
    
    def connect(self):
        """Connect to RCON server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(10)
            self.socket.connect((self.host, self.port))
            
            # Authenticate
            auth_response = self._send_packet(3, self.password)
            if auth_response is None:
                raise Exception("Authentication failed")
            
            SystemLog.info(f'RCON connected to {self.host}:{self.port}', 'rcon')
            return True
            
        except Exception as e:
            SystemLog.error(f'RCON connection failed: {str(e)}', 'rcon')
            if self.socket:
                self.socket.close()
                self.socket = None
            return False
    
    def disconnect(self):
        """Disconnect from RCON server"""
        if self.socket:
            self.socket.close()
            self.socket = None
            SystemLog.info('RCON disconnected', 'rcon')
    
    def execute_command(self, command, log_to_db=True):
        """Execute RCON command"""
        if not self.socket:
            if not self.connect():
                error_msg = "RCON not connected"
                if log_to_db:
                    RconCommand.log_command(command, error_message=error_msg, success=False)
                return None, error_msg
        
        try:
            response = self._send_packet(2, command)
            
            if response is not None:
                if log_to_db:
                    RconCommand.log_command(command, response=response, success=True)
                SystemLog.info(f'RCON command executed: {command}', 'rcon')
                return response, None
            else:
                error_msg = "No response from server"
                if log_to_db:
                    RconCommand.log_command(command, error_message=error_msg, success=False)
                return None, error_msg
                
        except Exception as e:
            error_msg = f"RCON command failed: {str(e)}"
            if log_to_db:
                RconCommand.log_command(command, error_message=error_msg, success=False)
            SystemLog.error(error_msg, 'rcon')
            return None, error_msg
    
    def _send_packet(self, packet_type, data):
        """Send RCON packet"""
        if not self.socket:
            return None
        
        # Create packet
        packet_id = self.request_id
        self.request_id += 1
        
        packet_data = data.encode('utf-8') + b'\x00\x00'
        packet_size = len(packet_data) + 10
        
        packet = struct.pack('<iii', packet_size - 4, packet_id, packet_type) + packet_data
        
        try:
            # Send packet
            self.socket.send(packet)
            
            # Receive response
            response_size = struct.unpack('<i', self.socket.recv(4))[0]
            response_data = self.socket.recv(response_size)
            
            response_id, response_type = struct.unpack('<ii', response_data[:8])
            response_body = response_data[8:-2].decode('utf-8', errors='ignore')
            
            return response_body
            
        except Exception as e:
            SystemLog.error(f'RCON packet send failed: {str(e)}', 'rcon')
            return None
    
    def test_connection(self):
        """Test RCON connection"""
        try:
            if self.connect():
                response, error = self.execute_command('status', log_to_db=False)
                self.disconnect()
                return response is not None, error
            return False, "Connection failed"
        except Exception as e:
            return False, str(e)
    
    def add_vip(self, steam_id, order_id=None):
        """Add VIP to user"""
        command = f"chat user add {steam_id} vip"
        response, error = self.execute_command(command)
        
        if order_id:
            RconCommand.log_command(command, response=response, success=error is None, order_id=order_id)
        
        if error is None:
            SystemLog.success(f'VIP added to {steam_id}', 'vip_management')
            ActivityLog.log_activity(
                action='vip_added',
                description=f'VIP added to Steam ID: {steam_id}',
                ip_address=None
            )
        else:
            SystemLog.error(f'Failed to add VIP to {steam_id}: {error}', 'vip_management')
        
        return error is None, error
    
    def remove_vip(self, steam_id, order_id=None):
        """Remove VIP from user"""
        command = f"chat user remove {steam_id} vip"
        response, error = self.execute_command(command)
        
        if order_id:
            RconCommand.log_command(command, response=response, success=error is None, order_id=order_id)
        
        if error is None:
            SystemLog.success(f'VIP removed from {steam_id}', 'vip_management')
            ActivityLog.log_activity(
                action='vip_removed',
                description=f'VIP removed from Steam ID: {steam_id}',
                ip_address=None
            )
        else:
            SystemLog.error(f'Failed to remove VIP from {steam_id}: {error}', 'vip_management')
        
        return error is None, error
    
    def send_message(self, message):
        """Send message to server chat"""
        command = f'say "{message}"'
        response, error = self.execute_command(command)
        return error is None, error

class VipManager:
    """VIP management utilities"""
    
    @staticmethod
    def process_completed_order(order):
        """Process a completed order and add VIP"""
        if order.rcon_executed:
            return True, "VIP already added"
        
        auto_management = Settings.get_setting('auto_vip_management', 'true') == 'true'
        if not auto_management:
            SystemLog.info(f'Auto VIP management disabled for order {order.order_number}', 'vip_management')
            return True, "Auto management disabled"
        
        rcon = RconClient()
        success, error = rcon.add_vip(order.steam_id, order.id)
        rcon.disconnect()
        
        if success:
            order.rcon_executed = True
            db.session.commit()
            
            SystemLog.success(f'VIP added for order {order.order_number}', 'vip_management')
            return True, None
        else:
            SystemLog.error(f'Failed to add VIP for order {order.order_number}: {error}', 'vip_management')
            return False, error
    
    @staticmethod
    def process_expired_vips():
        """Process expired VIPs and remove them"""
        auto_management = Settings.get_setting('auto_vip_management', 'true') == 'true'
        if not auto_management:
            return
        
        # Find expired VIPs
        expired_orders = Order.query.filter(
            Order.status == 'completed',
            Order.vip_expires_at <= datetime.utcnow(),
            Order.rcon_executed == True
        ).all()
        
        if not expired_orders:
            return
        
        rcon = RconClient()
        if not rcon.connect():
            SystemLog.error('Failed to connect to RCON for VIP expiration processing', 'vip_management')
            return
        
        processed = 0
        for order in expired_orders:
            success, error = rcon.remove_vip(order.steam_id, order.id)
            if success:
                # Mark as processed by setting rcon_executed to False
                order.rcon_executed = False
                processed += 1
                
                SystemLog.success(f'Expired VIP removed for order {order.order_number}', 'vip_management')
            else:
                SystemLog.error(f'Failed to remove expired VIP for order {order.order_number}: {error}', 'vip_management')
        
        rcon.disconnect()
        
        if processed > 0:
            db.session.commit()
            SystemLog.info(f'Processed {processed} expired VIPs', 'vip_management')
    
    @staticmethod
    def check_pending_orders():
        """Check and expire pending orders"""
        expired_orders = Order.query.filter(
            Order.status == 'pending',
            Order.expires_at <= datetime.utcnow()
        ).all()
        
        for order in expired_orders:
            order.expire_order()
            SystemLog.info(f'Order {order.order_number} expired', 'order_management')
        
        if expired_orders:
            SystemLog.info(f'Expired {len(expired_orders)} pending orders', 'order_management')

class TaskScheduler:
    """Background task scheduler"""
    
    def __init__(self, app):
        self.app = app
        self.running = False
    
    def start(self):
        """Start the scheduler"""
        if self.running:
            return
        
        self.running = True
        
        # Schedule tasks
        schedule.every(5).minutes.do(self._run_with_app_context, VipManager.process_expired_vips)
        schedule.every(1).minutes.do(self._run_with_app_context, VipManager.check_pending_orders)
        schedule.every(1).hours.do(self._run_with_app_context, self._cleanup_old_logs)
        
        # Start scheduler thread
        scheduler_thread = Thread(target=self._run_scheduler, daemon=True)
        scheduler_thread.start()
        
        SystemLog.info('Task scheduler started', 'scheduler')
    
    def _run_scheduler(self):
        """Run the scheduler"""
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(1)
            except Exception as e:
                SystemLog.error(f'Scheduler error: {str(e)}', 'scheduler')
                time.sleep(5)
    
    def _run_with_app_context(self, func):
        """Run function with Flask app context"""
        with self.app.app_context():
            try:
                func()
            except Exception as e:
                SystemLog.error(f'Task execution error: {str(e)}', 'scheduler')
    
    def _cleanup_old_logs(self):
        """Clean up old logs"""
        # Keep logs for 30 days
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        
        # Clean activity logs
        old_activity_logs = ActivityLog.query.filter(ActivityLog.created_at < cutoff_date).count()
        ActivityLog.query.filter(ActivityLog.created_at < cutoff_date).delete()
        
        # Clean system logs
        old_system_logs = SystemLog.query.filter(SystemLog.created_at < cutoff_date).count()
        SystemLog.query.filter(SystemLog.created_at < cutoff_date).delete()
        
        # Clean RCON command logs
        old_rcon_logs = RconCommand.query.filter(RconCommand.executed_at < cutoff_date).count()
        RconCommand.query.filter(RconCommand.executed_at < cutoff_date).delete()
        
        db.session.commit()
        
        total_cleaned = old_activity_logs + old_system_logs + old_rcon_logs
        if total_cleaned > 0:
            SystemLog.info(f'Cleaned up {total_cleaned} old log entries', 'maintenance')
    
    def stop(self):
        """Stop the scheduler"""
        self.running = False
        SystemLog.info('Task scheduler stopped', 'scheduler')

class PaymentValidator:
    """Payment validation utilities"""
    
    @staticmethod
    def validate_crypto_address(address, crypto_type):
        """Basic crypto address validation"""
        if not address:
            return False
        
        # Basic length and character validation
        if crypto_type == 'bitcoin':
            return len(address) >= 26 and len(address) <= 35 and address.isalnum()
        elif crypto_type == 'ethereum':
            return len(address) == 42 and address.startswith('0x') and all(c in '0123456789abcdefABCDEF' for c in address[2:])
        elif crypto_type == 'litecoin':
            return len(address) >= 26 and len(address) <= 35 and address.isalnum()
        elif crypto_type == 'usdt':
            # USDT can be on different networks, basic validation
            return len(address) >= 26 and len(address) <= 42
        
        return False
    
    @staticmethod
    def validate_steam_id(steam_id):
        """Validate Steam ID format"""
        if not steam_id:
            return False
        
        # Steam ID64 format (17 digits starting with 7656119)
        if steam_id.isdigit() and len(steam_id) == 17 and steam_id.startswith('7656119'):
            return True
        
        # Steam ID format (STEAM_0:X:XXXXXXX)
        if steam_id.startswith('STEAM_') and ':' in steam_id:
            parts = steam_id.split(':')
            if len(parts) == 3 and parts[1] in ['0', '1'] and parts[2].isdigit():
                return True
        
        return False

class SecurityUtils:
    """Security utilities"""
    
    @staticmethod
    def is_ip_allowed(ip_address):
        """Check if IP address is allowed"""
        ip_restriction = Settings.get_setting('ip_restriction_enabled', 'false') == 'true'
        if not ip_restriction:
            return True
        
        allowed_ips = Settings.get_setting('allowed_ips', '')
        if not allowed_ips:
            return True
        
        allowed_list = [ip.strip() for ip in allowed_ips.split(',') if ip.strip()]
        return ip_address in allowed_list
    
    @staticmethod
    def log_security_event(event_type, description, ip_address=None, user_id=None):
        """Log security events"""
        ActivityLog.log_activity(
            action=f'security_{event_type}',
            description=description,
            user_id=user_id,
            ip_address=ip_address
        )
        
        SystemLog.warning(f'Security event: {description}', 'security')

class StatsCalculator:
    """Statistics calculation utilities"""
    
    @staticmethod
    def get_dashboard_stats():
        """Get dashboard statistics"""
        from sqlalchemy import func
        
        # Total orders
        total_orders = Order.query.count()
        
        # Total revenue
        total_revenue = db.session.query(func.sum(Order.amount)).filter(
            Order.status == 'completed'
        ).scalar() or 0
        
        # Active VIPs
        active_vips = Order.query.filter(
            Order.status == 'completed',
            Order.vip_expires_at > datetime.utcnow()
        ).count()
        
        # Total users
        from models import User
        total_users = User.query.count()
        
        # Pending orders
        pending_orders = Order.query.filter(Order.status == 'pending').count()
        
        # Today's revenue
        today = datetime.utcnow().date()
        today_revenue = db.session.query(func.sum(Order.amount)).filter(
            Order.status == 'completed',
            func.date(Order.completed_at) == today
        ).scalar() or 0
        
        # This month's revenue
        month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_revenue = db.session.query(func.sum(Order.amount)).filter(
            Order.status == 'completed',
            Order.completed_at >= month_start
        ).scalar() or 0
        
        return {
            'total_orders': total_orders,
            'total_revenue': float(total_revenue),
            'active_vips': active_vips,
            'total_users': total_users,
            'pending_orders': pending_orders,
            'today_revenue': float(today_revenue),
            'month_revenue': float(month_revenue)
        }
    
    @staticmethod
    def get_sales_chart_data(period='7d'):
        """Get sales chart data"""
        from sqlalchemy import func
        
        if period == '7d':
            days = 7
        elif period == '30d':
            days = 30
        else:
            days = 7
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get daily sales
        daily_sales = db.session.query(
            func.date(Order.completed_at).label('date'),
            func.sum(Order.amount).label('revenue'),
            func.count(Order.id).label('orders')
        ).filter(
            Order.status == 'completed',
            Order.completed_at >= start_date
        ).group_by(func.date(Order.completed_at)).all()
        
        # Format data
        chart_data = {
            'labels': [],
            'revenue': [],
            'orders': []
        }
        
        for sale in daily_sales:
            chart_data['labels'].append(sale.date.strftime('%Y-%m-%d'))
            chart_data['revenue'].append(float(sale.revenue or 0))
            chart_data['orders'].append(sale.orders or 0)
        
        return chart_data

# Initialize logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Global RCON client instance
rcon_client = None

def get_rcon_client():
    """Get global RCON client instance"""
    global rcon_client
    if rcon_client is None:
        rcon_client = RconClient()
    return rcon_client

def format_currency(amount):
    """Format currency amount"""
    return f"${amount:.2f}"

def format_datetime(dt):
    """Format datetime for display"""
    if dt is None:
        return 'N/A'
    return dt.strftime('%Y-%m-%d %H:%M:%S')

def format_date(dt):
    """Format date for display"""
    if dt is None:
        return 'N/A'
    return dt.strftime('%Y-%m-%d')

def time_ago(dt):
    """Get time ago string"""
    if dt is None:
        return 'N/A'
    
    now = datetime.utcnow()
    diff = now - dt
    
    if diff.days > 0:
        return f"{diff.days} gün önce"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} saat önce"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} dakika önce"
    else:
        return "Az önce"