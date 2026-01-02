/**
 * Bundles Page JavaScript
 * Handles bundle selection, preview, and apply functionality
 */

let currentBundle = null;

/**
 * Select a bundle and show its details
 */
function selectBundle(cardElement) {
    // Remove active from all cards
    document.querySelectorAll('.bundle-card').forEach(c => c.classList.remove('active'));
    
    // Add active to selected card
    cardElement.classList.add('active');
    
    // Parse bundle data
    const bundleData = JSON.parse(cardElement.dataset.bundle);
    currentBundle = bundleData;
    
    // Show details panel
    showBundleDetails(bundleData);
}

/**
 * Show bundle details in the right panel
 */
function showBundleDetails(bundle) {
    const detailsPanel = document.getElementById('bundleDetails');
    const template = document.getElementById('bundleDetailsTemplate');
    
    // Clone template content
    const content = template.content.cloneNode(true);
    
    // Fill in bundle data
    content.querySelector('.bundle-detail-name').textContent = bundle.name;
    content.querySelector('.bundle-detail-description').textContent = bundle.description;
    
    const colors = bundle.theme.colors || ['#0d1117', '#161b22', '#21262d', '#00d4ff', '#58a6ff', '#c9a0dc'];
    const primaryAccent = colors[3] || '#00d4ff';
    const secondaryAccent = colors[4] || '#58a6ff';
    const tertiaryAccent = colors[5] || '#c9a0dc';

    // Helper to render media into a slot
    const renderMedia = (slotId, path, fallbackIcon) => {
        const slot = content.querySelector(`#${slotId}`);
        if (!slot) return;
        
        if (!path) return; // Keep fallback mock if no path

        const fullPath = path.startsWith('/') ? path : '/static/' + path;
        const isVideo = fullPath.match(/\.(mp4|webm|ogg|mov)$/i);
        
        slot.innerHTML = '';
        if (isVideo) {
            const video = document.createElement('video');
            video.src = fullPath;
            video.muted = true;
            video.loop = true;
            video.playsInline = true;
            video.className = 'visual-media';
            // Play on hover for better performance
            video.onmouseover = () => video.play();
            video.onmouseout = () => { video.pause(); video.currentTime = 0; };
            
            const overlay = document.createElement('div');
            overlay.className = 'play-hint-overlay';
            overlay.innerHTML = '<i class="fas fa-play"></i>';
            
            slot.appendChild(video);
            slot.appendChild(overlay);
        } else {
            const img = document.createElement('img');
            img.src = fullPath;
            img.className = 'visual-media';
            slot.appendChild(img);
        }
    };

    // Render Real Media
    const theme = bundle.theme || {};
    renderMedia('detail-banner-slot', theme.banner_path);
    renderMedia('detail-manga-slot', theme.manga_path);
    renderMedia('detail-login-slot', theme.login_animation);
    renderMedia('detail-logout-slot', theme.logout_animation);

    // Color swatches (mini)
    const colorsContainer = content.querySelector('.bundle-preview-colors');
    colorsContainer.innerHTML = colors.slice(0, 4).map(color => 
        `<div class="color-swatch" style="background: ${color}"></div>`
    ).join('');
    
    // Typography preview with accent color
    const typographyPreview = content.querySelector('.bundle-preview-typography');
    typographyPreview.style.color = primaryAccent;
    
    // Includes list
    const includesList = content.querySelector('.bundle-includes-list');
    includesList.innerHTML = (bundle.includes || []).map(item => 
        `<li><i class="fas fa-check"></i> ${item}</li>`
    ).join('');
    
    // Edit button (admin only)
    const editBtn = content.querySelector('#editBundleBtn');
    if (editBtn) {
        editBtn.href = `/admin/bundles/${bundle.id}/edit`;
    }
    
    // Plan Enforcement
    const planRank = { 'basic': 0, 'plus': 1, 'premium': 2 };
    const userPlanRaw = (typeof USER_PLAN !== 'undefined' ? USER_PLAN : 'basic').toLowerCase();
    const userRank = planRank[userPlanRaw] || 0;
    const bundlePlanRaw = (bundle.min_plan || 'basic').toLowerCase();
    const bundleRank = planRank[bundlePlanRaw] || 0;
    const isLocked = userRank < bundleRank;

    // Apply Button handling
    const applyBtn = content.querySelector('.btn-apply');
    if (isLocked) {
        applyBtn.disabled = true;
        applyBtn.innerHTML = `<i class="fas fa-lock"></i> ${bundlePlanRaw.toUpperCase()} Required`;
        applyBtn.classList.add('locked-btn');
        applyBtn.onclick = () => showToast(`Upgrade to ${bundlePlanRaw.toUpperCase()} to unlock this bundle!`, 'error');
    }

    // Clear and append
    detailsPanel.innerHTML = '';
    detailsPanel.appendChild(content);

    // After appending, if locked, we might want to add a special overlay or banner
    if (isLocked) {
        const header = detailsPanel.querySelector('.bundle-detail-header');
        const lockBanner = document.createElement('div');
        lockBanner.className = 'lock-banner';
        lockBanner.innerHTML = `
            <i class="fas fa-exclamation-triangle"></i>
            <span>This bundle requires a <strong>${bundlePlanRaw.toUpperCase()}</strong> subscription.</span>
        `;
        header.after(lockBanner);
    }
}

/**
 * Apply the currently selected bundle
 */
function applyCurrentBundle() {
    if (!currentBundle) {
        showToast('No bundle selected', 'error');
        return;
    }
    
    applyBundle(currentBundle);
}

