/**
 * Rust VIP Satış - Ana JavaScript Dosyası
 */

document.addEventListener('DOMContentLoaded', function() {
    // Sayfa yüklendiğinde çalışacak kodlar
    initTooltips();
    initCopyButtons();
    initFormValidation();
    
    // Sayfa geçişlerinde animasyon
    animatePageTransitions();
});

/**
 * Bootstrap tooltip'lerini başlat
 */
function initTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Kopyalama butonlarını başlat
 */
function initCopyButtons() {
    const copyButtons = document.querySelectorAll('.copy-btn');
    
    if (copyButtons.length > 0) {
        copyButtons.forEach(button => {
            button.addEventListener('click', function() {
                const textToCopy = this.getAttribute('data-clipboard-text');
                navigator.clipboard.writeText(textToCopy).then(() => {
                    // Kopyalama başarılı olduğunda buton metnini değiştir
                    const originalHTML = this.innerHTML;
                    this.innerHTML = '<i class="fas fa-check"></i>';
                    
                    // 2 saniye sonra orijinal metni geri yükle
                    setTimeout(() => {
                        this.innerHTML = originalHTML;
                    }, 2000);
                });
            });
        });
    }
}

/**
 * Form doğrulama işlemlerini başlat
 */
function initFormValidation() {
    const forms = document.querySelectorAll('.needs-validation');
    
    if (forms.length > 0) {
        forms.forEach(form => {
            form.addEventListener('submit', function(event) {
                if (!form.checkValidity()) {
                    event.preventDefault();
                    event.stopPropagation();
                }
                
                form.classList.add('was-validated');
            }, false);
        });
    }
    
    // Steam ID doğrulama
    const steamIdInputs = document.querySelectorAll('input[name="steam_id"]');
    if (steamIdInputs.length > 0) {
        steamIdInputs.forEach(input => {
            input.addEventListener('blur', function() {
                validateSteamId(this);
            });
        });
    }
}

/**
 * Steam ID doğrulama
 */
function validateSteamId(input) {
    const steamId = input.value.trim();
    const feedback = input.nextElementSibling;
    
    // Basit bir doğrulama - gerçek uygulamada daha kapsamlı olabilir
    if (steamId.length < 5) {
        input.classList.add('is-invalid');
        input.classList.remove('is-valid');
        if (feedback) {
            feedback.textContent = 'Geçerli bir Steam ID girin.';
            feedback.classList.add('invalid-feedback');
        }
        return false;
    } else {
        input.classList.remove('is-invalid');
        input.classList.add('is-valid');
        if (feedback) {
            feedback.textContent = 'Steam ID geçerli görünüyor.';
            feedback.classList.add('valid-feedback');
        }
        return true;
    }
}

/**
 * Sayfa geçişlerinde animasyon
 */
function animatePageTransitions() {
    // Sayfa içeriğine fade-in animasyonu ekle
    const content = document.querySelector('.container');
    if (content) {
        content.classList.add('fade-in');
    }
}

/**
 * Sayfa yüklenme göstergesi
 */
window.addEventListener('load', function() {
    // Sayfa tamamen yüklendiğinde yükleme göstergesini gizle
    const loader = document.querySelector('.page-loader');
    if (loader) {
        loader.style.display = 'none';
    }
});