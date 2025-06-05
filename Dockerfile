FROM python:3.9-slim

WORKDIR /app

# Gerekli paketleri yükle
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Uygulama dosyalarını kopyala
COPY . /app/

# Gereksinimleri yükle
RUN pip install --no-cache-dir -r requirements.txt

# Çalışma zamanı yapılandırması
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# Port yapılandırması
EXPOSE 5000

# Uygulamayı başlat
CMD ["gunicorn", "app:app", "-b", "0.0.0.0:5000", "--workers=2", "--threads=4"]