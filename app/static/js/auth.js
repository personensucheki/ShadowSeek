// Modal-Handling für Login, Register, Forgot Password
function showModal(id) {
  document.getElementById(id).style.display = 'flex';
  document.body.style.overflow = 'hidden';
}
function hideModal(id) {
  document.getElementById(id).style.display = 'none';
  document.body.style.overflow = '';
}
function hideAllModals() {
  ['login-modal','register-modal','forgot-modal'].forEach(hideModal);
}
window.addEventListener('openLoginModal', () => {
  hideAllModals();
  showModal('login-modal');
});
window.addEventListener('openRegisterModal', () => {
  hideAllModals();
  showModal('register-modal');
});
document.addEventListener('DOMContentLoaded', function() {
  document.querySelectorAll('.modal-close').forEach(btn => {
    btn.addEventListener('click', () => hideAllModals());
  });
  document.querySelectorAll('.modal-overlay').forEach(overlay => {
    overlay.addEventListener('mousedown', function(e) {
      if (e.target === overlay) hideAllModals();
    });
  });
  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') hideAllModals();
  });
  // Forgot Password Link
  const forgotLink = document.getElementById('forgot-link');
  if (forgotLink) {
    forgotLink.addEventListener('click', function(e) {
      e.preventDefault();
      hideAllModals();
      showModal('forgot-modal');
    });
  }
});
