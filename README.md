# Rust VIP Satış Uygulaması

Bu uygulama, Rust sunucuları için VIP satış hizmeti sunan bir Flask web uygulamasıdır. Pterodactyl panel üzerinde kolayca kurulabilir ve çalıştırılabilir.

## Özellikler

- Kullanıcı hesabı oluşturma ve giriş yapma
- Ana sayfada aktif oyuncu sayısı gösterimi
- VIP paket satın alma sistemi
- Steam ID doğrulama
- Kripto para ile ödeme seçenekleri (Bitcoin, Ethereum, Litecoin)
- Sipariş takip sistemi
- Admin paneli ile sipariş yönetimi
- RCON entegrasyonu ile otomatik VIP grup atama

## Kurulum

### Pterodactyl Panel Üzerinden Kurulum

1. Pterodactyl panel üzerinde yeni bir sunucu oluşturun
2. Egg olarak `rust_vip_sales.json` dosyasını içe aktarın
3. Sunucuyu kurun ve başlatın
4. Çevre değişkenlerini (RCON bilgileri, admin bilgileri, kripto para adresleri) yapılandırın

### Manuel Kurulum

1. Gereksinimleri yükleyin:
   ```
   pip install -r requirements.txt
   ```

2. Çevre değişkenlerini ayarlayın (`.env` dosyası oluşturun):
   ```
   FLASK_APP=app.py
   FLASK_ENV=production
   SECRET_KEY=your_secret_key
   RCON_HOST=your_rust_server_ip
   RCON_PORT=28016
   RCON_PASSWORD=your_rcon_password
   ADMIN_USERNAME=admin
   ADMIN_PASSWORD=your_admin_password
   BTC_ADDRESS=your_bitcoin_address
   ETH_ADDRESS=your_ethereum_address
   LTC_ADDRESS=your_litecoin_address
   ```

3. Uygulamayı başlatın:
   ```
   flask run
   ```
   veya üretim ortamı için:
   ```
   gunicorn app:app -b 0.0.0.0:5000 --workers=2 --threads=4
   ```

## Kullanım

### Kullanıcı Arayüzü

- **Ana Sayfa**: Aktif oyuncu sayısını ve VIP satın alma seçeneklerini görüntüler
- **VIP Satın Al**: Farklı VIP paketlerini görüntüler ve sepete ekleme imkanı sunar
- **Sepet**: Steam ID girişi ve ödeme yöntemi seçimi için form sunar
- **Sipariş Onayı**: Ödeme bilgilerini ve sipariş detaylarını gösterir
- **Siparişlerim**: Kullanıcının geçmiş siparişlerini listeler

### Admin Paneli

- **Gösterge Paneli**: Genel istatistikleri ve son siparişleri gösterir
- **Siparişler**: Tüm siparişleri görüntüleme, onaylama veya iptal etme imkanı sunar
- **RCON Durumu**: Rust sunucusu ile bağlantı durumunu gösterir

## Güvenlik

- Şifreler bcrypt ile hashlenir
- Flask-Login ile oturum yönetimi
- CSRF koruması
- Güvenli form doğrulama

## Lisans

Bu proje MIT lisansı altında lisanslanmıştır. Daha fazla bilgi için `LICENSE` dosyasına bakın.

## İletişim

Herhangi bir soru veya geri bildirim için lütfen iletişime geçin.