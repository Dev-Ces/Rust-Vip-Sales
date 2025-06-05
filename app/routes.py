from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Order, ServerStats
import requests
from config import Config

main = Blueprint('main', __name__)

@main.route('/')
def index():
    stats = ServerStats.get_current_stats()
    return render_template('index.html', stats=stats)

@main.route('/shop')
@login_required
def shop():
    return render_template('shop.html')

@main.route('/cart')
@login_required
def cart():
    return render_template('cart.html')

@main.route('/create-order', methods=['POST'])
@login_required
def create_order():
    steam_id = request.form.get('steam_id')
    amount = float(request.form.get('amount'))
    
    # Validate Steam ID
    try:
        response = requests.get(f'http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={Config.STEAM_API_KEY}&steamids={steam_id}')
        if not response.json()['response']['players']:
            flash('Invalid Steam ID')
            return redirect(url_for('main.cart'))
    except:
        flash('Error validating Steam ID')
        return redirect(url_for('main.cart'))
    
    order = Order(
        user_id=current_user.id,
        steam_id=steam_id,
        amount=amount,
        payment_address=Config.CRYPTO_ADDRESS
    )
    
    db.session.add(order)
    db.session.commit()
    
    flash('Order created successfully!')
    return redirect(url_for('main.order_status', order_id=order.id))

@main.route('/order/<int:order_id>')
@login_required
def order_status(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id:
        flash('Unauthorized access')
        return redirect(url_for('main.index'))
    return render_template('order_status.html', order=order)

@main.route('/update-player-count', methods=['POST'])
def update_player_count():
    count = request.json.get('count', 0)
    stats = ServerStats()
    stats.player_count = count
    db.session.add(stats)
    db.session.commit()
    return jsonify({'success': True}) 