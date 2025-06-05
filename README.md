# Rust VIP Sales System

Modern ve kullanıcı dostu Rust sunucu VIP satış sistemi. Flask ile geliştirilmiş, RCON entegrasyonu ve otomatik VIP yönetimi içerir.

## Özellikler

### 🎮 Oyun Sunucu Entegrasyonu
- **RCON Bağlantısı**: Rust sunucusu ile doğrudan iletişim
- **Otomatik VIP Ekleme**: Sipariş onaylandığında otomatik `chat user add steamid vip`
- **Otomatik VIP Kaldırma**: Süre dolduğunda otomatik `chat user remove steamid vip`
- **Sunucu Durumu**: Gerçek zamanlı sunucu bilgileri

### 💰 Ödeme Sistemi
- **Kripto Para Desteği**: Bitcoin, Ethereum, Litecoin, USDT
- **Güvenli Ödeme**: Blockchain tabanlı doğrulama
- **Otomatik Sipariş Takibi**: Ödeme durumu kontrolü

### 👤 Kullanıcı Yönetimi
- **Kayıt/Giriş Sistemi**: Güvenli kullanıcı hesapları
- **Sipariş Geçmişi**: Kullanıcıların tüm siparişlerini görüntüleme
- **VIP Durumu**: Aktif VIP'lerin takibi

### 🛠️ Admin Paneli
- **Sipariş Yönetimi**: Siparişleri onaylama/iptal etme
- **VIP Paket Yönetimi**: Paket ekleme/düzenleme/silme
- **RCON Ayarları**: Sunucu bağlantı ayarları
- **İstatistikler**: Satış ve kullanıcı istatistikleri
- **Sistem Logları**: Detaylı aktivite kayıtları

### 🎨 Modern Tasarım
- **Rust Teması**: Oyun atmosferine uygun tasarım
- **Responsive**: Mobil ve masaüstü uyumlu
- **Animasyonlar**: Smooth geçişler ve efektler
- **Dark Mode**: Göz yormayan karanlık tema

## Kurulum

### Gereksinimler
- Python 3.8+
- Rust sunucusu (RCON etkin)
- SQLite/PostgreSQL/MySQL

### Adımlar

1. **Projeyi klonlayın**
```bash
git clone <repository-url>
cd rust-vip-sales
```

2. **Sanal ortam oluşturun**
```bash
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
```

3. **Bağımlılıkları yükleyin**
```bash
pip install -r requirements.txt
```

4. **Çevre değişkenlerini ayarlayın**
`.env` dosyası oluşturun:
```env
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///vip_sales.db
RCON_HOST=your-rust-server-ip
RCON_PORT=28016
RCON_PASSWORD=your-rcon-password
BTC_ADDRESS=your-bitcoin-address
ETH_ADDRESS=your-ethereum-address
LTC_ADDRESS=your-litecoin-address
USDT_ADDRESS=your-usdt-address
```

5. **Uygulamayı başlatın**
```bash
python app.py
```

## Kullanım

### İlk Kurulum
1. Uygulama başlatıldığında otomatik olarak admin kullanıcısı oluşturulur
2. Admin paneline `/admin` adresinden erişin
3. RCON ayarlarını yapılandırın
4. Kripto para adreslerini ekleyin
5. VIP paketlerini oluşturun

### Admin Paneli
- **Dashboard**: `/admin` - Genel istatistikler ve hızlı erişim
- **Siparişler**: `/admin/orders` - Sipariş yönetimi
- **VIP Paketleri**: `/admin/vip-packages` - Paket yönetimi
- **Ayarlar**: `/admin/settings` - Sistem ayarları

### API Endpoints
- `POST /api/test-rcon` - RCON bağlantısı test
- `POST /api/validate-payment` - Ödeme doğrulama

## Yapılandırma

### RCON Ayarları
```python
RCON_HOST = "your-server-ip"
RCON_PORT = 28016
RCON_PASSWORD = "your-rcon-password"
```

### VIP Komutları
- **VIP Ekleme**: `chat user add {steam_id} vip`
- **VIP Kaldırma**: `chat user remove {steam_id} vip`

### Ödeme Adresleri
Admin panelinden kripto para adreslerini güncelleyebilirsiniz:
- Bitcoin (BTC)
- Ethereum (ETH)
- Litecoin (LTC)
- Tether (USDT)

## Güvenlik

- **Şifre Hashleme**: Werkzeug ile güvenli şifre saklama
- **Session Yönetimi**: Flask-Login ile güvenli oturum
- **CSRF Koruması**: Form güvenliği
- **IP Kısıtlama**: Admin paneli için IP kontrolü
- **Rate Limiting**: API isteklerinde hız sınırı

## Veritabanı

### Modeller
- **User**: Kullanıcı bilgileri
- **VipPackage**: VIP paket tanımları
- **Order**: Sipariş kayıtları
- **Settings**: Sistem ayarları
- **ActivityLog**: Aktivite logları
- **SystemLog**: Sistem logları

## Arka Plan Görevleri

- **VIP Süresi Kontrolü**: Her 5 dakikada bir süresi dolan VIP'leri kaldırır
- **Bekleyen Sipariş Kontrolü**: Ödeme durumunu kontrol eder
- **Log Temizleme**: Eski logları temizler

## Sorun Giderme

### RCON Bağlantı Sorunları
1. Sunucu IP ve port kontrolü
2. RCON şifre doğrulaması
3. Firewall ayarları
4. Sunucu RCON etkinleştirme

### Veritabanı Sorunları
1. Dosya izinleri kontrolü
2. Disk alanı kontrolü
3. Veritabanı bağlantı ayarları

### Ödeme Sorunları
1. Kripto adres doğrulaması
2. Blockchain bağlantısı
3. API anahtarları

## Katkıda Bulunma

1. Fork yapın
2. Feature branch oluşturun (`git checkout -b feature/amazing-feature`)
3. Commit yapın (`git commit -m 'Add amazing feature'`)
4. Push yapın (`git push origin feature/amazing-feature`)
5. Pull Request oluşturun

## Lisans

Bu proje MIT lisansı altında lisanslanmıştır.

## Destek

Sorularınız için:
- GitHub Issues
- Discord: [Sunucu Linki]
- E-posta: support@rustvip.com

---

**Not**: Bu sistem Rust sunucuları için özel olarak tasarlanmıştır. Diğer oyun sunucuları için RCON komutlarının uyarlanması gerekebilir.