/**
 * Apply a bundle's settings
 */
function applyBundle(bundle) {
    const theme = bundle.theme || {};
    
    // Save bundle slug to localStorage
    localStorage.setItem('selectedBundle', bundle.slug);
    
    // Save theme settings (compatible with appearance.js)
    const appearanceSettings = {
        theme: theme.theme || 'dark',
        accentColor: theme.accentColor || 'cyan',
        fontSize: theme.fontSize || 'medium',
        density: theme.density || 'comfortable',
        smoothScroll: theme.smoothScroll !== false,
        pageTransitions: theme.pageTransitions !== false,
        animations: theme.animations !== false,
        uiEffects: theme.uiEffects !== false,
        specialEffects: theme.specialEffects !== false
    };
    
    localStorage.setItem('novus-appearance-settings', JSON.stringify(appearanceSettings));
    
    // Explicitly merge custom animation paths into the theme object if they exist at bundle top-level
    const finalTheme = {
        ...theme,
        banner_path: bundle.banner_path || theme.banner_path,
        manga_path: bundle.manga_path || theme.manga_path,
        login_animation: bundle.login_animation || theme.login_animation,
        logout_animation: bundle.logout_animation || theme.logout_animation
    };
    
    localStorage.setItem('appThemeSettings', JSON.stringify(finalTheme));
    
    // Apply theme immediately
    applyThemeToDocument(theme);
    
    // Update banner preset
    if (bundle.banner_preset && bundle.banner_preset !== 'none') {
        document.body.classList.remove('banner-glow-strip', 'banner-neon-pulse', 'banner-warm-gradient', 'banner-subtle-shadow');
        document.body.classList.add('banner-' + bundle.banner_preset);
    }
    
    // Mark as applied in UI
    document.querySelectorAll('.bundle-card').forEach(c => {
        c.classList.remove('applied');
        c.querySelector('.bundle-applied-badge').style.display = 'none';
    });
    
    const appliedCard = document.querySelector(`[data-bundle-id="${bundle.id}"]`);
    if (appliedCard) {
        appliedCard.classList.add('applied');
        appliedCard.querySelector('.bundle-applied-badge').style.display = 'inline-block';
    }
    
    // Show success toast
    showToast('Bundle applied successfully!', 'success');
}

/**
 * Apply theme settings to the document
 */
function applyThemeToDocument(theme) {
    const body = document.body;
    
    // Remove existing theme classes
    body.classList.remove(
        'theme-dark', 'theme-light', 'theme-blue', 'theme-purple',
        'theme-midnight', 'theme-forest', 'theme-sunset', 'theme-nebula',
        'theme-angelic', 'theme-demonic'
    );
    
    // Add new theme class
    if (theme.theme) {
        body.classList.add('theme-' + theme.theme);
    }
    
    // Apply accent color via CSS variable
    const accentColors = {
        cyan: { primary: '#00d4ff', secondary: '#0090ff' },
        purple: { primary: '#667eea', secondary: '#764ba2' },
        pink: { primary: '#ff9a9e', secondary: '#fecfef' },
        green: { primary: '#56ab2f', secondary: '#a8e6cf' },
        orange: { primary: '#ff6b35', secondary: '#f7931e' },
        emerald: { primary: '#10b981', secondary: '#059669' },
        ruby: { primary: '#ef4444', secondary: '#b91c1c' },
        amber: { primary: '#f59e0b', secondary: '#d97706' },
        indigo: { primary: '#6366f1', secondary: '#4338ca' }
    };
    
    const accent = accentColors[theme.accentColor] || accentColors.cyan;
    document.documentElement.style.setProperty('--neon-blue', accent.primary);
    document.documentElement.style.setProperty('--accent-primary', accent.primary);
    document.documentElement.style.setProperty('--accent-secondary', accent.secondary);
    
    // Apply animation settings
    if (theme.animations === false) {
        body.classList.add('no-animations');
    } else {
        body.classList.remove('no-animations');
    }
    
    if (theme.pageTransitions === false) {
        body.classList.add('no-transitions');
    } else {
        body.classList.remove('no-transitions');
    }
}

/**
 * Clear bundle selection
 */
function clearBundleSelection() {
    document.querySelectorAll('.bundle-card').forEach(c => c.classList.remove('active'));
    currentBundle = null;
    
    const detailsPanel = document.getElementById('bundleDetails');
    detailsPanel.innerHTML = `
        <div class="bundle-empty-state">
            <i class="fas fa-box-open"></i>
            <p>Select a bundle to see details</p>
        </div>
    `;
}

/**
 * Filter bundles by search query
 */
function filterBundles(query) {
    const cards = document.querySelectorAll('.bundle-card');
    const lowerQuery = query.toLowerCase().trim();
    
    cards.forEach(card => {
        const bundle = JSON.parse(card.dataset.bundle);
        const searchText = (bundle.name + ' ' + bundle.description).toLowerCase();
        
        if (lowerQuery === '' || searchText.includes(lowerQuery)) {
            card.style.display = '';
        } else {
            card.style.display = 'none';
        }
    });
}

/**
 * Show toast notification
 */
function showToast(message, type = 'success') {
    const toast = document.getElementById('bundleToast');
    const icon = toast.querySelector('i');
    const text = toast.querySelector('span');
    
    // Update content
    text.textContent = message;
    
    // Update icon based on type
    icon.className = type === 'success' ? 'fas fa-check-circle' : 'fas fa-exclamation-circle';
    toast.className = 'bundle-toast ' + type;
    
    // Show toast
    toast.classList.add('show');
    
    // Hide after 3 seconds
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}
