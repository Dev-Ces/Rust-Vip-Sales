from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user, login_user, logout_user
from werkzeug.security import generate_password_hash
from app import db
from app.models import Order, User
from app.utils import get_player_count, add_vip
from config import Config
import os

main = Blueprint('main', __name__)

@main.route('/')
def index():
    player_count = get_player_count()
    return render_template('index.html', player_count=player_count)

@main.route('/shop')
def shop():
    return render_template('shop.html')

@main.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            flash('Successfully logged in!', 'success')
            return redirect(url_for('main.index'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@main.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        steam_id = request.form.get('steam_id')
        discord_id = request.form.get('discord_id')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('register.html')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
            return render_template('register.html')
        
        if User.query.filter_by(steam_id=steam_id).first():
            flash('Steam ID already registered', 'danger')
            return render_template('register.html')
        
        if User.query.filter_by(discord_id=discord_id).first():
            flash('Discord ID already registered', 'danger')
            return render_template('register.html')
        
        user = User(username=username, steam_id=steam_id, discord_id=discord_id)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('main.login'))
    
    return render_template('register.html')

@main.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Successfully logged out!', 'success')
    return redirect(url_for('main.index'))

@main.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    if request.method == 'POST':
        # Create a new order
        order = Order(
            user_id=current_user.id,
            amount=5.00,  # Fixed price for VIP package
            status='pending'
        )
        db.session.add(order)
        db.session.commit()
        
        # Here you would typically redirect to payment processing
        # For now, we'll just mark it as completed for testing
        order.status = 'completed'
        db.session.commit()
        
        # Grant VIP access
        if add_vip(current_user.steam_id):
            flash('VIP access granted successfully!', 'success')
        else:
            flash('Error granting VIP access. Please contact support.', 'danger')
        
        return redirect(url_for('main.index'))
    
    return render_template('checkout.html')

@main.route('/admin')
@login_required
def admin():
    if not current_user.is_admin:
        flash('Access denied', 'danger')
        return redirect(url_for('main.index'))
    
    orders = Order.query.order_by(Order.created_at.desc()).all()
    return render_template('admin/dashboard.html', orders=orders)

@main.route('/admin/order/<int:order_id>/approve', methods=['POST'])
@login_required
def approve_order(order_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    
    order = Order.query.get_or_404(order_id)
    if order.status != 'pending':
        return jsonify({'error': 'Order already processed'}), 400
    
    order.status = 'completed'
    db.session.commit()
    
    user = User.query.get(order.user_id)
    if add_vip(user.steam_id):
        return jsonify({'message': 'Order approved and VIP access granted'})
    else:
        return jsonify({'error': 'Error granting VIP access'}), 500 