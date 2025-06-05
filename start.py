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

    # Add the current directory to Python path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
        print(f"Added {current_dir} to Python path")
    
    print("Python path:", sys.path)
    print("Current directory:", os.getcwd())
    print("Directory contents:", os.listdir())

    try:
        # Şimdi uygulamayı başlat
        from app import create_app
        app = create_app()
        
        port = int(os.environ.get('PORT', 8080))
        app.run(host='0.0.0.0', port=port)
    except Exception as e:
        print(f"Error starting app: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main() 