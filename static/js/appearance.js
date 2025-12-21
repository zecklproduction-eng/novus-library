// Appearance Settings JavaScript
// This file handles all the functionality for the appearance modal

class AppearanceSettings {
  constructor() {
    this.settings = {
      theme: 'dark',
      fontSize: 'medium',
      density: 'comfortable',
      accentColor: 'cyan',
      preferences: {
        smoothScroll: false,
        pageTransitions: true,
        animations: true
      }
    };
    this.init();
  }

  init() {
    this.loadSettings();
    this.bindEvents();
    this.updateUI();
  }

  bindEvents() {
    // Modal controls
    window.openAppearanceModal = () => this.openModal();
    window.closeAppearanceModal = () => this.closeModal();
    
    // Use event delegation for data-attribute-based handlers
    document.addEventListener('click', (e) => {
      const element = e.target.closest('[data-action]');
      if (!element) return;
      
      const action = element.dataset.action;
      const value = element.dataset.theme || element.dataset.size || element.dataset.density || element.dataset.color;
      
      switch (action) {
        case 'selectTheme':
          this.selectTheme(value);
          break;
        case 'selectFontSize':
          this.selectFontSize(value);
          break;
        case 'selectDensity':
          this.selectDensity(value);
          break;
        case 'selectAccentColor':
          this.selectAccentColor(value);
          break;
        case 'resetToDefaults':
          this.resetToDefaults();
          break;
        case 'closeAppearanceModal':
          this.closeModal();
          break;
        case 'saveAppearanceSettings':
          this.saveSettings();
          break;
      }
    });
    
    // Handle checkbox changes for preferences
    document.addEventListener('change', (e) => {
      const element = e.target;
      if (!element.dataset.action) return;
      
      const action = element.dataset.action;
      if (action.startsWith('toggle')) {
        const preference = action.replace('toggle', '').replace(/^./, str => str.toLowerCase());
        this.togglePreference(preference, element);
      }
    });
    
    // Close modal when clicking outside
    document.addEventListener('click', (e) => {
      const modal = document.getElementById('appearanceModal');
      if (e.target === modal?.querySelector('.appearance-backdrop')) {
        this.closeModal();
      }
    });

    // Close modal with Escape key
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        this.closeModal();
      }
    });
  }

  openModal() {
    const modal = document.getElementById('appearanceModal');
    if (modal) {
      modal.classList.add('show');
      document.body.classList.add('no-scroll');
      this.loadSettings();
      this.updateUI();
    }
  }

  closeModal() {
    const modal = document.getElementById('appearanceModal');
    if (modal) {
      modal.classList.remove('show');
      document.body.classList.remove('no-scroll');
    }
  }

  selectTheme(theme) {
    this.settings.theme = theme;
    this.updateTheme();
    this.updateUI();
    this.showToast(`Theme changed to ${theme}`);
  }

  selectFontSize(size) {
    this.settings.fontSize = size;
    this.updateFontSize();
    this.updateUI();
    this.showToast(`Font size changed to ${size}`);
  }

  selectDensity(density) {
    this.settings.density = density;
    this.updateDensity();
    this.updateUI();
    this.showToast(`Layout density changed to ${density}`);
  }

  selectAccentColor(color) {
    this.settings.accentColor = color;
    this.updateAccentColor();
    this.updateUI();
    this.showToast(`Accent color changed to ${color}`);
  }

  togglePreference(preference, checkbox) {
    this.settings.preferences[preference] = checkbox.checked;
    this.updatePreferences();
    this.updateUI();
    this.showToast(`${preference.replace(/([A-Z])/g, ' $1').toLowerCase()} ${checkbox.checked ? 'enabled' : 'disabled'}`);
  }

  resetToDefaults() {
    if (confirm('Are you sure you want to reset all appearance settings to defaults?')) {
      this.settings = {
        theme: 'dark',
        fontSize: 'medium',
        density: 'comfortable',
        accentColor: 'cyan',
        preferences: {
          smoothScroll: false,
          pageTransitions: true,
          animations: true
        }
      };
      this.applyAllSettings();
      this.updateUI();
      this.showToast('Settings reset to defaults');
    }
  }

  saveSettings() {
    this.saveToLocalStorage();
    this.showToast('Appearance settings saved successfully!', 'success');
    
    // Auto close modal after save
    setTimeout(() => {
      this.closeModal();
    }, 1500);
  }

  loadSettings() {
    const saved = localStorage.getItem('novus-appearance-settings');
    if (saved) {
      try {
        const parsedSettings = JSON.parse(saved);
        this.settings = { ...this.settings, ...parsedSettings };
      } catch (e) {
        console.warn('Failed to parse saved appearance settings:', e);
      }
    }
    this.applyAllSettings();
  }

  saveToLocalStorage() {
    try {
      localStorage.setItem('novus-appearance-settings', JSON.stringify(this.settings));
    } catch (e) {
      console.warn('Failed to save appearance settings:', e);
    }
  }

  updateUI() {
    // Update theme selection
    document.querySelectorAll('.theme-option').forEach(option => {
      option.classList.toggle('active', option.dataset.theme === this.settings.theme);
    });

    // Update font size selection
    document.querySelectorAll('.font-size-btn').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.size === this.settings.fontSize);
    });

    // Update density selection
    document.querySelectorAll('.density-btn').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.density === this.settings.density);
    });

    // Update accent color selection
    document.querySelectorAll('.accent-option').forEach(option => {
      option.classList.toggle('active', option.dataset.color === this.settings.accentColor);
    });

    // Update preference toggles
    const toggleSmoothScroll = document.getElementById('toggleSmoothScroll');
    const togglePageTransitions = document.getElementById('togglePageTransitions');
    const toggleAnimations = document.getElementById('toggleAnimations');

    if (toggleSmoothScroll) toggleSmoothScroll.checked = this.settings.preferences.smoothScroll;
    if (togglePageTransitions) togglePageTransitions.checked = this.settings.preferences.pageTransitions;
    if (toggleAnimations) toggleAnimations.checked = this.settings.preferences.animations;
  }

  updateTheme() {
    const body = document.body;
    
    // Remove existing theme classes
    body.classList.remove('theme-dark', 'theme-light', 'theme-blue', 'theme-purple');
    
    // Add new theme class
    body.classList.add(`theme-${this.settings.theme}`);
    
    // Apply theme-specific CSS custom properties
    this.applyThemeColors();
  }

  applyThemeColors() {
    const root = document.documentElement;
    
    const themeColors = {
      dark: {
        '--bg-main': '#1f1f1f',
        '--bg-card': '#2a2a2a',
        '--text-primary': '#e0e0e0'
      },
      light: {
        '--bg-main': '#ffffff',
        '--bg-card': '#f8f9fa',
        '--text-primary': '#212529'
      },
      blue: {
        '--bg-main': '#0a1628',
        '--bg-card': '#1e3a8a',
        '--text-primary': '#e0e7ff'
      },
      purple: {
        '--bg-main': '#2d1b69',
        '--bg-card': '#581c87',
        '--text-primary': '#f3e8ff'
      }
    };

    const colors = themeColors[this.settings.theme];
    if (colors) {
      Object.entries(colors).forEach(([property, value]) => {
        root.style.setProperty(property, value);
      });
    }
  }

  updateFontSize() {
    const body = document.body;
    
    // Remove existing font size classes
    body.classList.remove('font-small', 'font-medium', 'font-large', 'font-xlarge');
    
    // Add new font size class
    body.classList.add(`font-${this.settings.fontSize}`);
    
    // Apply font size via CSS custom properties
    const root = document.documentElement;
    const fontSizes = {
      small: '14px',
      medium: '16px',
      large: '18px',
      xlarge: '20px'
    };
    
    root.style.setProperty('--base-font-size', fontSizes[this.settings.fontSize]);
    body.style.fontSize = fontSizes[this.settings.fontSize];
  }

  updateDensity() {
    const body = document.body;
    
    // Remove existing density classes
    body.classList.remove('density-compact', 'density-comfortable', 'density-spacious');
    
    // Add new density class
    body.classList.add(`density-${this.settings.density}`);
    
    // Apply density via CSS custom properties
    const root = document.documentElement;
    const densities = {
      compact: '0.8',
      comfortable: '1.0',
      spacious: '1.2'
    };
    
    root.style.setProperty('--content-density', densities[this.settings.density]);
  }

  updateAccentColor() {
    const root = document.documentElement;
    
    // Apply accent color via CSS custom properties
    const accentColors = {
      cyan: '#00d4ff',
      purple: '#667eea',
      pink: '#ff9a9e',
      green: '#56ab2f',
      orange: '#ff6b35'
    };
    
    root.style.setProperty('--neon-blue', accentColors[this.settings.accentColor]);
    root.style.setProperty('--accent-color', accentColors[this.settings.accentColor]);
  }

  updatePreferences() {
    const body = document.body;
    
    // Smooth scrolling
    if (this.settings.preferences.smoothScroll) {
      body.style.scrollBehavior = 'smooth';
    } else {
      body.style.scrollBehavior = 'auto';
    }
    
    // Page transitions
    if (this.settings.preferences.pageTransitions) {
      body.classList.remove('no-transitions');
    } else {
      body.classList.add('no-transitions');
    }
    
    // Animations
    if (this.settings.preferences.animations) {
      body.classList.remove('no-animations');
    } else {
      body.classList.add('no-animations');
    }
  }

  applyAllSettings() {
    this.updateTheme();
    this.updateFontSize();
    this.updateDensity();
    this.updateAccentColor();
    this.updatePreferences();
  }

  showToast(message, type = 'info') {
    // Remove existing toasts
    const existingToast = document.querySelector('.appearance-toast');
    if (existingToast) {
      existingToast.remove();
    }

    // Create toast element
    const toast = document.createElement('div');
    toast.className = `appearance-toast toast-${type}`;
    toast.innerHTML = `
      <div class="toast-content">
        <i class="fas ${type === 'success' ? 'fa-check-circle' : 'fa-info-circle'}"></i>
        <span>${message}</span>
      </div>
    `;

    // Add toast styles if not already present
    if (!document.querySelector('#appearance-toast-styles')) {
      const styles = document.createElement('style');
      styles.id = 'appearance-toast-styles';
      styles.textContent = `
        .appearance-toast {
          position: fixed;
          top: 20px;
          right: 20px;
          background: rgba(0, 212, 255, 0.9);
          color: white;
          padding: 12px 20px;
          border-radius: 8px;
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
          z-index: 10000;
          animation: toastSlideIn 0.3s ease-out;
          backdrop-filter: blur(10px);
        }
        
        .toast-success {
          background: rgba(34, 197, 94, 0.9);
        }
        
        .toast-content {
          display: flex;
          align-items: center;
          gap: 8px;
          font-weight: 500;
        }
        
        .toast-content i {
          font-size: 16px;
        }
        
        @keyframes toastSlideIn {
          from {
            transform: translateX(100%);
            opacity: 0;
          }
          to {
            transform: translateX(0);
            opacity: 1;
          }
        }
      `;
      document.head.appendChild(styles);
    }

    // Add toast to document
    document.body.appendChild(toast);

    // Remove toast after 3 seconds
    setTimeout(() => {
      if (toast.parentNode) {
        toast.style.animation = 'toastSlideIn 0.3s ease-out reverse';
        setTimeout(() => {
          if (toast.parentNode) {
            toast.remove();
          }
        }, 300);
      }
    }, 3000);
  }
}

// Font size CSS classes
const fontSizeStyles = document.createElement('style');
fontSizeStyles.textContent = `
  .font-small { font-size: 14px; }
  .font-medium { font-size: 16px; }
  .font-large { font-size: 18px; }
  .font-xlarge { font-size: 20px; }
  
  .density-compact { --content-density: 0.8; }
  .density-comfortable { --content-density: 1.0; }
  .density-spacious { --content-density: 1.2; }
  
  /* Apply density to spacing */
  .density-compact .section-container { padding: 15px; }
  .density-comfortable .section-container { padding: 25px; }
  .density-spacious .section-container { padding: 35px; }
  
  .density-compact .main-content { margin-left: 70px; }
  .density-comfortable .main-content { margin-left: 90px; }
  .density-spacious .main-content { margin-left: 110px; }
  
  /* Disable transitions and animations when disabled */
  .no-transitions * {
    transition: none !important;
  }
  
  .no-animations * {
    animation: none !important;
  }
`;
document.head.appendChild(fontSizeStyles);

// Initialize appearance settings when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  new AppearanceSettings();
});

// Make AppearanceSettings globally available for debugging
window.AppearanceSettings = AppearanceSettings;
