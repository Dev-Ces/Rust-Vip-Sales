import os
import subprocess
import sys

def install_requirements():
    """Install required packages to user's home directory"""
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--user', '-r', 'requirements.txt'])
        return True
    except subprocess.CalledProcessError:
        return False

def main():
    # İlk olarak requirements'ları yükle
    print("Installing requirements...")
    if not install_requirements():
        print("Error installing requirements!")
        sys.exit(1)

    # Python path'ine kullanıcının site-packages'ını ekle
    python_version = f"python{sys.version_info.major}.{sys.version_info.minor}"
    user_site_packages = os.path.expanduser(f"~/.local/lib/{python_version}/site-packages")
    sys.path.append(user_site_packages)

    # Şimdi uygulamayı başlat
    from app import create_app
    app = create_app()
    
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

if __name__ == '__main__':
    main() 