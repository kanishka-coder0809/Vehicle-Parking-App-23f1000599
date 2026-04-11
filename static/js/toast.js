// Modern Toast Notifications for FindMySpot
// Glassmorphism, animated, premium SaaS style
(function () {
  const ICONS = {
    success: '<i class="bi bi-check-circle-fill" style="color:#22c55e"></i>',
    error: '<i class="bi bi-x-octagon-fill" style="color:#ef4444"></i>',
    danger: '<i class="bi bi-x-octagon-fill" style="color:#ef4444"></i>',
    warning: '<i class="bi bi-exclamation-triangle-fill" style="color:#f59e0b"></i>',
    info: '<i class="bi bi-info-circle-fill" style="color:#3b82f6"></i>',
    default: '<i class="bi bi-bell-fill" style="color:#a855f7"></i>'
  };
  const TITLES = {
    success: 'Success',
    error: 'Error',
    danger: 'Error',
    warning: 'Warning',
    info: 'Info',
    default: 'Notice'
  };
  function getIcon(type) {
    return ICONS[type] || ICONS.default;
  }
  function getTitle(type) {
    return TITLES[type] || TITLES.default;
  }
  function ensureStack() {
    let stack = document.querySelector('.toast-stack');
    if (!stack) {
      stack = document.createElement('div');
      stack.className = 'toast-stack';
      document.body.appendChild(stack);
    }
    return stack;
  }
  function createToast({ type = 'info', title, message, duration = 4000 }) {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.setAttribute('role', 'status');
    toast.innerHTML = `
      <span class="toast-icon">${getIcon(type)}</span>
      <span class="toast-content">
        <span class="toast-title">${title || getTitle(type)}</span>
        <span class="toast-message">${message || ''}</span>
      </span>
      <button class="toast-close" aria-label="Close">&times;</button>
      <span class="toast-progress"></span>
    `;
    // Progress bar
    const progress = toast.querySelector('.toast-progress');
    progress.style.transition = `transform ${duration}ms linear`;
    setTimeout(() => {
      progress.style.transform = 'scaleX(0)';
    }, 30);
    // Dismiss logic
    let timer, remaining = duration, start;
    function close() {
      toast.classList.add('toast-exit');
      setTimeout(() => toast.remove(), 380);
    }
    function startTimer() {
      start = Date.now();
      timer = setTimeout(close, remaining);
    }
    function pauseTimer() {
      clearTimeout(timer);
      remaining -= Date.now() - start;
    }
    toast.addEventListener('mouseenter', () => {
      pauseTimer();
      toast.classList.add('toast-active');
      progress.style.transition = 'none';
    });
    toast.addEventListener('mouseleave', () => {
      progress.style.transition = `transform ${remaining}ms linear`;
      setTimeout(() => { progress.style.transform = 'scaleX(0)'; }, 30);
      toast.classList.remove('toast-active');
      startTimer();
    });
    toast.querySelector('.toast-close').onclick = close;
    // Optional: click to expand
    // Optional: swipe to dismiss (advanced)
    startTimer();
    return toast;
  }
  function showToast(opts) {
    const stack = ensureStack();
    const toast = createToast(opts);
    stack.appendChild(toast);
    // Animate in
    setTimeout(() => toast.classList.add('toast-in'), 10);
  }
  // Show toasts for Flask flash messages and migrate old alerts
  function migrateFlashes() {
    // Flask flash messages (new system)
    const toastMsgDiv = document.getElementById('toast-messages');
    if (toastMsgDiv) {
      Array.from(toastMsgDiv.children).forEach((el) => {
        const type = el.getAttribute('data-toast-category') || 'info';
        const msg = el.getAttribute('data-toast-message') || '';
        showToast({ type, message: msg, duration: 4000 });
      });
      toastMsgDiv.remove();
    }
    // Migrate any old Bootstrap alerts (shouldn't exist, but fallback)
    const alerts = Array.from(document.querySelectorAll('.alert[role="alert"]'));
    alerts.forEach((el) => {
      let type = 'info';
      el.classList.forEach((cls) => {
        if (cls.startsWith('alert-')) type = cls.replace('alert-', '');
      });
      const msg = el.textContent.trim();
      showToast({ type, message: msg, duration: Number(el.getAttribute('data-auto-dismiss')) || 4000 });
      el.remove();
    });
  }
  // Expose for global use
  window.showToast = showToast;
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', migrateFlashes);
  } else {
    migrateFlashes();
  }
})();
