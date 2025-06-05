from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required
from app import db
from app.admin import admin
from app.models import Order
from functools import wraps
from config import Config

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth = request.authorization
        if not auth or not (auth.username == Config.ADMIN_USERNAME and 
                          auth.password == Config.ADMIN_PASSWORD):
            return ('Could not verify your access level for that URL.\n'
                   'You have to login with proper credentials', 401,
                   {'WWW-Authenticate': 'Basic realm="Login Required"'})
        return f(*args, **kwargs)
    return decorated_function

@admin.route('/')
@admin_required
def index():
    orders = Order.query.order_by(Order.created_at.desc()).all()
    return render_template('admin/index.html', orders=orders)

@admin.route('/order/<int:order_id>', methods=['GET', 'POST'])
@admin_required
def order_detail(order_id):
    order = Order.query.get_or_404(order_id)
    if request.method == 'POST':
        status = request.form.get('status')
        if status in ['pending', 'completed', 'cancelled']:
            order.status = status
            db.session.commit()
            flash('Order status updated successfully!')
        return redirect(url_for('admin.order_detail', order_id=order_id))
    return render_template('admin/order_detail.html', order=order)

@admin.route('/settings', methods=['GET', 'POST'])
@admin_required
def settings():
    if request.method == 'POST':
        crypto_address = request.form.get('crypto_address')
        if crypto_address:
            # In a real application, you would update the environment variables
            # or a configuration file here
            flash('Settings updated successfully!')
        return redirect(url_for('admin.settings'))
    return render_template('admin/settings.html', crypto_address=Config.CRYPTO_ADDRESS) 