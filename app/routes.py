from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Order, ServerStats, User
from app.utils import get_player_count, grant_vip_access
from config import Config
from functools import wraps

main = Blueprint('main', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Bu sayfaya erişim yetkiniz yok.')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@main.route('/')
def index():
    player_count = get_player_count()
    return render_template('index.html', stats={'player_count': player_count})

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
    if order.user_id != current_user.id and not current_user.is_admin:
        flash('Yetkisiz erişim')
        return redirect(url_for('main.index'))
    return render_template('order_status.html', order=order)

@main.route('/admin/orders')
@admin_required
def admin_orders():
    orders = Order.query.order_by(Order.created_at.desc()).all()
    return render_template('admin/orders.html', orders=orders)

@main.route('/admin/order/<int:order_id>/complete', methods=['POST'])
@admin_required
def complete_order(order_id):
    order = Order.query.get_or_404(order_id)
    
    if order.status == 'completed':
        flash('Bu sipariş zaten tamamlanmış.')
        return redirect(url_for('main.admin_orders'))
    
    # VIP yetkisi ver
    if grant_vip_access(order.steam_id):
        order.status = 'completed'
        order.payment_confirmed = True
        db.session.commit()
        flash('Sipariş tamamlandı ve VIP yetkileri verildi.')
    else:
        flash('VIP yetkileri verilirken bir hata oluştu. Lütfen manuel olarak kontrol edin.')
    
    return redirect(url_for('main.admin_orders'))

@main.route('/api/player-count')
def get_current_player_count():
    """API endpoint to get current player count"""
    count = get_player_count()
    return jsonify({'player_count': count}) 