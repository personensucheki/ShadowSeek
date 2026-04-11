// ShadowSeek Feature-Gating & Billing UI
// Markiert und deaktiviert gesperrte Features/Plattformen im Frontend

function fetchEntitlements(userId, cb) {
  fetch(`/api/entitlements/${userId}`)
    .then(r => r.json())
    .then(cb)
    .catch(() => cb(null));
}

function applyFeatureGating(entitlements) {
  if (!entitlements) return;
  // Features
  document.querySelectorAll('[data-feature]').forEach(el => {
    const feat = el.getAttribute('data-feature');
    if (!entitlements.ui_modules || !entitlements.ui_modules.includes(feat)) {
      el.classList.add('feature-locked');
      el.setAttribute('disabled', 'disabled');
      el.setAttribute('title', 'Upgrade nötig für dieses Feature');
    }
  });
  // Plattformen
  document.querySelectorAll('[data-platform]').forEach(el => {
    const plat = el.getAttribute('data-platform');
    if (!entitlements.enabled_platforms || !entitlements.enabled_platforms.includes(plat)) {
      el.classList.add('feature-locked');
      el.setAttribute('disabled', 'disabled');
      el.setAttribute('title', 'Upgrade nötig für diese Plattform');
    }
  });
}

// Optional: User-ID aus globalem Kontext/Sitzung holen
const userId = window.SHADOWSEEK_USER_ID || (window.session && window.session.user_id);
if (userId) {
  fetchEntitlements(userId, applyFeatureGating);
}

// CSS für Ausgrauen
const style = document.createElement('style');
style.innerHTML = `
  .feature-locked, .feature-locked * {
    filter: grayscale(0.8) brightness(0.7) !important;
    pointer-events: none !important;
    opacity: 0.7 !important;
    cursor: not-allowed !important;
    position: relative;
  }
`;
document.head.appendChild(style);
