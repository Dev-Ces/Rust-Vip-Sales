from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Order, ServerStats
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
    amount = request.args.get('amount')
    package = request.args.get('package')
    if not amount or not package:
        flash('Lütfen önce bir paket seçin.')
        return redirect(url_for('main.shop'))
    return render_template('cart.html')

@main.route('/create-order', methods=['POST'])
@login_required
def create_order():
    steam_id = request.form.get('steam_id')
    steam_id_confirm = request.form.get('steam_id_confirm')
    amount = float(request.form.get('amount'))
    
    if not steam_id or not steam_id_confirm:
        flash('Lütfen Steam ID\'nizi girin')
        return redirect(url_for('main.cart'))
    
    if steam_id != steam_id_confirm:
        flash('Steam ID\'ler eşleşmiyor. Lütfen kontrol edin.')
        return redirect(url_for('main.cart'))
    
    if not steam_id.isdigit() or len(steam_id) != 17:
        flash('Geçerli bir Steam ID girin (17 haneli numara)')
        return redirect(url_for('main.cart'))
    
    order = Order(
        user_id=current_user.id,
        steam_id=steam_id,
        amount=amount,
        payment_address=Config.CRYPTO_ADDRESS
    )
    
    db.session.add(order)
    db.session.commit()
    
    flash('Siparişiniz başarıyla oluşturuldu!')
    return redirect(url_for('main.order_status', order_id=order.id))

@main.route('/order/<int:order_id>')
@login_required
def order_status(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id:
        flash('Yetkisiz erişim')
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